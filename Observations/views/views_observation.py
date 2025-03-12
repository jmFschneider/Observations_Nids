# views_home.py
from django.shortcuts import render, get_object_or_404, redirect
from Observations.models import  FicheObservation
import logging
logger = logging.getLogger('Observations')

def fiche_observation_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    localisation = fiche.localisation  # Récupérer la localisation liée

    # Vérifie si un résumé existe, sinon passe None
    resume = fiche.resume if hasattr(fiche, 'resume') else None

    # Vérifie si un nid existe, sinon passe None
    nid = fiche.nid if hasattr(fiche, 'nid') else None

    # Vérifie si un objet CausesEchec existe, sinon passe None
    causes_echec = fiche.causes_echec if hasattr(fiche, 'causes_echec') else None

    context = {
        'fiche': fiche,
        'localisation': localisation,
        'resume' : resume,
        'nid' : nid,
        'causes_echec': causes_echec,  # Ajout explicite de l'objet CausesEchec dans le contexte
    }
    return render(request, 'fiche_observation.html', context)

def nid_detail_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    nid = fiche.nid  # Accès direct via la relation OneToOne

    context = {
        'fiche': fiche,
        'nid': nid,
    }
    return render(request, 'observations/fiche_observation/nid_detail.html', context)

def resume_observation_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    resume = fiche.resume  # Accès direct via OneToOneField

    context = {
        'fiche': fiche,
        'resume': resume,
    }
    return render(request, 'observations/fiche_observation/resume_observation.html', context)

def causes_echec_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)

    # Vérifie si un objet CausesEchec existe, sinon passe None
    causes_echec = fiche.causes_echec if hasattr(fiche, 'causes_echec') else None

    context = {
        'fiche': fiche,
        'causes_echec': causes_echec,  # Ajout explicite de l'objet CausesEchec dans le contexte
    }
    return render(request, 'observations/fiche_observation/causes_echec.html', context)

def remarque_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)

    # Vérifie si un objet CausesEchec existe, sinon passe None
    causes_echec = fiche.causes_echec if hasattr(fiche, 'causes_echec') else None

    context = {
        'fiche': fiche,
        'causes_echec': causes_echec,  # Ajout explicite de l'objet CausesEchec dans le contexte
    }
    return render(request, 'observations/fiche_observation/causes_echec.html', context)
