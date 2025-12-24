"""Tâches Celery pour l'application taxonomy."""

import contextlib
import logging
from io import StringIO

from celery import shared_task
from django.core.management import call_command
from django.db import connection

logger = logging.getLogger('taxonomy')


@shared_task(bind=True, name='taxonomy.recuperer_liens_oiseaux_net')
def recuperer_liens_oiseaux_net_task(self, force=False, limit=None, dry_run=False, delay=1.0):
    """
    Tâche Celery pour récupérer les liens oiseaux.net de manière asynchrone.

    Cette tâche permet d'exécuter le script de récupération des liens en arrière-plan,
    évitant ainsi les timeouts 504 Gateway Timeout.

    Args:
        force: Mettre à jour même les espèces qui ont déjà un lien
        limit: Limiter à N espèces (pour tests)
        dry_run: Simuler sans modifier la base de données
        delay: Délai en secondes entre chaque requête (défaut: 1.0)

    Returns:
        dict: Résultats du traitement avec statistiques
    """
    try:
        # Fermer les connexions DB existantes pour éviter TransactionManagementError
        connection.close()

        # Capturer la sortie du script
        output = StringIO()

        # Construire les arguments pour la commande
        args = []
        if force:
            args.append('--force')
        if limit:
            args.extend(['--limit', str(limit)])
        if dry_run:
            args.append('--dry-run')
        args.extend(['--delay', str(delay)])

        logger.info(
            f"Démarrage de la tâche recuperer_liens_oiseaux_net "
            f"(force={force}, limit={limit}, dry_run={dry_run}, delay={delay})"
        )

        # Mise à jour de l'état initial
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'started',
                'message': 'Récupération des liens oiseaux.net en cours...',
                'percent': 0,
            },
        )

        # Exécuter la commande Django
        call_command('recuperer_liens_oiseaux_net', *args, stdout=output, stderr=output)

        # Récupérer la sortie
        result_output = output.getvalue()

        # Parser la sortie pour extraire les statistiques (format simple)
        # On cherche les lignes de statistiques dans la sortie
        stats = {
            'success_direct': 0,
            'success_google': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0,
        }

        # Extraction basique des stats depuis la sortie
        for line in result_output.split('\n'):
            if '[OK] Succes direct' in line:
                with contextlib.suppress(ValueError, IndexError):
                    stats['success_direct'] = int(line.split(':')[-1].strip())
            elif '[OK] Succes Google' in line:
                with contextlib.suppress(ValueError, IndexError):
                    stats['success_google'] = int(line.split(':')[-1].strip())
            elif '[X] Echecs' in line:
                with contextlib.suppress(ValueError, IndexError):
                    stats['failed'] = int(line.split(':')[-1].strip())
            elif '[!] Ignores' in line:
                with contextlib.suppress(ValueError, IndexError):
                    stats['skipped'] = int(line.split(':')[-1].strip())
            elif 'Total traite' in line:
                with contextlib.suppress(ValueError, IndexError):
                    stats['total'] = int(line.split(':')[-1].strip())

        total_success = stats['success_direct'] + stats['success_google']
        success_rate = (
            round((total_success / stats['total']) * 100, 1) if stats['total'] > 0 else 0
        )

        logger.info(
            f"Tâche recuperer_liens_oiseaux_net terminée avec succès: "
            f"{total_success}/{stats['total']} espèces traitées ({success_rate}%)"
        )

        # Mise à jour finale
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'completed',
                'message': 'Récupération des liens terminée avec succès',
                'percent': 100,
                'stats': stats,
                'success_rate': success_rate,
                'output': result_output,
            },
        )

        return {
            'status': 'SUCCESS',
            'stats': stats,
            'success_rate': success_rate,
            'output': result_output,
            'total_success': total_success,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la tâche recuperer_liens_oiseaux_net: {str(e)}")

        # Mise à jour de l'état en cas d'erreur
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'message': f'Erreur: {str(e)}',
                'percent': 0,
            },
        )

        return {'status': 'ERROR', 'error': str(e)}

    finally:
        # Toujours fermer la connexion
        connection.close()
