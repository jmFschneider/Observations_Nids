from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Feedback


def is_admin(user):
    return user.is_authenticated and user.role == "administrateur"


@login_required
@require_POST
def submit_feedback(request):
    """Vue pour recevoir le feedback en AJAX"""
    from .tasks import process_feedback_ai  # noqa: PLC0415

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


@user_passes_test(is_admin)
def feedback_triage(request):
    """Vue de gestion (triage) pour les administrateurs"""
    # On sépare les retours par statut pour faciliter le traitement
    new_feedbacks = Feedback.objects.filter(status__in=["NEW", "READ"]).order_by(
        "-urgency", "-created_at"
    )
    processing_feedbacks = Feedback.objects.filter(status="IN_PROGRESS").order_by("-created_at")
    resolved_feedbacks = Feedback.objects.filter(status__in=["RESOLVED", "ARCHIVED"]).order_by(
        "-created_at"
    )

    context = {
        "new_feedbacks": new_feedbacks,
        "processing_feedbacks": processing_feedbacks,
        "resolved_feedbacks": resolved_feedbacks,
    }
    return render(request, "feedback/feedback_triage.html", context)


@user_passes_test(is_admin)
@require_POST
def update_feedback(request, feedback_id):
    """Vue AJAX pour mettre à jour un feedback"""
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        feedback.status = request.POST.get("status", feedback.status)
        feedback.category = request.POST.get("category", feedback.category)
        feedback.admin_note = request.POST.get("admin_note", feedback.admin_note)
        feedback.is_public_response = request.POST.get("is_public_response") == "true"
        feedback.save()
        return JsonResponse({"status": "success"})
    except Feedback.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Feedback introuvable"}, status=404)
