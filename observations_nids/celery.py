# observations_nids/celery.py
import os

from celery import Celery

from .config import get_settings

# Obtenir les paramètres
settings = get_settings()

# Définir les variables d'environnement par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')

# Créer l'instance de l'application Celery
app = Celery('observations_nids')

# Configuration de base pour Celery
app.conf.update(
    broker_url=settings.celery.broker_url,
    result_backend=settings.celery.result_backend,
    task_serializer=settings.celery.task_serializer,
    accept_content=settings.celery.accept_content,
    result_serializer=settings.celery.result_serializer,
    timezone=settings.celery.timezone,
    task_track_started=settings.celery.task_track_started,
    task_time_limit=settings.celery.task_time_limit,
    worker_hijack_root_logger=settings.celery.worker_hijack_root_logger,
    # --- Améliorations robustesse ---
    task_acks_late=True,
    task_default_retry_delay=30,  # 30s avant un retry automatique
    # --- Routage par files (désactivé pour l’instant) ---
    # task_routes={
    #     "importation.tasks.*": {"queue": "import"},
    #     "Transcription.tasks.*": {"queue": "ocr"},
    #     # tu peux en ajouter d’autres si besoin
    # },
)

# Charger automatiquement les tâches des applications Django installées
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
