from .models import Feedback


def feedback_notifications(request):
    """
    Vérifie si l'utilisateur a des feedbacks en attente de réponse.
    Ajoute 'has_waiting_feedback' au contexte du template.
    """
    has_waiting = False

    if request.user.is_authenticated:
        # On regarde s'il existe au moins un feedback de cet utilisateur
        # avec le statut WAITING_USER (En attente d'infos)
        has_waiting = Feedback.objects.filter(user=request.user, status="WAITING_USER").exists()

    return {'has_waiting_feedback': has_waiting}
