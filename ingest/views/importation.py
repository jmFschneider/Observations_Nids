import json
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ingest.importation_service import ImportationService
from ingest.models import ImportationEnCours

from .auth import peut_transcrire

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(peut_transcrire)
def importer_json(request):
    """Vue pour importer des fichiers JSON depuis un répertoire"""
    # Chemin vers le répertoire de résultats de transcription
    base_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results')

    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Répertoire créé: {base_dir}")

    # Liste tous les sous-répertoires (pas les fichiers)
    directories = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    if request.method == 'POST':
        repertoire = request.POST.get('repertoire')
        if not repertoire:
            messages.error(request, "Veuillez sélectionner un répertoire")
            return redirect('importer_json')

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

        return redirect('accueil_importation')

    return render(request, 'ingest/importer_json.html', {'directories': directories})


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
            f"{resultats['utilisateurs_crees']} nouveaux utilisateurs créés, "
            f"{resultats['communes_geocodees']} communes géocodées",
        )

        return redirect('accueil_importation')

    return render(request, 'ingest/extraire_candidats.html')


@login_required
@user_passes_test(peut_transcrire)
def preparer_importations(request):
    """Vue pour préparer les importations des transcriptions"""
    if request.method == 'POST':
        service = ImportationService()
        importations_creees = service.preparer_importations()

        messages.success(request, f"{importations_creees} importations préparées pour traitement")

        return redirect('liste_importations')

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

        return redirect('liste_importations')

    return redirect('detail_importation', importation_id=importation_id)


@login_required
@user_passes_test(peut_transcrire)
def finaliser_importations_multiples(request):
    """Vue pour finaliser plusieurs importations en même temps"""
    if request.method == 'POST':
        importation_ids = request.POST.getlist('importation_ids')

        if not importation_ids:
            messages.warning(request, "Aucune importation sélectionnée")
            return redirect('liste_importations')

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

        return redirect('liste_importations')

    return redirect('liste_importations')


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

    return redirect('liste_importations')


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

    return redirect('liste_importations')
