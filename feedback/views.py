from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Feedback
from .tasks import process_feedback_ai


def is_admin(user):
    return user.is_authenticated and user.role == "administrateur"


@login_required
@require_POST
def submit_feedback(request):
    # ... (code existant inchangé)
    content = request.POST.get("content")
    url_source = request.POST.get("url_source")

    if not content or len(content.strip()) < 5:
        return JsonResponse({"status": "error", "message": "Message trop court"}, status=400)

    # Création du feedback
    feedback = Feedback.objects.create(user=request.user, content=content, url_source=url_source)

    # Lancement de l'analyse IA en arrière-plan
    process_feedback_ai.delay(feedback.id)

    return JsonResponse(
        {"status": "success", "message": "Merci ! Votre retour a bien été pris en compte."}
    )


@login_required
def feedback_list(request):
    """Vue pour lister les feedbacks (Tous les utilisateurs connectés)"""
    feedbacks = Feedback.objects.all().order_by("-created_at")
    return render(request, "feedback/feedback_list.html", {"feedbacks": feedbacks})
