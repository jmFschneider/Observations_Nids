import logging

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Feedback, FeedbackMessage

logger = logging.getLogger(__name__)


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

    # Lancement de l'analyse IA en arrière-plan (silencieux si Celery indisponible)
    try:
        process_feedback_ai.delay(feedback.id)
    except Exception:
        logger.warning("Celery indisponible, analyse IA du feedback %s ignorée.", feedback.id)

    return JsonResponse(
        {"status": "success", "message": "Merci ! Votre retour a bien été pris en compte."}
    )


@login_required
def feedback_list(request):
    """Ancienne vue liste, redirige vers la nouvelle vue unifiée de triage"""
    return redirect("feedback:triage")


@login_required
def feedback_detail(request, feedback_id):
    """Vue pour voir le détail d'un feedback et discuter"""
    feedback = get_object_or_404(Feedback, id=feedback_id)

    # ACCÈS OUVERT : Tout utilisateur connecté peut voir et répondre (Logique collaborative)
    # L'ancienne restriction (auteur ou admin seulement) est supprimée.

    if request.method == "POST":
        content = request.POST.get("content")
        if content and len(content.strip()) >= 2:
            FeedbackMessage.objects.create(feedback=feedback, author=request.user, content=content)

            # Mise à jour de la dernière activité
            feedback.last_activity = timezone.now()

            # Changement de statut automatique selon qui répond
            if is_admin(request.user):
                # Si l'admin répond, on peut suggérer qu'on attend une réponse ou que c'est en cours
                if feedback.status in ["NEW", "READ"]:
                    feedback.status = "IN_PROGRESS"
            # Si l'utilisateur répond et que c'était en attente, on repasse en cours
            elif feedback.status == "WAITING_USER":
                feedback.status = "IN_PROGRESS"

            feedback.save()
            return redirect("feedback:detail", feedback_id=feedback.id)

    feedback_messages = feedback.messages.all().select_related("author")
    return render(
        request,
        "feedback/feedback_detail.html",
        {"feedback": feedback, "feedback_messages": feedback_messages},
    )


@login_required
def feedback_triage(request):
    """Vue unifiée de gestion et liste des retours (Admin + Utilisateurs)"""
    # Pour l'instant, tout le monde voit tout (comme l'ancienne vue 'list')
    # Mais on utilise l'interface 'triage' qui est mieux organisée.

    # On sépare les retours par statut
    new_feedbacks = Feedback.objects.filter(status__in=["NEW", "READ"]).order_by(
        "-urgency", "-last_activity"
    )
    processing_feedbacks = Feedback.objects.filter(
        status__in=["IN_PROGRESS", "WAITING_USER"]
    ).order_by("-last_activity")
    resolved_feedbacks = Feedback.objects.filter(status__in=["RESOLVED", "ARCHIVED"]).order_by(
        "-last_activity"
    )

    context = {
        "new_feedbacks": new_feedbacks,
        "processing_feedbacks": processing_feedbacks,
        "resolved_feedbacks": resolved_feedbacks,
        "is_admin": is_admin(request.user),  # Pour conditionner l'affichage dans le template
    }
    return render(request, "feedback/feedback_triage.html", context)


@login_required
def technical_problems(request):
    """Vue unifiée pour les problèmes techniques OCR et Ingest"""
    from observations.models import FicheObservation  # noqa: PLC0415

    errors = {}
    form_data = {}

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category = request.POST.get("category", "OCR").strip()
        fiche_id = request.POST.get("fiche_id", "").strip()
        form_data = {"title": title, "content": content, "category": category, "fiche_id": fiche_id}

        if category not in ("OCR", "INGEST"):
            category = "OCR"

        if not title:
            errors["title"] = "Le titre est obligatoire."
        if not content or len(content) < 5:
            errors["content"] = "La description est obligatoire (5 caractères minimum)."

        if not errors:
            fiche = None
            if fiche_id:
                try:
                    fiche = FicheObservation.objects.get(pk=int(fiche_id))
                except (FicheObservation.DoesNotExist, ValueError):
                    errors["fiche_id"] = f"Fiche n°{fiche_id} introuvable."

        if not errors:
            Feedback.objects.create(
                user=request.user,
                title=title,
                content=content,
                category=category,
                status="IN_PROGRESS",
                urgency=3,
                fiche_observation=fiche,
            )
            return redirect("feedback:technical_problems")

    # Filtre par catégorie (onglets)
    active_tab = request.GET.get("tab", "OCR")
    if active_tab not in ("OCR", "INGEST"):
        active_tab = "OCR"

    ocr_problems = Feedback.objects.filter(category="OCR").order_by("-last_activity")
    ingest_problems = Feedback.objects.filter(category="INGEST").order_by("-last_activity")

    return render(
        request,
        "feedback/technical_problems.html",
        {
            "ocr_problems": ocr_problems,
            "ingest_problems": ingest_problems,
            "active_tab": active_tab,
            "errors": errors,
            "form_data": form_data,
        },
    )


@login_required
def ocr_problems(request):
    """Redirige vers la vue unifiée (compatibilité ascendante)"""
    return redirect("feedback:technical_problems")  # noqa: RET504


@user_passes_test(is_admin)
@require_POST
def update_feedback(request, feedback_id):
    """Vue AJAX pour mettre à jour un feedback (statut, catégorie)"""
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        feedback.status = request.POST.get("status", feedback.status)
        feedback.category = request.POST.get("category", feedback.category)
        feedback.is_public_response = request.POST.get("is_public_response") == "true"
        feedback.save()
        return JsonResponse({"status": "success"})
    except Feedback.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Feedback introuvable"}, status=404)
