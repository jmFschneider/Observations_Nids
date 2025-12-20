"""
Vues pour l'app pilot - Optimisation OCR

Système de transcription batch pour l'évaluation des modèles OCR
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, cast

from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from observations.decorators import transcription_required
from observations.models import FicheObservation
from pilot.tasks import process_batch_transcription_task

logger = logging.getLogger(__name__)


@transcription_required
def optimisation_ocr_home(request):
    """Page d'accueil de l'optimisation OCR"""
    return render(request, 'pilot/optimisation_ocr_home.html')


@transcription_required
def selection_repertoire_ocr(request):
    """
    Vue pour sélectionner un répertoire d'images à transcrire en batch

    Navigation dans media/ avec détection automatique du type
    de fiche et du traitement d'après l'arborescence des dossiers.
    """
    # Répertoire de base : media/
    base_dir = settings.MEDIA_ROOT

    # Récupérer le chemin actuel depuis les paramètres GET
    current_path = request.GET.get('path', '')

    # Sécurité : normaliser le chemin
    safe_path = os.path.normpath(current_path).replace('..', '')
    full_current_path = os.path.join(base_dir, safe_path)

    # Vérifier que le chemin est dans le répertoire de base
    if not full_current_path.startswith(base_dir):
        safe_path = ''
        full_current_path = base_dir

    # Récupérer la liste des sous-répertoires avec statistiques
    directories = []
    try:
        dir_list = [
            d
            for d in os.listdir(full_current_path)
            if os.path.isdir(os.path.join(full_current_path, d))
        ]

        for dir_name in dir_list:
            dir_path = os.path.join(full_current_path, dir_name)

            try:
                # Compter les sous-répertoires
                subdirs_count = len(
                    [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))]
                )

                # Compter les fichiers images
                images_count = len(
                    [
                        f
                        for f in os.listdir(dir_path)
                        if os.path.isfile(os.path.join(dir_path, f))
                        and f.lower().endswith(('.jpg', '.jpeg', '.png'))
                    ]
                )

                directories.append(
                    {
                        'name': dir_name,
                        'subdirs_count': subdirs_count,
                        'images_count': images_count,
                    }
                )
            except (OSError, PermissionError):
                directories.append(
                    {
                        'name': dir_name,
                        'subdirs_count': 0,
                        'images_count': 0,
                    }
                )

        directories.sort(key=lambda x: x['name'].lower())
    except (OSError, PermissionError):
        directories = []
        messages.error(request, "Impossible d'accéder à ce répertoire")
        safe_path = ''
        full_current_path = base_dir

    # Créer le fil d'Ariane
    breadcrumb = []
    if safe_path:
        parts = safe_path.split(os.sep)
        current = ''
        for part in parts:
            if part:
                current = os.path.join(current, part) if current else part
                breadcrumb.append({'name': part, 'path': current})

    # Compter les images dans le répertoire actuel
    try:
        image_count = len(
            [
                f
                for f in os.listdir(full_current_path)
                if os.path.isfile(os.path.join(full_current_path, f))
                and f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]
        )
    except (OSError, PermissionError):
        image_count = 0

    # Déduire les métadonnées du chemin
    type_fiche = None
    type_traitement = None

    if safe_path:
        parts = safe_path.split(os.sep)
        if len(parts) >= 1:
            type_fiche = parts[0]  # Ex: "Ancienne_fiche" ou "Nouvelle_fiche"
        if len(parts) >= 2:
            type_traitement = parts[1]  # Ex: "Sans_traitement", "Traitement_1"

    context = {
        'directories': directories,
        'current_path': safe_path,
        'breadcrumb': breadcrumb,
        'image_count': image_count,
        'parent_path': os.path.dirname(safe_path) if safe_path else None,
        'type_fiche': type_fiche,
        'type_traitement': type_traitement,
    }

    return render(request, 'pilot/selection_repertoire_ocr.html', context)


@transcription_required
def analyser_correspondances(request):
    """
    Analyse les images d'un répertoire et trouve les fiches correspondantes

    Retourne un JSON avec les correspondances trouvées
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    repertoire = request.POST.get('repertoire', '')
    if not repertoire:
        return JsonResponse({'error': 'Répertoire non spécifié'}, status=400)

    # Construire le chemin complet
    base_dir = settings.MEDIA_ROOT
    full_path = os.path.join(base_dir, repertoire)

    # Vérifier que le chemin existe et est dans le répertoire de base
    if not full_path.startswith(base_dir) or not os.path.isdir(full_path):
        return JsonResponse({'error': 'Répertoire invalide'}, status=400)

    # Lister les images
    try:
        images = [
            f
            for f in os.listdir(full_path)
            if os.path.isfile(os.path.join(full_path, f))
            and f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
    except (OSError, PermissionError):
        return JsonResponse({'error': "Impossible d'accéder au répertoire"}, status=500)

    # Analyser chaque image pour trouver la fiche correspondante
    correspondances = []
    for image_filename in images:
        # Extraire le nom de base (enlever l'extension)
        nom_base = Path(image_filename).stem

        # Chercher une fiche dont le chemin_image contient ce nom
        fiches = FicheObservation.objects.filter(chemin_image__contains=nom_base)

        if fiches.count() == 1:
            fiche = fiches.first()
            correspondances.append(
                {
                    'image': image_filename,
                    'statut': 'trouvee',
                    'fiche_id': fiche.num_fiche,
                    'fiche_info': {
                        'numero': fiche.num_fiche,
                        'espece': fiche.espece.nom if fiche.espece else 'Non spécifié',
                        'annee': fiche.annee,
                        'observateur': fiche.observateur.username,
                        'chemin_image': fiche.chemin_image,
                    },
                }
            )
        elif fiches.count() > 1:
            correspondances.append(
                {
                    'image': image_filename,
                    'statut': 'multiple',
                    'fiches_possibles': [
                        {
                            'numero': f.num_fiche,
                            'espece': f.espece.nom if f.espece else 'Non spécifié',
                            'annee': f.annee,
                            'chemin_image': f.chemin_image,
                        }
                        for f in fiches
                    ],
                }
            )
        else:
            correspondances.append(
                {
                    'image': image_filename,
                    'statut': 'non_trouvee',
                }
            )

    # Compter les résultats
    nb_trouvees = len([c for c in correspondances if c['statut'] == 'trouvee'])
    nb_multiples = len([c for c in correspondances if c['statut'] == 'multiple'])
    nb_non_trouvees = len([c for c in correspondances if c['statut'] == 'non_trouvee'])

    return JsonResponse(
        {
            'success': True,
            'total_images': len(images),
            'nb_trouvees': nb_trouvees,
            'nb_multiples': nb_multiples,
            'nb_non_trouvees': nb_non_trouvees,
            'correspondances': correspondances,
        }
    )


@transcription_required
def lancer_transcription_batch(request):  # noqa: PLR0911
    """
    Lance la transcription batch pour les images sélectionnées avec le modèle OCR choisi.

    Attend un POST avec:
    - directories: JSON array des répertoires sélectionnés (avec 'path' et 'name')
    - modele_ocr: Nom du modèle OCR à utiliser
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        # Récupérer les paramètres
        directories_json = request.POST.get('directories')
        modeles_ocr_json = request.POST.get('modeles_ocr')

        if not directories_json or not modeles_ocr_json:
            return JsonResponse(
                {'error': 'Paramètres manquants (directories ou modeles_ocr)'}, status=400
            )

        # Parser la liste des répertoires
        try:
            directories = json.loads(directories_json)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Format JSON invalide pour directories'}, status=400)

        if not directories or not isinstance(directories, list):
            return JsonResponse(
                {'error': 'La liste des répertoires est vide ou invalide'}, status=400
            )

        # Parser la liste des modèles OCR
        try:
            modeles_ocr = json.loads(modeles_ocr_json)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Format JSON invalide pour modeles_ocr'}, status=400)

        if not modeles_ocr or not isinstance(modeles_ocr, list):
            return JsonResponse(
                {'error': 'La liste des modèles OCR est vide ou invalide'}, status=400
            )

        logger.info(
            f"[PILOT] Lancement transcription batch: {len(directories)} répertoire(s), "
            f"{len(modeles_ocr)} modèle(s) ({', '.join(modeles_ocr)}) - Mode évaluation (JSON uniquement)"
        )

        # Lancer la tâche Celery (mode pilote : génération JSON uniquement)
        task = process_batch_transcription_task.delay(directories, modeles_ocr)
        task_id = task.id

        # Stocker l'ID de tâche en session pour le suivi
        request.session['pilot_task_id'] = task_id
        request.session['pilot_batch_config'] = {
            'directories': directories,
            'modeles_ocr': modeles_ocr,
            'start_time': timezone.now().isoformat(),
        }

        logger.info(f"Tâche batch créée avec ID: {task_id}")

        return JsonResponse(
            {
                'success': True,
                'task_id': task_id,
                'message': 'Traitement batch démarré',
                'progress_url': '/pilot/optimisation-ocr/verifier-progression/',
            }
        )

    except Exception as e:
        logger.error(f"Erreur lors du lancement de la transcription batch: {str(e)}")
        return JsonResponse({'error': f"Erreur serveur: {str(e)}"}, status=500)


@transcription_required
def check_batch_progress(request):
    """
    Endpoint AJAX pour vérifier la progression du traitement batch
    """
    task_id = request.session.get('pilot_task_id')
    if not task_id:
        logger.warning("check_batch_progress called with no task_id in session")
        return JsonResponse({'status': 'NO_TASK'})

    result = AsyncResult(task_id)
    logger.debug(f"check_batch_progress for task {task_id}: status={result.status}")

    response: dict[str, Any] = {
        'status': result.status,
        'task_id': task_id,
    }

    if result.status == 'PENDING':
        response['message'] = 'Tâche en attente de démarrage...'
        response['percent'] = 0

    elif result.status in ('STARTED', 'RETRY', 'PROGRESS'):
        raw_info: Any = result.info
        info: dict = cast(dict, raw_info if isinstance(raw_info, dict) else {})

        total = int(info.get('total', 0) or 0)
        processed = int(info.get('processed', 0) or 0)

        response['percent'] = int(processed * 100 / total) if total > 0 else 0
        response['processed'] = processed
        response['total'] = total
        response['current_file'] = info.get('current_file', '')
        response['current_directory'] = info.get('current_directory', '')
        response['message'] = f"Traitement en cours... ({processed}/{total})"

    elif result.status == 'SUCCESS':
        raw_ok: Any = result.result
        ok: dict = cast(dict, raw_ok if isinstance(raw_ok, dict) else {})

        response.update(ok)
        response['percent'] = 100
        response['message'] = 'Traitement terminé avec succès'

        # Stocker les résultats en session
        request.session['pilot_batch_results'] = ok

        # Redirection vers la page de résultats
        response['redirect'] = '/pilot/optimisation-ocr/resultats/'
        response['force_redirect'] = True
        logger.info(f"Task {task_id} completed. Sending redirect to results page")

    elif result.status == 'FAILURE':
        response['percent'] = 0
        response['error'] = str(result.result)
        response['message'] = "Une erreur s'est produite lors du traitement batch."
        logger.error(f"Task {task_id} failed: {result.result}")

    else:
        response['message'] = f"État de tâche : {result.status}"
        response['percent'] = 0

    logger.debug(f"check_batch_progress response for task {task_id}: {response}")
    return JsonResponse(response)


@transcription_required
def batch_results(request):
    """
    Affiche les résultats du traitement batch
    """
    # Vérifier si on est en mode tracking (suivi en temps réel)
    is_tracking = request.GET.get('tracking') == 'true'

    # Récupérer les résultats stockés en session
    results = request.session.get('pilot_batch_results', {})
    config = request.session.get('pilot_batch_config', {})

    # Si pas de résultats ET qu'on n'est pas en mode tracking, afficher un message d'erreur
    if not results and not is_tracking:
        messages.warning(
            request, "Aucun résultat disponible. Veuillez lancer un traitement batch d'abord."
        )
        return render(request, 'pilot/batch_results.html', {'no_results': True})

    # Si on est en mode tracking mais pas encore de résultats, afficher le template sans no_results
    # Le JavaScript va gérer le polling
    if is_tracking and not results:
        return render(request, 'pilot/batch_results.html', {'no_results': False})

    # Enrichir le contexte
    modeles_ocr = results.get('modeles_ocr', config.get('modeles_ocr', []))
    duration = results.get('duration', 0)
    total_images = results.get('total_images', 0)
    duration_per_image = duration / total_images if total_images > 0 else 0

    context = {
        'results': results,
        'config': config,
        'modeles_ocr': modeles_ocr,
        'modeles_ocr_display': ', '.join(modeles_ocr)
        if isinstance(modeles_ocr, list)
        else modeles_ocr,
        'total_directories': results.get('total_directories', 0),
        'total_models': results.get('total_models', 0),
        'total_images': total_images,
        'total_success': results.get('total_success', 0),
        'total_errors': results.get('total_errors', 0),
        'success_rate': results.get('success_rate', 0),
        'duration': duration,
        'duration_per_image': duration_per_image,
        'directory_results': results.get('results', []),
    }

    return render(request, 'pilot/batch_results.html', context)
