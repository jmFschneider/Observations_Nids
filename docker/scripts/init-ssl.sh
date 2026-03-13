#!/bin/bash
# =============================================================================
# init-ssl.sh - Obtention du certificat Let's Encrypt (premier démarrage)
# =============================================================================
# À exécuter UNE SEULE FOIS avant de lancer docker-compose.prod.yml
# Prérequis :
#   - Le domaine pointe déjà vers l'IP de ce serveur (DNS propagé)
#   - Le port 80 est libre (Nginx pas encore démarré)
#   - certbot installé sur le serveur (sudo apt install certbot -y)
# =============================================================================
#
# NOTE : On utilise certbot installé sur l'hôte (pas via Docker).
# Les conteneurs Docker peuvent avoir des problèmes de connectivité IPv6 sortante
# qui empêchent d'atteindre les serveurs Let's Encrypt.
# =============================================================================

set -e

DOMAIN="observation-nids.meteo-poelley50.fr"
EMAIL="admin@meteo-poelley50.fr"  # ← Modifier avec l'email de l'admin

echo "=== Obtention du certificat Let's Encrypt pour $DOMAIN ==="
echo ""
echo "Vérifications préalables :"
echo "  - Le domaine $DOMAIN doit pointer vers $(curl -4 -s ifconfig.me)"
echo "  - Le port 80 doit être libre (Nginx pas encore démarré)"
echo ""

# Vérifier que certbot est installé
if ! command -v certbot &> /dev/null; then
    echo "certbot non trouvé. Installation..."
    sudo apt install certbot -y
fi

read -p "Continuer ? (o/N) " confirm
if [[ "$confirm" != "o" && "$confirm" != "O" ]]; then
    echo "Annulé."
    exit 0
fi

# Obtention du certificat via certbot standalone
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

echo ""
echo "=== Certificat obtenu avec succès ! ==="
echo "Fichiers dans : /etc/letsencrypt/live/$DOMAIN/"
echo ""
echo "Prochaine étape : démarrer le stack de production :"
echo "  cd /opt/observations_nids"
echo "  docker compose -f docker/docker-compose.prod.yml up -d"
echo ""
echo "Penser à configurer le renouvellement automatique (cron) :"
echo "  0 3 * * 1 certbot renew --quiet && docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml exec nginx nginx -s reload"
