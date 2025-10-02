# observations/views/saisie_observation_view.py
import logging
from datetime import datetime
from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Utilisateur
from audit.models import HistoriqueModification
from observations.forms import (
    CausesEchecForm,
    FicheObservationForm,
    LocalisationForm,
    NidForm,
    ObservationForm,
    RemarqueForm,
    ResumeObservationForm,
)
from observations.models import FicheObservation, Observation, Remarque

logger = logging.getLogger('observations')


def handle_remarques_update(request, fiche_instance, remarqueformset):
    """
    Traite uniquement la mise à jour des remarques via AJAX.
    """
    try:
        with transaction.atomic():
            # Créer le formset avec les données POST
            remarque_formset = remarqueformset(request.POST, instance=fiche_instance)

            if remarque_formset.is_valid():
                # Récupérer les remarques avant modification pour l'historique
                remarques_avant = {r.id: r for r in fiche_instance.remarques.all()}

                # Tracer les modifications avant sauvegarde
                for form in remarque_formset:
                    if form.cleaned_data:
                        remarque_id = form.cleaned_data.get('id')
                        remarque_text = form.cleaned_data.get('remarque', '')
                        is_deleted = form.cleaned_data.get('DELETE', False)

                        if remarque_id and is_deleted:
                            # Remarque supprimée
                            if remarque_id.id in remarques_avant:
                                HistoriqueModification.objects.create(
                                    fiche=fiche_instance,
                                    champ_modifie='remarque_supprimee',
                                    ancienne_valeur=remarques_avant[remarque_id.id].remarque,
                                    nouvelle_valeur="",
                                    categorie='remarque',
                                    modifie_par=request.user,
                                )
                        elif remarque_id and not is_deleted:
                            # Remarque modifiée
                            if remarque_id.id in remarques_avant and remarques_avant[remarque_id.id].remarque != remarque_text:
                                HistoriqueModification.objects.create(
                                    fiche=fiche_instance,
                                    champ_modifie='remarque_modifiee',
                                    ancienne_valeur=remarques_avant[remarque_id.id].remarque,
                                    nouvelle_valeur=remarque_text,
                                    categorie='remarque',
                                    modifie_par=request.user,
                                )
                        elif not remarque_id and remarque_text.strip():
                            # Nouvelle remarque
                            HistoriqueModification.objects.create(
                                fiche=fiche_instance,
                                champ_modifie='remarque_ajoutee',
                                ancienne_valeur="",
                                nouvelle_valeur=remarque_text,
                                categorie='remarque',
                                modifie_par=request.user,
                            )

                # Sauvegarder le formset (gère automatiquement les suppressions)
                remarque_formset.save()

                return JsonResponse({'status': 'success'})
            else:
                logger.error(f"Erreurs dans le formset de remarques: {remarque_formset.errors}")
                return JsonResponse({'status': 'error', 'errors': remarque_formset.errors}, status=400)

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des remarques: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def handle_get_remarques(request, fiche_instance):
    """
    Retourne les remarques d'une fiche au format JSON.
    """
    try:
        if fiche_instance:
            remarques = []
            for remarque in fiche_instance.remarques.all():
                remarques.append({
                    'id': remarque.id,
                    'remarque': remarque.remarque,
                    'date_remarque': remarque.date_remarque.strftime('%d/%m/%Y %H:%M'),
                    'toDelete': False
                })
            return JsonResponse({'remarques': remarques})
        else:
            return JsonResponse({'remarques': []})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des remarques: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
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


@login_required
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
        extra=0,
        can_delete=True,
        validate_min=False,
        can_order=False,
        min_num=0,
        max_num=None,  # Pas de limite sur le nombre max
    )

    # Définir le formset pour les remarques
    remarqueformset = inlineformset_factory(
        FicheObservation,
        Remarque,
        form=RemarqueForm,
        fields=['remarque'],
        extra=1,  # Une ligne vide pour ajouter
        can_delete=True,
        validate_min=False,
        can_order=False,
        min_num=0,
    )

    if request.method == "POST":

        # Traitement spécial pour la mise à jour des remarques uniquement (via AJAX)
        if request.POST.get('action') == 'update_remarques':
            return handle_remarques_update(request, fiche_instance, remarqueformset)

    # Traitement spécial pour récupérer les remarques via AJAX (GET)
    if request.GET.get('get_remarques') == '1' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return handle_get_remarques(request, fiche_instance)

    if request.method == "POST":
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

        observation_formset = observationformset(post_data, request.FILES, instance=fiche_instance)
        remarque_formset = remarqueformset(post_data, instance=fiche_instance)

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

        if not remarque_formset.is_valid():
            logger.error(f"Erreurs dans le formset de remarques: {remarque_formset.errors}")
            for i, form in enumerate(remarque_formset):
                if form.has_changed() and form.errors:
                    validation_errors.append(f"Erreurs dans la remarque #{i + 1}: {form.errors}")
            if remarque_formset.non_form_errors():
                validation_errors.append(
                    f"Erreurs globales de remarques: {remarque_formset.non_form_errors()}"
                )
            forms_valid = False

        # Si tous les formulaires sont valides, procéder à la sauvegarde
        if forms_valid:
            try:
                with transaction.atomic():

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
                            fiche, fiche_avant, fiche, 'fiche', request.user, fiche_form.changed_data
                        )

                    # Sauvegarder les objets liés
                    localisation = localisation_form.save(commit=False)
                    localisation.fiche = fiche
                    localisation.save()
                    if fiche_id and localisation_avant:
                        enregistrer_modifications_historique(
                            fiche, localisation_avant, localisation, 'localisation', request.user, localisation_form.changed_data
                        )

                    resume = resume_form.save(commit=False)
                    resume.fiche = fiche
                    resume.save()
                    if fiche_id and resume_avant:
                        enregistrer_modifications_historique(
                            fiche, resume_avant, resume, 'resume_observation', request.user, resume_form.changed_data
                        )

                    nid = nid_form.save(commit=False)
                    nid.fiche = fiche
                    nid.save()
                    if fiche_id and nid_avant:
                        enregistrer_modifications_historique(
                            fiche, nid_avant, nid, 'nid', request.user, nid_form.changed_data
                        )

                    causes_echec = causes_echec_form.save(commit=False)
                    causes_echec.fiche = fiche
                    causes_echec.save()
                    if fiche_id and causes_echec_avant:
                        enregistrer_modifications_historique(
                            fiche, causes_echec_avant, causes_echec, 'causes_echec', request.user, causes_echec_form.changed_data
                        )

                    # Gérer les observations
                    if fiche_id:
                        observations_avant = {
                            obs.id: obs for obs in Observation.objects.filter(fiche=fiche_id)
                        }

                    # Sauvegarder le formset d'observations avec gestion manuelle des suppressions
                    saved_observations = observation_formset.save(commit=False)

                    # Utiliser uniquement deleted_objects du formset pour gérer les suppressions
                    observations_a_supprimer = list(observation_formset.deleted_objects)

                    # Sauvegarder les observations modifiées/nouvelles
                    for obs in saved_observations:
                        obs.fiche = fiche
                        obs.save()

                    # Gérer l'historique pour les observations modifiées
                    for form in observation_formset:
                        if form.has_changed() and form.instance.pk:
                            if fiche_id and form.instance.pk in observations_avant:
                                # Observation existante modifiée
                                ancienne_obs = observations_avant[form.instance.pk]
                                champs_modifies = list(form.changed_data)

                                enregistrer_modifications_historique(
                                    fiche,
                                    ancienne_obs,
                                    form.instance,
                                    'observation',
                                    request.user,
                                    champs_modifies
                                )
                        elif form.has_changed() and not form.instance.pk and form.cleaned_data.get('date_observation'):
                            # Nouvelle observation
                            for field_name in ['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations']:
                                if field_name in form.cleaned_data and form.cleaned_data[field_name]:
                                    HistoriqueModification.objects.create(
                                        fiche=fiche,
                                        champ_modifie=field_name,
                                        ancienne_valeur="",
                                        nouvelle_valeur=str(form.cleaned_data[field_name]),
                                        categorie='observation',
                                        modifie_par=request.user,
                                    )

                    # Traiter les suppressions d'observations
                    for obs_a_supprimer in observations_a_supprimer:
                        HistoriqueModification.objects.create(
                            fiche=fiche,
                            champ_modifie='observation_supprimee',
                            ancienne_valeur=f"Date: {obs_a_supprimer.date_observation}, Œufs: {obs_a_supprimer.nombre_oeufs}, Poussins: {obs_a_supprimer.nombre_poussins}",
                            nouvelle_valeur="",
                            categorie='observation',
                            modifie_par=request.user,
                        )
                        obs_a_supprimer.delete()

                    # Sauvegarder le formset des remarques
                    saved_remarques = remarque_formset.save(commit=False)
                    for remarque in saved_remarques:
                        remarque.fiche = fiche
                        remarque.save()
                    remarque_formset.save_m2m()

                    # Traiter les suppressions et ajouts de remarques pour l'historique
                    if fiche_id:
                        # Récupérer les remarques avant et après
                        remarques_avant_ids = {r.id for r in remarques}
                        remarques_apres_ids = {r.id for r in saved_remarques if r.id}

                        # Gestion des suppressions de remarques
                        remarques_supprimees_ids = remarques_avant_ids - remarques_apres_ids
                        for remarque in remarques:
                            if remarque.id in remarques_supprimees_ids:
                                HistoriqueModification.objects.create(
                                    fiche=fiche,
                                    champ_modifie='remarque_supprimee',
                                    ancienne_valeur=remarque.remarque,
                                    nouvelle_valeur="",
                                    categorie='remarque',
                                    modifie_par=request.user,
                                )

                    # Gestion de l'ajout de remarques nouvelles
                    for remarque in saved_remarques:
                        if not remarque.id or remarque.id not in {r.id for r in remarques}:
                            HistoriqueModification.objects.create(
                                fiche=fiche,
                                champ_modifie='remarque_ajoutee',
                                ancienne_valeur="",
                                nouvelle_valeur=remarque.remarque,
                                categorie='remarque',
                                modifie_par=request.user,
                            )

                    if not fiche_id:
                        remarque_initiale = post_data.get('remarque-initiale')
                        if remarque_initiale:
                            Remarque.objects.create(fiche=fiche, remarque=remarque_initiale)

                    # Mettre à jour les années des observations APRÈS le traitement du formset
                    if fiche_id and fiche_avant and 'annee' in fiche_form.changed_data and fiche_avant.annee != fiche.annee:
                        mettre_a_jour_annee_observations(
                            fiche, fiche_avant.annee, fiche.annee, request.user
                        )

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
        if fiche_instance:
            # HACK: Remove unsaved observations that may be lingering in memory
            if hasattr(fiche_instance, 'observations'):
                unsaved_obs = [obs for obs in fiche_instance.observations.all() if obs.pk is None]
                if unsaved_obs:
                    fiche_instance.observations.remove(*unsaved_obs)

        observation_formset = observationformset(instance=fiche_instance)
        remarque_formset = remarqueformset(instance=fiche_instance)

    context = {
        'fiche_form': fiche_form,
        'localisation_form': localisation_form,
        'resume_form': resume_form,
        'nid_form': nid_form,
        'causes_echec_form': causes_echec_form,
        'observation_formset': observation_formset,
        'remarque_formset': remarque_formset,
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

            # Enregistrer l'ajout dans l'historique des modifications (une seule ligne)
            HistoriqueModification.objects.create(
                fiche=fiche,
                champ_modifie='observation_ajoutee',
                ancienne_valeur="",
                nouvelle_valeur=f"Date: {observation.date_observation}, Œufs: {observation.nombre_oeufs}, Poussins: {observation.nombre_poussins}",
                categorie='observation',
                modifie_par=request.user,
            )

            return redirect('modifier_observation', fiche_id=fiche_id)
    else:
        form = ObservationForm()
    return render(request, 'saisie/ajouter_observation.html', {'form': form, 'fiche': fiche, 'fiche_id': fiche_id})


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


def mettre_a_jour_annee_observations(fiche, ancienne_annee, nouvelle_annee, modifie_par):
    """
    Met à jour l'année de toutes les observations d'une fiche lorsque l'année de la fiche change.
    """
    if ancienne_annee == nouvelle_annee:
        return

    for observation in fiche.observations.all():
        if observation.date_observation and observation.date_observation.year == ancienne_annee:
            nouvelle_date = observation.date_observation.replace(year=nouvelle_annee)

            HistoriqueModification.objects.create(
                fiche=fiche,
                champ_modifie='date_observation',
                ancienne_valeur=str(observation.date_observation),
                nouvelle_valeur=str(nouvelle_date),
                categorie='observation',
                modifie_par=modifie_par,
            )

            observation.date_observation = nouvelle_date
            observation.save()


def enregistrer_modifications_historique(
    fiche, ancienne_instance, nouvelle_instance, categorie, modifie_par, champs_modifies=None
):
    if not ancienne_instance or not nouvelle_instance:
        return

    champs_ignores = ['id', 'fiche', 'DELETE']

    # Si on a une liste de champs modifiés, ne traiter que ceux-ci
    if champs_modifies:
        champs_a_verifier = champs_modifies
    else:
        champs_a_verifier = [field.name for field in ancienne_instance._meta.fields]

    for champ in champs_a_verifier:
        if champ in champs_ignores:
            continue

        # Vérifier que l'attribut existe vraiment sur le modèle
        if not hasattr(ancienne_instance, champ) or not hasattr(nouvelle_instance, champ):
            continue

        ancienne_valeur = getattr(ancienne_instance, champ)
        nouvelle_valeur = getattr(nouvelle_instance, champ)

        # Comparaison spéciale pour les DateTimeField avec fuseau horaire
        if hasattr(ancienne_valeur, 'year') and hasattr(nouvelle_valeur, 'year'):
            ancienne_dt = (ancienne_valeur.year, ancienne_valeur.month, ancienne_valeur.day,
                          ancienne_valeur.hour, ancienne_valeur.minute, ancienne_valeur.second)
            nouvelle_dt = (nouvelle_valeur.year, nouvelle_valeur.month, nouvelle_valeur.day,
                          nouvelle_valeur.hour, nouvelle_valeur.minute, nouvelle_valeur.second)
            valeurs_egales = ancienne_dt == nouvelle_dt
        elif ancienne_valeur is None and nouvelle_valeur is None:
            valeurs_egales = True
        elif ancienne_valeur is None or nouvelle_valeur is None:
            valeurs_egales = False
        else:
            valeurs_egales = str(ancienne_valeur) == str(nouvelle_valeur)

        if not valeurs_egales:
            HistoriqueModification.objects.create(
                fiche=fiche,
                champ_modifie=champ,
                ancienne_valeur=str(ancienne_valeur) if ancienne_valeur is not None else "",
                nouvelle_valeur=str(nouvelle_valeur) if nouvelle_valeur is not None else "",
                categorie=categorie,
                modifie_par=modifie_par,
            )


@login_required
def supprimer_observation(request, observation_id):
    """Vue pour supprimer une observation spécifique"""
    observation = get_object_or_404(Observation, id=observation_id)
    fiche_id = observation.fiche.num_fiche
    user = cast(Utilisateur, request.user)

    if user != observation.fiche.observateur and user.role != "administrateur":
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cette observation")
        return redirect("detail_observation", fiche_id=fiche_id)

    if request.method == 'POST':
        observation.delete()
        messages.success(request, "Observation supprimée avec succès")

    return redirect('modifier_observation', fiche_id=fiche_id)
