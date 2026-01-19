import json
import logging
import os
from typing import Any, cast

from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ingest.importation_service import ImportationService
from ingest.models import ImportationEnCours
from ingest.tasks import process_json_batch_task

from .auth import peut_transcrire

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(peut_transcrire)
def importer_json(request):
    """
    Vue pour importer des fichiers JSON depuis un répertoire.

    Navigation arborescente dans transcription_results/ avec détection
    automatique du nombre de fichiers JSON et sous-répertoires.
    """
    # Répertoire de base : MEDIA_ROOT/transcription_results/
    base_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results')

    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Répertoire créé: {base_dir}")

    # Récupérer le chemin actuel depuis les paramètres GET
    current_path = request.GET.get('path', '')

    # Sécurité : normaliser le chemin (utiliser '/' pour compatibilité URL)
    # Remplacer les backslashes par des forward slashes et supprimer '..'
    safe_path = current_path.replace('\\', '/').replace('..', '').strip('/')
    # Reconstruire le chemin complet avec os.path.join (qui gère le séparateur OS)
    full_current_path = os.path.join(base_dir, safe_path.replace('/', os.sep))

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

                # Compter les fichiers JSON
                json_count = len(
                    [
                        f
                        for f in os.listdir(dir_path)
                        if os.path.isfile(os.path.join(dir_path, f)) and f.lower().endswith('.json')
                    ]
                )

                directories.append(
                    {
                        'name': dir_name,
                        'subdirs_count': subdirs_count,
                        'json_count': json_count,
                    }
                )
            except (OSError, PermissionError):
                directories.append(
                    {
                        'name': dir_name,
                        'subdirs_count': 0,
                        'json_count': 0,
                    }
                )

        directories.sort(key=lambda x: str(x['name']).lower())
    except (OSError, PermissionError):
        directories = []
        messages.error(request, "Impossible d'accéder à ce répertoire")
        safe_path = ''
        full_current_path = base_dir

    # Créer le fil d'Ariane
    breadcrumb = []
    if safe_path:
        # Utiliser '/' comme séparateur pour les URLs (indépendant de l'OS)
        parts = safe_path.replace('\\', '/').split('/')
        current = ''
        for part in parts:
            if part:
                current = f"{current}/{part}" if current else part
                breadcrumb.append({'name': part, 'path': current})

    # Compter les fichiers JSON dans le répertoire actuel
    try:
        json_count = len(
            [
                f
                for f in os.listdir(full_current_path)
                if os.path.isfile(os.path.join(full_current_path, f))
                and f.lower().endswith('.json')
            ]
        )
    except (OSError, PermissionError):
        json_count = 0

    # Traitement du formulaire POST
    if request.method == 'POST':
        repertoire = request.POST.get('repertoire')
        if not repertoire:
            messages.error(request, "Veuillez sélectionner un répertoire")
            return redirect('ingest:importer_json')

        service = ImportationService()
        resultats = service.importer_fichiers_json(repertoire)

        if resultats['erreurs']:
            for erreur in resultats['erreurs']:
                messages.warning(request, erreur)

        messages.success(
            request,
            f"Importation terminée: {resultats['reussis']} fichiers importés, "
            f"{resultats['ignores']} fichiers ignorés (déjà importés), "
            f"{len(resultats['erreurs'])} erreurs",
        )

        return redirect('ingest:accueil_importation')

    # Calculer le chemin parent avec '/' pour les URLs
    parent_path = None
    if safe_path:
        # Utiliser '/' comme séparateur pour les URLs
        path_parts = safe_path.replace('\\', '/').split('/')
        parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''

    context = {
        'directories': directories,
        'current_path': safe_path,
        'breadcrumb': breadcrumb,
        'json_count': json_count,
        'parent_path': parent_path,
    }

    return render(request, 'ingest/importer_json.html', context)


@login_required
@user_passes_test(peut_transcrire)
def extraire_candidats(request):
    """Vue pour extraire les espèces et créer automatiquement les utilisateurs"""
    if request.method == 'POST':
        service = ImportationService()
        resultats = service.extraire_donnees_candidats()

        messages.success(
            request,
            f"Extraction terminée: {resultats['especes_ajoutees']} nouvelles espèces, "
            f"{resultats['utilisateurs_crees']} nouveaux utilisateurs créés",
        )

        return redirect('ingest:accueil_importation')

    return render(request, 'ingest/extraire_candidats.html')


@login_required
@user_passes_test(peut_transcrire)
def preparer_importations(request):
    """Vue pour préparer les importations des transcriptions"""
    if request.method == 'POST':
        service = ImportationService()
        importations_creees = service.preparer_importations()

        messages.success(request, f"{importations_creees} importations préparées pour traitement")

        return redirect('ingest:liste_importations')

    return render(request, 'ingest/preparer_importations.html')


@login_required
@user_passes_test(peut_transcrire)
def liste_importations(request):
    """Vue pour afficher la liste des importations en cours"""
    # Filtre de recherche
    statut = request.GET.get('statut', 'tous')

    importations = ImportationEnCours.objects.all()

    # Appliquer les filtres
    if statut != 'tous':
        importations = importations.filter(statut=statut)

    # Pagination
    paginator = Paginator(importations.order_by('-date_creation'), 20)
    page = request.GET.get('page', 1)
    importations_page = paginator.get_page(page)

    context = {'importations': importations_page, 'statut': statut}

    return render(request, 'ingest/liste_importations.html', context)


@login_required
@user_passes_test(peut_transcrire)
def detail_importation(request, importation_id):
    """Vue pour afficher les détails d'une importation"""
    importation = get_object_or_404(ImportationEnCours, id=importation_id)
    transcription = importation.transcription

    # Afficher le contenu JSON formaté
    donnees_json = json.dumps(transcription.json_brut, indent=2, ensure_ascii=False)

    context = {
        'importation': importation,
        'transcription': transcription,
        'donnees_json': donnees_json,
    }

    return render(request, 'ingest/detail_importation.html', context)


@login_required
@user_passes_test(peut_transcrire)
def finaliser_importation(request, importation_id):
    """Vue pour finaliser une importation"""
    if request.method == 'POST':
        service = ImportationService()
        success, message = service.finaliser_importation(importation_id)

        if success:
            messages.success(request, message)
        else:
            messages.error(request, f"Erreur lors de l'importation: {message}")

        return redirect('ingest:liste_importations')

    return redirect('detail_importation', importation_id=importation_id)


@login_required
@user_passes_test(peut_transcrire)
def finaliser_importations_multiples(request):
    """Vue pour finaliser plusieurs importations en même temps"""
    if request.method == 'POST':
        importation_ids = request.POST.getlist('importation_ids')

        if not importation_ids:
            messages.warning(request, "Aucune importation sélectionnée")
            return redirect('ingest:liste_importations')

        service = ImportationService()
        success_count = 0
        error_count = 0

        for importation_id in importation_ids:
            success, message = service.finaliser_importation(importation_id)
            if success:
                success_count += 1
            else:
                error_count += 1
                messages.error(request, f"Importation {importation_id}: {message}")

        if success_count > 0:
            messages.success(request, f"{success_count} importation(s) finalisée(s) avec succès")
        if error_count > 0:
            messages.warning(request, f"{error_count} importation(s) en erreur")

        return redirect('ingest:liste_importations')

    return redirect('ingest:liste_importations')


@login_required
@user_passes_test(peut_transcrire)
def reinitialiser_importation(request, importation_id):
    """Vue pour réinitialiser une importation spécifique"""
    if request.method == 'POST':
        service = ImportationService()
        resultat = service.reinitialiser_importation(importation_id=importation_id)

        if resultat['success']:
            messages.success(request, resultat['message'])
        else:
            messages.error(request, resultat['message'])

    return redirect('ingest:liste_importations')


@login_required
@user_passes_test(peut_transcrire)
def reinitialiser_toutes_importations(request):
    """Vue pour réinitialiser toutes les importations"""
    if request.method == 'POST':
        statut = request.POST.get('statut', 'all')

        # Filtrer les importations à réinitialiser
        query = Q()
        if statut == 'complete':
            query = Q(statut='complete')
        elif statut == 'erreur':
            query = Q(statut='erreur')
        elif statut == 'en_attente':
            query = Q(statut='en_attente')  # Ajout de cette option
        elif statut == 'all':
            query = (
                Q(statut='complete') | Q(statut='erreur') | Q(statut='en_attente')
            )  # Inclure 'en_attente'

        importations = ImportationEnCours.objects.filter(query)
        count = 0
        service = ImportationService()

        for importation in importations:
            resultat = service.reinitialiser_importation(importation_id=importation.id)
            if resultat['success']:
                count += 1

        if count > 0:
            messages.success(request, f"{count} importation(s) réinitialisée(s) avec succès")
        else:
            messages.info(request, "Aucune importation n'a été réinitialisée")

    return redirect('ingest:liste_importations')


@login_required
@user_passes_test(peut_transcrire)
def importer_json_batch(request):
    """
    Vue pour importer et traiter des fichiers JSON en une seule étape (workflow unifié).

    Cette vue utilise la méthode traiter_fichier_json() qui :
    - Importe le JSON
    - Matche l'espèce (avec fallback sur placeholders)
    - Crée l'utilisateur
    - Crée la fiche immédiatement
    """
    # Répertoire de base : MEDIA_ROOT/transcription_results/
    base_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results')

    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Répertoire créé: {base_dir}")

    # Récupérer le chemin actuel depuis les paramètres GET
    current_path = request.GET.get('path', '')

    # Sécurité : normaliser le chemin
    safe_path = current_path.replace('\\', '/').replace('..', '').strip('/')
    full_current_path = os.path.join(base_dir, safe_path.replace('/', os.sep))

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

                # Compter les fichiers JSON
                json_count = len(
                    [
                        f
                        for f in os.listdir(dir_path)
                        if os.path.isfile(os.path.join(dir_path, f)) and f.lower().endswith('.json')
                    ]
                )

                directories.append(
                    {
                        'name': dir_name,
                        'subdirs_count': subdirs_count,
                        'json_count': json_count,
                    }
                )
            except (OSError, PermissionError):
                directories.append(
                    {
                        'name': dir_name,
                        'subdirs_count': 0,
                        'json_count': 0,
                    }
                )

        directories.sort(key=lambda x: str(x['name']).lower())
    except (OSError, PermissionError):
        directories = []
        messages.error(request, "Impossible d'accéder à ce répertoire")
        safe_path = ''
        full_current_path = base_dir

    # Créer le fil d'Ariane
    breadcrumb = []
    if safe_path:
        parts = safe_path.replace('\\', '/').split('/')
        current = ''
        for part in parts:
            if part:
                current = f"{current}/{part}" if current else part
                breadcrumb.append({'name': part, 'path': current})

    # Compter les fichiers JSON dans le répertoire actuel
    try:
        fichiers_json = [
            f
            for f in os.listdir(full_current_path)
            if os.path.isfile(os.path.join(full_current_path, f)) and f.lower().endswith('.json')
        ]
        json_count = len(fichiers_json)
    except (OSError, PermissionError):
        fichiers_json = []
        json_count = 0

    # Traitement du formulaire POST
    if request.method == 'POST':
        repertoire = request.POST.get('repertoire')
        if not repertoire:
            messages.error(request, "Veuillez sélectionner un répertoire")
            return redirect('ingest:importer_json_batch')

        # Lancer la tâche Celery en arrière-plan
        task = process_json_batch_task.delay(fichiers_json, repertoire)
        task_id = task.id

        # Stocker le task_id en session pour récupération ultérieure
        request.session['ingest_batch_task_id'] = task_id

        logger.info(f"Tâche batch lancée: {task_id} pour {len(fichiers_json)} fichier(s)")

        # Rediriger vers la page de progression
        return redirect('ingest:batch_progress')

    # Calculer le chemin parent
    parent_path = None
    if safe_path:
        path_parts = safe_path.replace('\\', '/').split('/')
        parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''

    context = {
        'directories': directories,
        'current_path': safe_path,
        'breadcrumb': breadcrumb,
        'json_count': json_count,
        'parent_path': parent_path,
    }

    return render(request, 'ingest/importer_json_batch.html', context)


@login_required
@user_passes_test(peut_transcrire)
def check_batch_progress(request: HttpRequest) -> JsonResponse:
    """
    Endpoint AJAX pour vérifier la progression du traitement batch.
    """
    task_id = request.session.get('ingest_batch_task_id')
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
        success_count = int(info.get('success_count', 0) or 0)
        error_count = int(info.get('error_count', 0) or 0)
        ignored_count = int(info.get('ignored_count', 0) or 0)

        response['percent'] = int((processed / total) * 100) if total > 0 else 0
        response['processed'] = processed
        response['total'] = total
        response['success_count'] = success_count
        response['error_count'] = error_count
        response['ignored_count'] = ignored_count
        response['current_file'] = info.get('current_file', '')
        response['message'] = f"Traitement en cours... ({processed}/{total})"
        response['logs'] = info.get('logs', [])

    elif result.status == 'SUCCESS':
        raw_ok: Any = result.result
        ok: dict = cast(dict, raw_ok if isinstance(raw_ok, dict) else {})

        response.update(ok)
        response['percent'] = 100

        success_count = ok.get('success_count', 0)
        ignored_count = ok.get('ignored_count', 0)
        error_count = ok.get('error_count', 0)

        response['message'] = (
            f"✅ Traitement terminé: {success_count} réussis, {ignored_count} ignorés, {error_count} erreurs"
        )

        # Stocker les messages dans la session pour affichage après redirection
        if success_count > 0:
            request.session['batch_success_message'] = (
                f"✅ {success_count} fiche(s) créée(s) avec succès"
            )

        if ignored_count > 0:
            request.session['batch_info_message'] = (
                f"ℹ️ {ignored_count} fichier(s) ignoré(s) (déjà importés)"
            )

        if error_count > 0:
            request.session['batch_warning_message'] = f"⚠️ {error_count} erreur(s)"
            # Stocker les premières erreurs pour affichage
            erreurs = ok.get('erreurs', [])[:5]
            if erreurs:
                request.session['batch_errors'] = erreurs

        # Nettoyer le task_id de la session
        if 'ingest_batch_task_id' in request.session:
            del request.session['ingest_batch_task_id']

        # Redirection vers la page d'accueil
        response['redirect'] = '/ingest/'
        response['force_redirect'] = True
        logger.info(f"Task {task_id} completed. Sending redirect to accueil")

    elif result.status == 'FAILURE':
        response['percent'] = 0
        response['error'] = str(result.result)
        response['message'] = "Une erreur s'est produite lors du traitement batch."
        logger.error(f"Task {task_id} failed: {result.result}")

        # Nettoyer le task_id de la session
        if 'ingest_batch_task_id' in request.session:
            del request.session['ingest_batch_task_id']

    else:
        response['message'] = f"État de tâche : {result.status}"
        response['percent'] = 0

    logger.debug(f"check_batch_progress response for task {task_id}: {response}")
    return JsonResponse(response)


@login_required
@user_passes_test(peut_transcrire)
def batch_progress(request):
    """
    Page d'affichage de la progression du traitement batch.
    """
    task_id = request.session.get('ingest_batch_task_id')
    if not task_id:
        messages.warning(request, "Aucune tâche batch en cours")
        return redirect('ingest:accueil_importation')

    context = {
        'task_id': task_id,
    }
    return render(request, 'ingest/batch_progress.html', context)
