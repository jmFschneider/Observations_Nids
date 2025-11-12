"""
Context processors for observations_nids project.
"""

from django.conf import settings


def environment(request):
    """
    Ajoute la variable ENVIRONMENT au contexte de tous les templates.

    Permet d'afficher des bandeaux d'environnement (dev, pilote, production).
    """
    return {
        'environment': settings.ENVIRONMENT,
    }
