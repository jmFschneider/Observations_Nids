"""
Décorateurs personnalisés pour les vues de l'application observations.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def transcription_required(view_func):
    """
    Décorateur pour restreindre l'accès aux vues de transcription.

    Autorise l'accès uniquement si :
    - L'utilisateur est connecté ET
    - L'utilisateur a le champ est_transcription = True OU est administrateur

    Lève une PermissionDenied (403) si l'utilisateur n'a pas les droits.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Vérifier si l'utilisateur peut transcrire
        if user.est_transcription or user.role == 'administrateur':
            return view_func(request, *args, **kwargs)

        # Sinon, refuser l'accès
        raise PermissionDenied("Vous n'avez pas les droits pour accéder à cette page.")

    return wrapper
