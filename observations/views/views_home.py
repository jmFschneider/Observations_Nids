# views_home.py
import logging

from django.shortcuts import render

from administration.models import Utilisateur  # importation mise à jour
from observations.models import Observation

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

    return render(
        request,
        'home.html',
        {
            'user': user,  # Renommé pour éviter la confusion avec le modèle
            'users_count': users_count,
            'observations_count': observations_count,
        },
    )


def default_view(request):
    return render(request, 'access_restricted.html')
