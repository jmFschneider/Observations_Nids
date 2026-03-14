#!/bin/bash
# =============================================================================
# enable-phpmyadmin.sh - Active l'accès phpMyAdmin
# =============================================================================
set -e

COMPOSE_FILE="/opt/observations_nids/docker/docker-compose.prod.yml"
ENV_FILE="/opt/observations_nids/.env.prod"
HTPASSWD_FILE="/opt/observations_nids/docker/nginx/auth/.htpasswd"

# Vérifier que le fichier htpasswd existe
if [ ! -f "$HTPASSWD_FILE" ]; then
    echo "ERREUR : Fichier htpasswd introuvable : $HTPASSWD_FILE"
    echo "Créez-le d'abord avec :"
    echo "  bash docker/scripts/setup-phpmyadmin-auth.sh"
    exit 1
fi

DELAI_MINUTES=30

echo "Démarrage du container phpMyAdmin..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile admin up -d phpmyadmin

# Planifier l'arrêt automatique via la commande 'at'
if command -v at &> /dev/null; then
    # Annuler un éventuel job précédent
    atq | awk '{print $1}' | while read job_id; do
        at -c "$job_id" 2>/dev/null | grep -q "disable-phpmyadmin" && atrm "$job_id"
    done
    # Planifier le nouvel arrêt
    echo "bash $COMPOSE_FILE/../scripts/disable-phpmyadmin.sh >> /tmp/phpmyadmin-autostop.log 2>&1" \
        | at now + ${DELAI_MINUTES} minutes 2>/dev/null
    HEURE_ARRET=$(date -d "+${DELAI_MINUTES} minutes" "+%H:%M")
    AUTOSTOP_MSG="Arrêt automatique planifié à $HEURE_ARRET (dans ${DELAI_MINUTES} min)"
else
    AUTOSTOP_MSG="ATTENTION : commande 'at' non disponible — arrêt manuel requis (sudo apt install at)"
fi

echo ""
echo "=== phpMyAdmin activé ==="
echo "URL  : https://observation-nids.meteo-poelley50.fr/phpmyadmin/"
echo "Login: voir docker/nginx/auth/.htpasswd"
echo "$AUTOSTOP_MSG"
echo ""
echo "Pour désactiver manuellement (avant l'arrêt automatique) :"
echo "  bash docker/scripts/disable-phpmyadmin.sh"
