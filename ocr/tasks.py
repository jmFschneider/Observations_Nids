"""
Tâches Celery pour le traitement OCR en production.
"""

import json
import logging
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

import redis
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from google import genai
from PIL import Image

from observations.json_rep.json_sanitizer import corriger_json, validate_json_structure
from ocr.models import TranscriptionOCR

logger = logging.getLogger('ocr')

P = ParamSpec("P")
R = TypeVar("R")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: int = 2,
    max_delay: int = 16,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Décorateur pour retry avec exponential backoff."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            delay = initial_delay
            last_error: Exception | None = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"⚠️ Tentative {attempt + 1}/{max_retries} échouée pour {func.__name__}: {str(e)}. "
                            f"Retry dans {delay}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)
                    else:
                        logger.error(
                            f"❌ Toutes les tentatives échouées pour {func.__name__} après {max_retries} essais"
                        )

            if last_error is None:
                raise RuntimeError(f"{func.__name__} a échoué sans exception")
            raise last_error

        return wrapper

    return decorator


@retry_with_backoff(max_retries=3, initial_delay=2)
def call_gemini_api_with_timeout(
    client: Any,
    model_name: str,
    prompt: str,
    image_path: str,
    timeout: int = 120,
) -> str:
    """Appel API Gemini avec timeout via ThreadPoolExecutor (future annulable)."""

    def api_call() -> str:
        image = Image.open(image_path)
        try:
            response = client.models.generate_content(model=model_name, contents=[prompt, image])
            return response.text.encode('utf-8').decode('utf-8')
        finally:
            image.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(api_call)
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError:
            future.cancel()
            raise TimeoutError(f"API call exceeded {timeout}s timeout") from None


class RedisRateLimiter:
    """
    Rate limiter distribué via Redis pour respecter le quota Gemini (60 RPM global).

    Utilise une fenêtre fixe par minute avec INCR atomique.
    En cas d'indisponibilité Redis, bascule en mode local avec avertissement.
    """

    KEY_PREFIX = 'ocr:rate_limiter'
    KEY_TTL = 70  # secondes (légèrement > 60 pour couvrir la transition de fenêtre)
    POLL_INTERVAL = 5  # secondes entre chaque vérification quand le quota est atteint

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.rpm = requests_per_minute
        self._redis: redis.Redis | None = None
        # Fallback local (mode dégradé)
        self._fallback_min_delay = 60.0 / requests_per_minute
        self._fallback_last_request: float = 0.0

        redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
        try:
            client = redis.Redis.from_url(
                redis_url, decode_responses=True, socket_connect_timeout=2
            )
            client.ping()
            self._redis = client
            logger.info(
                "RedisRateLimiter initialisé — mode distribué (%d RPM partagés entre workers)",
                self.rpm,
            )
        except Exception as exc:
            logger.warning(
                "Redis inaccessible pour le rate limiter (%s). "
                "Mode local activé : le quota Gemini n'est PAS partagé entre workers.",
                exc,
            )

    def wait_if_needed(self) -> None:
        """Acquiert un slot dans la fenêtre courante, attend si le quota global est atteint."""
        if self._redis is None:
            self._wait_local()
            return

        while True:
            minute_bucket = int(time.time() // 60)
            key = f"{self.KEY_PREFIX}:{minute_bucket}"
            try:
                count = cast(int, self._redis.incr(key))
                if count == 1:
                    self._redis.expire(key, self.KEY_TTL)
                if count <= self.rpm:
                    return
                # Quota atteint : calculer le temps restant dans la fenêtre courante
                seconds_to_next = 60 - (time.time() % 60)
                logger.info(
                    "Rate limit OCR atteint (%d/%d RPM) — attente %.1fs avant la prochaine fenêtre",
                    count,
                    self.rpm,
                    seconds_to_next,
                )
                time.sleep(min(seconds_to_next, self.POLL_INTERVAL))
            except redis.RedisError as exc:
                logger.warning(
                    "Erreur Redis dans le rate limiter (%s) — requête envoyée sans limitation pour ce slot.",
                    exc,
                )
                return

    def _wait_local(self) -> None:
        """Fallback : rate limiting local (non partagé, mode dégradé)."""
        now = time.time()
        elapsed = now - self._fallback_last_request
        if elapsed < self._fallback_min_delay:
            time.sleep(self._fallback_min_delay - elapsed)
        self._fallback_last_request = time.time()


def _charger_prompt_production(image_path: str) -> str:
    """Charge le prompt approprié (Ancienne vs Standard)."""
    # On se base sur le nom du répertoire parent pour détecter les anciennes fiches
    repertoire_parent = os.path.basename(os.path.dirname(image_path)).lower()

    if 'ancien' in repertoire_parent or 'anciennes' in repertoire_parent:
        prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'
    else:
        prompt_filename = 'prompt_gemini_transcription.txt'

    prompt_path = os.path.join(settings.BASE_DIR, 'observations', 'json_rep', prompt_filename)
    with open(prompt_path, encoding='utf-8') as f:
        return f.read()


@shared_task(bind=True, name='ocr.process_images_production', queue='ocr')
def process_images_production_task(self, image_paths_relatifs: list[str]):
    """
    Tâche de production pour traiter un lot d'images.
    Utilise gemini-3-flash par défaut.
    """
    logger.info(
        "OCR: tâche démarrée (task_id=%s) — %d image(s) à traiter",
        self.request.id,
        len(image_paths_relatifs),
    )
    media_root = str(settings.MEDIA_ROOT)
    api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
    if not api_key:
        return {'status': 'ERROR', 'error': "Clé API Gemini non configurée"}

    client = genai.Client(api_key=api_key)
    rate_limiter = RedisRateLimiter(60)

    total = len(image_paths_relatifs)
    success_count = 0
    ignored_count = 0
    errors: list[dict] = []
    logs: list[dict] = []

    def log_progress(message: str, level: str = 'info') -> None:
        """Log un message et met à jour l'état Celery en une seule écriture Redis."""
        timestamp = timezone.now().strftime('%H:%M:%S')
        logs.append({'timestamp': timestamp, 'message': message, 'level': level})
        self.update_state(
            state='PROGRESS',
            meta={
                'processed': index + 1,
                'total': total,
                'percent': int(((index + 1) / total) * 100),
                'logs': logs[-100:],
            },
        )

    for index, img_rel_path in enumerate(image_paths_relatifs):
        basename = os.path.basename(img_rel_path)

        # Déduplication : ignorer les images déjà transcrites avec succès
        if TranscriptionOCR.objects.filter(chemin_image=img_rel_path, statut='succes').exists():
            log_progress(f"⏭️ [{index + 1}/{total}] {basename} déjà transcrit, ignoré", 'warning')
            ignored_count += 1
            continue

        img_full_path = os.path.join(media_root, img_rel_path)
        start_time = time.time()

        # Construction du chemin de sortie
        # media/transcription_results/[chemin_image]/gemini_3_flash/
        img_dir_rel = os.path.dirname(img_rel_path)
        results_dir_rel = os.path.join('transcription_results', img_dir_rel, 'gemini_3_flash')
        results_dir_full = os.path.join(media_root, results_dir_rel)
        os.makedirs(results_dir_full, exist_ok=True)

        json_filename = f"{os.path.splitext(os.path.basename(img_rel_path))[0]}_result.json"
        json_full_path = os.path.join(results_dir_full, json_filename)
        json_rel_path = os.path.join(results_dir_rel, json_filename)

        log_progress(f"🖼️ [{index + 1}/{total}] Traitement de {basename}")

        try:
            rate_limiter.wait_if_needed()
            prompt = _charger_prompt_production(img_full_path)

            text_response = call_gemini_api_with_timeout(
                client=client,
                model_name='gemini-3-flash-preview',
                prompt=prompt,
                image_path=img_full_path,
            )

            # Nettoyage Markdown
            if text_response.startswith("```json"):
                text_response = text_response[7:].split("```")[0].strip()

            json_data = json.loads(text_response)

            # Validation structurelle + normalisation (toujours appliquée)
            structure_errors = validate_json_structure(json_data)
            if structure_errors:
                logger.warning(
                    f"Structure JSON non conforme pour {img_rel_path}: {structure_errors}"
                )
            json_data = corriger_json(json_data)

            # Sauvegarde
            with open(json_full_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            duration = time.time() - start_time

            # Tracking BDD
            TranscriptionOCR.objects.create(
                chemin_json=json_rel_path,
                chemin_image=img_rel_path,
                modele_ocr='gemini_3_flash',
                statut='succes',
                temps_traitement_secondes=duration,
            )

            success_count += 1
            log_progress(f"✅ {basename} traité avec succès", 'success')

        except Exception as e:
            logger.error(f"Erreur OCR sur {img_rel_path}: {str(e)}")
            TranscriptionOCR.objects.create(
                chemin_image=img_rel_path, chemin_json='', statut='erreur', erreur_message=str(e)
            )
            errors.append({'file': img_rel_path, 'error': str(e)})
            log_progress(f"❌ Erreur sur {basename}", 'error')

    return {
        'status': 'SUCCESS',
        'total': total,
        'success': success_count,
        'ignored': ignored_count,
        'errors': errors,
    }
