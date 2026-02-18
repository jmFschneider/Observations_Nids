"""
Tâches Celery pour le traitement OCR en production.
"""

import json
import logging
import os
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

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
    """Appel API Gemini avec timeout et retry automatique."""
    result: list[str | None] = [None]
    exception: list[Exception | None] = [None]

    def api_call():
        try:
            image = Image.open(image_path)
            try:
                response = client.models.generate_content(
                    model=model_name, contents=[prompt, image]
                )
                result[0] = response.text.encode('utf-8').decode('utf-8')
            finally:
                image.close()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=api_call)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"API call exceeded {timeout}s timeout")

    if exception[0]:
        raise exception[0]

    if result[0] is None:
        raise ValueError("API call returned None")

    return result[0]


class RateLimiter:
    """Gestionnaire de rate limiting pour Gemini API (60 RPM)."""

    def __init__(self, requests_per_minute=60):
        self.min_delay = 60.0 / requests_per_minute
        self.last_request_time = 0.0

    def wait_if_needed(self):
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()


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


@shared_task(bind=True, name='ocr.process_images_production')
def process_images_production_task(self, image_paths_relatifs: list[str]):
    """
    Tâche de production pour traiter un lot d'images.
    Utilise gemini-3-flash par défaut.
    """
    media_root = str(settings.MEDIA_ROOT)
    api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
    if not api_key:
        return {'status': 'ERROR', 'error': "Clé API Gemini non configurée"}

    client = genai.Client(api_key=api_key)
    rate_limiter = RateLimiter(60)

    total = len(image_paths_relatifs)
    success_count = 0
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

        log_progress(f"🖼️ [{index + 1}/{total}] Traitement de {os.path.basename(img_rel_path)}")

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
            log_progress(f"✅ {os.path.basename(img_rel_path)} traité avec succès", 'success')

        except Exception as e:
            logger.error(f"Erreur OCR sur {img_rel_path}: {str(e)}")
            TranscriptionOCR.objects.create(
                chemin_image=img_rel_path, chemin_json='', statut='erreur', erreur_message=str(e)
            )
            errors.append({'file': img_rel_path, 'error': str(e)})
            log_progress(f"❌ Erreur sur {os.path.basename(img_rel_path)}", 'error')

    return {'status': 'SUCCESS', 'total': total, 'success': success_count, 'errors': errors}
