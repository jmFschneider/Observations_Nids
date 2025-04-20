# Importation/views/especes.py
import logging
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator

from Observations.models import Espece
from Importation.models import EspeceCandidate
from .auth import est_admin

logger = logging.getLogger(__name__)


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