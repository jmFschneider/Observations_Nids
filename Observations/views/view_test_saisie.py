from django.shortcuts import render, redirect, get_object_or_404
from Observations.forms import (
    FicheObservationForm,
    LocalisationForm,
    ResumeObservationForm,
    NidForm,
    CausesEchecForm, RemarqueForm, ObservationForm,
)
from Observations.models import FicheObservation, Remarque
from datetime import datetime
from django.contrib.auth.decorators import login_required


@login_required
def fiche_test_observation_view(request, fiche_id=None):
    fiche_instance = None
    remarques = []
    observations = []

    if fiche_id:
        try:
            fiche_instance = FicheObservation.objects.get(pk=fiche_id)
            localisation_instance = fiche_instance.localisation
            resume_instance = fiche_instance.resume
            nid_instance = fiche_instance.nid
            causes_echec_instance = fiche_instance.causes_echec
            remarques = Remarque.objects.filter(fiche=fiche_instance)
            observations = fiche_instance.observations.all()
        except FicheObservation.DoesNotExist:
            return render(request, 'saisie/error_page.html', {'message': "Fiche non trouvée"})
    else:
        localisation_instance = None
        resume_instance = None
        nid_instance = None
        causes_echec_instance = None

    if request.method == "POST":
        fiche_form = FicheObservationForm(request.POST, request.FILES, instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(request.POST, instance=localisation_instance)
        resume_form = ResumeObservationForm(request.POST, instance=resume_instance)
        nid_form = NidForm(request.POST, instance=nid_instance)
        causes_echec_form = CausesEchecForm(request.POST, instance=causes_echec_instance)

        forms = [fiche_form, localisation_form, resume_form, nid_form, causes_echec_form]

        if all(form.is_valid() for form in forms):
            fiche = fiche_form.save(commit=False)

            # Empêcher la modification de l'observateur si l'utilisateur n'est pas admin ou reviewer
            if request.user.role not in ['administrateur', 'reviewer']:
                fiche.observateur = request.user

            fiche.annee = datetime.now().year
            fiche.save()

            # Lier les autres sous-modèles à la fiche
            for form in forms[1:]:
                instance = form.save(commit=False)
                instance.fiche = fiche
                instance.save()

            # Gérer la remarque initiale
            remarque_initiale = request.POST.get('remarque-initiale')
            if remarque_initiale:
                Remarque.objects.create(fiche=fiche, remarque=remarque_initiale)

            return redirect('saisie_test_edit', fiche_id=fiche.pk)

    else:
        fiche_form = FicheObservationForm(instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(instance=localisation_instance)
        resume_form = ResumeObservationForm(instance=resume_instance)
        nid_form = NidForm(instance=nid_instance)
        causes_echec_form = CausesEchecForm(instance=causes_echec_instance)

    return render(request, 'saisie/saisie_observation_test.html', {
        'fiche_form': fiche_form,
        'localisation_form': localisation_form,
        'resume_form': resume_form,
        'nid_form': nid_form,
        'causes_echec_form': causes_echec_form,
        'remarques': remarques,
        'observations': observations,
    })

@login_required
def ajouter_observation(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    if request.method == 'POST':
        form = ObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.fiche = fiche
            observation.save()
            return redirect('saisie_test_edit', fiche_id=fiche_id)
    else:
        form = ObservationForm()
    return render(request, 'saisie/ajouter_observation.html', {'form': form, 'fiche': fiche})


@login_required
def ajouter_remarque(request, fiche_id):
    fiche = FicheObservation.objects.get(pk=fiche_id)
    if request.method == 'POST':
        form = RemarqueForm(request.POST)
        if form.is_valid():
            remarque = form.save(commit=False)
            remarque.fiche = fiche
            remarque.save()
            return redirect('saisie_test_edit', fiche_id=fiche_id)
    else:
        form = RemarqueForm(initial={'fiche': fiche})
    return render(request, 'saisie/ajouter_remarque.html', {'form': form})
