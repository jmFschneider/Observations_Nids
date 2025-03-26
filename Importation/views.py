# views_importation.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.core.paginator import Paginator

from .importation_service import ImportationService
from .models import (
    TranscriptionBrute, EspeceCandidate, ObservateurCandidat, ImportationEnCours
)
from Observations.models import Espece, Utilisateur

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
    observateurs_candidats = ObservateurCandidat.objects.count()
    observateurs_valides = ObservateurCandidat.objects.exclude(utilisateur_valide=None).count()

    importations_en_attente = ImportationEnCours.objects.filter(statut='en_attente').count()
    importations_erreur = ImportationEnCours.objects.filter(statut='erreur').count()
    importations_completees = ImportationEnCours.objects.filter(statut='complete').count()

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_candidats': observateurs_candidats,
        'observateurs_valides': observateurs_valides,
        'importations_en_attente': importations_en_attente,
        'importations_erreur': importations_erreur,
        'importations_completees': importations_completees,
    }

    return render(request, 'importation/accueil.html', context)


@login_required
@user_passes_test(est_admin)
def importer_json(request):
    import os
    from django.conf import settings

    # Chemin vers le répertoire de résultats de transcription
    base_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results')

    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Répertoire créé: {base_dir}")

    # Liste tous les sous-répertoires (pas les fichiers)
    directories = [d for d in os.listdir(base_dir)
                   if os.path.isdir(os.path.join(base_dir, d))]

    logger.debug(f"Sous-répertoires trouvés: {directories}")

    """Vue pour importer des fichiers JSON depuis un répertoire"""
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
    """Vue pour extraire les espèces et observateurs candidats"""
    if request.method == 'POST':
        service = ImportationService()
        resultats = service.extraire_donnees_candidats()

        messages.success(
            request,
            f"Extraction terminée: {resultats['especes_ajoutees']} nouvelles espèces, "
            f"{resultats['observateurs_ajoutes']} nouveaux observateurs"
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
        else:
            messages.error(request, "Veuillez sélectionner une espèce valide")

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
def liste_observateurs_candidats(request):
    """Vue pour afficher et gérer les observateurs candidats"""
    # Filtre de recherche
    recherche = request.GET.get('recherche', '')
    statut = request.GET.get('statut', 'tous')

    observateurs = ObservateurCandidat.objects.all()

    # Appliquer les filtres
    if recherche:
        observateurs = observateurs.filter(nom_complet_transcrit__icontains=recherche)

    if statut == 'valides':
        observateurs = observateurs.exclude(utilisateur_valide=None)
    elif statut == 'non_valides':
        observateurs = observateurs.filter(utilisateur_valide=None)

    # Pagination
    paginator = Paginator(observateurs.order_by('nom_complet_transcrit'), 20)
    page = request.GET.get('page', 1)
    observateurs_page = paginator.get_page(page)

    # Liste des utilisateurs validés pour le menu déroulant
    utilisateurs_valides = Utilisateur.objects.filter(est_valide=True).order_by('last_name', 'first_name')

    context = {
        'observateurs': observateurs_page,
        'recherche': recherche,
        'statut': statut,
        'utilisateurs_valides': utilisateurs_valides
    }

    return render(request, 'importation/liste_observateurs_candidats.html', context)


@login_required
@user_passes_test(est_admin)
def valider_observateur(request, observateur_id):
    """Vue pour valider un observateur candidat"""
    if request.method == 'POST':
        observateur_candidat = get_object_or_404(ObservateurCandidat, id=observateur_id)
        utilisateur_valide_id = request.POST.get('utilisateur_valide')

        if utilisateur_valide_id:
            try:
                utilisateur_valide = Utilisateur.objects.get(id=utilisateur_valide_id)
                observateur_candidat.utilisateur_valide = utilisateur_valide
                observateur_candidat.validation_manuelle = True
                observateur_candidat.save()

                messages.success(
                    request,
                    f"L'observateur '{observateur_candidat.nom_complet_transcrit}' a été associé à '{utilisateur_valide.first_name} {utilisateur_valide.last_name}'"
                )
            except Utilisateur.DoesNotExist:
                messages.error(request, "L'utilisateur sélectionné n'existe pas")
        else:
            messages.error(request, "Veuillez sélectionner un utilisateur valide")

    return redirect('liste_observateurs_candidats')


@login_required
@user_passes_test(est_admin)
def creer_nouvel_utilisateur(request):
    """Vue pour créer un nouvel utilisateur à partir d'une transcription"""
    if request.method == 'POST':
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        username = request.POST.get('username')
        observateur_candidat_id = request.POST.get('observateur_candidat_id')

        if prenom and nom and email and username:
            # Vérifier si le nom d'utilisateur existe déjà
            if Utilisateur.objects.filter(username=username).exists():
                messages.error(request, f"Le nom d'utilisateur '{username}' existe déjà")
                return redirect('liste_observateurs_candidats')

            # Créer le nouvel utilisateur
            utilisateur = Utilisateur.objects.create(
                username=username,
                email=email,
                first_name=prenom,
                last_name=nom,
                est_valide=True,
                role='observateur'
            )
            utilisateur.set_password('password123')  # Mot de passe par défaut
            utilisateur.save()

            # Si un observateur candidat est spécifié, l'associer
            if observateur_candidat_id:
                try:
                    observateur_candidat = ObservateurCandidat.objects.get(id=observateur_candidat_id)
                    observateur_candidat.utilisateur_valide = utilisateur
                    observateur_candidat.validation_manuelle = True
                    observateur_candidat.save()

                    messages.success(
                        request,
                        f"Nouvel utilisateur '{prenom} {nom}' créé et associé à '{observateur_candidat.nom_complet_transcrit}'"
                    )
                except ObservateurCandidat.DoesNotExist:
                    messages.success(request, f"Nouvel utilisateur '{prenom} {nom}' créé")
            else:
                messages.success(request, f"Nouvel utilisateur '{prenom} {nom}' créé")
        else:
            messages.error(request, "Veuillez remplir tous les champs requis")

    return redirect('liste_observateurs_candidats')


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
    import json
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

