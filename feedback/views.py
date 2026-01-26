from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Feedback
from .tasks import process_feedback_ai


@login_required
@require_POST
def submit_feedback(request):
    """Vue pour recevoir le feedback en AJAX"""
    content = request.POST.get('content')
    url_source = request.POST.get('url_source')

    if not content or len(content.strip()) < 5:
        return JsonResponse({'status': 'error', 'message': 'Message trop court'}, status=400)

    # Création du feedback
    feedback = Feedback.objects.create(user=request.user, content=content, url_source=url_source)

    # Lancement de l'analyse IA en arrière-plan
    process_feedback_ai.delay(feedback.id)

    return JsonResponse(
        {'status': 'success', 'message': 'Merci ! Votre retour a bien été pris en compte.'}
    )
