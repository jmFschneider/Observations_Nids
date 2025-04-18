# Exemple de vue améliorée pour la saisie d'observations
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime

from Observations.models import (
    FicheObservation, Localisation, Nid, ResumeObservation,
    CausesEchec, Observation, Remarque
)
from Administration.models import Utilisateur
# Supposons que vous avez des formulaires pour chaque modèle
from .forms import (
    FicheObservationForm, LocalisationForm, NidForm, ObservationForm,
    ResumeObservationForm, CausesEchecForm, RemarqueForm
)


@login_required
@transaction.atomic
def saisie_observation(request, fiche_id=None):
    """Vue pour la saisie d'une nouvelle observation ou la modification d'une existante"""

    # En cas de modification, récupérer les objets existants
    if fiche_id:
        fiche = get_object_or_404(FicheObservation, num_fiche=fiche_id)
        try:
            localisation = Localisation.objects.get(fiche=fiche)
        except Localisation.DoesNotExist:
            # Créer l'objet s'il n'existe pas (ne devrait pas arriver avec la nouvelle logique)
            localisation = Localisation.objects.create(fiche=fiche)

        try:
            nid = Nid.objects.get(fiche=fiche)
        except Nid.DoesNotExist:
            # Créer l'objet s'il n'existe pas (ne devrait pas arriver avec la nouvelle logique)
            nid = Nid.objects.create(fiche=fiche)

        try:
            resume = ResumeObservation.objects.get(fiche=fiche)
        except ResumeObservation.DoesNotExist:
            # Créer l'objet s'il n'existe pas (ne devrait pas arriver avec la nouvelle logique)
            resume = ResumeObservation.objects.create(fiche=fiche)

        try:
            causes_echec = CausesEchec.objects.get(fiche=fiche)
        except CausesEchec.DoesNotExist:
            # Créer l'objet s'il n'existe pas (ne devrait pas arriver avec la nouvelle logique)
            causes_echec = CausesEchec.objects.create(fiche=fiche)

        mode = 'modification'
    else:
        # Nouvelle fiche - initialiser des objets vides
        fiche = None
        localisation = None
        nid = None
        resume = None
        causes_echec = None
        mode = 'creation'

    if request.method == 'POST':
        # Traitement des formulaires pour chaque section

        # 1. Récupérer tous les formulaires avec les données POST
        if mode == 'modification':
            fiche_form = FicheObservationForm(request.POST, instance=fiche)
            localisation_form = LocalisationForm(request.POST, instance=localisation)
            nid_form = NidForm(request.POST, instance=nid)
            resume_form = ResumeObservationForm(request.POST, instance=resume)
            causes_echec_form = CausesEchecForm(request.POST, instance=causes_echec)
        else:
            fiche_form = FicheObservationForm(request.POST)
            localisation_form = LocalisationForm(request.POST)
            nid_form = NidForm(request.POST)
            resume_form = ResumeObservationForm(request.POST)
            causes_echec_form = CausesEchecForm(request.POST)

        # Formulaire pour les observations (toujours création ou liste d'instances pour modification en masse)
        observation_form = ObservationForm(request.POST)
        remarque_form = RemarqueForm(request.POST)

        # 2. Vérifier la validité de tous les formulaires requis
        if fiche_form.is_valid() and localisation_form.is_valid() and nid_form.is_valid() and resume_form.is_valid():
            # 3. Enregistrer la fiche principale en premier
            # Si nouvelle fiche: observateur = utilisateur actuel, sinon conserver la valeur
            if mode == 'creation':
                fiche = fiche_form.save(commit=False)
                fiche.observateur = request.user  # Utilisateur actuel comme observateur par défaut
                fiche.save()
                # Les objets liés (Localisation, Nid, etc.) seront créés automatiquement par la méthode save()
            else:
                fiche = fiche_form.save()

            # 4. Mettre à jour les objets liés maintenant que la fiche existe
            # Les objets existent déjà grâce à la méthode save() de FicheObservation ou parce qu'on est en mode modification
            localisation = localisation_form.save(commit=False)
            localisation.fiche = fiche
            localisation.save()

            nid = nid_form.save(commit=False)
            nid.fiche = fiche
            nid.save()

            resume = resume_form.save(commit=False)
            resume.fiche = fiche
            resume.save()

            if causes_echec_form.is_valid():
                causes_echec = causes_echec_form.save(commit=False)
                causes_echec.fiche = fiche
                causes_echec.save()

            # 5. Gérer les observations (peut être multiple, donc logique différente)
            if 'ajouter_observation' in request.POST and observation_form.is_valid():
                observation = observation_form.save(commit=False)
                observation.fiche = fiche
                observation.save()
                messages.success(request, "Observation ajoutée avec succès")

            # 6. Gérer les remarques
            if remarque_form.is_valid() and remarque_form.cleaned_data.get('remarque'):
                remarque = remarque_form.save(commit=False)
                remarque.fiche = fiche
                remarque.save()

            # 7. Redirection selon le mode et le bouton utilisé
            if 'enregistrer_continuer' in request.POST:
                return redirect('saisie_observation', fiche_id=fiche.num_fiche)
            else:
                messages.success(request, f"Fiche d'observation {'modifiée' if mode == 'modification' else 'créée'} avec succès")
                return redirect('detail_observation', fiche_id=fiche.num_fiche)
        else:
            # Erreurs dans les formulaires
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire")
    else:
        # Initialiser les formulaires avec les données existantes s'il s'agit d'une modification
        if mode == 'modification':
            fiche_form = FicheObservationForm(instance=fiche)
            localisation_form = LocalisationForm(instance=localisation)
            nid_form = NidForm(instance=nid)
            resume_form = ResumeObservationForm(instance=resume)
            causes_echec_form = CausesEchecForm(instance=causes_echec)
            # Récupérer les observations existantes
            observations = Observation.objects.filter(fiche=fiche).order_by('date_observation')
            remarques = Remarque.objects.filter(fiche=fiche).order_by('-date_remarque')
        else:
            fiche_form = FicheObservationForm()
            localisation_form = LocalisationForm()
            nid_form = NidForm()
            resume_form = ResumeObservationForm()
            causes_echec_form = CausesEchecForm()
            observations = []
            remarques = []

        observation_form = ObservationForm()
        remarque_form = RemarqueForm()

    context = {
        'fiche_form': fiche_form,
        'localisation_form': localisation_form,
        'nid_form': nid_form,
        'resume_form': resume_form,
        'causes_echec_form': causes_echec_form,
        'observation_form': observation_form,
        'remarque_form': remarque_form,
        'fiche': fiche,
        'mode': mode,
        'observations': observations if mode == 'modification' else [],
        'remarques': remarques if mode == 'modification' else [],
    }

    return render(request, 'observations/saisie_observation.html', context)


@login_required
def supprimer_observation(request, observation_id):
    """Vue pour supprimer une observation spécifique"""
    observation = get_object_or_404(Observation, id=observation_id)
    fiche_id = observation.fiche.num_fiche

    # Vérifier que l'utilisateur est autorisé (observateur, admin, etc.)
    if request.user != observation.fiche.observateur and request.user.role != 'administrateur':
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cette observation")
        return redirect('detail_observation', fiche_id=fiche_id)

    if request.method == 'POST':
        observation.delete()
        messages.success(request, "Observation supprimée avec succès")

    return redirect('saisie_observation', fiche_id=fiche_id)