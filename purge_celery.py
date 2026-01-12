"""
Script simple pour purger la queue Celery.
À exécuter depuis le répertoire du projet.

Usage:
    python purge_celery.py
"""

from observations_nids.celery import app

print("=" * 60)
print("  PURGE DES TÂCHES CELERY EN ATTENTE")
print("=" * 60)

print("\n📋 Tâches enregistrées:")
for task_name in sorted(app.tasks.keys()):
    if not task_name.startswith('celery.'):
        print(f"  ✓ {task_name}")

print("\n🔍 Vérification de la queue...")

try:
    # Purger directement
    purged = app.control.purge()
    print(f"\n✅ {purged} message(s) purgé(s) de la queue Celery")
except Exception as e:
    print(f"\n❌ Erreur lors de la purge: {e}")
    print("\nSi Celery est en cours d'exécution, arrête-le d'abord (Ctrl+C)")

print("\n✅ Terminé !")
