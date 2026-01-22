# observations_nids/celery.py
import os

from celery import Celery

# Définir les variables d'environnement par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')

# Créer l'instance de l'application Celery
app = Celery('observations_nids')

# Configuration de Celery directement depuis les variables d'environnement
# Cela évite d'appeler get_settings() au niveau du module, ce qui causerait
# des erreurs Pydantic pendant le build Docker quand les variables ne sont pas définies
redis_host = os.environ.get('REDIS_HOST', '127.0.0.1')
redis_port = os.environ.get('REDIS_PORT', '6379')
broker_url = os.environ.get('CELERY_BROKER_URL', f'redis://{redis_host}:{redis_port}/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{redis_host}:{redis_port}/0')

# Configuration de base pour Celery
app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_hijack_root_logger=False,
    # --- Améliorations robustesse ---
    task_acks_late=True,
    task_default_retry_delay=30,  # 30s avant un retry automatique
    # --- Routage par files (désactivé pour l'instant) ---
    # task_routes={
    #     "importation.tasks.*": {"queue": "import"},
    #     "Transcription.tasks.*": {"queue": "ocr"},
    #     # tu peux en ajouter d'autres si besoin
    # },
)

# Configuration spécifique à Windows pour Celery
if os.name == 'nt':
    app.conf.worker_concurrency = 1
    app.conf.worker_pool = 'solo'

# Charger automatiquement les tâches des applications Django installées
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
