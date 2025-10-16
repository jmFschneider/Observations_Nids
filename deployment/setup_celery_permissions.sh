#!/bin/bash
# Script de configuration des permissions pour Celery
# À exécuter sur le Raspberry Pi avec sudo

set -e

echo "Configuration des permissions pour Celery..."

APP_DIR="/var/www/html/Observations_Nids"
LOGS_DIR="$APP_DIR/logs"
MEDIA_DIR="$APP_DIR/media"

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier que le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté avec sudo${NC}"
    exit 1
fi

# 1. Créer le répertoire de logs s'il n'existe pas
echo -e "${YELLOW}Création du répertoire de logs...${NC}"
mkdir -p "$LOGS_DIR"
chown -R www-data:www-data "$LOGS_DIR"
chmod 755 "$LOGS_DIR"
echo -e "${GREEN}✓ Répertoire de logs configuré${NC}"

# 2. Créer le répertoire media s'il n'existe pas
echo -e "${YELLOW}Création du répertoire media...${NC}"
mkdir -p "$MEDIA_DIR"
chown -R www-data:www-data "$MEDIA_DIR"
chmod 755 "$MEDIA_DIR"
echo -e "${GREEN}✓ Répertoire media configuré${NC}"

# 3. Vérifier et corriger les permissions du virtualenv
echo -e "${YELLOW}Vérification des permissions du virtualenv...${NC}"
if [ -d "$APP_DIR/.venv" ]; then
    # Donner les permissions d'exécution sur les binaires du virtualenv
    chmod -R 755 "$APP_DIR/.venv/bin"

    # S'assurer que www-data peut lire le virtualenv
    chown -R www-data:www-data "$APP_DIR/.venv"

    # Vérifier que celery est exécutable
    if [ -f "$APP_DIR/.venv/bin/celery" ]; then
        chmod +x "$APP_DIR/.venv/bin/celery"
        echo -e "${GREEN}✓ Celery est exécutable${NC}"
    else
        echo -e "${RED}✗ Celery n'est pas trouvé dans le virtualenv${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Le virtualenv n'existe pas à $APP_DIR/.venv${NC}"
    exit 1
fi

# 4. Vérifier les permissions du fichier .env
echo -e "${YELLOW}Vérification des permissions du fichier .env...${NC}"
if [ -f "$APP_DIR/.env" ]; then
    chown www-data:www-data "$APP_DIR/.env"
    chmod 640 "$APP_DIR/.env"
    echo -e "${GREEN}✓ Fichier .env configuré${NC}"
else
    echo -e "${YELLOW}⚠ Fichier .env non trouvé (optionnel)${NC}"
fi

# 5. Configurer les permissions sur le répertoire de l'application
echo -e "${YELLOW}Configuration des permissions du répertoire de l'application...${NC}"
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"

# Rendre les fichiers Python lisibles mais pas exécutables
find "$APP_DIR" -type f -name "*.py" -exec chmod 644 {} \;

echo -e "${GREEN}✓ Permissions du répertoire de l'application configurées${NC}"

# 6. Créer les fichiers de logs s'ils n'existent pas
echo -e "${YELLOW}Création des fichiers de logs...${NC}"
touch "$LOGS_DIR/celery-worker.log"
touch "$LOGS_DIR/celery-beat.log"
chown www-data:www-data "$LOGS_DIR/celery-worker.log"
chown www-data:www-data "$LOGS_DIR/celery-beat.log"
chmod 644 "$LOGS_DIR/celery-worker.log"
chmod 644 "$LOGS_DIR/celery-beat.log"
echo -e "${GREEN}✓ Fichiers de logs créés${NC}"

# 7. Tester l'exécution de Celery en tant que www-data
echo -e "${YELLOW}Test de l'exécution de Celery...${NC}"
if sudo -u www-data "$APP_DIR/.venv/bin/celery" --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Celery peut être exécuté par www-data${NC}"
else
    echo -e "${RED}✗ Erreur lors de l'exécution de Celery par www-data${NC}"
    echo -e "${YELLOW}Diagnostic:${NC}"
    sudo -u www-data "$APP_DIR/.venv/bin/celery" --version
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Configuration des permissions terminée !${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Prochaines étapes :"
echo "1. Copier le fichier service : sudo cp deployment/celery-worker.service /etc/systemd/system/"
echo "2. Recharger systemd : sudo systemctl daemon-reload"
echo "3. Activer le service : sudo systemctl enable celery-worker"
echo "4. Démarrer le service : sudo systemctl start celery-worker"
echo "5. Vérifier le statut : sudo systemctl status celery-worker"
