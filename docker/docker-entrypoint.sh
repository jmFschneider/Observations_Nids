#!/bin/bash
# Script d'entrée pour le conteneur Django

set -e

# Fonction pour attendre que la base de données soit prête
wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 1
    done
    echo "Database is ready!"
}

# Fonction pour attendre que Redis soit prêt
wait_for_redis() {
    echo "Waiting for Redis to be ready..."
    while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Attendre que les services soient prêts
wait_for_db
wait_for_redis

# Migrations et collectstatic uniquement pour le service web (gunicorn)
# Les workers Celery, Beat et Flower n'ont pas besoin de ces opérations
if echo "$1" | grep -q "gunicorn"; then
    echo "Running database migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    # Créer un superuser si les variables sont définies
    # Utilise os.environ pour éviter les problèmes d'échappement des caractères spéciaux
    if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
        echo "Creating superuser if it doesn't exist..."
        python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ['DJANGO_SUPERUSER_USERNAME']
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=os.environ['DJANGO_SUPERUSER_EMAIL'],
        password=os.environ['DJANGO_SUPERUSER_PASSWORD'],
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
    fi
else
    echo "Skipping migrations and collectstatic for non-web service"
fi

echo "Starting application..."
# Exécuter la commande passée au conteneur
exec "$@"
