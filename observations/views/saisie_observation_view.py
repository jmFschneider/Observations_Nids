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
from django.urls import reverse
from django.utils import timezone

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


def disable_form_fields(form):
    for field in form.fields.values():
        field.disabled = True


def disable_formset_fields(formset):
    for form in formset.forms:
        disable_form_fields(form)


def handle_remarques_update(request, fiche_instance, remarqueformset):
    """
    Traite uniquement la mise à jour des remarques via AJAX.
    """
    try:
        if request.user != fiche_instance.observateur and request.user.role not in [
            'administrateur',
            'reviewer',
        ]:
            return JsonResponse(
                {
                    'status': 'forbidden',
                    'message': "Vous n'êtes pas autorisé à modifier les remarques de cette fiche.",
                }
            )
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
                            if (
                                remarque_id.id in remarques_avant
                                and remarques_avant[remarque_id.id].remarque != remarque_text
                            ):
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
                return JsonResponse(
                    {'status': 'error', 'errors': remarque_formset.errors}, status=400
                )

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
                remarques.append(
                    {
                        'id': remarque.id,
                        'remarque': remarque.remarque,
                        'date_remarque': remarque.date_remarque.strftime('%d/%m/%Y %H:%M'),
                        'toDelete': False,
                    }
                )
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
def saisie_observation(request, fiche_id=None):  # noqa: PLR0911
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
    read_only = False
    if fiche_id:
        try:
            fiche_instance = FicheObservation.objects.get(pk=fiche_id)
            user = cast(Utilisateur, request.user)
            # Les administrateurs et reviewers peuvent toujours modifier (sauf si validée ou verrouillée)
            # Les observateurs ne peuvent modifier que leurs propres fiches
            read_only = user != fiche_instance.observateur and user.role not in [
                'administrateur',
                'reviewer',
            ]

            # Vérifier les permissions pour les fiches en cours de saisie
            redirect_response = None
            if hasattr(fiche_instance, 'etat_correction'):
                etat = fiche_instance.etat_correction
                # Si la fiche est validée, elle ne peut plus être modifiée
                if etat.statut == 'valide':
                    messages.warning(
                        request,
                        "Cette fiche a été validée et ne peut plus être modifiée.",
                    )
                    redirect_response = redirect(
                        'observations:fiche_observation', fiche_id=fiche_id
                    )
                # Si la fiche est en cours de correction (en_cours), vérifier le verrouillage
                elif etat.statut == 'en_cours':
                    if etat.est_verrouillee() and user != etat.en_correction_par:
                        # Un autre reviewer ou un admin tente d'accéder
                        if user.role == 'administrateur':
                            messages.warning(
                                request,
                                f"Cette fiche est en cours de correction par "
                                f"{etat.en_correction_par.get_full_name() or etat.en_correction_par.username}. "
                                f"Pour la modifier, vous devez d'abord la débloquer.",
                            )
                        else:
                            messages.info(
                                request,
                                f"Cette fiche est en cours de correction par "
                                f"{etat.en_correction_par.get_full_name() or etat.en_correction_par.username}. "
                                f"Vous pouvez consulter la fiche en lecture seule.",
                            )
                        # Rediriger vers la vue en lecture seule
                        redirect_response = redirect(
                            'observations:fiche_observation', fiche_id=fiche_id
                        )
                # Si la fiche est en cours de saisie (nouveau ou en_edition),
                # seul l'auteur ou un administrateur peut l'éditer
                elif etat.statut in ['nouveau', 'en_edition'] and read_only:
                    messages.info(
                        request,
                        f"Vous consultez cette fiche en lecture seule. "
                        f"Seul l'auteur ({fiche_instance.observateur.username}) peut la modifier.",
                    )

            if redirect_response:
                return redirect_response

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
        fields=[
            'date_observation',
            'heure_connue',
            'nombre_oeufs',
            'nombre_poussins',
            'observations',
        ],
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

    if request.method == "POST" and request.POST.get('action') == 'update_remarques':
        # Traitement spécial pour la mise à jour des remarques uniquement (via AJAX)
        return handle_remarques_update(request, fiche_instance, remarqueformset)

    # Traitement spécial pour récupérer les remarques via AJAX (GET)
    if (
        request.GET.get('get_remarques') == '1'
        and request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    ):
        return handle_get_remarques(request, fiche_instance)

    if request.method == "POST" and not read_only:
        # Préparer les données POST
        post_data = request.POST.copy()
        # Ne définir l'observateur que s'il n'est pas fourni dans le formulaire (pour les nouvelles fiches uniquement)
        if not post_data.get('observateur'):
            if (
                fiche_instance
                and hasattr(fiche_instance, 'observateur')
                and fiche_instance.observateur
            ):
                post_data['observateur'] = fiche_instance.observateur.id
            else:
                post_data['observateur'] = request.user.id

        # Si le champ coordonnees est vide, essayer de le construire depuis lat/lon
        if not post_data.get('coordonnees'):
            latitude = post_data.get('latitude')
            longitude = post_data.get('longitude')
            if latitude and longitude:
                post_data['coordonnees'] = f"{latitude},{longitude}"
            else:
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
                        # Définir l'année actuelle seulement si non fournie
                        if not fiche.annee:
                            fiche.annee = datetime.now().year
                    else:
                        original_fiche = FicheObservation.objects.get(pk=fiche_id)
                        if original_fiche.chemin_image and not fiche.chemin_image:
                            fiche.chemin_image = original_fiche.chemin_image

                    # L'observateur est géré par le formulaire, mais on garde un fallback de sécurité
                    # Le formulaire.save() a déjà défini l'observateur à partir de la valeur du formulaire
                    if not fiche.observateur:
                        fiche.observateur = request.user

                    # Gérer le numéro personnel
                    numero_personnel = request.POST.get('numero_personnel')
                    if numero_personnel:
                        try:
                            fiche.numero_personnel = int(numero_personnel)
                        except (ValueError, TypeError):
                            fiche.numero_personnel = None
                    else:
                        fiche.numero_personnel = None

                    fiche.save()

                    if fiche_id and fiche_avant:
                        enregistrer_modifications_historique(
                            fiche,
                            (fiche_avant, fiche),
                            'fiche',
                            request.user,
                            fiche_form.changed_data,
                        )

                    # Sauvegarder les objets liés
                    # Pour une nouvelle fiche, ils ont déjà été créés par FicheObservation.save()
                    # On les récupère et on les met à jour
                    if fiche_id:
                        # Modification : on met à jour les objets existants
                        localisation = localisation_form.save(commit=False)
                        localisation.fiche = fiche
                        localisation.save()
                        if localisation_avant:
                            enregistrer_modifications_historique(
                                fiche,
                                (localisation_avant, localisation),
                                'localisation',
                                request.user,
                                localisation_form.changed_data,
                            )

                        resume = resume_form.save(commit=False)
                        resume.fiche = fiche
                        resume.save()
                        if resume_avant:
                            enregistrer_modifications_historique(
                                fiche,
                                (resume_avant, resume),
                                'resume_observation',
                                request.user,
                                resume_form.changed_data,
                            )

                        nid = nid_form.save(commit=False)
                        nid.fiche = fiche
                        nid.save()
                        if nid_avant:
                            enregistrer_modifications_historique(
                                fiche, (nid_avant, nid), 'nid', request.user, nid_form.changed_data
                            )

                        causes_echec = causes_echec_form.save(commit=False)
                        causes_echec.fiche = fiche
                        causes_echec.save()
                        if causes_echec_avant:
                            enregistrer_modifications_historique(
                                fiche,
                                (causes_echec_avant, causes_echec),
                                'causes_echec',
                                request.user,
                                causes_echec_form.changed_data,
                            )
                    else:
                        # Nouvelle fiche : les objets ont été créés automatiquement
                        # On les récupère et on les met à jour avec les données du formulaire

                        localisation = fiche.localisation
                        for field in localisation_form.cleaned_data:
                            setattr(localisation, field, localisation_form.cleaned_data[field])
                        localisation.save()

                        resume = fiche.resume
                        for field in resume_form.cleaned_data:
                            setattr(resume, field, resume_form.cleaned_data[field])
                        resume.save()

                        nid = fiche.nid
                        for field in nid_form.cleaned_data:
                            setattr(nid, field, nid_form.cleaned_data[field])
                        nid.save()

                        causes_echec = fiche.causes_echec
                        for field in causes_echec_form.cleaned_data:
                            setattr(causes_echec, field, causes_echec_form.cleaned_data[field])
                        causes_echec.save()

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
                                    (ancienne_obs, form.instance),
                                    'observation',
                                    request.user,
                                    champs_modifies,
                                )
                        elif (
                            form.has_changed()
                            and not form.instance.pk
                            and form.cleaned_data.get('date_observation')
                        ):
                            # Nouvelle observation
                            for field_name in [
                                'date_observation',
                                'heure_connue',
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

                    # Sauvegarder le formset des remarques (commit=False pour accéder à deleted_objects)
                    saved_remarques = remarque_formset.save(commit=False)

                    # Traiter les suppressions de remarques (comme pour les observations)
                    if fiche_id:
                        # Utiliser deleted_objects du formset pour gérer les suppressions
                        remarques_a_supprimer = list(remarque_formset.deleted_objects)
                        for remarque in remarques_a_supprimer:
                            HistoriqueModification.objects.create(
                                fiche=fiche,
                                champ_modifie='remarque_supprimee',
                                ancienne_valeur=remarque.remarque,
                                nouvelle_valeur="",
                                categorie='remarque',
                                modifie_par=request.user,
                            )
                            remarque.delete()

                    # Récupérer les IDs des remarques existantes pour détecter les nouvelles
                    remarques_existantes_ids = {r.id for r in remarques} if fiche_id else set()

                    for remarque in saved_remarques:
                        remarque.fiche = fiche
                        remarque.save()

                        # Gestion de l'ajout de remarques nouvelles
                        if not remarque.id or (
                            fiche_id and remarque.id not in remarques_existantes_ids
                        ):
                            HistoriqueModification.objects.create(
                                fiche=fiche,
                                champ_modifie='remarque_ajoutee',
                                ancienne_valeur="",
                                nouvelle_valeur=remarque.remarque,
                                categorie='remarque',
                                modifie_par=request.user,
                            )

                    remarque_formset.save_m2m()

                    if not fiche_id:
                        remarque_initiale = post_data.get('remarque-initiale')
                        if remarque_initiale:
                            Remarque.objects.create(fiche=fiche, remarque=remarque_initiale)

                    # Mettre à jour les années des observations APRÈS le traitement du formset
                    if (
                        fiche_id
                        and fiche_avant
                        and 'annee' in fiche_form.changed_data
                        and fiche_avant.annee != fiche.annee
                    ):
                        mettre_a_jour_annee_observations(
                            fiche, fiche_avant.annee, fiche.annee, request.user
                        )

                    # Verrouiller la fiche si elle est en cours de correction et pas encore verrouillée
                    if hasattr(fiche, 'etat_correction'):
                        etat = fiche.etat_correction
                        if etat.statut == 'en_cours' and not etat.est_verrouillee():
                            # Verrouiller la fiche pour le reviewer actuel
                            etat.verrouiller_pour(request.user)
                            logger.info(
                                f"Fiche {fiche.pk} verrouillée pour {request.user.username}"
                            )

                    messages.success(request, "Fiche d'observation sauvegardée avec succès!")

                    # Vérifier si une redirection après sauvegarde a été demandée (depuis JavaScript)
                    redirect_url = post_data.get('redirect_after_save')
                    if redirect_url:
                        return redirect(redirect_url)

                    # Vérifier si on doit rouvrir la modal des remarques après sauvegarde
                    reopen_remarques = post_data.get('reopen_remarques_modal')
                    if reopen_remarques:
                        # Rediriger vers la même page avec un paramètre GET pour rouvrir la modal
                        redirect_url = reverse(
                            'observations:modifier_observation', kwargs={'fiche_id': fiche.pk}
                        )
                        redirect_url += '?reopen_remarques_modal=1'
                        return redirect(redirect_url)

                    return redirect('observations:modifier_observation', fiche_id=fiche.pk)

            except Exception as e:
                logger.exception(f"Erreur lors de la sauvegarde: {e}")
                messages.error(request, f"Une erreur est survenue lors de la sauvegarde: {str(e)}")
        else:
            for error in validation_errors:
                messages.error(request, error)

    else:  # GET request ou POST en lecture seule
        if request.method == "POST" and read_only:
            messages.error(
                request,
                "Vous n'êtes pas autorisé à enregistrer les modifications de cette fiche.",
            )
        fiche_form = FicheObservationForm(instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(instance=localisation_instance)
        resume_form = ResumeObservationForm(instance=resume_instance)
        nid_form = NidForm(instance=nid_instance)
        causes_echec_form = CausesEchecForm(instance=causes_echec_instance)
        if fiche_instance and hasattr(fiche_instance, 'observations'):
            # HACK: Remove unsaved observations that may be lingering in memory
            unsaved_obs = [obs for obs in fiche_instance.observations.all() if obs.pk is None]
            if unsaved_obs:
                fiche_instance.observations.remove(*unsaved_obs)

        observation_formset = observationformset(instance=fiche_instance)
        remarque_formset = remarqueformset(instance=fiche_instance)

    if read_only:
        disable_form_fields(fiche_form)
        disable_form_fields(localisation_form)
        disable_form_fields(resume_form)
        disable_form_fields(nid_form)
        disable_form_fields(causes_echec_form)
        disable_formset_fields(observation_formset)
        disable_formset_fields(remarque_formset)

    context = {
        'fiche_form': fiche_form,
        'localisation_form': localisation_form,
        'resume_form': resume_form,
        'nid_form': nid_form,
        'causes_echec_form': causes_echec_form,
        'observation_formset': observation_formset,
        'remarque_formset': remarque_formset,
        'remarques': remarques,
        'read_only': read_only,
    }

    return render(request, 'saisie/saisie_observation.html', context)


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

            return redirect('observations:modifier_observation', fiche_id=fiche_id)
    else:
        # Préremplir avec la date du jour à 00:00
        initial_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        form = ObservationForm(initial={'date_observation': initial_date, 'heure_connue': False})
    return render(
        request,
        'saisie/ajouter_observation.html',
        {'form': form, 'fiche': fiche, 'fiche_id': fiche_id},
    )


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
    fiche, instances, categorie, modifie_par, champs_modifies=None
):
    ancienne_instance, nouvelle_instance = instances
    if not ancienne_instance or not nouvelle_instance:
        return

    champs_ignores = ['id', 'fiche', 'DELETE']

    # Si on a une liste de champs modifiés, ne traiter que ceux-ci
    champs_a_verifier = champs_modifies or [field.name for field in ancienne_instance._meta.fields]

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
            try:
                # On calcule la différence absolue pour gérer les fuseaux horaires
                # (ex: 10:00 UTC == 11:00 CET)
                diff = ancienne_valeur - nouvelle_valeur
                if hasattr(diff, 'total_seconds'):
                    valeurs_egales = abs(diff.total_seconds()) < 1
                else:
                    # Cas date simple sans heure
                    valeurs_egales = diff.days == 0
            except (TypeError, ValueError):
                # Cas de secours si mélange naive/aware impossible à soustraire
                valeurs_egales = str(ancienne_valeur) == str(nouvelle_valeur)

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

    return redirect('observations:modifier_observation', fiche_id=fiche_id)


@login_required
def soumettre_pour_correction(request, fiche_id):
    """Soumettre une fiche pour correction (passage du statut en_edition à en_cours)"""
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    user = cast(Utilisateur, request.user)

    logger.info(
        f"soumettre_pour_correction appelé pour fiche {fiche_id}, méthode: {request.method}"
    )

    # Vérifier que c'est bien l'observateur de la fiche
    if user != fiche.observateur and user.role != "administrateur":
        messages.error(request, "Vous n'êtes pas autorisé à soumettre cette fiche")
        return redirect('modifier_observation', fiche_id=fiche_id)

    if request.method == 'POST':
        # Récupérer l'état de correction
        etat_correction = fiche.etat_correction
        logger.info(f"Statut actuel de la fiche {fiche_id}: {etat_correction.statut}")

        # Passer en mode correction (révision) seulement si en édition
        if etat_correction.statut in ['nouveau', 'en_edition']:
            # Calculer le pourcentage de complétion
            pourcentage = etat_correction.calculer_pourcentage_completion()

            # Forcer le statut à "en_cours" et sauvegarder sans recalcul automatique
            etat_correction.statut = 'en_cours'
            etat_correction.pourcentage_completion = pourcentage
            etat_correction.save(skip_auto_calculation=True)

            logger.info(
                f"Fiche {fiche_id} passée en statut 'en_cours', pourcentage: {pourcentage}%"
            )

            messages.success(
                request, f"Fiche #{fiche_id} soumise pour correction. Complétion : {pourcentage}%"
            )
        else:
            logger.warning(f"Fiche {fiche_id} déjà en statut: {etat_correction.statut}")
            messages.warning(
                request, f"La fiche est déjà en statut '{etat_correction.get_statut_display()}'"
            )

        # Rediriger vers la vue de détail (lecture seule)
        logger.info(f"Redirection vers fiche_observation pour fiche {fiche_id}")
        return redirect('observations:fiche_observation', fiche_id=fiche_id)

    logger.info(f"Méthode GET, redirection vers modifier_observation pour fiche {fiche_id}")
    return redirect('observations:modifier_observation', fiche_id=fiche_id)


@login_required
def valider_correction(request, fiche_id):
    """Valider la correction d'une fiche (passage du statut en_cours à valide)"""
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    user = cast(Utilisateur, request.user)

    logger.info(f"valider_correction appelé pour fiche {fiche_id}, méthode: {request.method}")

    # Vérifier que l'utilisateur est un reviewer ou administrateur
    if user.role not in ["reviewer", "administrateur"]:
        messages.error(request, "Vous n'êtes pas autorisé à valider cette correction")
        return redirect('observations:modifier_observation', fiche_id=fiche_id)

    if request.method == 'POST':
        # Récupérer l'état de correction
        etat_correction = fiche.etat_correction
        logger.info(f"Statut actuel de la fiche {fiche_id}: {etat_correction.statut}")

        # Passer en statut validé seulement si en cours de correction
        if etat_correction.statut == 'en_cours':
            # Calculer le pourcentage de complétion final
            pourcentage = etat_correction.calculer_pourcentage_completion()

            # Enregistrer dans l'historique avant la modification
            ancien_statut = etat_correction.get_statut_display()

            # Forcer le statut à "valide" et renseigner les champs de validation
            etat_correction.statut = 'valide'
            etat_correction.pourcentage_completion = pourcentage
            etat_correction.validee_par = user
            etat_correction.date_validation = timezone.now()
            etat_correction.save(skip_auto_calculation=True)

            # Enregistrer la validation dans l'historique
            HistoriqueModification.objects.create(
                fiche=fiche,
                champ_modifie='statut_validation',
                ancienne_valeur=ancien_statut,
                nouvelle_valeur=etat_correction.get_statut_display(),
                modifie_par=user,
                categorie='validation',
            )

            # Libérer le verrou technique si présent
            if etat_correction.en_correction_par:
                etat_correction.liberer_verrou(motif='validation')

            logger.info(
                f"Fiche {fiche_id} passée en statut 'valide' par {user.username}, "
                f"pourcentage: {pourcentage}%"
            )

            messages.success(
                request, f"Fiche #{fiche_id} validée avec succès. La correction est terminée."
            )
        else:
            logger.warning(
                f"Fiche {fiche_id} n'est pas en cours de correction: {etat_correction.statut}"
            )
            messages.warning(
                request,
                f"La fiche n'est pas en cours de correction (statut actuel: '{etat_correction.get_statut_display()}')",
            )

        # Rediriger selon l'option choisie
        redirect_option = request.POST.get('redirect_option', 'fiche')
        if redirect_option == 'home':
            logger.info(
                f"Redirection vers accueil (Ma Page) après validation de la fiche {fiche_id}"
            )
            return redirect('observations:home')
        elif redirect_option == 'liste':
            logger.info(f"Redirection vers liste globale après validation de la fiche {fiche_id}")
            return redirect('observations:liste_fiches_observations')
        else:
            logger.info(f"Redirection vers fiche_observation pour fiche {fiche_id}")
            return redirect('observations:fiche_observation', fiche_id=fiche_id)

    logger.info(f"Méthode GET, redirection vers modifier_observation pour fiche {fiche_id}")
    return redirect('observations:modifier_observation', fiche_id=fiche_id)


@login_required
def rouvrir_fiche(request, fiche_id):
    """
    Permet à un administrateur ou au validateur de rouvrir une fiche validée (repassage au statut 'en_cours').
    """
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    user = cast(Utilisateur, request.user)
    etat = fiche.etat_correction

    # Vérification du rôle administrateur ou de l'auteur de la validation
    if user.role != 'administrateur' and user != etat.validee_par:
        messages.error(request, "Vous n'avez pas les droits pour rouvrir cette fiche.")
        return redirect('observations:fiche_observation', fiche_id=fiche_id)

    # Vérifier que la fiche est bien validée
    if etat.statut != 'valide':
        messages.warning(request, "Cette fiche n'est pas validée, impossible de la rouvrir.")
        return redirect('observations:fiche_observation', fiche_id=fiche_id)

    # Action de réouverture
    ancien_statut = etat.get_statut_display()

    # On repasse en 'en_cours'
    etat.statut = 'en_cours'
    # On efface les infos de validation
    etat.validee_par = None
    etat.date_validation = None

    # On assigne la correction à l'admin qui rouvre (optionnel, mais logique)
    etat.en_correction_par = user
    etat.date_debut_correction = timezone.now()

    etat.save(skip_auto_calculation=True)

    # Historique
    HistoriqueModification.objects.create(
        fiche=fiche,
        champ_modifie='statut_validation',
        ancienne_valeur=ancien_statut,
        nouvelle_valeur="En cours de correction (Réouverture)",
        modifie_par=user,
        categorie='validation',
    )

    logger.info(f"Fiche {fiche_id} rouverte par l'administrateur {user.username}")
    messages.success(
        request, f"La fiche #{fiche_id} a été rouverte et placée en cours de correction."
    )

    return redirect('observations:modifier_observation', fiche_id=fiche_id)


@login_required
def rechercher_fiches(request):
    """
    Endpoint AJAX pour rechercher des fiches d'observation.
    Permet de filtrer par observateur, année, espèce, numéro personnel.
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête AJAX uniquement'}, status=400)

    # Récupérer les paramètres de recherche
    observateur_id = request.GET.get('observateur')
    annee = request.GET.get('annee')
    espece_id = request.GET.get('espece')
    numero_personnel = request.GET.get('numero_personnel')
    fiche_id_min = request.GET.get('fiche_id_min')
    fiche_id_max = request.GET.get('fiche_id_max')

    # Construire la requête
    fiches = FicheObservation.objects.select_related('observateur', 'espece', 'localisation')

    if observateur_id:
        fiches = fiches.filter(observateur_id=observateur_id)
    if annee:
        fiches = fiches.filter(annee=annee)
    if espece_id:
        fiches = fiches.filter(espece_id=espece_id)
    if numero_personnel:
        fiches = fiches.filter(numero_personnel=numero_personnel)
    if fiche_id_min:
        fiches = fiches.filter(num_fiche__gte=fiche_id_min)
    if fiche_id_max:
        fiches = fiches.filter(num_fiche__lte=fiche_id_max)

    # Limiter les résultats
    fiches = fiches.order_by('-annee', '-num_fiche')[:50]

    # Formater les résultats
    resultats = []
    for fiche in fiches:
        commune = ''
        if hasattr(fiche, 'localisation') and fiche.localisation:
            commune = fiche.localisation.commune or ''

        resultats.append(
            {
                'num_fiche': fiche.num_fiche,
                'observateur': f"{fiche.observateur.first_name} {fiche.observateur.last_name}",
                'espece': fiche.espece.nom,
                'code_gonm': fiche.espece.code_gonm or '-',
                'annee': fiche.annee,
                'numero_personnel': fiche.numero_personnel or '',
                'commune': commune,
            }
        )

    return JsonResponse({'fiches': resultats})


@login_required
def liberer_verrou_fiche(request, fiche_id):
    """
    Vue pour libérer manuellement le verrou d'une fiche en cours de correction.

    Permissions:
    - Un reviewer peut libérer le verrou de sa propre fiche
    - Un administrateur peut libérer le verrou de n'importe quelle fiche
    """
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    user = cast(Utilisateur, request.user)

    # Vérifier que la fiche a un état de correction
    if not hasattr(fiche, 'etat_correction'):
        messages.error(request, "Cette fiche n'a pas d'état de correction.")
        return redirect('observations:fiche_observation', fiche_id=fiche_id)

    etat = fiche.etat_correction

    # Vérifier que la fiche est verrouillée
    if not etat.est_verrouillee():
        messages.info(request, "Cette fiche n'est pas verrouillée.")
        return redirect('observations:fiche_observation', fiche_id=fiche_id)

    # Vérifier les permissions
    peut_debloquer = False

    if user.role == 'administrateur':
        # Les administrateurs peuvent toujours débloquer
        peut_debloquer = True
    elif etat.en_correction_par == user:
        # Un reviewer peut débloquer sa propre fiche
        peut_debloquer = True

    if not peut_debloquer:
        messages.error(
            request,
            f"Vous n'êtes pas autorisé à débloquer cette fiche. "
            f"Elle est actuellement en correction par {etat.en_correction_par.get_full_name() or etat.en_correction_par.username}.",
        )
        return redirect('observations:fiche_observation', fiche_id=fiche_id)

    # Débloquer la fiche
    reviewer_precedent = etat.en_correction_par.get_full_name() or etat.en_correction_par.username
    etat.liberer_verrou()

    logger.info(
        f"Fiche {fiche_id} débloquée par {user.username}. "
        f"Était verrouillée par {reviewer_precedent}."
    )

    messages.success(
        request,
        f"La fiche #{fiche_id} a été débloquée avec succès. "
        f"Elle était en correction par {reviewer_precedent}.",
    )

    return redirect('observations:modifier_observation', fiche_id=fiche_id)
