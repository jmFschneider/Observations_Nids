# Dockerfile pour l'application Django Observations Nids
# Base image avec Python 3.12
FROM python:3.12-slim-bookworm

# Métadonnées
LABEL maintainer="observations_nids"
LABEL description="Application Django pour gestion d'observations de nids d'oiseaux"

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    # Dépendances pour mysqlclient
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    # Dépendances pour Pillow
    libjpeg-dev \
    zlib1g-dev \
    # Outils utiles
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour plus de sécurité
RUN groupadd -r django && useradd -r -g django django

# Créer les répertoires nécessaires
RUN mkdir -p /app /app/staticfiles /app/mediafiles /app/logs

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements-prod.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements-prod.txt

# Copier le code de l'application
COPY --chown=django:django . .

# Copier le script d'entrée (depuis le contexte de build à la racine)
COPY docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Collecter les fichiers statiques (sera refait au démarrage si nécessaire)
RUN python manage.py collectstatic --noinput || true

# Changer les permissions
RUN chown -R django:django /app

# Basculer vers l'utilisateur non-root
USER django

# Exposer le port
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["docker-entrypoint.sh"]

# Commande par défaut (peut être overridée dans docker-compose)
CMD ["gunicorn", "observations_nids.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
