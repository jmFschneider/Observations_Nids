# views_home.py
import logging

from django.shortcuts import render

from accounts.models import Utilisateur
from observations.models import FicheObservation, Observation

logger = logging.getLogger('observations')


def home(request):
    logger.info("Accueil visité")

    # 🔹 Redirection vers `access_restricted.html` si l'utilisateur n'est pas connecté
    if not request.user.is_authenticated:
        logger.debug("Visite anonyme - Redirection vers access_restricted.html")
        return render(request, 'access_restricted.html')

    # 🔹 Renommage pour éviter la confusion avec le modèle `Utilisateur`
    user = request.user  # L'utilisateur Django connecté

    users_count = Utilisateur.objects.count()
    observations_count = Observation.objects.count()

    # Récupérer les fiches en cours d'édition de l'observateur connecté
    fiches_en_edition = FicheObservation.objects.filter(
        observateur=user,
        etat_correction__statut__in=['nouveau', 'en_edition']
    ).select_related('espece', 'etat_correction').order_by('-date_creation')[:5]

    return render(
        request,
        'home.html',
        {
            'user': user,  # Renommé pour éviter la confusion avec le modèle
            'users_count': users_count,
            'observations_count': observations_count,
            'fiches_en_edition': fiches_en_edition,
        },
    )


def default_view(request):
    return render(request, 'access_restricted.html')
