#!/bin/bash
# =============================================================================
# enable-phpmyadmin.sh - Active l'accès phpMyAdmin
# =============================================================================
set -e

COMPOSE_FILE="/opt/observations_nids/docker/docker-compose.prod.yml"
HTPASSWD_FILE="/opt/observations_nids/docker/nginx/auth/.htpasswd"

# Vérifier que le fichier htpasswd existe
if [ ! -f "$HTPASSWD_FILE" ]; then
    echo "ERREUR : Fichier htpasswd introuvable : $HTPASSWD_FILE"
    echo "Créez-le d'abord avec :"
    echo "  bash docker/scripts/setup-phpmyadmin-auth.sh"
    exit 1
fi

echo "Démarrage du container phpMyAdmin..."
docker compose -f "$COMPOSE_FILE" --profile admin up -d phpmyadmin

echo ""
echo "=== phpMyAdmin activé ==="
echo "URL  : https://observation-nids.meteo-poelley50.fr/phpmyadmin/"
echo "Login: voir docker/nginx/auth/.htpasswd"
echo ""
echo "N'oubliez pas de désactiver après utilisation :"
echo "  bash docker/scripts/disable-phpmyadmin.sh"
