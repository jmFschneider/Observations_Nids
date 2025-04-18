# Importation/views.py
import logging
import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings

# Importer Utilisateur depuis Administration au lieu de Observations
from Administration.models import Utilisateur
from Observations.models import Espece, FicheObservation
from .importation_service import ImportationService
from .models import (
    TranscriptionBrute, EspeceCandidate, ImportationEnCours
)

logger = logging.getLogger(__name__)


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'administrateur'


@login_required
@user_passes_test(est_admin)
def accueil_importation(request):
    """Vue d'accueil pour le système d'importation"""
    # Statistiques
    total_transcriptions = TranscriptionBrute.objects.count()
    transcriptions_traitees = TranscriptionBrute.objects.filter(traite=True).count()
    especes_candidates = EspeceCandidate.objects.count()
    especes_validees = EspeceCandidate.objects.exclude(espece_validee=None).count()
    observateurs_transcription = Utilisateur.objects.filter(est_transcription=True).count()

    importations_en_attente = ImportationEnCours.objects.filter(statut='en_attente').count()
    importations_erreur = ImportationEnCours.objects.filter(statut='erreur').count()
    importations_completees = ImportationEnCours.objects.filter(statut='complete').count()

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_transcription': observateurs_transcription,
        'importations_en_attente': importations_en_attente,
        'importations_erreur': importations_erreur,
        'importations_completees': importations_completees,
    }

    return render(request, 'importation/accueil.html', context)


@login_required
@user_passes_test(est_admin)
def importer_json(request):
    """Vue pour importer des fichiers JSON depuis un répertoire"""
    # Chemin vers le répertoire de résultats de transcription
    base_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results')

    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Répertoire créé: {base_dir}")

    # Liste tous les sous-répertoires (pas les fichiers)
    directories = [d for d in os.listdir(base_dir)
                   if os.path.isdir(os.path.join(base_dir, d))]

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
            f"{len(resultats['erreurs'])} erreurs"
        )

        return redirect('accueil_importation')

    return render(request, 'importation/importer_json.html', {'directories': directories})


@login_required
@user_passes_test(est_admin)
def extraire_candidats(request):
    """Vue pour extraire les espèces et créer automatiquement les utilisateurs"""
    if request.method == 'POST':
        service = ImportationService()
        resultats = service.extraire_donnees_candidats()

        messages.success(
            request,
            f"Extraction terminée: {resultats['especes_ajoutees']} nouvelles espèces, "
            f"{resultats['utilisateurs_crees']} nouveaux utilisateurs créés"
        )

        return redirect('accueil_importation')

    return render(request, 'importation/extraire_candidats.html')


@login_required
@user_passes_test(est_admin)
def liste_especes_candidates(request):
    """Vue pour afficher et gérer les espèces candidates"""
    # Filtre de recherche
    recherche = request.GET.get('recherche', '')
    statut = request.GET.get('statut', 'tous')

    especes = EspeceCandidate.objects.all()

    # Appliquer les filtres
    if recherche:
        especes = especes.filter(nom_transcrit__icontains=recherche)

    if statut == 'valides':
        especes = especes.exclude(espece_validee=None)
    elif statut == 'non_valides':
        especes = especes.filter(espece_validee=None)

    # Pagination
    paginator = Paginator(especes.order_by('nom_transcrit'), 20)
    page = request.GET.get('page', 1)
    especes_page = paginator.get_page(page)

    # Liste des espèces validées pour le menu déroulant
    especes_validees = Espece.objects.filter(valide_par_admin=True).order_by('nom')

    context = {
        'especes': especes_page,
        'recherche': recherche,
        'statut': statut,
        'especes_validees': especes_validees
    }

    return render(request, 'importation/liste_especes_candidates.html', context)


@login_required
@user_passes_test(est_admin)
def valider_espece(request, espece_id):
    """Vue pour valider une espèce candidate"""
    if request.method == 'POST':
        espece_candidate = get_object_or_404(EspeceCandidate, id=espece_id)
        espece_validee_id = request.POST.get('espece_validee')
        nom_espece = request.POST.get('nom_espece')

        # Cas 1: Une espèce existante a été sélectionnée
        if espece_validee_id:
            try:
                espece_validee = Espece.objects.get(id=espece_validee_id)
                espece_candidate.espece_validee = espece_validee
                espece_candidate.validation_manuelle = True
                espece_candidate.save()

                messages.success(
                    request,
                    f"L'espèce '{espece_candidate.nom_transcrit}' a été associée à '{espece_validee.nom}'"
                )
            except Espece.DoesNotExist:
                messages.error(request, "L'espèce sélectionnée n'existe pas")

        # Cas 2: Un nouveau nom d'espèce a été saisi
        elif nom_espece and nom_espece.strip():
            try:
                # Vérifier si l'espèce existe déjà avec ce nom
                espece_existante = Espece.objects.filter(nom__iexact=nom_espece.strip()).first()

                if espece_existante:
                    # Si elle existe, l'utiliser
                    espece_candidate.espece_validee = espece_existante
                    espece_candidate.validation_manuelle = True
                    espece_candidate.save()

                    messages.success(
                        request,
                        f"L'espèce '{espece_candidate.nom_transcrit}' a été associée à l'espèce existante '{espece_existante.nom}'"
                    )
                else:
                    # Sinon, créer une nouvelle espèce
                    nouvelle_espece = Espece.objects.create(
                        nom=nom_espece.strip(),
                        valide_par_admin=True  # Validée par un admin
                    )

                    espece_candidate.espece_validee = nouvelle_espece
                    espece_candidate.validation_manuelle = True
                    espece_candidate.save()

                    messages.success(
                        request,
                        f"Une nouvelle espèce '{nouvelle_espece.nom}' a été créée et associée à '{espece_candidate.nom_transcrit}'"
                    )
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de l'espèce: {str(e)}")
        else:
            messages.error(request,
                           "Veuillez soit sélectionner une espèce existante, soit saisir un nouveau nom d'espèce")

    return redirect('liste_especes_candidates')

@login_required
@user_passes_test(est_admin)
def creer_nouvelle_espece(request):
    """Vue pour créer une nouvelle espèce à partir d'une transcription"""
    if request.method == 'POST':
        nom_espece = request.POST.get('nom_espece')
        espece_candidate_id = request.POST.get('espece_candidate_id')

        if nom_espece:
            # Créer la nouvelle espèce
            espece = Espece.objects.create(
                nom=nom_espece,
                valide_par_admin=True
            )

            # Si une espèce candidate est spécifiée, l'associer
            if espece_candidate_id:
                try:
                    espece_candidate = EspeceCandidate.objects.get(id=espece_candidate_id)
                    espece_candidate.espece_validee = espece
                    espece_candidate.validation_manuelle = True
                    espece_candidate.save()

                    messages.success(
                        request,
                        f"Nouvelle espèce '{nom_espece}' créée et associée à '{espece_candidate.nom_transcrit}'"
                    )
                except EspeceCandidate.DoesNotExist:
                    messages.success(request, f"Nouvelle espèce '{nom_espece}' créée")
            else:
                messages.success(request, f"Nouvelle espèce '{nom_espece}' créée")
        else:
            messages.error(request, "Veuillez spécifier un nom d'espèce")

    # Rediriger vers la liste des espèces candidates
    return redirect('liste_especes_candidates')


@login_required
@user_passes_test(est_admin)
def preparer_importations(request):
    """Vue pour préparer les importations des transcriptions"""
    if request.method == 'POST':
        service = ImportationService()
        importations_creees = service.preparer_importations()

        messages.success(
            request,
            f"{importations_creees} importations préparées pour traitement"
        )

        return redirect('liste_importations')

    return render(request, 'importation/preparer_importations.html')


@login_required
@user_passes_test(est_admin)
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

    context = {
        'importations': importations_page,
        'statut': statut
    }

    return render(request, 'importation/liste_importations.html', context)


@login_required
@user_passes_test(est_admin)
def detail_importation(request, importation_id):
    """Vue pour afficher les détails d'une importation"""
    importation = get_object_or_404(ImportationEnCours, id=importation_id)
    transcription = importation.transcription

    # Afficher le contenu JSON formaté
    donnees_json = json.dumps(transcription.json_brut, indent=2, ensure_ascii=False)

    context = {
        'importation': importation,
        'transcription': transcription,
        'donnees_json': donnees_json
    }

    return render(request, 'importation/detail_importation.html', context)


@login_required
@user_passes_test(est_admin)
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
@user_passes_test(est_admin)
def resume_importation(request):
    """Vue pour afficher un résumé des importations"""
    # Statistiques
    total_transcriptions = TranscriptionBrute.objects.count()
    transcriptions_traitees = TranscriptionBrute.objects.filter(traite=True).count()

    # Espèces
    especes_candidates = EspeceCandidate.objects.count()
    especes_validees = EspeceCandidate.objects.exclude(espece_validee=None).count()

    # Observateurs
    observateurs_transcription = Utilisateur.objects.filter(est_transcription=True).count()

    # Fiches
    fiches_importees = FicheObservation.objects.filter(
        observateur__est_transcription=True
    ).count()

    # Récentes importations
    recentes_importations = ImportationEnCours.objects.filter(
        statut='complete'
    ).order_by('-date_creation')[:10]

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_transcription': observateurs_transcription,
        'fiches_importees': fiches_importees,
        'recentes_importations': recentes_importations,
    }

    return render(request, 'importation/resume_importation.html', context)


@login_required
@user_passes_test(est_admin)
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
@user_passes_test(est_admin)
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
            query = Q(statut='complete') | Q(statut='erreur') | Q(statut='en_attente')  # Inclure 'en_attente'

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