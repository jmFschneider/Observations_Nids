import logging
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from Observations.models import (Espece, FicheObservation, Localisation, Utilisateur,
                                 Observation, Nid, Remarque, ResumeObservation, CausesEchec)

# Configuration du logger
logger = logging.getLogger(__name__)


@login_required
def saisie_observation(request):
    assert isinstance(request.user, Utilisateur)  # Assertion de type
    request.user.refresh_from_db()  # Force le rechargement de l'utilisateur

    especes_disponibles = Espece.objects.all()
    annee_actuelle = timezone.now().year

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

def traiter_saisie_observation(request):
    if request.method == "POST":
        # Log du contenu de la requête POST pour debug
        logger.debug(f"📝 Données reçues du formulaire : {request.POST}")

        observateur = request.user
        espece_id = request.POST.get("espece")
        annee = timezone.now().year

        # Récupération des données du formulaire
        commune = request.POST.get("commune")
        departement = request.POST.get("departement")
        lieu_dit = request.POST.get("lieu_dit")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        altitude = request.POST.get("altitude")

        nid_prec_t_meme_couple = request.POST.get("nid_prec_t_meme_couple") == "oui"
        hauteur_nid = request.POST.get("hauteur_nid")
        hauteur_couvert = request.POST.get("hauteur_couvert")
        details_nid = request.POST.get("details_nid")
        paysage = request.POST.get("paysage")
        alentours = request.POST.get("alentours")

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

        causes_echec_description = request.POST.get("causes_echec")
        remarque_texte = request.POST.get("remarque")

        dates = request.POST.getlist("observations_date")
        oeufs = request.POST.getlist("observations_oeufs")
        poussins = request.POST.getlist("observations_poussins")
        textes = request.POST.getlist("observations_text")

        try:
            espece = Espece.objects.get(id=espece_id)

            # Création de la fiche d'observation
            fiche_observation = FicheObservation.objects.create(
                observateur=observateur,
                espece=espece,
                annee=annee,
                chemin_image=""  # Vous devrez gérer l'upload d'image séparément
            )

            # Création de la localisation
            Localisation.objects.filter(fiche=fiche_observation).update(
                commune=commune,
                departement=departement,
                lieu_dit=lieu_dit,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                paysage=paysage,
                alentours=alentours,
            )

            # Création du nid
            Nid.objects.filter(fiche=fiche_observation).update(
                nid_prec_t_meme_couple=nid_prec_t_meme_couple,
                hauteur_nid=hauteur_nid,
                hauteur_couvert=hauteur_couvert,
                details_nid=details_nid,
            )

            # Création du résumé d'observation
            ResumeObservation.objects.filter(fiche=fiche_observation).update(
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
            )

            # Gestion des observations détaillées
            for i in range(len(dates)):
                Observation.objects.create(
                    fiche=fiche_observation,
                    date_observation=timezone.make_aware(datetime.fromisoformat(dates[i])),
                    nombre_oeufs=int(oeufs[i]) if oeufs[i] else 0,
                    nombre_poussins=int(poussins[i]) if poussins[i] else 0,
                    observations=textes[i]
                )

            # Gestion des causes d'échec
            CausesEchec.objects.filter(fiche=fiche_observation).update(
                description=causes_echec_description
            )

            # Gestion des remarques
            if remarque_texte:
                Remarque.objects.create(
                    fiche=fiche_observation,  # Associer la remarque à la fiche
                    remarque=remarque_texte,
                )

            messages.success(request, "Observation enregistrée avec succès!")
            return redirect('fiche_observation', fiche_id=fiche_observation.pk)

        except Espece.DoesNotExist:
            messages.error(request, "Erreur : l'espèce sélectionnée est invalide.")
            return redirect('saisie_observation')
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'observation : {e}")
            messages.error(request, "Erreur lors de l'enregistrement de l'observation.")
            return redirect('saisie_observation')

    return redirect('saisie_observation')