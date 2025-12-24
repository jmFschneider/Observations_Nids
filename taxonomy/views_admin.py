"""
Vues d'administration des données pour la gestion des espèces d'oiseaux.

Permet l'exécution des scripts de chargement et maintenance des données taxonomiques.
Réservé aux administrateurs uniquement.
"""

import logging
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.management import call_command
from django.db import connection
from django.shortcuts import redirect, render

from taxonomy.models import Espece, Famille, Ordre
from taxonomy.tasks import recuperer_liens_oiseaux_net_task

logger = logging.getLogger(__name__)


def is_admin(user):
    """Vérifie que l'utilisateur est administrateur."""
    return user.is_authenticated and user.is_staff


# ============================================================================
# VUE PRINCIPALE D'ADMINISTRATION DES DONNÉES
# ============================================================================


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def administration_donnees(request):
    """
    Page d'administration des données taxonomiques.

    Permet d'exécuter les scripts de chargement et maintenance des espèces.
    Accessible uniquement aux administrateurs (is_staff=True).
    """
    # Statistiques pour affichage
    stats = {
        'total': Espece.objects.count(),
        'ordres': Ordre.objects.count(),
        'familles': Famille.objects.count(),
        'source_lof': Espece.objects.filter(commentaire__icontains='LOF').count(),
        'source_taxref': Espece.objects.filter(commentaire__icontains='TaxRef').count(),
        'avec_liens': Espece.objects.exclude(lien_oiseau_net='').count(),
    }

    context = {
        'stats': stats,
    }

    return render(request, 'taxonomy/administration_donnees.html', context)


# ============================================================================
# VUES D'EXÉCUTION DES SCRIPTS DE CHARGEMENT
# ============================================================================


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def charger_especes_lof_view(request):
    """
    Exécute le script de chargement des espèces depuis la Liste Officielle de France (LOF).

    Accessible uniquement aux administrateurs (is_staff=True).
    """
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée")
        return redirect('taxonomy:administration_donnees')

    force = request.POST.get('force', 'false') == 'true'
    limit = request.POST.get('limit', '').strip()

    try:
        # Fermer toute transaction en cours pour éviter les conflits
        connection.close()

        # Capturer la sortie du script
        output = StringIO()

        # Construire les arguments
        args = []
        if force:
            args.append('--force')
        if limit:
            args.extend(['--limit', limit])

        # Exécuter le script
        logger.info(f"Lancement du chargement LOF (force={force}, limit={limit or 'none'})")

        call_command('charger_lof', *args, stdout=output, stderr=output)

        # Récupérer le résultat
        result = output.getvalue()

        # Afficher le succès
        messages.success(request, f"✅ Chargement LOF terminé avec succès !\n\n{result}")
        logger.info(f"Chargement LOF réussi: {result}")

    except Exception as e:
        # Fermer la connexion en cas d'erreur pour éviter TransactionManagementError
        connection.close()
        messages.error(request, f"❌ Erreur lors du chargement LOF: {str(e)}")
        logger.error(f"Erreur lors du chargement LOF: {e}", exc_info=True)

    return redirect('taxonomy:administration_donnees')


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def charger_especes_taxref_view(request):
    """
    Exécute le script de chargement des espèces depuis TaxRef (MNHN/INPN).

    Accessible uniquement aux administrateurs (is_staff=True).
    """
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée")
        return redirect('taxonomy:administration_donnees')

    force = request.POST.get('force', 'false') == 'true'
    limit = request.POST.get('limit', '').strip()
    taxref_version = request.POST.get('taxref_version', '').strip()

    try:
        # Fermer toute transaction en cours pour éviter les conflits
        connection.close()

        # Capturer la sortie du script
        output = StringIO()

        # Construire les arguments
        args = []
        if force:
            args.append('--force')
        if limit:
            args.extend(['--limit', limit])
        if taxref_version:
            args.extend(['--taxref-version', taxref_version])

        # Exécuter le script
        logger.info(
            f"Lancement du chargement TaxRef (force={force}, limit={limit or 'none'}, "
            f"version={taxref_version or 'default'})"
        )

        call_command('charger_taxref', *args, stdout=output, stderr=output)

        # Récupérer le résultat
        result = output.getvalue()

        # Afficher le succès
        messages.success(request, f"✅ Chargement TaxRef terminé avec succès !\n\n{result}")
        logger.info(f"Chargement TaxRef réussi: {result}")

    except Exception as e:
        # Fermer la connexion en cas d'erreur pour éviter TransactionManagementError
        connection.close()
        messages.error(request, f"❌ Erreur lors du chargement TaxRef: {str(e)}")
        logger.error(f"Erreur lors du chargement TaxRef: {e}", exc_info=True)

    return redirect('taxonomy:administration_donnees')


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def recuperer_liens_oiseaux_net_view(request):
    """
    Lance la récupération des liens oiseaux.net en arrière-plan via Celery.

    Cette tâche peut prendre plusieurs minutes et s'exécute de manière asynchrone
    pour éviter les timeouts 504 Gateway Timeout.

    Accessible uniquement aux administrateurs (is_staff=True).
    """
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée")
        return redirect('taxonomy:administration_donnees')

    force = request.POST.get('force', 'false') == 'true'
    limit = request.POST.get('limit', '').strip()
    dry_run = request.POST.get('dry_run', 'false') == 'true'
    delay = request.POST.get('delay', '1.0')

    try:
        # Convertir limit en int ou None
        limit_int = int(limit) if limit else None

        # Convertir delay en float
        delay_float = float(delay)

        logger.info(
            f"Lancement asynchrone de la récupération des liens oiseaux.net "
            f"(force={force}, limit={limit_int or 'none'}, dry_run={dry_run}, delay={delay_float})"
        )

        # Lancer la tâche Celery en arrière-plan
        task = recuperer_liens_oiseaux_net_task.delay(
            force=force, limit=limit_int, dry_run=dry_run, delay=delay_float
        )

        # Message de confirmation avec ID de tâche
        messages.success(
            request,
            f"✅ Tâche lancée avec succès (ID: {task.id})\n\n"
            f"La récupération des liens s'exécute en arrière-plan. "
            f"Flower s'est ouvert dans un nouvel onglet pour suivre la progression.",
        )
        logger.info(f"Tâche Celery lancée: {task.id}")

        # Rediriger avec le task_id pour ouvrir Flower automatiquement
        return redirect(f"{request.scheme}://{request.get_host()}/taxonomy/administration/?task_id={task.id}")

    except Exception as e:
        messages.error(request, f"❌ Erreur lors du lancement de la tâche: {str(e)}")
        logger.error(f"Erreur lors du lancement de la tâche: {e}", exc_info=True)

    return redirect('taxonomy:administration_donnees')
