from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from Observations.forms import (
    FicheObservationForm,
    LocalisationForm,
    ResumeObservationForm,
    NidForm,
    CausesEchecForm, RemarqueForm, ObservationForm,
)
from Observations.models import FicheObservation, Remarque, Observation
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory

import logging

logger = logging.getLogger('Observations')


@login_required
def fiche_test_observation_view(request, fiche_id=None):
    fiche_instance = None
    remarques = []

    if fiche_id:
        try:
            fiche_instance = FicheObservation.objects.get(pk=fiche_id)
            localisation_instance = fiche_instance.localisation
            resume_instance = fiche_instance.resume
            nid_instance = fiche_instance.nid
            causes_echec_instance = fiche_instance.causes_echec
            remarques = fiche_instance.remarques.all()
        except FicheObservation.DoesNotExist:
            return render(request, 'saisie/error_page.html', {'message': "Fiche non trouvée"})
    else:
        localisation_instance = None
        resume_instance = None
        nid_instance = None
        causes_echec_instance = None

    # --- Formset pour les observations ---
    ObservationFormSet = inlineformset_factory(
        FicheObservation,
        Observation,
        form=ObservationForm,
        fields=['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations'],
        extra=1,
        can_delete=False,
        validate_min=False,  # Ne pas valider les formulaires vides
        can_order=False,
        min_num=0,  # Pas de minimum requis
    )

    if request.method == "POST":
        logger.info("Formulaire soumis en POST")

        # Assurez-vous que l'observateur est défini correctement
        post_data = request.POST.copy()
        if not post_data.get('observateur'):
            # Si c'est une nouvelle fiche, utiliser l'utilisateur actuel
            if not fiche_id:
                post_data['observateur'] = request.user.id
            # Si c'est une fiche existante, utiliser l'observateur original
            else:
                post_data['observateur'] = str(fiche_instance.observateur.id)

        # Si le champ coordonnees est vide, donnez-lui une valeur par défaut
        if not post_data.get('coordonnees'):
            post_data['coordonnees'] = '0,0'

        # Note: Le paramètre user=request.user est également passé au formulaire pour
        # contrôler les permissions et la présentation du champ observateur
        fiche_form = FicheObservationForm(post_data, request.FILES, instance=fiche_instance, user=request.user)

        localisation_form = LocalisationForm(post_data, instance=localisation_instance)
        resume_form = ResumeObservationForm(post_data, instance=resume_instance)
        nid_form = NidForm(post_data, instance=nid_instance)
        causes_echec_form = CausesEchecForm(post_data, instance=causes_echec_instance)
        observation_formset = ObservationFormSet(post_data, instance=fiche_instance)

        # Validation de chaque formulaire
        validation_errors = []
        if not fiche_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de fiche: {fiche_form.errors}")
            validation_errors.append(f"Erreurs dans les informations de base: {fiche_form.errors}")

        if not localisation_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de localisation: {localisation_form.errors}")
            validation_errors.append(f"Erreurs dans les informations de localisation: {localisation_form.errors}")

        if not resume_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de résumé: {resume_form.errors}")
            validation_errors.append(f"Erreurs dans le résumé de l'observation: {resume_form.errors}")

        if not nid_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de nid: {nid_form.errors}")
            validation_errors.append(f"Erreurs dans les informations du nid: {nid_form.errors}")

        if not causes_echec_form.is_valid():
            logger.error(f"Erreurs dans le formulaire des causes d'échec: {causes_echec_form.errors}")
            validation_errors.append(f"Erreurs dans les causes d'échec: {causes_echec_form.errors}")

        if not observation_formset.is_valid():
            logger.error(f"Erreurs dans le formset d'observations: {observation_formset.errors}")
            for i, form in enumerate(observation_formset):
                # Ne vérifier les erreurs que si le formulaire n'est pas vide
                if form.has_changed() and form.errors:
                    validation_errors.append(f"Erreurs dans l'observation #{i + 1}: {form.errors}")
            if observation_formset.non_form_errors():
                validation_errors.append(f"Erreurs globales d'observations: {observation_formset.non_form_errors()}")

        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
        else:
            try:
                with transaction.atomic():
                    logger.info("Tous les formulaires sont valides, sauvegarde...")

                    # Sauvegarde de la fiche principale
                    fiche = fiche_form.save(commit=False)
                    if not fiche_id:  # Nouvelle fiche
                        fiche.annee = datetime.now().year

                    # S'assurer que l'observateur est défini
                    if not hasattr(fiche, 'observateur') or not fiche.observateur:
                        fiche.observateur = request.user

                    fiche.save()
                    logger.info(f"Fiche sauvegardée avec ID: {fiche.pk}")

                    # Sauvegarde des sous-formulaires
                    localisation = localisation_form.save(commit=False)
                    localisation.fiche = fiche
                    localisation.save()

                    resume = resume_form.save(commit=False)
                    resume.fiche = fiche
                    resume.save()

                    nid = nid_form.save(commit=False)
                    nid.fiche = fiche
                    nid.save()

                    causes_echec = causes_echec_form.save(commit=False)
                    causes_echec.fiche = fiche
                    causes_echec.save()

                    # Sauvegarde des observations
                    observation_formset.instance = fiche
                    # Ne sauvegarder que les formulaires qui ont été modifiés et qui sont valides
                    for form in observation_formset:
                        # Vérifier si le formulaire a été modifié
                        if form.has_changed():
                            # Vérifier si la date d'observation est renseignée
                            if form.cleaned_data.get('date_observation'):
                                try:
                                    form.save()
                                    logger.info(f"Observation sauvegardée avec date: {form.cleaned_data.get('date_observation')}")
                                except Exception as e:
                                    logger.error(f"Erreur lors de la sauvegarde de l'observation: {e}")
                            else:
                                logger.warning("Formulaire d'observation modifié mais sans date d'observation")
                    # observation_formset.save()

                    # Remarque initiale pour nouvelle fiche
                    if not fiche_id:
                        remarque_initiale = post_data.get('remarque-initiale')
                        if remarque_initiale:
                            Remarque.objects.create(fiche=fiche, remarque=remarque_initiale)

                    messages.success(request, "Fiche d'observation sauvegardée avec succès!")

                    # Redirection vers la page d'édition
                    return redirect('modifier_observation', fiche_id=fiche.pk)

            except Exception as e:
                logger.exception(f"Erreur lors de la sauvegarde: {e}")
                messages.error(request, f"Une erreur est survenue lors de la sauvegarde: {str(e)}")

    else:
        # GET request - affichage du formulaire
        fiche_form = FicheObservationForm(instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(instance=localisation_instance)
        resume_form = ResumeObservationForm(instance=resume_instance)
        nid_form = NidForm(instance=nid_instance)
        causes_echec_form = CausesEchecForm(instance=causes_echec_instance)
        observation_formset = ObservationFormSet(instance=fiche_instance)

    return render(request, 'saisie/saisie_observation_test.html', {
        'fiche_form': fiche_form,
        'localisation_form': localisation_form,
        'resume_form': resume_form,
        'nid_form': nid_form,
        'causes_echec_form': causes_echec_form,
        'observation_formset': observation_formset,
        'remarques': remarques,
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
            return redirect('modifier_observation', fiche_id=fiche_id)
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
            return redirect('modifier_observation', fiche_id=fiche_id)
    else:
        form = RemarqueForm(initial={'fiche': fiche})
    return render(request, 'saisie/ajouter_remarque.html', {'form': form})
