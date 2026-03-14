#!/bin/bash
# =============================================================================
# disable-phpmyadmin.sh - Désactive l'accès phpMyAdmin
# =============================================================================
set -e

COMPOSE_FILE="/opt/observations_nids/docker/docker-compose.prod.yml"

# Annuler le job d'arrêt automatique s'il existe
if command -v at &> /dev/null; then
    atq | awk '{print $1}' | while read job_id; do
        at -c "$job_id" 2>/dev/null | grep -q "disable-phpmyadmin" && atrm "$job_id" && \
            echo "Job d'arrêt automatique annulé."
    done
fi

echo "Arrêt du container phpMyAdmin..."
docker compose -f "$COMPOSE_FILE" stop phpmyadmin
docker compose -f "$COMPOSE_FILE" rm -f phpmyadmin

echo ""
echo "=== phpMyAdmin désactivé ==="
echo "L'URL /phpmyadmin/ retourne désormais 502 (container arrêté)."
