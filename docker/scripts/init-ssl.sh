#!/bin/bash
# =============================================================================
# init-ssl.sh - Obtention du certificat Let's Encrypt (premier démarrage)
# =============================================================================
# À exécuter UNE SEULE FOIS avant de lancer docker-compose.prod.yml
# Prérequis :
#   - Le domaine pointe déjà vers l'IP de ce serveur (DNS propagé)
#   - Les ports 80 et 443 sont libres (Nginx pas encore démarré)
#   - Docker est installé
# =============================================================================

set -e

DOMAIN="observation-nids.meteo-poelley50.fr"
EMAIL="admin@meteo-poelley50.fr"  # ← Modifier avec l'email de l'admin

echo "=== Obtention du certificat Let's Encrypt pour $DOMAIN ==="
echo ""
echo "Vérifications préalables :"
echo "  - Le domaine $DOMAIN doit pointer vers $(curl -s ifconfig.me)"
echo "  - Les ports 80 et 443 doivent être libres"
echo ""
read -p "Continuer ? (o/N) " confirm
if [[ "$confirm" != "o" && "$confirm" != "O" ]]; then
    echo "Annulé."
    exit 0
fi

# Obtention du certificat via certbot standalone
# (Nginx n'est pas encore démarré, certbot utilise son propre serveur HTTP)
docker run --rm \
    -p 80:80 \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    certbot/certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

echo ""
echo "=== Certificat obtenu avec succès ! ==="
echo ""
echo "Prochaine étape : démarrer le stack de production :"
echo "  cd /opt/observations_nids"
echo "  docker compose -f docker/docker-compose.prod.yml up -d"
echo ""
echo "Pour renouveler le certificat (à planifier en cron) :"
echo "  bash docker/scripts/renew-ssl.sh"
