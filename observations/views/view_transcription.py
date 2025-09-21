import logging
import os

from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

# Importer la tâche Celery
from observations.tasks import process_images_task
from observations_nids.celery import app

logger = logging.getLogger(__name__)


def select_directory(request):
    """Vue pour sélectionner un répertoire d'images à traiter"""
    # Définir un répertoire racine pour les images
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


def is_celery_operational():
    """Vérifie si Celery est opérationnel en essayant de contacter les workers"""
    try:
        # Essayer de ping les workers Celery
        response = app.control.ping(timeout=1.0)
        # Si aucun worker ne répond, Celery n'est pas opérationnel
        return len(response) > 0
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de Celery: {str(e)}")
        return False


def process_images(request):
    """Vue pour démarrer le traitement des images via Celery"""
    directory = request.session.get('processing_directory')
    if not directory:
        # Rediriger vers la sélection de répertoire si aucun n'est défini
        return redirect('select_directory')

    # Vérifier si Celery est opérationnel
    if not is_celery_operational():
        # Si Celery n'est pas opérationnel, ajouter un message d'erreur et rediriger
        messages.error(request, "Celery n'est pas en fonction sur le serveur")
        return redirect('select_directory')

    # Créer le répertoire de résultats
    results_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results', directory)
    os.makedirs(results_dir, exist_ok=True)

    # Lancer la tâche Celery
    task = process_images_task.delay(directory)
    task_id = task.id

    # Stocker l'ID de tâche en session pour le suivi
    request.session['task_id'] = task_id

    # Initialiser le suivi de progression
    progress_data = {
        'task_id': task_id,
        'directory': directory,
        'start_time': timezone.now().isoformat()
    }
    request.session['processing_progress'] = progress_data

    # Rendu de la page de suivi
    return render(request, 'transcription/processing.html', {
        'task_id': task_id,
        'directory': directory
    })


def check_progress(request):
    """Endpoint AJAX pour vérifier la progression du traitement"""
    task_id = request.session.get('task_id')
    if not task_id:
        logger.warning("check_progress called with no task_id in session")
        return JsonResponse({'status': 'NO_TASK'})

    result = AsyncResult(task_id, app=app)
    logger.debug(f"check_progress for task {task_id}: status={result.status}")

    response = {
        'status': result.status,
        'task_id': task_id,
    }

    # Ajouter les informations de progression si disponibles
    if result.status == 'PENDING':
        # La tâche est en attente de démarrage
        response['message'] = 'Tâche en attente de démarrage...'
    elif result.status == 'PROGRESS' and result.info:
        # La tâche est en cours, ajouter les informations de progression
        response.update(result.info)
        # Calculer le pourcentage de progression
        if 'total' in result.info and result.info['total'] > 0:
            response['percent'] = int((result.info.get('processed', 0) / result.info['total']) * 100)
        else:
            response['percent'] = 0
    elif result.status == 'SUCCESS':
        # La tâche est terminée avec succès
        response.update(result.result)
        # Stocker les résultats en session pour référence ultérieure
        request.session['transcription_results'] = {
            'directory': result.result.get('directory', request.session.get('processing_directory')),
            'total_duration': result.result.get('duration', 0),
            'results': result.result.get('results', []),
            'total_files': result.result.get('total', 0),
            'successful_files': result.result.get('success_count', 0),
            'error_files': result.result.get('total', 0) - result.result.get('success_count', 0),
            'success_rate': result.result.get('success_rate', 0),
            'timestamp': timezone.now().isoformat()
        }
        # Rediriger vers les résultats
        response['redirect'] = '/transcription/resultats/'
        response['force_redirect'] = True  # Ajouter un flag pour forcer la redirection
        logger.info(f"Task {task_id} completed successfully. Sending redirect to /transcription/resultats/ with force_redirect flag")
    elif result.status == 'FAILURE':
        # La tâche a échoué
        response['error'] = str(result.result)
        response['message'] = "Une erreur s'est produite lors du traitement."

    logger.debug(f"check_progress response for task {task_id}: {response}")
    return JsonResponse(response)


def transcription_results(request):
    """Vue pour afficher les résultats de la transcription"""
    # Récupérer les résultats stockés en session
    results = request.session.get('transcription_results', {})

    # Si pas de résultats et une tâche est en cours, rediriger vers la page de suivi
    if not results and request.session.get('task_id'):
        return redirect('process_images')

    # Préparer les chemins complets pour les liens
    if 'results' in results:
        for result in results.get('results', []):
            if result.get('status') == 'success' and 'json_path' in result:
                # Ajouter le préfixe MEDIA_URL pour les liens
                result[
                    'json_url'] = f"{settings.MEDIA_URL}transcription_results/{results.get('directory')}/{result['json_path']}"

    # Ajouter MEDIA_URL au contexte
    context = results.copy()
    context['media_url'] = settings.MEDIA_URL

    return render(request, 'transcription/results.html', context)


# Vue pour démarrer la transcription (utilisation de l'API AJAX)

def start_transcription_view(request):
    """API pour démarrer le traitement des images via AJAX"""
    directory = request.session.get('processing_directory')
    if not directory:
        return JsonResponse({'error': 'Aucun répertoire sélectionné'}, status=400)

    # Vérifier si Celery est opérationnel
    if not is_celery_operational():
        return JsonResponse({
            'error': "Celery n'est pas en fonction sur le serveur",
            'celery_error': True
        }, status=503)  # 503 Service Unavailable

    task = process_images_task.delay(directory)
    request.session['task_id'] = task.id

    return JsonResponse({
        'task_id': task.id,
        'message': 'Traitement démarré',
        'processing_url': '/transcription/verifier-progression/'
    })
