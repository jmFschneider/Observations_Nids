#!/bin/bash
# Script de déploiement automatique des services Celery
# À exécuter sur le Raspberry Pi avec sudo

set -e

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR="/var/www/html/Observations_Nids"
SCRIPT_DIR="$APP_DIR/deployment"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Déploiement des services Celery${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Vérifier que le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté avec sudo${NC}"
    exit 1
fi

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}Erreur: Le répertoire $APP_DIR n'existe pas${NC}"
    exit 1
fi

# 1. Arrêter les services existants
echo -e "${YELLOW}1. Arrêt des services existants...${NC}"
systemctl stop celery-worker 2>/dev/null || true
# systemctl stop celery-beat 2>/dev/null || true
echo -e "${GREEN}✓ Services arrêtés${NC}"
echo ""

# 2. Configurer les permissions
echo -e "${YELLOW}2. Configuration des permissions...${NC}"
if [ -f "$SCRIPT_DIR/setup_celery_permissions.sh" ]; then
    chmod +x "$SCRIPT_DIR/setup_celery_permissions.sh"
    "$SCRIPT_DIR/setup_celery_permissions.sh"
else
    echo -e "${RED}✗ Script de permissions non trouvé${NC}"
    exit 1
fi
echo ""

# 3. Installer les fichiers service
echo -e "${YELLOW}3. Installation des fichiers service...${NC}"
if [ -f "$SCRIPT_DIR/celery-worker.service" ]; then
    cp "$SCRIPT_DIR/celery-worker.service" /etc/systemd/system/
    echo -e "${GREEN}✓ celery-worker.service copié${NC}"
else
    echo -e "${RED}✗ celery-worker.service non trouvé${NC}"
    exit 1
fi

# if [ -f "$SCRIPT_DIR/celery-beat.service" ]; then
    # cp "$SCRIPT_DIR/celery-beat.service" /etc/systemd/system/
    # echo -e "${GREEN}✓ celery-beat.service copié${NC}"
# else
    # echo -e "${RED}✗ celery-beat.service non trouvé${NC}"
    # exit 1
# fi
# echo ""

# 4. Recharger systemd
echo -e "${YELLOW}4. Rechargement de systemd...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ systemd rechargé${NC}"
echo ""

# 5. Activer les services
echo -e "${YELLOW}5. Activation des services au démarrage...${NC}"
systemctl enable celery-worker
# systemctl enable celery-beat
echo -e "${GREEN}✓ Services activés${NC}"
echo ""

# 6. Démarrer les services
echo -e "${YELLOW}6. Démarrage des services...${NC}"
systemctl start celery-worker
sleep 2
# systemctl start celery-beat
sleep 2
echo -e "${GREEN}✓ Services démarrés${NC}"
echo ""

# 7. Vérifier le statut
echo -e "${YELLOW}7. Vérification du statut des services...${NC}"
echo ""
echo -e "${BLUE}--- Celery Worker ---${NC}"
if systemctl is-active --quiet celery-worker; then
    echo -e "${GREEN}✓ celery-worker est actif${NC}"
    systemctl status celery-worker --no-pager -l | head -n 10
else
    echo -e "${RED}✗ celery-worker n'est pas actif${NC}"
    echo -e "${YELLOW}Logs:${NC}"
    journalctl -u celery-worker -n 20 --no-pager
fi
echo ""

# echo -e "${BLUE}--- Celery Beat ---${NC}"
# if systemctl is-active --quiet celery-beat; then
    # echo -e "${GREEN}✓ celery-beat est actif${NC}"
    # systemctl status celery-beat --no-pager -l | head -n 10
# else
    # echo -e "${RED}✗ celery-beat n'est pas actif${NC}"
    # echo -e "${YELLOW}Logs:${NC}"
    # journalctl -u celery-beat -n 20 --no-pager
# fi
# echo ""

# 8. Résumé
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Déploiement terminé${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Commandes utiles :"
echo "  - Voir les logs worker : sudo journalctl -u celery-worker -f"
echo "  - Voir les logs beat : sudo journalctl -u celery-beat -f"
echo "  - Redémarrer worker : sudo systemctl restart celery-worker"
echo "  - Redémarrer beat : sudo systemctl restart celery-beat"
echo "  - Voir le statut : sudo systemctl status celery-worker celery-beat"
echo ""

# Vérifier si les deux services sont actifs
if systemctl is-active --quiet celery-worker  then # && systemctl is-active --quiet celery-beat;
    echo -e "${GREEN}✓ Tous les services sont opérationnels !${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Certains services ne sont pas actifs. Vérifiez les logs ci-dessus.${NC}"
    exit 1
fi
