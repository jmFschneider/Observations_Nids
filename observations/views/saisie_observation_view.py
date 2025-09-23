# observations/views/saisie_observation_view.py
import logging
from datetime import datetime  # import datetime as dt
from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import inlineformset_factory
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, redirect, render

from administration.models import Utilisateur  # <-- adapte le chemin

# from django.utils import timezone
from observations.forms import (
    CausesEchecForm,
    FicheObservationForm,
    LocalisationForm,
    NidForm,
    ObservationForm,
    RemarqueForm,
    ResumeObservationForm,
)
from observations.models import FicheObservation, HistoriqueModification, Observation, Remarque

# from observations.views.ajouter_observation import ajouter_observation

logger = logging.getLogger('observations')


def fiche_observation_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    localisation = fiche.localisation

    resume = fiche.resume if hasattr(fiche, 'resume') else None
    nid = fiche.nid if hasattr(fiche, 'nid') else None
    causes_echec = fiche.causes_echec if hasattr(fiche, 'causes_echec') else None

    # Ajout de vérification pour les champs manquants
    observations = fiche.observations.all() if hasattr(fiche, 'observations') else None
    remarques = fiche.remarques.all() if hasattr(fiche, 'remarques') else None

    context = {
        'fiche': fiche,
        'localisation': localisation,
        'resume': resume,
        'nid': nid,
        'causes_echec': causes_echec,
        'observations': observations,
        'remarques': remarques,
    }
    return render(request, 'fiche_observation.html', context)


def saisie_observation(request, fiche_id=None):
    """
    Vue optimisée pour la saisie d'une nouvelle observation ou la modification d'une existante.
    Combine la structure claire de 'saisie_observation_optimisee' avec la logique de sauvegarde robuste
    de 'fiche_test_observation_view'.
    """
    # Définir les variables par défaut
    fiche_instance = None
    localisation_instance = None
    nid_instance = None
    resume_instance = None
    causes_echec_instance = None
    remarques = []

    # Récupérer les données existantes si on est en mode modification
    if fiche_id:
        try:
            fiche_instance = FicheObservation.objects.get(pk=fiche_id)
            localisation_instance = fiche_instance.localisation
            nid_instance = fiche_instance.nid
            resume_instance = fiche_instance.resume
            causes_echec_instance = fiche_instance.causes_echec
            remarques = fiche_instance.remarques.all()
        except FicheObservation.DoesNotExist:
            return render(request, 'saisie/error_page.html', {'message': "Fiche non trouvée"})

    # Définir le formset pour les observations
    observationformset = inlineformset_factory(
        FicheObservation,
        Observation,
        form=ObservationForm,
        fields=['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations'],
        extra=1,
        can_delete=True,  # Mettre True si vous voulez pouvoir supprimer des observations via le formset
        validate_min=False,
        can_order=False,
        min_num=0,
    )

    if request.method == "POST":
        logger.info("Formulaire soumis en POST")

        # Préparer les données POST pour s'assurer que l'observateur est correctement défini
        post_data = request.POST.copy()
        if not post_data.get('observateur'):
            if not fiche_id:
                post_data['observateur'] = request.user.id
            else:
                post_data['observateur'] = str(fiche_instance.observateur.id)

        # Si le champ coordonnees est vide, donner une valeur par défaut
        if not post_data.get('coordonnees'):
            post_data['coordonnees'] = '0,0'

        # Initialiser tous les formulaires avec les données POST
        fiche_form = FicheObservationForm(
            post_data, request.FILES, instance=fiche_instance, user=request.user
        )
        localisation_form = LocalisationForm(post_data, instance=localisation_instance)
        nid_form = NidForm(post_data, instance=nid_instance)
        resume_form = ResumeObservationForm(post_data, instance=resume_instance)
        causes_echec_form = CausesEchecForm(post_data, instance=causes_echec_instance)
        observation_formset = observationformset(post_data, instance=fiche_instance)

        # Validation des formulaires
        validation_errors = []
        forms_valid = True

        if not fiche_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de fiche: {fiche_form.errors}")
            validation_errors.append(f"Erreurs dans les informations de base: {fiche_form.errors}")
            forms_valid = False

        if not localisation_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de localisation: {localisation_form.errors}")
            validation_errors.append(
                f"Erreurs dans les informations de localisation: {localisation_form.errors}"
            )
            forms_valid = False

        if not resume_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de résumé: {resume_form.errors}")
            validation_errors.append(
                f"Erreurs dans le résumé de l'observation: {resume_form.errors}"
            )
            forms_valid = False

        if not nid_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de nid: {nid_form.errors}")
            validation_errors.append(f"Erreurs dans les informations du nid: {nid_form.errors}")
            forms_valid = False

        if not causes_echec_form.is_valid():
            logger.error(
                f"Erreurs dans le formulaire des causes d'échec: {causes_echec_form.errors}"
            )
            validation_errors.append(f"Erreurs dans les causes d'échec: {causes_echec_form.errors}")
            forms_valid = False

        if not observation_formset.is_valid():
            logger.error(f"Erreurs dans le formset d'observations: {observation_formset.errors}")
            for i, form in enumerate(observation_formset):
                if form.has_changed() and form.errors:
                    validation_errors.append(f"Erreurs dans l'observation #{i + 1}: {form.errors}")
            if observation_formset.non_form_errors():
                validation_errors.append(
                    f"Erreurs globales d'observations: {observation_formset.non_form_errors()}"
                )
            forms_valid = False

        # Si tous les formulaires sont valides, procéder à la sauvegarde
        if forms_valid:
            try:
                with transaction.atomic():
                    logger.info("Tous les formulaires sont valides, sauvegarde en cours...")

                    # Récupérer les anciennes instances pour l'historique
                    if fiche_id:
                        fiche_avant = FicheObservation.objects.select_related().get(pk=fiche_id)
                        localisation_avant = fiche_avant.localisation
                        resume_avant = fiche_avant.resume
                        nid_avant = fiche_avant.nid
                        causes_echec_avant = fiche_avant.causes_echec
                    else:
                        (
                            fiche_avant,
                            localisation_avant,
                            resume_avant,
                            nid_avant,
                            causes_echec_avant,
                        ) = None, None, None, None, None

                    # Sauvegarder la fiche principale
                    fiche = fiche_form.save(commit=False)
                    if not fiche_id:
                        fiche.annee = datetime.now().year
                    else:
                        original_fiche = FicheObservation.objects.get(pk=fiche_id)
                        if original_fiche.chemin_image and not fiche.chemin_image:
                            fiche.chemin_image = original_fiche.chemin_image

                    if not hasattr(fiche, 'observateur') or not fiche.observateur:
                        fiche.observateur = request.user
                    fiche.save()

                    if fiche_id and fiche_avant:
                        enregistrer_modifications_historique(
                            fiche, fiche_avant, fiche, 'fiche', request.user
                        )

                    # Sauvegarder les objets liés
                    localisation = localisation_form.save(commit=False)
                    localisation.fiche = fiche
                    localisation.save()
                    if fiche_id and localisation_avant:
                        enregistrer_modifications_historique(
                            fiche, localisation_avant, localisation, 'localisation', request.user
                        )

                    resume = resume_form.save(commit=False)
                    resume.fiche = fiche
                    resume.save()
                    if fiche_id and resume_avant:
                        enregistrer_modifications_historique(
                            fiche, resume_avant, resume, 'resume_observation', request.user
                        )

                    nid = nid_form.save(commit=False)
                    nid.fiche = fiche
                    nid.save()
                    if fiche_id and nid_avant:
                        enregistrer_modifications_historique(
                            fiche, nid_avant, nid, 'nid', request.user
                        )

                    causes_echec = causes_echec_form.save(commit=False)
                    causes_echec.fiche = fiche
                    causes_echec.save()
                    if fiche_id and causes_echec_avant:
                        enregistrer_modifications_historique(
                            fiche, causes_echec_avant, causes_echec, 'causes_echec', request.user
                        )

                    # Gérer les observations
                    if fiche_id:
                        observations_avant = {
                            obs.id: obs for obs in Observation.objects.filter(fiche=fiche_id)
                        }

                    observation_formset.instance = fiche
                    for form in observation_formset:
                        if form.has_changed():
                            if form.cleaned_data.get('date_observation'):
                                try:
                                    if form.instance.pk and form.instance.pk in observations_avant:
                                        # *** MODIFICATION APPLIQUÉE ICI ***
                                        # Mise à jour d'une observation existante (méthode robuste)
                                        nouvelle_obs = form.save(commit=False)
                                        ancienne_obs = observations_avant[form.instance.pk]
                                        enregistrer_modifications_historique(
                                            fiche,
                                            ancienne_obs,
                                            nouvelle_obs,
                                            'observation',
                                            request.user,
                                        )
                                        nouvelle_obs.save()  # Sauvegarde après l'historique
                                    else:
                                        # Nouvelle observation
                                        nouvelle_obs = form.save()
                                        for field_name in [
                                            'date_observation',
                                            'nombre_oeufs',
                                            'nombre_poussins',
                                            'observations',
                                        ]:
                                            if (
                                                field_name in form.cleaned_data
                                                and form.cleaned_data[field_name]
                                            ):
                                                HistoriqueModification.objects.create(
                                                    fiche=fiche,
                                                    champ_modifie=field_name,
                                                    ancienne_valeur="",
                                                    nouvelle_valeur=str(
                                                        form.cleaned_data[field_name]
                                                    ),
                                                    categorie='observation',
                                                    modifie_par=request.user,
                                                )
                                    logger.info(
                                        f"Observation sauvegardée: {form.cleaned_data.get('date_observation')}"
                                    )
                                except Exception as e:
                                    logger.error(f"Erreur sauvegarde observation: {e}")
                            else:
                                logger.warning("Formulaire d'observation modifié mais sans date.")

                    if not fiche_id:
                        remarque_initiale = post_data.get('remarque-initiale')
                        if remarque_initiale:
                            Remarque.objects.create(fiche=fiche, remarque=remarque_initiale)

                    messages.success(request, "Fiche d'observation sauvegardée avec succès!")
                    return redirect('modifier_observation', fiche_id=fiche.pk)

            except Exception as e:
                logger.exception(f"Erreur lors de la sauvegarde: {e}")
                messages.error(request, f"Une erreur est survenue lors de la sauvegarde: {str(e)}")
        else:
            for error in validation_errors:
                messages.error(request, error)

    else:  # GET request
        fiche_form = FicheObservationForm(instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(instance=localisation_instance)
        resume_form = ResumeObservationForm(instance=resume_instance)
        nid_form = NidForm(instance=nid_instance)
        causes_echec_form = CausesEchecForm(instance=causes_echec_instance)
        observation_formset = observationformset(instance=fiche_instance)

    context = {
        'fiche_form': fiche_form,
        'localisation_form': localisation_form,
        'resume_form': resume_form,
        'nid_form': nid_form,
        'causes_echec_form': causes_echec_form,
        'observation_formset': observation_formset,
        'remarques': remarques,
    }

    return render(request, 'saisie/saisie_observation_optimise.html', context)


@login_required
def ajouter_observation(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    if request.method == 'POST':
        form = ObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.fiche = fiche
            observation.save()

            # Enregistrer l'ajout dans l'historique des modifications
            for field_name in [
                'date_observation',
                'nombre_oeufs',
                'nombre_poussins',
                'observations',
            ]:
                if field_name in form.cleaned_data and form.cleaned_data[field_name]:
                    HistoriqueModification.objects.create(
                        fiche=fiche,
                        champ_modifie=field_name,
                        ancienne_valeur="",
                        nouvelle_valeur=str(form.cleaned_data[field_name]),
                        categorie='observation',
                        modifie_par=request.user,
                    )
                    logger.info(
                        f"Ajout d'observation, champ '{field_name}', "
                        f"nouvelle valeur: '{form.cleaned_data[field_name]}', "
                        f"par {request.user.username}"
                    )

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


@login_required
def historique_modifications(request, fiche_id):
    """
    Affiche l'historique des modifications d'une fiche d'observation.
    """
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    modifications = HistoriqueModification.objects.filter(fiche=fiche).order_by(
        '-date_modification'
    )

    return render(
        request,
        'saisie/historique_modifications.html',
        {'fiche': fiche, 'modifications': modifications},
    )


def enregistrer_modifications_historique(
    fiche, ancienne_instance, nouvelle_instance, categorie, modifie_par
):
    if not ancienne_instance or not nouvelle_instance:
        return

    ancien_dict = model_to_dict(ancienne_instance)
    nouveau_dict = model_to_dict(nouvelle_instance)
    champs_ignores = ['id', 'fiche']

    for champ, ancienne_valeur in ancien_dict.items():
        if champ in champs_ignores:
            continue

        nouvelle_valeur = nouveau_dict.get(champ)

        # Normalisation et comparaison
        if str(ancienne_valeur) != str(nouvelle_valeur):
            HistoriqueModification.objects.create(
                fiche=fiche,
                champ_modifie=champ,
                ancienne_valeur=str(ancienne_valeur) if ancienne_valeur is not None else "",
                nouvelle_valeur=str(nouvelle_valeur) if nouvelle_valeur is not None else "",
                categorie=categorie,
                modifie_par=modifie_par,
            )
            logger.info(
                f"Modification sur {categorie}, champ '{champ}', "
                f"ancienne: '{ancienne_valeur}', nouvelle: '{nouvelle_valeur}', par {modifie_par.username}"
            )


@login_required
def supprimer_observation(request, observation_id):
    """Vue pour supprimer une observation spécifique"""
    observation = get_object_or_404(Observation, id=observation_id)
    fiche_id = observation.fiche.num_fiche

    # utilisateur connecté garanti ? idéalement avec @login_required sur la vue
    user = cast(Utilisateur, request.user)
    # Vérifier que l'utilisateur est autorisé (observateur, admin, etc.)
    if user != observation.fiche.observateur and user.role != "administrateur":
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cette observation")
        return redirect("detail_observation", fiche_id=fiche_id)

    if request.method == 'POST':
        observation.delete()
        messages.success(request, "Observation supprimée avec succès")

    return redirect('modifier_observation', fiche_id=fiche_id)
