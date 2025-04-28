# saisie_observation_optimClaude.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import inlineformset_factory
from django.db.models import Q
from datetime import datetime
import logging

from Observations.models import (
    FicheObservation, Localisation, Nid, ResumeObservation,
    CausesEchec, Observation, Remarque, HistoriqueModification
)
from Observations.forms import (
    FicheObservationForm, LocalisationForm, NidForm, ObservationForm,
    ResumeObservationForm, CausesEchecForm, RemarqueForm
)

logger = logging.getLogger('Observations')


@login_required
def saisie_observation_optimisee(request, fiche_id=None):
    """
    Vue optimisée pour la saisie d'une nouvelle observation ou la modification d'une existante.
    Combine les fonctionnalités de fiche_test_observation_view avec une structure plus claire.
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
    ObservationFormSet = inlineformset_factory(
        FicheObservation,
        Observation,
        form=ObservationForm,
        fields=['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations'],
        extra=1,
        can_delete=False,
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
        fiche_form = FicheObservationForm(post_data, request.FILES, instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(post_data, instance=localisation_instance)
        nid_form = NidForm(post_data, instance=nid_instance)
        resume_form = ResumeObservationForm(post_data, instance=resume_instance)
        causes_echec_form = CausesEchecForm(post_data, instance=causes_echec_instance)
        observation_formset = ObservationFormSet(post_data, instance=fiche_instance)

        # Validation des formulaires
        validation_errors = []
        forms_valid = True

        if not fiche_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de fiche: {fiche_form.errors}")
            validation_errors.append(f"Erreurs dans les informations de base: {fiche_form.errors}")
            forms_valid = False

        if not localisation_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de localisation: {localisation_form.errors}")
            validation_errors.append(f"Erreurs dans les informations de localisation: {localisation_form.errors}")
            forms_valid = False

        if not resume_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de résumé: {resume_form.errors}")
            validation_errors.append(f"Erreurs dans le résumé de l'observation: {resume_form.errors}")
            forms_valid = False

        if not nid_form.is_valid():
            logger.error(f"Erreurs dans le formulaire de nid: {nid_form.errors}")
            validation_errors.append(f"Erreurs dans les informations du nid: {nid_form.errors}")
            forms_valid = False

        if not causes_echec_form.is_valid():
            logger.error(f"Erreurs dans le formulaire des causes d'échec: {causes_echec_form.errors}")
            validation_errors.append(f"Erreurs dans les causes d'échec: {causes_echec_form.errors}")
            forms_valid = False

        if not observation_formset.is_valid():
            logger.error(f"Erreurs dans le formset d'observations: {observation_formset.errors}")
            for i, form in enumerate(observation_formset):
                if form.has_changed() and form.errors:
                    validation_errors.append(f"Erreurs dans l'observation #{i + 1}: {form.errors}")
            if observation_formset.non_form_errors():
                validation_errors.append(f"Erreurs globales d'observations: {observation_formset.non_form_errors()}")
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
                        fiche_avant = None
                        localisation_avant = None
                        resume_avant = None
                        nid_avant = None
                        causes_echec_avant = None

                    # Sauvegarder la fiche principale
                    fiche = fiche_form.save(commit=False)

                    # Pour une nouvelle fiche, définir l'année
                    if not fiche_id:
                        fiche.annee = datetime.now().year
                    else:
                        # Conserver le chemin d'image si non modifié
                        original_fiche = FicheObservation.objects.get(pk=fiche_id)
                        if original_fiche.chemin_image and not fiche.chemin_image:
                            fiche.chemin_image = original_fiche.chemin_image

                    # S'assurer que l'observateur est défini
                    if not hasattr(fiche, 'observateur') or not fiche.observateur:
                        fiche.observateur = request.user

                    fiche.save()

                    # Enregistrer les modifications dans l'historique
                    if fiche_id and fiche_avant:
                        enregistrer_modifications_historique(
                            fiche=fiche,
                            ancienne_instance=fiche_avant,
                            nouvelle_instance=fiche,
                            categorie='fiche',
                            modifie_par=request.user
                        )

                    # Sauvegarder la localisation
                    localisation = localisation_form.save(commit=False)
                    localisation.fiche = fiche
                    localisation.save()

                    if fiche_id and localisation_avant:
                        enregistrer_modifications_historique(
                            fiche=fiche,
                            ancienne_instance=localisation_avant,
                            nouvelle_instance=localisation,
                            categorie='localisation',
                            modifie_par=request.user
                        )

                    # Sauvegarder le résumé
                    resume = resume_form.save(commit=False)
                    resume.fiche = fiche
                    resume.save()

                    if fiche_id and resume_avant:
                        enregistrer_modifications_historique(
                            fiche=fiche,
                            ancienne_instance=resume_avant,
                            nouvelle_instance=resume,
                            categorie='resume_observation',
                            modifie_par=request.user
                        )

                    # Sauvegarder le nid
                    nid = nid_form.save(commit=False)
                    nid.fiche = fiche
                    nid.save()

                    if fiche_id and nid_avant:
                        enregistrer_modifications_historique(
                            fiche=fiche,
                            ancienne_instance=nid_avant,
                            nouvelle_instance=nid,
                            categorie='nid',
                            modifie_par=request.user
                        )

                    # Sauvegarder les causes d'échec
                    causes_echec = causes_echec_form.save(commit=False)
                    causes_echec.fiche = fiche
                    causes_echec.save()

                    if fiche_id and causes_echec_avant:
                        enregistrer_modifications_historique(
                            fiche=fiche,
                            ancienne_instance=causes_echec_avant,
                            nouvelle_instance=causes_echec,
                            categorie='causes_echec',
                            modifie_par=request.user
                        )

                    # Gérer les observations - traitement du formset
                    if fiche_id:
                        # Récupérer les observations existantes pour comparaison
                        observations_avant = {obs.id: obs for obs in Observation.objects.filter(fiche=fiche_id)}

                    # Sauvegarder les observations
                    observation_formset.instance = fiche

                    # Traiter chaque formulaire d'observation
                    for form in observation_formset:
                        # Ne traiter que les formulaires modifiés
                        if form.has_changed():
                            # Vérifier si la date d'observation est renseignée
                            if form.cleaned_data.get('date_observation'):
                                try:
                                    # Mise à jour d'une observation existante
                                    if form.instance.pk and form.instance.pk in observations_avant:
                                        ancienne_obs = observations_avant[form.instance.pk]
                                        nouvelle_obs = form.save()
                                        enregistrer_modifications_historique(
                                            fiche=fiche,
                                            ancienne_instance=ancienne_obs,
                                            nouvelle_instance=nouvelle_obs,
                                            categorie='observation',
                                            modifie_par=request.user
                                        )
                                    else:
                                        # Nouvelle observation
                                        nouvelle_obs = form.save()
                                        # Enregistrer l'ajout dans l'historique
                                        for field_name in ['date_observation', 'nombre_oeufs', 'nombre_poussins',
                                                           'observations']:
                                            if field_name in form.cleaned_data and form.cleaned_data[field_name]:
                                                HistoriqueModification.objects.create(
                                                    fiche=fiche,
                                                    champ_modifie=field_name,
                                                    ancienne_valeur="",
                                                    nouvelle_valeur=str(form.cleaned_data[field_name]),
                                                    categorie='observation',
                                                    modifie_par=request.user
                                                )

                                    logger.info(
                                        f"Observation sauvegardée avec date: {form.cleaned_data.get('date_observation')}")
                                except Exception as e:
                                    logger.error(f"Erreur lors de la sauvegarde de l'observation: {e}")
                            else:
                                logger.warning("Formulaire d'observation modifié mais sans date d'observation")

                    # Traiter la remarque initiale pour nouvelle fiche
                    if not fiche_id:
                        remarque_initiale = post_data.get('remarque-initiale')
                        if remarque_initiale:
                            Remarque.objects.create(fiche=fiche, remarque=remarque_initiale)

                    messages.success(request, "Fiche d'observation sauvegardée avec succès!")

                    # Redirection vers la page d'édition
                    return redirect('saisie_observation_optimisee', fiche_id=fiche.pk)

            except Exception as e:
                logger.exception(f"Erreur lors de la sauvegarde: {e}")
                messages.error(request, f"Une erreur est survenue lors de la sauvegarde: {str(e)}")
        else:
            # Afficher les erreurs de validation
            for error in validation_errors:
                messages.error(request, error)
    else:
        # GET request - affichage du formulaire
        fiche_form = FicheObservationForm(instance=fiche_instance, user=request.user)
        localisation_form = LocalisationForm(instance=localisation_instance)
        resume_form = ResumeObservationForm(instance=resume_instance)
        nid_form = NidForm(instance=nid_instance)
        causes_echec_form = CausesEchecForm(instance=causes_echec_instance)
        observation_formset = ObservationFormSet(instance=fiche_instance)

    # Préparer le contexte pour le template
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
def ajouter_observation_optimisee(request, fiche_id):
    """Vue optimisée pour ajouter une observation à une fiche existante"""
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)

    if request.method == 'POST':
        form = ObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.fiche = fiche
            observation.save()

            # Enregistrer l'ajout dans l'historique
            for field_name in ['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations']:
                if field_name in form.cleaned_data and form.cleaned_data[field_name]:
                    HistoriqueModification.objects.create(
                        fiche=fiche,
                        champ_modifie=field_name,
                        ancienne_valeur="",
                        nouvelle_valeur=str(form.cleaned_data[field_name]),
                        categorie='observation',
                        modifie_par=request.user
                    )
                    logger.info(
                        f"Ajout d'observation, champ '{field_name}', "
                        f"nouvelle valeur: '{form.cleaned_data[field_name]}', "
                        f"par {request.user.username}"
                    )

            return redirect('saisie_observation_optimisee', fiche_id=fiche_id)
    else:
        form = ObservationForm()

    return render(request, 'saisie/ajouter_observation.html', {'form': form, 'fiche': fiche})


@login_required
def historique_modifications_optimisee(request, fiche_id):
    """Vue optimisée pour afficher l'historique des modifications d'une fiche"""
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    modifications = HistoriqueModification.objects.filter(fiche=fiche).order_by('-date_modification')

    return render(request, 'saisie/historique_modifications.html', {
        'fiche': fiche,
        'modifications': modifications
    })


def enregistrer_modifications_historique(fiche, ancienne_instance, nouvelle_instance, categorie, modifie_par):
    """
    Fonction pour enregistrer les modifications dans l'historique.
    Compare les valeurs entre l'ancienne et la nouvelle instance.
    """
    from django.forms.models import model_to_dict
    from django.utils import timezone
    import datetime

    if not ancienne_instance or not nouvelle_instance:
        return

    # Convertir les instances en dictionnaires
    ancien_dict = model_to_dict(ancienne_instance)
    nouveau_dict = model_to_dict(nouvelle_instance)

    # Ignorer certains champs système
    champs_ignores = ['id', 'fiche']

    # Journalisation
    logger.info(f"Début de la comparaison pour {categorie}, classe: {ancienne_instance.__class__.__name__}")
    logger.info(f"Champs disponibles: {list(ancien_dict.keys())}")

    # Comparer les champs et enregistrer les différences
    for champ, ancienne_valeur in ancien_dict.items():
        if champ in champs_ignores:
            continue

        nouvelle_valeur = nouveau_dict.get(champ)
        logger.info(
            f"Comparaison du champ '{champ}': ancienne valeur = {ancienne_valeur}, nouvelle valeur = {nouvelle_valeur}")

        # Variable pour suivre si un changement a été détecté
        changement_detecte = False

        # Normaliser les valeurs datetime pour la comparaison
        if isinstance(ancienne_valeur, datetime.datetime) and isinstance(nouvelle_valeur, datetime.datetime):
            logger.info(f"  Champ '{champ}' est un datetime, normalisation...")
            # Convertir les deux valeurs en UTC pour une comparaison équitable
            if timezone.is_aware(ancienne_valeur):
                ancienne_valeur = ancienne_valeur.astimezone(timezone.utc)
            if timezone.is_aware(nouvelle_valeur):
                nouvelle_valeur = nouvelle_valeur.astimezone(timezone.utc)

            # Comparer uniquement les composantes date et heure
            ancienne_valeur_normalisee = ancienne_valeur.replace(tzinfo=None)
            nouvelle_valeur_normalisee = nouvelle_valeur.replace(tzinfo=None)

            logger.info(
                f"  Après normalisation: ancienne = {ancienne_valeur_normalisee}, nouvelle = {nouvelle_valeur_normalisee}")

            # Utiliser ces valeurs normalisées pour la comparaison
            if ancienne_valeur_normalisee != nouvelle_valeur_normalisee:
                logger.info(f"  Changement détecté pour le champ '{champ}' après normalisation")
                changement_detecte = True
            else:
                logger.info(f"  Pas de changement pour le champ '{champ}' après normalisation")
        else:
            logger.info(f"  Champ '{champ}' n'est pas un datetime, comparaison directe")
            # Pour les champs non-datetime, faire une comparaison directe
            if ancienne_valeur != nouvelle_valeur:
                logger.info(f"  Changement détecté pour le champ '{champ}'")
                changement_detecte = True
            else:
                logger.info(f"  Pas de changement pour le champ '{champ}'")

        # Si un changement a été détecté, enregistrer dans l'historique
        if changement_detecte:
            # Convertir en chaîne pour stocker dans la base
            ancienne_valeur_str = str(ancienne_valeur) if ancienne_valeur is not None else ""
            nouvelle_valeur_str = str(nouvelle_valeur) if nouvelle_valeur is not None else ""

            # Créer l'entrée d'historique
            HistoriqueModification.objects.create(
                fiche=fiche,
                champ_modifie=champ,
                ancienne_valeur=ancienne_valeur_str,
                nouvelle_valeur=nouvelle_valeur_str,
                categorie=categorie,
                modifie_par=modifie_par
            )

            # Journalisation pour le suivi
            logger.info(
                f"Modification sur {categorie}, champ '{champ}', "
                f"ancienne valeur: '{ancienne_valeur_str}', "
                f"nouvelle valeur: '{nouvelle_valeur_str}', "
                f"par {modifie_par.username}"
            )

    logger.info(f"Fin de la comparaison pour {categorie}")