"""
Vues pour l'app ocr en production.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, cast

from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render

from observations.decorators import transcription_required
from ocr.models import TranscriptionOCR
from ocr.tasks import process_images_production_task

logger = logging.getLogger('ocr')


@transcription_required
def ocr_home(request):
    """Page d'accueil de l'OCR"""
    return render(request, 'ocr/home.html')


@transcription_required
def selection_images(request):
    """Sélection d'images pour transcription."""
    # Navigation désormais ancrée dans media/images/
    base_dir = os.path.join(settings.MEDIA_ROOT, 'images')
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    current_path = request.GET.get('path', '')
    base_path = Path(base_dir).resolve()
    requested = (base_path / current_path).resolve()
    if not str(requested).startswith(str(base_path)):
        requested = base_path
    full_current_path = str(requested)
    safe_path = str(requested.relative_to(base_path)).replace('\\', '/')

    directories = []
    images = []

    try:
        for item in os.listdir(full_current_path):
            item_path = os.path.join(full_current_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            elif item.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(item)

        directories.sort()
        images.sort()
    except (OSError, PermissionError):
        messages.error(request, "Impossible d'accéder à ce répertoire")

    breadcrumb = []
    if safe_path and safe_path != '.':
        parts = safe_path.split('/')
        current = ''
        for part in parts:
            if part:
                current = f"{current}/{part}" if current else part
                breadcrumb.append({'name': part, 'path': current})

    context = {
        'directories': directories,
        'images': images,
        'current_path': safe_path,
        'breadcrumb': breadcrumb,
        'parent_path': '/'.join(safe_path.split('/')[:-1])
        if safe_path and safe_path != '.'
        else None,
    }

    return render(request, 'ocr/selection_images.html', context)


@transcription_required
def lancer_ocr(request):
    """Lance la transcription des images sélectionnées."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        images_json = request.POST.get('images')
        repertoire = request.POST.get('repertoire', '')

        if not images_json:
            return JsonResponse({'error': 'Aucune image sélectionnée'}, status=400)

        image_filenames = json.loads(images_json)
        # On ajoute le préfixe 'images/' car la sélection est ancrée dans media/images/
        image_paths = [
            os.path.join('images', repertoire, f).replace('\\', '/') for f in image_filenames
        ]

        task = process_images_production_task.delay(image_paths)
        request.session['ocr_task_id'] = task.id

        return JsonResponse(
            {'success': True, 'task_id': task.id, 'message': 'Transcription démarrée'}
        )

    except Exception as e:
        logger.error(f"Erreur lancement OCR: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@transcription_required
def verifier_progression(request: HttpRequest) -> JsonResponse:
    """Suivi de progression Celery."""
    task_id = request.session.get('ocr_task_id')
    if not task_id:
        return JsonResponse({'status': 'NO_TASK'})

    result = AsyncResult(task_id)
    response: dict[str, Any] = {'status': result.status}

    if result.status == 'PROGRESS':
        info = cast(dict, result.info)
        response.update(
            {
                'percent': info.get('percent', 0),
                'processed': info.get('processed', 0),
                'total': info.get('total', 0),
                'logs': info.get('logs', []),
            }
        )
    elif result.status == 'SUCCESS':
        response.update(cast(dict, result.result))
        response['percent'] = 100

    return JsonResponse(response)


@transcription_required
def historique_ocr(request: HttpRequest):
    """Historique des transcriptions OCR avec filtres statut et pagination."""
    statut = request.GET.get('statut', '')
    qs = TranscriptionOCR.objects.select_related('fiche')
    if statut in ('succes', 'erreur', 'en_cours'):
        qs = qs.filter(statut=statut)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(
        request,
        'ocr/historique.html',
        {
            'page_obj': page_obj,
            'statut_filtre': statut,
            'total': qs.count(),
        },
    )
