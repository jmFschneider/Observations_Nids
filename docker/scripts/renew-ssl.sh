#!/bin/bash
# =============================================================================
# renew-ssl.sh - Renouvellement du certificat Let's Encrypt
# =============================================================================
# À planifier en cron (ex: tous les lundis à 3h) :
#   0 3 * * 1 /opt/observations_nids/docker/scripts/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1
# =============================================================================

set -e

COMPOSE_FILE="/opt/observations_nids/docker/docker-compose.prod.yml"
WEBROOT="/var/www/certbot"

echo "[$(date)] Renouvellement du certificat Let's Encrypt..."

# Renouvellement via webroot (Nginx doit être en cours d'exécution)
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    -v "$WEBROOT:/var/www/certbot" \
    certbot/certbot renew \
    --webroot \
    --webroot-path=/var/www/certbot \
    --quiet

# Rechargement de Nginx pour prendre en compte le nouveau certificat
docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

echo "[$(date)] Renouvellement terminé."
