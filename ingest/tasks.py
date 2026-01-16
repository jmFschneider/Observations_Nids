# ingest/tasks.py
"""
Tâches Celery pour l'importation batch de fichiers JSON.
"""

import logging
import os

from celery import shared_task
from celery.result import AsyncResult
from django.conf import settings
from django.utils import timezone

from ingest.importation_service import ImportationService
from ingest.models import TranscriptionBrute

logger = logging.getLogger(__name__)


def _log_progress(task_self, message, level='info', details=None):
    """
    Ajoute un message au log de progression visible en temps réel.

    Args:
        task_self: Instance de la tâche Celery (self)
        message: Message à logger
        level: Niveau du log ('info', 'success', 'warning', 'error')
        details: Détails optionnels (dict)
    """
    timestamp = timezone.now().strftime('%H:%M:%S')

    # Construire l'entrée de log
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level,
    }
    if details:
        log_entry['details'] = details

    # Récupérer la meta actuelle de la tâche via AsyncResult
    try:
        result = AsyncResult(task_self.request.id)
        current_meta = result.info if result.info and isinstance(result.info, dict) else {}
    except Exception:
        current_meta = {}

    # Ajouter le nouveau log
    logs = current_meta.get('logs', [])
    logs.append(log_entry)

    # Limiter à 200 dernières entrées pour ne pas surcharger Redis
    if len(logs) > 200:
        logs = logs[-200:]

    # Mettre à jour la meta avec les logs (préserve les autres champs comme processed, total, etc.)
    current_meta['logs'] = logs

    # Utiliser update_state pour mettre à jour Redis
    task_self.update_state(state='PROGRESS', meta=current_meta)

    # Logger aussi dans les logs serveur pour historique
    log_method = getattr(logger, level if level in ['info', 'warning', 'error'] else 'info')
    log_method(f"[{timestamp}] {message}")


@shared_task(bind=True, name='ingest.process_json_batch')
def process_json_batch_task(self, fichiers_json, repertoire):
    """
    Tâche Celery pour traiter un batch de fichiers JSON en arrière-plan.

    Args:
        fichiers_json: Liste des noms de fichiers JSON à traiter
        repertoire: Chemin relatif du répertoire contenant les fichiers JSON

    Returns:
        dict: Résultats du traitement avec statistiques
    """
    _log_progress(
        self, f"🚀 Démarrage du traitement batch de {len(fichiers_json)} fichier(s)", 'info'
    )
    _log_progress(self, f"📁 Répertoire: {repertoire}", 'info')

    service = ImportationService()
    total = len(fichiers_json)
    processed = 0
    success_count = 0
    error_count = 0
    ignored_count = 0
    fiches_creees = []
    erreurs = []

    # Initialiser la progression
    self.update_state(
        state='PROGRESS',
        meta={
            'total': total,
            'processed': 0,
            'success_count': 0,
            'error_count': 0,
            'ignored_count': 0,
            'current_file': '',
            'logs': [],
        },
    )

    # Traiter chaque fichier JSON
    for index, fichier in enumerate(fichiers_json, 1):
        try:
            # Mettre à jour le fichier en cours
            current_meta = {
                'total': total,
                'processed': processed,
                'success_count': success_count,
                'error_count': error_count,
                'ignored_count': ignored_count,
                'current_file': fichier,
                'percent': int((processed / total) * 100) if total > 0 else 0,
                'logs': [],
            }
            self.update_state(state='PROGRESS', meta=current_meta)

            _log_progress(self, f"📄 [{index}/{total}] Traitement de {fichier}...", 'info')

            # Éviter les doublons : si la transcription existe déjà, ignorer
            if TranscriptionBrute.objects.filter(fichier_source=fichier).exists():
                ignored_count += 1
                processed += 1
                _log_progress(self, f"⏭️  {fichier} ignoré (déjà importé)", 'warning')
                continue

            # Traiter le fichier
            resultat = service.traiter_fichier_json(fichier, repertoire)

            if resultat['success']:
                success_count += 1
                fiche_id = resultat.get('fiche_id')
                fiches_creees.append({'fichier': fichier, 'fiche_id': fiche_id})
                _log_progress(self, f"✅ {fichier} → Fiche {fiche_id} créée avec succès", 'success')
            else:
                error_count += 1
                message = resultat.get('message', 'Erreur inconnue')
                erreurs.append({'fichier': fichier, 'message': message})
                _log_progress(self, f"❌ {fichier} → Erreur: {message}", 'error')

            processed += 1

            # Mettre à jour la progression après chaque fichier
            percent = int((processed / total) * 100) if total > 0 else 0
            self.update_state(
                state='PROGRESS',
                meta={
                    'total': total,
                    'processed': processed,
                    'success_count': success_count,
                    'error_count': error_count,
                    'ignored_count': ignored_count,
                    'current_file': fichier,
                    'percent': percent,
                    'logs': current_meta.get('logs', []),
                },
            )

        except Exception as e:
            error_count += 1
            processed += 1
            error_msg = str(e)[:200]  # Limiter la longueur du message
            erreurs.append({'fichier': fichier, 'message': error_msg})
            _log_progress(self, f"❌ {fichier} → Exception: {error_msg}", 'error')
            logger.error(f"Erreur lors du traitement de {fichier}: {str(e)}", exc_info=True)

    # Résumé final
    _log_progress(
        self,
        f"✨ Traitement terminé: {success_count} réussis, {ignored_count} ignorés, {error_count} erreurs",
        'success',
    )

    return {
        'total': total,
        'processed': processed,
        'success_count': success_count,
        'error_count': error_count,
        'ignored_count': ignored_count,
        'fiches_creees': fiches_creees,
        'erreurs': erreurs[:20],  # Limiter à 20 erreurs pour ne pas surcharger
    }
