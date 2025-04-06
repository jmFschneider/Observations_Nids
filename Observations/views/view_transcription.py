# views.py
import copy
import json
import logging
import os
import time
import google.generativeai as genai
from PIL import Image
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
import datetime
from dotenv import load_dotenv

from Observations.json_rep.json_sanitizer import validate_json_structure, corriger_json


logger = logging.getLogger(__name__)


def select_directory(request):
    # Définir un répertoire racine pour les images (ajustez selon votre configuration)
    base_dir = os.path.join(settings.MEDIA_ROOT, '')

    if request.method == 'POST':
        selected_dir = request.POST.get('selected_directory')
        if selected_dir and os.path.isdir(os.path.join(base_dir, selected_dir)):
            # Stocker le répertoire sélectionné en session
            request.session['processing_directory'] = selected_dir

            # Compter les fichiers pour donner un aperçu à l'utilisateur
            full_path = os.path.join(base_dir, selected_dir)
            file_count = len([f for f in os.listdir(full_path)
                              if os.path.isfile(os.path.join(full_path, f))
                              and f.lower().endswith(('.jpg', '.jpeg'))])

            return JsonResponse({
                'success': True,
                'file_count': file_count,
                'directory': selected_dir
            })

        return JsonResponse({'success': False, 'error': 'Répertoire invalide'})

    # Récupérer la liste des répertoires disponibles
    directories = [d for d in os.listdir(base_dir)
                   if os.path.isdir(os.path.join(base_dir, d))]

    return render(request, 'transcription/upload_files.html', {'directories': directories})



def process_images(request):
    # Convertir les chemins au début de la fonction
    media_root = str(settings.MEDIA_ROOT)

    directory = request.session.get('processing_directory')
    if not directory:
        # Rediriger vers la sélection de répertoire si aucun n'est défini
        return redirect('select_directory')

    # Définir le chemin complet du répertoire
    base_dir = os.path.join(media_root, directory)

    # Créer un répertoire pour les résultats JSON
    results_dir = os.path.join(media_root, 'transcription_results', directory)
    os.makedirs(results_dir, exist_ok=True)

    # Récupérer tous les fichiers jpg dans le répertoire
    image_files = [f for f in os.listdir(base_dir)
                   if os.path.isfile(os.path.join(base_dir, f))
                   and f.lower().endswith(('.jpg', '.jpeg'))]

    # Préparation du traitement
    start_time_total = time.time()
    results = []

    # Configuration de l'API Gemini
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")  # À remplacer par votre clé API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Définir le prompt pour guider l'IA
    def load_prompt(nom_fichier):
        with open(os.path.join(settings.BASE_DIR, 'Observations', 'json_rep', nom_fichier), 'r', encoding='utf-8') as f:
            return f.read()

    prompt = load_prompt("prompt_gemini_transcription.txt")

    # Limiter le nombre de fichiers à traiter en développement (commentez en production)
    # image_files = image_files[:5]

    # Pour le suivi en temps réel
    request.session['processing_progress'] = {
        'total_files': len(image_files),
        'processed': 0,
        'current_file': '',
        'start_time': timezone.now().isoformat(),
        'results': []
    }
    request.session.save()

    # Traiter chaque image
    for index, img_file in enumerate(image_files):
        file_start_time = time.time()
        img_path = os.path.join(base_dir, img_file)

        # Mettre à jour le statut pour suivi en temps réel
        request.session['processing_progress']['current_file'] = img_file
        request.session.save()

        try:
            # Ouvrir l'image
            image = Image.open(img_path)

            # Envoyer l'image au modèle
            response = model.generate_content([prompt, image])
            text_response = response.text.encode('utf-8').decode('utf-8')

            # Nettoyage éventuel de markdown ```json
            if text_response.startswith("```json"):
                text_response = text_response[7:-3].strip()

            # Tenter de parser en JSON
            try:
                json_data = json.loads(text_response)
            except json.JSONDecodeError as e:
                json_data = None
                logger.error(f"Erreur de JSON invalide pour {img_file} : {str(e)}")

            if json_data:
                # Vérification de la structure
                erreurs = validate_json_structure(json_data)

                if erreurs:
                    json_data_raw = copy.deepcopy(json_data)  # sauvegarde avant correction
                    json_data = corriger_json(json_data_raw)

                    # Enregistrement du fichier brut si utile
                    raw_path = os.path.join(results_dir, f"{os.path.splitext(img_file)[0]}_raw.json")
                    with open(raw_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data_raw, f, indent=2, ensure_ascii=False)

                # Enregistrement du fichier corrigé ou valide directement
                json_filename = f"{os.path.splitext(img_file)[0]}_result.json"
                json_path = os.path.join(results_dir, json_filename)

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

            # Calculer le temps de traitement pour ce fichier
            file_duration = time.time() - file_start_time

            # Ajouter les informations de ce fichier au suivi
            file_result = {
                'filename': img_file,
                'status': 'success',
                'duration': round(file_duration, 2),
                'json_path': json_path
            }

            results.append(file_result)

            # Mettre à jour le statut dans la session
            request.session['processing_progress']['processed'] = index + 1
            request.session['processing_progress']['results'].append(file_result)
            request.session.save()

        except Exception as e:
            # En cas d'erreur, enregistrer l'information
            error_info = {
                'filename': img_file,
                'status': 'error',
                'error': str(e),
                'duration': round(time.time() - file_start_time, 2)
            }
            results.append(error_info)
            request.session['processing_progress']['results'].append(error_info)
            request.session['processing_progress']['processed'] = index + 1
            request.session.save()

    # Calculer le temps total
    total_duration = time.time() - start_time_total

    successful_files = sum(1 for r in results if r['status'] == 'success')
    error_files = sum(1 for r in results if r['status'] == 'error')
    total_files = len(image_files)
    success_rate = (successful_files / total_files * 100) if total_files > 0 else 0

    # Préparer le contexte pour le template
    context = {
        'directory': directory,
        'results': results,
        'total_duration': round(total_duration, 2),
        'total_files': total_files,
        'successful_files': successful_files,
        'error_files': error_files,
        'success_rate': round(success_rate, 1)
    }

    # Sauvegarder les résultats en session pour référence ultérieure
    request.session['transcription_results'] = {
        'directory': directory,
        'total_duration': round(total_duration, 2),
        'results': results,
        'timestamp': timezone.now().isoformat()
    }

    return render(request, 'transcription/results.html', context)

def check_progress(request):
    """Endpoint AJAX pour vérifier la progression du traitement"""
    progress = request.session.get('processing_progress', {})
    # Calculer le temps écoulé depuis le début
    if 'start_time' in progress:
        start_time = datetime.datetime.fromisoformat(progress['start_time'])
        elapsed_seconds = (timezone.now() - start_time).total_seconds()
    else:
        elapsed_seconds = 0

    return JsonResponse({
        'processed_count': progress.get('processed', 0),
        'total_files': progress.get('total_files', 0),
        'current_file': progress.get('current_file', ''),
        'elapsed_seconds': int(elapsed_seconds),
        'results': progress.get('results', [])[-5:]  # Uniquement les 5 derniers résultats pour alléger
    })

def transcription_results(request):
    return render(request, 'transcription/results.html',
                 request.session.get('transcription_results', {}))
