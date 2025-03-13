import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.timezone import now

from Observations.models import (Espece, FicheObservation, Localisation, Utilisateur,
                                 Observation, Remarque)

# Configuration du logger
logger = logging.getLogger(__name__)


@login_required
def saisie_observation(request):
    assert isinstance(request.user, Utilisateur)  # Assertion de type
    request.user.refresh_from_db()  # Force le rechargement de l'utilisateur

    especes_disponibles = Espece.objects.all()
    annee_actuelle = datetime.now().year

    dernier_fiche = FicheObservation.objects.order_by('-num_fiche').first()
    prochain_num_fiche = (dernier_fiche.num_fiche + 1) if dernier_fiche else 1

    utilisateur_nom = request.user.get_full_name()

    # Log pour voir ce que Django récupère réellement comme utilisateur
    logger.debug(f"Utilisateur connecté : {request.user} (Auth: {request.user.is_authenticated})")

    return render(request, 'saisie/saisie_observation.html', {
        'fiche': {'num_fiche': prochain_num_fiche},
        'especes_disponibles': especes_disponibles,
        'annee_actuelle': annee_actuelle,
        'utilisateur_nom': utilisateur_nom,
    })


@login_required
def traiter_saisie_observation(request):
    if request.method == "POST":
        observateur = request.user
        espece_id = request.POST.get("espece")
        annee = datetime.now().year

        # Localisation
        commune = request.POST.get("commune")
        departement = request.POST.get("departement")
        lieu_dit = request.POST.get("lieu_dit")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        altitude = request.POST.get("altitude")

        # Détails du Nid
        nid_prec_t_meme_couple = request.POST.get("nid_prec_t_meme_couple") == "oui"
        hauteur_nid = request.POST.get("hauteur_nid")
        hauteur_couvert = request.POST.get("hauteur_couvert")
        details_nid = request.POST.get("details_nid")

        # Observations générales
        observations = request.POST.get("observations")
        paysage = request.POST.get("paysage")
        alentours = request.POST.get("alentours")

        try:
            espece = Espece.objects.get(id=espece_id)

            localisation = Localisation.objects.create(
                commune=commune,
                departement=departement,
                lieu_dit=lieu_dit,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude
            )

            nouvelle_fiche = FicheObservation.objects.create(
                observateur=observateur,
                espece=espece,
                annee=annee,
                localisation=localisation,
                nid_prec_t_meme_couple=nid_prec_t_meme_couple,
                hauteur_nid=hauteur_nid,
                hauteur_couvert=hauteur_couvert,
                details_nid=details_nid,
                observations=observations,
                paysage=paysage,
                alentours=alentours
            )

            # Récupération des valeurs du formulaire (observation détaillée)
            premier_oeuf_pondu_jour = request.POST.get("premier_oeuf_pondu_jour")
            premier_oeuf_pondu_mois = request.POST.get("premier_oeuf_pondu_mois")
            premier_poussin_eclos_jour = request.POST.get("premier_poussin_eclos_jour")
            premier_poussin_eclos_mois = request.POST.get("premier_poussin_eclos_mois")
            premier_poussin_volant_jour = request.POST.get("premier_poussin_volant_jour")
            premier_poussin_volant_mois = request.POST.get("premier_poussin_volant_mois")
            nombre_oeufs_pondus = request.POST.get("nombre_oeufs_pondus")
            nombre_oeufs_eclos = request.POST.get("nombre_oeufs_eclos")
            nombre_oeufs_non_eclos = request.POST.get("nombre_oeufs_non_eclos")
            nombre_poussins = request.POST.get("nombre_poussins")
            causes_echec = request.POST.get("causes_echec")
            remarque_texte = request.POST.get("remarque")

            # Création et sauvegarde de l'observation détaillée
            observation = Observation.objects.create(
                fiche=nouvelle_fiche,  # Association avec la fiche créée
                premier_oeuf_pondu_jour=premier_oeuf_pondu_jour,
                premier_oeuf_pondu_mois=premier_oeuf_pondu_mois,
                premier_poussin_eclos_jour=premier_poussin_eclos_jour,
                premier_poussin_eclos_mois=premier_poussin_eclos_mois,
                premier_poussin_volant_jour=premier_poussin_volant_jour,
                premier_poussin_volant_mois=premier_poussin_volant_mois,
                nombre_oeufs_pondus=nombre_oeufs_pondus,
                nombre_oeufs_eclos=nombre_oeufs_eclos,
                nombre_oeufs_non_eclos=nombre_oeufs_non_eclos,
                nombre_poussins=nombre_poussins,
                causes_echec=causes_echec
            )

            # Enregistrement d'une remarque si renseignée
            if remarque_texte:
                Remarque.objects.create(
                    observation=observation,
                    date_remarque=now(),
                    remarque=remarque_texte
                )

            messages.success(request, "Observation enregistrée avec succès !")
            return redirect('fiche_observation', fiche_id=nouvelle_fiche.id)

        except Espece.DoesNotExist:
            messages.error(request, "Erreur : l'espèce sélectionnée est invalide.")
            return redirect('saisie_observation')

    return redirect('saisie_observation')