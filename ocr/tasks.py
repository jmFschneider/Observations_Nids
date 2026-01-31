# pilot/tasks.py
"""
Le text ci dessous n'est plus correct. Nous avons passsé toutes les fonctionnalités OCR dans ce module.
Tâches Celery spécifiques pour l'app pilot (optimisation OCR).
Ces tâches seront supprimées avec l'app une fois les tests terminés.
"""

import copy
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from celery import shared_task
from celery.result import AsyncResult
from django.conf import settings
from django.utils import timezone
from google import genai
from PIL import Image

from observations.json_rep.json_sanitizer import corriger_json, validate_json_structure
from observations.models import FicheObservation
from ocr.models import TranscriptionOCR
from ocr.services.comparateur import OCRComparator
from ocr.services.fichier_matcher import FichierMatcher

logger = logging.getLogger('ocr')


# ========================================
# UTILITAIRES DE ROBUSTESSE API
# ========================================


P = ParamSpec("P")
R = TypeVar("R")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: int = 2,
    max_delay: int = 16,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Décorateur pour retry avec exponential backoff.

    Délais progressifs : 2s → 4s → 8s → 16s (max)

    Args:
        max_retries: Nombre maximum de tentatives (défaut: 3)
        initial_delay: Délai initial en secondes (défaut: 2)
        max_delay: Délai maximum en secondes (défaut: 16)

    Returns:
        Décorateur de fonction

    Example:
        @retry_with_backoff(max_retries=3)
        def call_api():
            # Code qui peut échouer
    """

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
                        delay = min(delay * 2, max_delay)  # Exponential backoff
                    else:
                        logger.error(
                            f"❌ Toutes les tentatives échouées pour {func.__name__} après {max_retries} essais"
                        )

            # last_error ne peut pas être None ici car on sort de la boucle seulement après une exception
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
    """
    Appel API Gemini avec timeout et retry automatique.

    Args:
        client: Client Google GenAI initialisé
        model_name: Nom du modèle Gemini (ex: 'gemini-2.0-flash')
        prompt: Texte du prompt
        image_path: Chemin vers l'image
        timeout: Timeout en secondes (défaut: 120s = 2 minutes)

    Returns:
        Texte de la réponse Gemini (nettoyé UTF-8)

    Raises:
        TimeoutError: Si l'appel dépasse le timeout
        Exception: Autres erreurs API
    """
    result: list[str | None] = [None]
    exception: list[Exception | None] = [None]

    def api_call():
        """Fonction interne pour l'appel API threadé"""
        try:
            image = Image.open(image_path)
            try:
                response = client.models.generate_content(
                    model=model_name, contents=[prompt, image]
                )
                result[0] = response.text.encode('utf-8').decode('utf-8')
            finally:
                image.close()  # Libérer la mémoire
        except Exception as e:
            exception[0] = e

    # Lancer l'appel API dans un thread avec timeout
    thread = threading.Thread(target=api_call)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    # Vérifier le résultat
    if thread.is_alive():
        logger.error(f"⏱️ Timeout dépassé ({timeout}s) pour l'appel API")
        raise TimeoutError(f"API call exceeded {timeout}s timeout")

    if exception[0]:
        raise exception[0]

    if result[0] is None:
        raise ValueError("API call returned None")

    return result[0]


class RateLimiter:
    """
    Gestionnaire de rate limiting pour éviter de dépasser les quotas API.

    Google Gemini API a une limite de ~60 requêtes par minute.
    """

    def __init__(self, requests_per_minute=60):
        """
        Args:
            requests_per_minute: Nombre maximum de requêtes par minute (défaut: 60)
        """
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute  # Délai minimum entre requêtes
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """
        Attend si nécessaire pour respecter le rate limit.

        Cette méthode bloque l'exécution si le délai minimum n'est pas écoulé
        depuis la dernière requête.
        """
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_delay:
            delay = self.min_delay - elapsed
            logger.debug(f"⏱️ Rate limit: attente de {delay:.2f}s")
            time.sleep(delay)

        self.last_request_time = time.time()


# ========================================
# UTILITAIRES MÉTIER
# ========================================


def _extraire_nom_base_fichier(chemin_image: str) -> str:
    """
    Extrait le nom de base d'un fichier image (sans extension et sans suffixes _optimisee, _brute, etc.)

    Exemples:
        "fiche_123_optimisee.jpg" -> "fiche_123"
        "observation_456.jpg" -> "observation_456"
    """
    nom_fichier = os.path.splitext(os.path.basename(chemin_image))[0]

    # Retirer les suffixes courants (_optimisee, _brute, _result, etc.)
    suffixes_a_retirer = ['_optimisee', '_brute', '_result', '_raw', '_traitement']
    for suffixe in suffixes_a_retirer:
        if nom_fichier.endswith(suffixe):
            nom_fichier = nom_fichier[: -len(suffixe)]

    return nom_fichier


def _trouver_fiche_correspondante(nom_base_image: str) -> FicheObservation | None:
    """
    Trouve la FicheObservation correspondant à un nom de fichier image.

    Args:
        nom_base_image: Nom de base du fichier (ex: "fiche_123")

    Returns:
        FicheObservation trouvée ou None si non trouvée ou ambiguë
    """
    # Rechercher dans chemin_image
    fiches = FicheObservation.objects.filter(chemin_image__icontains=nom_base_image)

    if fiches.count() == 1:
        return fiches.first()
    elif fiches.count() > 1:
        logger.warning(
            f"Plusieurs fiches trouvées pour '{nom_base_image}': {fiches.count()} résultats. "
            "Correspondance ambiguë, aucune fiche ne sera liée."
        )
        return None
    else:
        logger.warning(f"Aucune fiche trouvée pour '{nom_base_image}'")
        return None


def _determiner_type_image(chemin_relatif: str) -> str:
    """
    Détermine le type d'image à partir du chemin relatif.

    Args:
        chemin_relatif: Chemin relatif du répertoire (ex: "Ancienne_fiche/Sans_traitement")

    Returns:
        'brute' ou 'optimisee'
    """
    if 'Sans_traitement' in chemin_relatif or 'sans_traitement' in chemin_relatif.lower():
        return 'brute'
    else:
        # Traitement_1, Traitement_2, etc. sont considérés comme optimisés
        return 'optimisee'


def _determiner_type_fiche_et_traitement(chemin_relatif: str) -> tuple[str, str]:
    """
    Extrait le type de fiche et le type de traitement du chemin.

    Args:
        chemin_relatif: Chemin relatif (ex: "Ancienne_fiche/Traitement_1")

    Returns:
        Tuple (type_fiche, type_traitement)
        Ex: ("Ancienne_fiche", "Traitement_1")
    """
    parts = chemin_relatif.split(os.sep)

    type_fiche = "Inconnu"
    type_traitement = "Inconnu"

    # Le type de fiche est généralement le premier niveau
    if len(parts) >= 1:
        type_fiche = parts[0]

    # Le type de traitement est généralement le second niveau
    if len(parts) >= 2:
        type_traitement = parts[1]

    return type_fiche, type_traitement


def _charger_prompt_selon_type_fiche(chemin_relatif: str) -> str:
    """
    Charge le bon prompt selon le type de fiche détecté dans le chemin.

    Règle de détection :
    - Si le chemin contient "ancien" ou "Ancien" → prompt anciennes fiches
    - Sinon → prompt standard

    Args:
        chemin_relatif: Chemin du répertoire (ex: "Ancienne_fiche/Traitement_1")

    Returns:
        Contenu du prompt en string

    Raises:
        ValueError: Si le prompt n'est pas trouvé

    Example:
        >>> _charger_prompt_selon_type_fiche("Ancienne_fiche/Sans_traitement")
        # Retourne le contenu de prompt_gemini_transcription_Ancienne_Fiche.txt
    """
    type_fiche, _ = _determiner_type_fiche_et_traitement(chemin_relatif)

    # Déterminer quel prompt utiliser (insensible à la casse)
    # Recherche "ancien" n'importe où dans le chemin complet
    if 'ancien' in chemin_relatif.lower():
        prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'
        logger.info(f"📄 Prompt ANCIENNES FICHES sélectionné pour: {chemin_relatif}")
    else:
        prompt_filename = 'prompt_gemini_transcription.txt'
        logger.info(f"📄 Prompt STANDARD sélectionné pour: {chemin_relatif}")

    prompt_path = os.path.join(settings.BASE_DIR, 'observations', 'json_rep', prompt_filename)

    try:
        with open(prompt_path, encoding='utf-8') as f:
            prompt_content = f.read()
            logger.debug(f"✓ Prompt chargé: {prompt_filename} ({len(prompt_content)} chars)")
            return prompt_content
    except FileNotFoundError as e:
        logger.error(f"❌ Prompt introuvable: {prompt_path}")
        raise ValueError(f"Prompt {prompt_filename} non trouvé dans observations/json_rep/") from e


def _log_progress(task_self, message, level='info', details=None):
    """
    Ajoute un message au log de progression visible en temps réel.

    Args:
        task_self: Instance de la tâche Celery (self)
        message: Message à logger
        level: Niveau du log ('info', 'success', 'warning', 'error')
        details: Détails optionnels (dict)
    """
    timestamp = timezone.now().strftime('%H:%M:%S')

    # Construire l'entrée de log
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level,
    }
    if details:
        log_entry['details'] = details

    # Récupérer la meta actuelle de la tâche via AsyncResult
    try:
        result = AsyncResult(task_self.request.id)
        current_meta = result.info if result.info and isinstance(result.info, dict) else {}
    except Exception:
        current_meta = {}

    # Ajouter le nouveau log
    logs = current_meta.get('logs', [])
    logs.append(log_entry)

    # Limiter à 150 dernières entrées pour ne pas surcharger Redis
    if len(logs) > 150:
        logs = logs[-150:]

    # Mettre à jour la meta avec les logs (préserve les autres champs comme processed, total, etc.)
    current_meta['logs'] = logs

    # Utiliser update_state pour mettre à jour Redis
    task_self.update_state(state='PROGRESS', meta=current_meta)

    # Logger aussi dans les logs serveur pour historique
    log_method = getattr(logger, level if level in ['info', 'warning', 'error'] else 'info')
    log_method(f"[{timestamp}] {message}")


@shared_task(bind=True, name='ocr.process_batch_transcription')
def process_batch_transcription_task(self, directories: list[dict], modeles_ocr: list[str]):
    """
    Tâche Celery pour traiter plusieurs répertoires en batch avec plusieurs modèles OCR.

    Cette tâche est spécifique à l'app pilot pour l'évaluation OCR.
    Elle traite chaque répertoire avec chaque modèle sélectionné (exécution séquentielle),
    génère les transcriptions JSON, et crée automatiquement les entrées TranscriptionOCR
    pour comparaison avec la vérité terrain.

    **Mode pilote uniquement** : Cette tâche génère les fichiers JSON pour évaluation.
    L'importation en base de données se fait depuis l'app observations.

    Args:
        directories: Liste de dictionnaires avec 'path' (chemin relatif) et 'name' (nom du répertoire)
        modeles_ocr: Liste des noms de modèles OCR à utiliser (ex: ["gemini_3_flash", "gemini_3_pro"])

    Returns:
        dict: Résultats globaux du traitement batch
    """
    media_root = str(settings.MEDIA_ROOT)

    # Mapper les noms de modèles vers les identifiants Gemini API
    modeles_mapping = {
        'gemini_3_flash': 'gemini-3-flash-preview',
        'gemini_3_pro': 'gemini-3-pro-preview',
        'gemini_2.5_pro': 'gemini-2.5-pro',
        'gemini_2.5_flash_lite': 'gemini-2.5-flash-lite',
    }

    logger.info(
        f"Début du traitement batch: {len(directories)} répertoire(s), "
        f"{len(modeles_ocr)} modèle(s) ({', '.join(modeles_ocr)})"
    )

    # Configuration API Gemini
    api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
    if not api_key:
        logger.error("Clé API Gemini non configurée")
        return {'status': 'ERROR', 'error': "Clé API Gemini non configurée"}

    client = genai.Client(api_key=api_key)

    # Log de démarrage
    _log_progress(
        self,
        f"🚀 Démarrage du traitement batch: {len(directories)} répertoire(s), {len(modeles_ocr)} modèle(s)",
        'info',
    )

    # Résultats globaux
    all_results = []
    total_success = 0
    total_errors = 0
    start_time_global = time.time()

    # Calculer le nombre total d'images par répertoire (pour la progression)
    images_par_repertoire = 0
    for dir_info in directories:
        dir_path = os.path.join(media_root, dir_info['path'])
        if os.path.exists(dir_path):
            images = [
                f
                for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))
                and f.lower().endswith(('.jpg', '.jpeg'))
            ]
            images_par_repertoire += len(images)

    # Total d'images = images par répertoire × nombre de modèles
    total_images = images_par_repertoire * len(modeles_ocr)

    if images_par_repertoire == 0:
        logger.warning("Aucune image trouvée dans les répertoires sélectionnés")
        return {
            'status': 'SUCCESS',
            'results': [],
            'modeles_ocr': modeles_ocr,
            'total_directories': len(directories),
            'total_images': 0,
            'total_success': 0,
            'total_errors': 0,
            'duration': 0,
        }

    processed_count = 0

    # Traiter avec chaque modèle OCR
    for modele_index, modele_ocr in enumerate(modeles_ocr):
        modele_api = modeles_mapping.get(modele_ocr, 'gemini-3-flash-preview')

        logger.info(
            f"═══ Traitement avec modèle {modele_index + 1}/{len(modeles_ocr)}: "
            f"{modele_ocr} ({modele_api}) ═══"
        )

        # Log du démarrage du modèle
        _log_progress(
            self,
            f"═══ Modèle {modele_index + 1}/{len(modeles_ocr)}: {modele_ocr} ({modele_api}) ═══",
            'info',
        )

        # Créer le rate limiter pour ce modèle (60 req/min = limite Google Gemini)
        rate_limiter = RateLimiter(requests_per_minute=60)

        # Traiter chaque répertoire avec ce modèle
        for dir_index, dir_info in enumerate(directories):
            dir_path_relatif = dir_info['path']
            dir_path_complet = os.path.join(media_root, dir_path_relatif)

            logger.info(
                f"  → Répertoire {dir_index + 1}/{len(directories)}: {dir_path_relatif} "
                f"(modèle: {modele_ocr})"
            )

            # Log du démarrage du répertoire
            _log_progress(
                self, f"→ Répertoire {dir_index + 1}/{len(directories)}: {dir_path_relatif}", 'info'
            )

            if not os.path.exists(dir_path_complet):
                logger.error(f"Le répertoire {dir_path_complet} n'existe pas")
                all_results.append(
                    {
                        'directory': dir_path_relatif,
                        'modele_ocr': modele_ocr,
                        'status': 'error',
                        'error': "Répertoire inexistant",
                    }
                )
                continue

            # Créer le répertoire de résultats (inclure le modèle dans le chemin)
            results_dir = os.path.join(
                media_root, 'transcription_results', dir_path_relatif, modele_ocr
            )
            os.makedirs(results_dir, exist_ok=True)

            # Récupérer les métadonnées du répertoire
            type_fiche, type_traitement = _determiner_type_fiche_et_traitement(dir_path_relatif)
            type_image = _determiner_type_image(dir_path_relatif)

            # Charger le prompt approprié selon le type de fiche
            try:
                prompt = _charger_prompt_selon_type_fiche(dir_path_relatif)
                # Log de sélection du prompt
                prompt_type = "ANCIENNES FICHES" if 'ancien' in type_fiche.lower() else "STANDARD"
                _log_progress(
                    self, f"📄 Prompt {prompt_type} sélectionné pour {type_fiche}", 'success'
                )
            except ValueError as e:
                logger.error(f"❌ Erreur chargement prompt pour {dir_path_relatif}: {e}")
                _log_progress(self, f"❌ Erreur chargement prompt: {str(e)}", 'error')
                all_results.append(
                    {
                        'directory': dir_path_relatif,
                        'modele_ocr': modele_ocr,
                        'status': 'error',
                        'error': f"Prompt introuvable: {str(e)}",
                        'files': [],
                    }
                )
                continue  # Passer au répertoire suivant

            # Récupérer les fichiers images
            image_files = [
                f
                for f in os.listdir(dir_path_complet)
                if os.path.isfile(os.path.join(dir_path_complet, f))
                and f.lower().endswith(('.jpg', '.jpeg'))
            ]

            if not image_files:
                logger.warning(f"Aucune image dans {dir_path_relatif}")
                all_results.append(
                    {
                        'directory': dir_path_relatif,
                        'modele_ocr': modele_ocr,
                        'status': 'success',
                        'images': [],
                    }
                )
                continue

            dir_results = []

            # Traiter chaque image
            for img_file in image_files:
                file_start = time.time()
                img_path_complet = os.path.join(dir_path_complet, img_file)
                img_path_relatif = os.path.join(dir_path_relatif, img_file)

                logger.info(
                    f"Traitement de {img_path_relatif} ({processed_count + 1}/{total_images})"
                )

                # Log du début du traitement
                _log_progress(
                    self, f"🖼️ Traitement {img_file} ({processed_count + 1}/{total_images})", 'info'
                )

                # Mise à jour de la progression
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'processed': processed_count,
                        'total': total_images,
                        'current_file': img_file,
                        'current_directory': dir_path_relatif,
                        'current_model': modele_ocr,
                        'percent': int((processed_count / total_images) * 100),
                    },
                )

                try:
                    # Respecter le rate limiting (1 req/sec max)
                    rate_limiter.wait_if_needed()

                    # Traitement de l'image avec le modèle OCR (avec retry, timeout)
                    api_start = time.time()
                    text_response = call_gemini_api_with_timeout(
                        client=client,
                        model_name=modele_api,
                        prompt=prompt,
                        image_path=img_path_complet,
                        timeout=120,  # 2 minutes max par image
                    )
                    api_duration = time.time() - api_start

                    # Log de succès de l'API
                    _log_progress(self, f"✓ API réussie ({api_duration:.1f}s)", 'success')

                    # Nettoyage des marqueurs markdown
                    if text_response.startswith("```json"):
                        text_response = text_response[7:].strip()
                        if text_response.endswith("```"):
                            text_response = text_response[:-3].strip()

                    # Parsing JSON
                    try:
                        json_data = json.loads(text_response)
                        logger.debug(f"JSON correctement parsé pour {img_file}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Erreur de décodage JSON pour {img_file}: {str(e)}")
                        raise ValueError(f"Réponse non JSON: {text_response[:100]}...") from e

                    if json_data:
                        # Validation et correction
                        erreurs = validate_json_structure(json_data)
                        if erreurs:
                            logger.warning(
                                f"Structure JSON invalide pour {img_file}, correction en cours. Erreurs: {erreurs}"
                            )
                            _log_progress(self, "⚠️ JSON invalide, correction en cours", 'warning')
                            json_data_raw = copy.deepcopy(json_data)
                            json_data = corriger_json(json_data_raw)

                            # Enregistrement du JSON brut
                            raw_path = os.path.join(
                                results_dir, f"{os.path.splitext(img_file)[0]}_raw.json"
                            )
                            with open(raw_path, 'w', encoding='utf-8') as f:
                                json.dump(json_data_raw, f, indent=2, ensure_ascii=False)

                            _log_progress(
                                self, "✓ JSON corrigé et sauvegardé (raw + corrigé)", 'success'
                            )
                        else:
                            _log_progress(self, "✓ JSON valide", 'success')

                        # Enregistrement du JSON final
                        json_filename = f"{os.path.splitext(img_file)[0]}_result.json"
                        json_path_complet = os.path.join(results_dir, json_filename)
                        json_path_relatif = os.path.join(
                            'transcription_results', dir_path_relatif, modele_ocr, json_filename
                        )

                        with open(json_path_complet, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)

                        _log_progress(self, f"💾 JSON sauvegardé: {json_filename}", 'success')

                        duration = round(time.time() - file_start, 2)
                        logger.info(f"Transcription réussie pour {img_file}, durée: {duration}s")

                        # Créer l'entrée TranscriptionOCR (mode pilote: JSON uniquement)
                        nom_base = _extraire_nom_base_fichier(img_path_relatif)

                        # Chercher une fiche correspondante pour la lier (utile pour l'évaluation)
                        fiche = _trouver_fiche_correspondante(nom_base)

                        transcription_ocr = TranscriptionOCR.objects.create(
                            fiche=fiche,  # Peut être None si pas de correspondance
                            chemin_json=json_path_relatif,
                            chemin_image=img_path_relatif,
                            type_image=type_image,
                            modele_ocr=modele_ocr,
                            temps_traitement_secondes=duration,
                            statut_evaluation='non_evaluee',
                        )

                        logger.info(
                            f"TranscriptionOCR créée (ID: {transcription_ocr.id}) pour {img_file}"
                            + (f" - Liée à fiche {fiche.pk}" if fiche else " - Aucune fiche liée")
                        )

                        # Log de création de TranscriptionOCR
                        fiche_info = f" (liée à fiche {fiche.pk})" if fiche else " (sans fiche)"
                        _log_progress(
                            self,
                            f"✓ TranscriptionOCR créée (ID: {transcription_ocr.id}){fiche_info}",
                            'success',
                        )

                        file_result = {
                            'filename': img_file,
                            'status': 'success',
                            'json_path': json_path_relatif,
                            'duration': duration,
                            'transcription_id': transcription_ocr.id,
                            'fiche_linked': fiche.pk if fiche else None,
                        }
                        total_success += 1
                    else:
                        raise ValueError("Données JSON vides ou invalides")

                except TimeoutError as e:
                    logger.error(f"⏱️ Timeout pour {img_file} après 120s (et {3} retries): {str(e)}")
                    _log_progress(
                        self, f"❌ Timeout après 120s (3 retries) pour {img_file}", 'error'
                    )
                    file_result = {
                        'filename': img_file,
                        'status': 'timeout',
                        'error': "Timeout après 120s (3 retries)",
                        'duration': round(time.time() - file_start, 2),
                    }
                    total_errors += 1

                except Exception as e:
                    logger.error(f"❌ Erreur lors du traitement de {img_file}: {str(e)}")
                    _log_progress(self, f"❌ Erreur: {str(e)[:100]}", 'error')
                    file_result = {
                        'filename': img_file,
                        'status': 'error',
                        'error': str(e),
                        'duration': round(time.time() - file_start, 2),
                    }
                    total_errors += 1

                dir_results.append(file_result)
                processed_count += 1

            all_results.append(
                {
                    'directory': dir_path_relatif,
                    'modele_ocr': modele_ocr,
                    'status': 'success',
                    'images': dir_results,
                    'type_fiche': type_fiche,
                    'type_traitement': type_traitement,
                    'type_image': type_image,
                }
            )

    # Résultats finaux
    duration_total = round(time.time() - start_time_global, 2)

    final_result = {
        'status': 'SUCCESS',
        'results': all_results,
        'modeles_ocr': modeles_ocr,
        'total_directories': len(directories),
        'total_models': len(modeles_ocr),
        'total_images': total_images,
        'total_success': total_success,
        'total_errors': total_errors,
        'success_rate': round((total_success / total_images) * 100, 1) if total_images > 0 else 0,
        'duration': duration_total,
    }

    logger.info("═══ Traitement batch terminé ═══")
    logger.info(
        f"  {len(modeles_ocr)} modèle(s) × {len(directories)} répertoire(s) = {total_images} images"
    )
    logger.info(
        f"  {total_success} succès / {total_errors} erreurs ({final_result['success_rate']}%)"
    )
    logger.info(f"  Durée totale: {duration_total}s")

    return final_result


@shared_task(bind=True, name="ocr.comparer_ocr_fichier")
def comparer_ocr_fichier_task(  # noqa: PLR0911
    self, chemin_json: str, options: dict[str, Any]
) -> dict[str, Any]:
    """
    Compare un fichier JSON OCR avec la fiche BDD correspondante.

    Args:
        chemin_json (str): chemin relatif ou absolu vers le fichier JSON OCR
        options (dict): {
            "force": bool,
            "dry_run": bool
        }
    """
    options_local = options or {}
    force = bool(options_local.get("force", False))
    dry_run = bool(options_local.get("dry_run", False))

    logger.info("Démarrage comparaison OCR pour %s", chemin_json)

    if not isinstance(chemin_json, str) or not chemin_json.strip():
        logger.error("chemin_json invalide: %s", chemin_json)
        return {"chemin_json": chemin_json, "statut": "ERREUR", "score_global": None}

    chemin_json_nettoye = chemin_json.strip()
    chemin_fichier = (
        chemin_json_nettoye
        if os.path.isabs(chemin_json_nettoye)
        else os.path.join(str(settings.MEDIA_ROOT), chemin_json_nettoye)
    )

    try:
        with open(chemin_fichier, encoding="utf-8") as handle:
            json_ocr = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Erreur chargement JSON %s: %s", chemin_fichier, exc)
        return {"chemin_json": chemin_json, "statut": "ERREUR", "score_global": None}

    try:
        fiche, metadata = FichierMatcher.trouver_fiche_depuis_json(chemin_json_nettoye)
    except Exception:
        logger.exception("Erreur match fiche pour %s", chemin_json_nettoye)
        return {"chemin_json": chemin_json, "statut": "ERREUR", "score_global": None}

    chemin_image_attendu = metadata.get("chemin_image_attendu", "")
    total_fiches = FicheObservation.objects.filter(chemin_image=chemin_image_attendu).count()

    if total_fiches == 0:
        logger.warning(
            "Fiche introuvable pour %s (chemin_image=%s)",
            chemin_json_nettoye,
            chemin_image_attendu,
        )
        if not dry_run:
            _transcription_ocr, created = TranscriptionOCR.objects.get_or_create(
                fiche=None,
                chemin_json=chemin_json_nettoye,
                modele_ocr=metadata.get("modele_ocr", ""),
                defaults={
                    "chemin_image": chemin_image_attendu,
                    "type_image": metadata.get("type_image", ""),
                    "statut_evaluation": "FICHE_INTROUVABLE",
                },
            )
            if not created:
                _transcription_ocr.chemin_image = chemin_image_attendu
                _transcription_ocr.type_image = metadata.get("type_image", "")
                _transcription_ocr.statut_evaluation = "FICHE_INTROUVABLE"
                _transcription_ocr.save(
                    update_fields=["chemin_image", "type_image", "statut_evaluation"]
                )
        return {"chemin_json": chemin_json, "statut": "ERREUR", "score_global": None}

    if total_fiches > 1:
        logger.warning(
            "Correspondance ambiguë pour %s (chemin_image=%s)",
            chemin_json_nettoye,
            chemin_image_attendu,
        )
        if not dry_run:
            _transcription_ocr, created = TranscriptionOCR.objects.get_or_create(
                fiche=None,
                chemin_json=chemin_json_nettoye,
                modele_ocr=metadata.get("modele_ocr", ""),
                defaults={
                    "chemin_image": chemin_image_attendu,
                    "type_image": metadata.get("type_image", ""),
                    "statut_evaluation": "AMBIGU",
                },
            )
            if not created:
                _transcription_ocr.chemin_image = chemin_image_attendu
                _transcription_ocr.type_image = metadata.get("type_image", "")
                _transcription_ocr.statut_evaluation = "AMBIGU"
                _transcription_ocr.save(
                    update_fields=["chemin_image", "type_image", "statut_evaluation"]
                )
        return {"chemin_json": chemin_json, "statut": "AMBIGU", "score_global": None}

    if fiche is None:
        logger.error(
            "Fiche non instanciée pour %s (chemin_image=%s)",
            chemin_json_nettoye,
            chemin_image_attendu,
        )
        return {"chemin_json": chemin_json, "statut": "ERREUR", "score_global": None}

    transcription_ocr: TranscriptionOCR | None = TranscriptionOCR.objects.filter(
        fiche=fiche,
        chemin_json=chemin_json_nettoye,
        modele_ocr=metadata.get("modele_ocr", ""),
    ).first()

    if transcription_ocr and not force and transcription_ocr.statut_evaluation == "evaluee":
        logger.info("Comparaison déjà évaluée pour %s", chemin_json_nettoye)
        return {
            "chemin_json": chemin_json,
            "statut": "OK",
            "score_global": transcription_ocr.score_global,
        }

    if transcription_ocr is None and not dry_run:
        transcription_ocr = TranscriptionOCR.objects.create(
            fiche=fiche,
            chemin_json=chemin_json_nettoye,
            chemin_image=chemin_image_attendu,
            type_image=metadata.get("type_image", ""),
            modele_ocr=metadata.get("modele_ocr", ""),
            statut_evaluation="en_cours",
        )

    try:
        comparateur = OCRComparator(fiche, json_ocr)
        resultats = comparateur.comparer()
        score_global = resultats.get("score_global")
    except Exception:
        logger.exception("Erreur comparaison OCR pour %s", chemin_json_nettoye)
        if transcription_ocr and not dry_run:
            transcription_ocr.statut_evaluation = "erreur"
            transcription_ocr.save(update_fields=["statut_evaluation"])
        return {"chemin_json": chemin_json, "statut": "ERREUR", "score_global": None}

    if dry_run:
        logger.info("Dry-run actif, aucun enregistrement pour %s", chemin_json_nettoye)
        return {"chemin_json": chemin_json, "statut": "OK", "score_global": score_global}

    if transcription_ocr is None:
        transcription_ocr = TranscriptionOCR(
            fiche=fiche,
            chemin_json=chemin_json_nettoye,
            chemin_image=chemin_image_attendu,
            type_image=metadata.get("type_image", ""),
            modele_ocr=metadata.get("modele_ocr", ""),
        )

    transcription_ocr.chemin_image = chemin_image_attendu
    transcription_ocr.type_image = metadata.get("type_image", "")
    transcription_ocr.statut_evaluation = "evaluee"
    transcription_ocr.date_evaluation = timezone.now()
    transcription_ocr.score_global = score_global
    transcription_ocr.nombre_champs_total = resultats.get("nombre_champs_total")
    transcription_ocr.nombre_champs_corrects = resultats.get("nombre_champs_corrects")
    transcription_ocr.nombre_erreurs_texte = resultats.get("nombre_erreurs_texte", 0)
    transcription_ocr.nombre_erreurs_nombres = resultats.get("nombre_erreurs_nombres", 0)
    transcription_ocr.nombre_erreurs_dates = resultats.get("nombre_erreurs_dates", 0)
    transcription_ocr.details_comparaison = resultats.get("details_comparaison")
    transcription_ocr.save()

    logger.info("Comparaison OCR terminée pour %s", chemin_json_nettoye)
    return {"chemin_json": chemin_json, "statut": "OK", "score_global": score_global}
