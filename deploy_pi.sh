#!/bin/bash

################################################################################
# Script de déploiement pour Raspberry Pi
# Observations Nids - Version Production
################################################################################

set -e  # Arrêt en cas d'erreur

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Déploiement Observations Nids${NC}"
echo -e "${GREEN}================================${NC}\n"

# Variables de configuration
PROJECT_DIR="/var/www/html/Observations_Nids"
VENV_DIR="$PROJECT_DIR/.venv"
BACKUP_DIR="$PROJECT_DIR/backups"
APACHE_BACKUP="$BACKUP_DIR/apache_config_$(date +%Y%m%d_%H%M%S)"

# Créer le dossier de backup s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# 1. Sauvegarder les fichiers Apache spécifiques
echo -e "${YELLOW}[1/10]${NC} Sauvegarde des configurations Apache..."
mkdir -p "$APACHE_BACKUP"

# Sauvegarder les fichiers de configuration Apache
if [ -f "$PROJECT_DIR/observations_nids.wsgi" ]; then
    cp "$PROJECT_DIR/observations_nids.wsgi" "$APACHE_BACKUP/"
fi
if [ -f "/etc/apache2/sites-available/observations_nids.conf" ]; then
    sudo cp "/etc/apache2/sites-available/observations_nids.conf" "$APACHE_BACKUP/"
fi

# Sauvegarder le fichier .env s'il existe
if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$APACHE_BACKUP/"
fi

echo -e "${GREEN}✓${NC} Fichiers Apache sauvegardés dans $APACHE_BACKUP\n"

# 2. Arrêter Apache
echo -e "${YELLOW}[2/10]${NC} Arrêt du serveur Apache..."
sudo systemctl stop apache2
echo -e "${GREEN}✓${NC} Apache arrêté\n"

# 3. Pull des changements depuis Git
echo -e "${YELLOW}[3/10]${NC} Récupération de la version production depuis Git..."
cd "$PROJECT_DIR"

# Stash les changements locaux si nécessaire
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}!${NC} Changements locaux détectés, sauvegarde temporaire..."
    git stash
fi

git fetch origin
git checkout production
git pull origin production

echo -e "${GREEN}✓${NC} Code mis à jour\n"

# 4. Restaurer les fichiers Apache
echo -e "${YELLOW}[4/10]${NC} Restauration des configurations Apache..."
if [ -f "$APACHE_BACKUP/observations_nids.wsgi" ]; then
    cp "$APACHE_BACKUP/observations_nids.wsgi" "$PROJECT_DIR/"
fi
if [ -f "$APACHE_BACKUP/.env" ]; then
    cp "$APACHE_BACKUP/.env" "$PROJECT_DIR/"
fi
echo -e "${GREEN}✓${NC} Configurations restaurées\n"

# 5. Activer l'environnement virtuel
echo -e "${YELLOW}[5/10]${NC} Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓${NC} Environnement virtuel activé\n"

# 6. Installer/Mettre à jour les dépendances
echo -e "${YELLOW}[6/10]${NC} Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements-prod.txt
echo -e "${GREEN}✓${NC} Dépendances installées\n"

# 7. Supprimer l'ancienne base de données
echo -e "${YELLOW}[7/10]${NC} Suppression de l'ancienne base de données..."
if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    mv "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_old_$(date +%Y%m%d_%H%M%S).sqlite3"
    echo -e "${GREEN}✓${NC} Ancienne base sauvegardée\n"
else
    echo -e "${YELLOW}!${NC} Aucune base de données trouvée\n"
fi

# 8. Créer la nouvelle base de données
echo -e "${YELLOW}[8/10]${NC} Création de la nouvelle base de données..."
python manage.py migrate
echo -e "${GREEN}✓${NC} Base de données créée\n"

# 9. Collecter les fichiers statiques
echo -e "${YELLOW}[9/10]${NC} Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✓${NC} Fichiers statiques collectés\n"

# 10. Redémarrer Apache
echo -e "${YELLOW}[10/10]${NC} Redémarrage du serveur Apache..."
sudo systemctl start apache2

# Vérifier que Apache a bien démarré
if sudo systemctl is-active --quiet apache2; then
    echo -e "${GREEN}✓${NC} Apache redémarré avec succès\n"
else
    echo -e "${RED}✗${NC} Erreur : Apache n'a pas pu démarrer\n"
    echo -e "${YELLOW}!${NC} Consultez les logs : sudo journalctl -xeu apache2.service\n"
    exit 1
fi

# Résumé
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Déploiement terminé !${NC}"
echo -e "${GREEN}================================${NC}\n"

echo -e "Prochaines étapes :\n"
echo -e "1. Créer un superutilisateur :"
echo -e "   ${YELLOW}cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser${NC}\n"
echo -e "2. Vérifier le site : ${YELLOW}http://$(hostname -I | awk '{print $1}')${NC}\n"
echo -e "3. Restaurer les données si nécessaire :"
echo -e "   ${YELLOW}python manage.py loaddata backup_YYYYMMDD.json${NC}\n"

echo -e "\nFichiers de configuration Apache sauvegardés dans :"
echo -e "${YELLOW}$APACHE_BACKUP${NC}\n"
