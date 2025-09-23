# observations/tasks.py
import copy
import json
import logging
import os
import time

import google.generativeai as genai
from celery import shared_task
from django.conf import settings
from PIL import Image

from observations.json_rep.json_sanitizer import corriger_json, validate_json_structure

logger = logging.getLogger('observations')


@shared_task(bind=True, name='observations.process_images')
def process_images_task(self, directory):
    """
    Tâche Celery pour traiter des images et générer des transcriptions JSON.

    Args:
        directory (str): Le répertoire contenant les images à traiter

    Returns:
        dict: Résultats du traitement avec statistiques
    """
    media_root = str(settings.MEDIA_ROOT)
    base_dir = os.path.join(media_root, directory)

    # Vérifier que le répertoire existe
    if not os.path.exists(base_dir):
        logger.error(f"Le répertoire {base_dir} n'existe pas")
        return {'status': 'ERROR', 'error': f"Le répertoire {directory} n'existe pas"}

    # Créer le répertoire de résultats
    results_dir = os.path.join(media_root, 'transcription_results', directory)
    os.makedirs(results_dir, exist_ok=True)

    # Récupérer la liste des fichiers image
    image_files = [
        f
        for f in os.listdir(base_dir)
        if os.path.isfile(os.path.join(base_dir, f)) and f.lower().endswith(('.jpg', '.jpeg'))
    ]

    if not image_files:
        logger.warning(f"Aucune image trouvée dans {base_dir}")
        return {'status': 'DONE', 'results': [], 'processed': 0, 'total': 0, 'duration': 0}

    # Configuration API Gemini
    api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
    if not api_key:
        logger.error("Clé API Gemini non configurée")
        return {'status': 'ERROR', 'error': "Clé API Gemini non configurée"}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Charger le prompt
    prompt_path = os.path.join(
        settings.BASE_DIR, 'observations', 'json_rep', 'prompt_gemini_transcription.txt'
    )
    try:
        with open(prompt_path, encoding='utf-8') as f:
            prompt = f.read()
    except Exception as e:
        logger.error(f"Erreur lors du chargement du prompt: {str(e)}")
        return {'status': 'ERROR', 'error': f"Erreur lors du chargement du prompt: {str(e)}"}

    results = []
    total_files = len(image_files)
    start_time_total = time.time()

    logger.info(f"Début du traitement de {total_files} images dans {directory}")

    for index, img_file in enumerate(image_files):
        file_start = time.time()
        current_file = img_file
        img_path = os.path.join(base_dir, img_file)

        logger.info(f"Traitement de l'image {index + 1}/{total_files}: {img_file}")

        # Mise à jour de l'état pour suivi
        self.update_state(
            state='PROGRESS',
            meta={
                'processed': index,
                'total': total_files,
                'current_file': current_file,
                'percent': int((index / total_files) * 100),
                'recent_results': results[-5:] if results else [],
            },
        )

        try:
            # Traitement de l'image
            image = Image.open(img_path)
            response = model.generate_content([prompt, image])
            text_response = response.text.encode('utf-8').decode('utf-8')

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
                    json_data_raw = copy.deepcopy(json_data)
                    json_data = corriger_json(json_data_raw)

                    # Enregistrement du JSON brut
                    raw_path = os.path.join(
                        results_dir, f"{os.path.splitext(img_file)[0]}_raw.json"
                    )
                    with open(raw_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data_raw, f, indent=2, ensure_ascii=False)

                # Enregistrement du JSON final
                json_filename = f"{os.path.splitext(img_file)[0]}_result.json"
                json_path = os.path.join(results_dir, json_filename)

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

                logger.info(
                    f"Transcription réussie pour {img_file}, durée: {round(time.time() - file_start, 2)}s"
                )

                # Résultat pour cette image
                file_result = {
                    'filename': img_file,
                    'status': 'success',
                    'json_path': json_filename,
                    'duration': round(time.time() - file_start, 2),
                }
            else:
                raise ValueError("Données JSON vides ou invalides")

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {img_file}: {str(e)}")
            file_result = {
                'filename': img_file,
                'status': 'error',
                'error': str(e),
                'duration': round(time.time() - file_start, 2),
            }

        results.append(file_result)

    # Statistiques finales
    duration_total = round(time.time() - start_time_total, 2)
    success_count = sum(1 for r in results if r['status'] == 'success')

    final_result = {
        'status': 'SUCCESS',  # <-- Changement ici
        'results': results,
        'directory': directory,  # Ajouter le répertoire pour la vue results
        'duration': duration_total,
        'processed': total_files,
        'total': total_files,
        'success_count': success_count,
        'success_rate': round((success_count / total_files) * 100, 1) if total_files > 0 else 0,
    }
    logger.info(f"Task completed successfully, returning: {final_result}")
    return final_result
