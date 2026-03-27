"""
Vues pour l'app ocr en production.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, cast

from celery import current_app
from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from observations.decorators import transcription_required
from ocr.models import TranscriptionOCR
from ocr.tasks import DEFAULT_MIN_CHUNK_SIZE, enqueue_parallel_ocr_tasks

logger = logging.getLogger('ocr')

# TTL du cache des comptages d'images par répertoire (secondes)
CACHE_IMG_COUNTS_TTL = 300


@transcription_required
def ocr_home(request: HttpRequest) -> HttpResponse:
    """Page d'accueil de l'OCR"""
    return render(request, 'ocr/home.html')


def _prefix_images(safe_path: str) -> str:
    """Préfixe DB pour chemin sous media/images/ (ex: 'images/' ou 'images/2024/')."""
    if not safe_path or safe_path == '.':
        return 'images/'
    return f"images/{safe_path.rstrip('/')}/"


def _comptages_ocr_par_sous_repertoire(prefix: str) -> dict[str, int]:
    """
    Une requête SQL : compte des transcriptions en succès par répertoire sous prefix.
    Retourne un dict {nom_sous_repertoire: count} (agrégé sur le premier niveau sous prefix).
    """
    qs = (
        TranscriptionOCR.objects.filter(statut='succes', repertoire__startswith=prefix)
        .values('repertoire')
        .annotate(count=Count('id'))
    )
    result: dict[str, int] = {}
    for entry in qs:
        rep = entry['repertoire']
        count = entry['count']
        if not rep or not rep.startswith(prefix):
            continue
        relative = rep[len(prefix) :].strip('/')
        if not relative:
            continue
        top_dir = relative.split('/')[0]
        result[top_dir] = result.get(top_dir, 0) + count
    return result


def _comptages_images_fs_par_sous_repertoire(
    full_current_path: str, cache_key: str
) -> dict[str, int]:
    """
    Compte récursif des images (jpg, jpeg, png) par sous-répertoire direct.
    Utilise le cache Django (TTL 5 min) pour éviter des os.walk répétés.
    """
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result: dict[str, int] = {}
    try:
        for root, _dirs, files in os.walk(full_current_path):
            img_count = sum(1 for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png')))
            if img_count == 0:
                continue
            rel = os.path.relpath(root, full_current_path).replace('\\', '/')
            if rel == '.':
                continue
            top_dir = rel.split('/')[0]
            result[top_dir] = result.get(top_dir, 0) + img_count
    except (OSError, PermissionError):
        pass
    cache.set(cache_key, result, timeout=CACHE_IMG_COUNTS_TTL)
    return result


@transcription_required
def selection_images(request: HttpRequest) -> HttpResponse:
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

    dir_names: list[str] = []
    images: list[str] = []

    try:
        for item in os.listdir(full_current_path):
            item_path = os.path.join(full_current_path, item)
            if os.path.isdir(item_path):
                dir_names.append(item)
            elif item.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(item)

        dir_names.sort()
        images.sort()
    except (OSError, PermissionError):
        messages.error(request, "Impossible d'accéder à ce répertoire")

    # Compteurs par répertoire (BDD + cache filesystem)
    prefix = _prefix_images(safe_path)
    ocr_counts = _comptages_ocr_par_sous_repertoire(prefix)
    cache_key = f"ocr:img_counts:{safe_path or '.'}"
    total_counts = _comptages_images_fs_par_sous_repertoire(full_current_path, cache_key)

    directories = [
        {
            'name': name,
            'total_images': total_counts.get(name, 0),
            'transcribed_count': ocr_counts.get(name, 0),
        }
        for name in dir_names
    ]

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
def lancer_ocr(request: HttpRequest) -> JsonResponse:
    """Lance la transcription des images sélectionnées."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        images_json = request.POST.get('images')
        repertoire = request.POST.get('repertoire', '')
        parallelism_raw = request.POST.get('parallelism')
        gemini_rpm_raw = request.POST.get('gemini_rpm')
        min_chunk_size_raw = request.POST.get('min_chunk_size')

        if not images_json:
            return JsonResponse({'error': 'Aucune image sélectionnée'}, status=400)

        image_filenames = json.loads(images_json)
        # On ajoute le préfixe 'images/' car la sélection est ancrée dans media/images/
        image_paths = [
            os.path.join('images', repertoire, f).replace('\\', '/') for f in image_filenames
        ]

        logger.info(
            "OCR: envoi tâche Celery queue=ocr — %d image(s), repertoire=%s",
            len(image_paths),
            repertoire,
        )
        parallelism: int | None = None
        if parallelism_raw:
            try:
                parallelism = max(1, int(parallelism_raw))
            except ValueError:
                parallelism = None

        gemini_rpm: int = 60
        if gemini_rpm_raw:
            try:
                gemini_rpm = max(1, min(60, int(gemini_rpm_raw)))
            except ValueError:
                gemini_rpm = 60

        min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE
        if min_chunk_size_raw:
            try:
                min_chunk_size = max(10, int(min_chunk_size_raw))
            except ValueError:
                min_chunk_size = DEFAULT_MIN_CHUNK_SIZE

        dispatch = enqueue_parallel_ocr_tasks(
            image_paths,
            requested_parallelism=parallelism,
            gemini_rpm=gemini_rpm,
            min_chunk_size=min_chunk_size,
        )
        task_ids = dispatch['task_ids']
        chunk_sizes = cast(list[int], dispatch.get('chunks', []))
        request.session['ocr_task_id'] = task_ids[0] if task_ids else None
        request.session['ocr_task_ids'] = task_ids
        request.session['ocr_total_images'] = len(image_paths)
        request.session['ocr_task_chunks'] = chunk_sizes

        return JsonResponse(
            {
                'success': True,
                'task_id': task_ids[0] if task_ids else None,
                'task_ids': task_ids,
                'chunks': chunk_sizes,
                'message': (
                    f"Transcription démarrée ({len(task_ids)} tâche(s) parallèle(s))"
                    if task_ids
                    else "Aucune image à traiter"
                ),
            }
        )

    except Exception as e:
        logger.error(f"Erreur lancement OCR: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@transcription_required
def verifier_progression(request: HttpRequest) -> JsonResponse:
    """Suivi de progression Celery."""
    task_ids = request.session.get('ocr_task_ids')
    if isinstance(task_ids, str):
        task_ids = [task_ids]
    if not task_ids:
        task_id = request.session.get('ocr_task_id')
        task_ids = [task_id] if task_id else []

    if not task_ids:
        return JsonResponse({'status': 'NO_TASK'})

    total = int(request.session.get('ocr_total_images') or 0)
    task_chunks = request.session.get('ocr_task_chunks')
    if not isinstance(task_chunks, list):
        task_chunks = []
    processed = 0
    success_count = 0
    ignored_count = 0
    errors: list[dict[str, str]] = []
    merged_logs: list[dict[str, str]] = []
    per_task: list[dict[str, Any]] = []
    has_failure = False
    all_success = True
    completed_tasks = 0
    total_tasks = len(task_ids)

    for index, task_id in enumerate(task_ids):
        result = AsyncResult(task_id)
        status = result.status
        chunk_total = (
            int(task_chunks[index])
            if index < len(task_chunks) and isinstance(task_chunks[index], int)
            else 0
        )
        task_entry: dict[str, Any] = {
            'task_id': task_id,
            'task_short_id': task_id[:8],
            'status': status,
            'processed': 0,
            'total': chunk_total,
            'percent': 0,
        }

        if status in {'FAILURE', 'REVOKED'}:
            has_failure = True
            all_success = False
            failure_message = str(result.result) if result.result else "Erreur inconnue"
            errors.append({'file': f'task:{task_id[:8]}', 'error': failure_message})
            task_entry['error'] = failure_message
            per_task.append(task_entry)
            continue

        if status == 'SUCCESS':
            payload = cast(dict[str, Any], result.result) if isinstance(result.result, dict) else {}
            task_processed = int(payload.get('total', chunk_total))
            task_total = int(payload.get('total', chunk_total))
            processed += task_processed
            success_count += int(payload.get('success', 0))
            ignored_count += int(payload.get('ignored', 0))
            task_errors = payload.get('errors', [])
            if isinstance(task_errors, list):
                errors.extend(cast(list[dict[str, str]], task_errors))
            task_entry.update(
                {
                    'processed': task_processed,
                    'total': task_total,
                    'percent': 100 if task_total else 0,
                }
            )
            completed_tasks += 1
            per_task.append(task_entry)
            continue

        all_success = False
        if status == 'PROGRESS':
            info = cast(dict[str, Any], result.info) if isinstance(result.info, dict) else {}
            task_processed = int(info.get('processed', 0))
            task_total = int(info.get('total', chunk_total))
            task_percent = int(info.get('percent', 0))
            processed += task_processed
            task_entry.update(
                {
                    'processed': task_processed,
                    'total': task_total,
                    'percent': task_percent,
                }
            )
            task_logs = info.get('logs', [])
            if isinstance(task_logs, list):
                for log in task_logs:
                    if isinstance(log, dict):
                        message = str(log.get('message', ''))
                        merged_logs.append(
                            {
                                'timestamp': str(log.get('timestamp', '')),
                                'level': str(log.get('level', 'info')),
                                'message': f"[{task_id[:8]}] {message}",
                            }
                        )
        elif status in {'PENDING', 'STARTED'}:
            task_entry.update({'processed': 0, 'total': chunk_total, 'percent': 0})
            all_success = False
        else:
            all_success = False

        per_task.append(task_entry)

    merged_logs = merged_logs[-100:]
    effective_total = max(total, processed, 1)
    percent = 100 if all_success else min(99, int((processed / effective_total) * 100))

    if has_failure:
        return JsonResponse(
            {
                'status': 'FAILURE',
                'percent': percent,
                'processed': processed,
                'total': effective_total,
                'logs': merged_logs,
                'errors': errors,
                'per_task': per_task,
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks,
            }
        )

    if all_success:
        return JsonResponse(
            {
                'status': 'SUCCESS',
                'percent': 100,
                'processed': effective_total,
                'total': effective_total,
                'success': success_count,
                'ignored': ignored_count,
                'errors': errors,
                'per_task': per_task,
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks,
            }
        )

    return JsonResponse(
        {
            'status': 'PROGRESS',
            'percent': percent,
            'processed': processed,
            'total': effective_total,
            'logs': merged_logs,
            'per_task': per_task,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
        }
    )


@transcription_required
def annuler_ocr(request: HttpRequest) -> JsonResponse:
    """Révoque les tâches OCR en cours."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    task_ids = request.session.get('ocr_task_ids')
    if isinstance(task_ids, str):
        task_ids = [task_ids]
    if not task_ids:
        task_id = request.session.get('ocr_task_id')
        task_ids = [task_id] if task_id else []

    if not task_ids:
        return JsonResponse({'error': 'Aucune tâche en cours'}, status=400)

    current_app.control.revoke(task_ids, terminate=True)

    # Purge uniquement la queue OCR pour nettoyer les tâches en attente
    purged = 0
    try:
        with current_app.connection_for_write() as conn, conn.channel() as ch:
            purged = ch.queue_purge('ocr')
    except Exception as exc:
        logger.warning("OCR: impossible de purger la queue ocr : %s", exc)

    logger.info(
        "OCR: révocation de %d tâche(s), %d message(s) purgé(s) de la queue ocr",
        len(task_ids),
        purged,
    )

    request.session.pop('ocr_task_ids', None)
    request.session.pop('ocr_task_id', None)
    request.session.pop('ocr_total_images', None)
    request.session.pop('ocr_task_chunks', None)

    return JsonResponse({'success': True, 'revoked': len(task_ids)})


@transcription_required
def historique_ocr(request: HttpRequest) -> HttpResponse:
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
