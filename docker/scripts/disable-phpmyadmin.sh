#!/bin/bash
# =============================================================================
# disable-phpmyadmin.sh - Désactive l'accès phpMyAdmin
# =============================================================================
set -e

COMPOSE_FILE="/opt/observations_nids/docker/docker-compose.prod.yml"

echo "Arrêt du container phpMyAdmin..."
docker compose -f "$COMPOSE_FILE" stop phpmyadmin
docker compose -f "$COMPOSE_FILE" rm -f phpmyadmin

echo ""
echo "=== phpMyAdmin désactivé ==="
echo "L'URL /phpmyadmin/ retourne désormais 502 (container arrêté)."
