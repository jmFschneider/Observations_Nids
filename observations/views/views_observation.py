# views_home.py
import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from observations.filters import FicheObservationFilter  # Import the filter
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
    fiches_queryset = (
        FicheObservation.objects.select_related(
            'observateur', 'espece', 'localisation', 'etat_correction'
        )
        .all()
        .order_by('date_creation')
    )

    fiche_filter = FicheObservationFilter(request.GET, queryset=fiches_queryset)
    fiches = fiche_filter.qs

    paginator = Paginator(fiches, 10)
    page = request.GET.get('page', 1)
    fiches_page = paginator.get_page(page)

    context = {
        'filter': fiche_filter,  # Pass the filter object to the template
        'fiches': fiches_page,
    }
    return render(request, 'liste_fiches_observations.html', context)

def get_statistics_context():
    """
    Prépare les données statistiques pour la page de statistiques.
    
    Retourne un dictionnaire contenant diverses statistiques sur les fiches d'observation.
    """
    from django.db.models import Count, Q
    from observations.models import FicheObservation
    
    # Total de fiches
    total_fiches = FicheObservation.objects.count()
    
    # Fiches en cours de saisie (statut 'nouveau' ou 'en_edition')
    fiches_EnCourSaisie = FicheObservation.objects.filter(
        Q(etat_correction__statut='nouveau') | Q(etat_correction__statut='en_edition')
    ).count()
    
    # Fiches en cours de correction (statut 'en_cours')
    fiches_EnCourCorrection = FicheObservation.objects.filter(
        etat_correction__statut='en_cours'
    ).count()
    
    # Fiches validées (statut 'valide')
    fiches_valides = FicheObservation.objects.filter(
        etat_correction__statut='valide'
    ).count()
    
    # Nombre d'espèces distinctes observées
    nb_especes = FicheObservation.objects.values('espece').distinct().count()
    
    # Nombre d'observateurs distincts
    nb_observateurs = FicheObservation.objects.values('observateur').distinct().count()
    
    # Top 4 espèces les plus fréquentes
    top_especes = (
        FicheObservation.objects
        .values('espece__nom')
        .annotate(count=Count('espece'))
        .order_by('-count')[:4]
    )
    
    # Fiches par année pour graphique
    fiches_par_annee_qs = (
        FicheObservation.objects
        .values('annee')
        .annotate(count=Count('num_fiche'))
        .order_by('annee')
    )
    fiches_par_annee = list(fiches_par_annee_qs)
    chart_labels = json.dumps([item['annee'] for item in fiches_par_annee])
    chart_data = json.dumps([item['count'] for item in fiches_par_annee])

    return {
        'total_fiches': total_fiches,
        'fiches_EnCourSaisie': fiches_EnCourSaisie,
        'fiches_EnCourCorrection': fiches_EnCourCorrection,
        'fiches_valides': fiches_valides,
        'nb_especes': nb_especes,
        'nb_observateurs': nb_observateurs,
        'top_especes': list(top_especes),
        'fiches_par_annee': fiches_par_annee,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }


@login_required
def statistiques_view(request):
    context = get_statistics_context()
    return render(request, 'observations/statistiques.html', context)