# views_home.py
import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from observations.models import FicheObservation

logger = logging.getLogger('observations')


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
def liste_fiches_observations(request):
    fiches = FicheObservation.objects.select_related(
        'observateur', 'espece', 'localisation', 'etat_correction'
    ).all().order_by('-date_creation')

    paginator = Paginator(fiches, 10)
    page = request.GET.get('page', 1)
    fiches_page = paginator.get_page(page)

    context = {
        'fiches': fiches_page,
    }
    return render(request, 'liste_fiches_observations.html', context)
