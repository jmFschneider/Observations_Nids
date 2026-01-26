import logging

from celery import shared_task

from .models import Feedback
from .services import analyze_feedback_with_ai

logger = logging.getLogger(__name__)


@shared_task
def process_feedback_ai(feedback_id):
    """Tâche Celery pour analyser un feedback après sa création"""
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        analysis = analyze_feedback_with_ai(feedback.content)

        if analysis:
            feedback.category = analysis.get('category', 'OTHER')
            feedback.urgency = analysis.get('urgency', 1)
            feedback.sentiment = analysis.get('sentiment', '')
            feedback.ai_summary = analysis.get('summary', '')
            feedback.save()
            logger.info(f"Feedback {feedback_id} analysé avec succès par l'IA.")
        else:
            logger.warning(f"L'analyse IA a échoué pour le feedback {feedback_id}.")

    except Feedback.DoesNotExist:
        logger.error(f"Feedback {feedback_id} introuvable pour analyse.")
    except Exception as e:
        logger.error(f"Erreur lors du traitement Celery du feedback {feedback_id}: {e}")
