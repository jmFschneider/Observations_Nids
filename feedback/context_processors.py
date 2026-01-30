from datetime import timedelta

from django.utils import timezone

from .models import Feedback


def feedback_notifications(request):
    """
    Fournit des informations globales sur les feedbacks au contexte des templates.
    """
    has_waiting = False
    has_recent = False
    # Date seuil pour considérer une activité comme "récente" (48 heures)
    recent_threshold = timezone.now() - timedelta(hours=48)

    if request.user.is_authenticated:
        # 1. En attente d'infos (Orange/Rouge dans le menu)
        has_waiting = Feedback.objects.filter(user=request.user, status="WAITING_USER").exists()

        # 2. Activité récente (Vert dans le menu)
        # On regarde si un feedback de l'utilisateur a eu une activité depuis moins de 48h
        # (en excluant ceux qui sont déjà en WAITING_USER pour ne pas mélanger les couleurs)
        has_recent = (
            Feedback.objects.filter(user=request.user, last_activity__gt=recent_threshold)
            .exclude(status="WAITING_USER")
            .exists()
        )

    return {
        'has_waiting_feedback': has_waiting,
        'has_recent_activity': has_recent,
        'recent_activity_threshold': recent_threshold,
    }
