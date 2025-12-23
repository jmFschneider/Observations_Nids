#!/bin/bash
################################################################################
# Script d'installation automatisée de l'environnement PILOTE
# Observations Nids - Environnement de test/staging
#
# Usage: sudo bash deploy_pilote.sh
#
# Prérequis:
#   - Raspberry Pi avec production déjà installée
#   - Sous-domaine DNS configuré (pilote.observation-nids.votre-domaine.fr)
#   - Accès sudo
################################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PILOTE_DIR="/var/www/observations_nids_pilote"
PILOTE_DOMAIN="pilote.observation-nids.votre-domaine.fr"  # À MODIFIER
REPO_URL="https://github.com/jmFschneider/Observations_Nids.git"
DB_NAME="observations_nids_pilote"

# Fonctions utilitaires
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_header "Vérification des prérequis"

    # Vérifier les droits sudo
    if [ "$EUID" -ne 0 ]; then
        print_error "Ce script doit être exécuté avec sudo"
        exit 1
    fi
    print_success "Droits sudo OK"

    # Vérifier que la production existe
    if [ ! -d "/var/www/observations_nids" ]; then
        print_error "La production n'est pas installée dans /var/www/observations_nids"
        exit 1
    fi
    print_success "Installation production trouvée"

    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas installé"
        exit 1
    fi
    print_success "Python 3 installé"

    # Vérifier MariaDB
    if ! systemctl is-active --quiet mariadb; then
        print_error "MariaDB n'est pas actif"
        exit 1
    fi
    print_success "MariaDB actif"

    # Vérifier Redis
    if ! systemctl is-active --quiet redis-server; then
        print_error "Redis n'est pas actif"
        exit 1
    fi
    print_success "Redis actif"
}

install_nginx() {
    print_header "Installation de Nginx et Gunicorn"

    if command -v nginx &> /dev/null; then
        print_warning "Nginx déjà installé"
    else
        apt update
        apt install -y nginx gunicorn3
        print_success "Nginx et Gunicorn installés"
    fi

    # Arrêter Nginx temporairement
    systemctl stop nginx
}

clone_repository() {
    print_header "Clonage du repository"

    if [ -d "$PILOTE_DIR" ]; then
        print_warning "Le répertoire $PILOTE_DIR existe déjà"
        read -p "Supprimer et réinstaller ? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PILOTE_DIR"
        else
            print_error "Installation annulée"
            exit 1
        fi
    fi

    mkdir -p "$PILOTE_DIR"
    chown $SUDO_USER:www-data "$PILOTE_DIR"

    sudo -u $SUDO_USER git clone "$REPO_URL" "$PILOTE_DIR"
    cd "$PILOTE_DIR"
    sudo -u $SUDO_USER git checkout main

    print_success "Repository cloné"
}

create_virtualenv() {
    print_header "Création de l'environnement virtuel Python"

    cd "$PILOTE_DIR"
    sudo -u $SUDO_USER python3 -m venv .venv
    sudo -u $SUDO_USER .venv/bin/pip install --upgrade pip
    sudo -u $SUDO_USER .venv/bin/pip install -r requirements-prod.txt

    print_success "Environnement virtuel créé et dépendances installées"
}

configure_env_file() {
    print_header "Configuration du fichier .env"

    # Générer une nouvelle SECRET_KEY
    SECRET_KEY=$(sudo -u $SUDO_USER $PILOTE_DIR/.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

    # Demander les informations nécessaires
    echo -e "${YELLOW}Configuration de la base de données:${NC}"
    read -p "Utilisateur MySQL (prod): " DB_USER
    read -sp "Mot de passe MySQL: " DB_PASSWORD
    echo

    echo -e "${YELLOW}Configuration email (optionnel, Entrée pour passer):${NC}"
    read -p "Email host (ex: smtp.gmail.com): " EMAIL_HOST
    read -p "Email user: " EMAIL_USER
    read -sp "Email password: " EMAIL_PASSWORD
    echo

    echo -e "${YELLOW}Configuration Gemini API:${NC}"
    read -p "Gemini API Key (pour transcription): " GEMINI_API_KEY

    # Créer le fichier .env
    cat > "$PILOTE_DIR/.env" <<EOF
# Configuration PILOTE - Généré automatiquement
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$PILOTE_DOMAIN

# Base de données
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Redis (DB 1 pour le pilote)
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Email
EMAIL_HOST=${EMAIL_HOST:-smtp.gmail.com}
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=${EMAIL_USER}
EMAIL_HOST_PASSWORD=${EMAIL_PASSWORD}
DEFAULT_FROM_EMAIL=${EMAIL_USER}
ADMIN_EMAIL=${EMAIL_USER}

# Gemini API
GEMINI_API_KEY=$GEMINI_API_KEY

# Environnement
ENVIRONMENT=pilote
VERSION=pilote-main

# Sécurité (sera activé après config SSL)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Logging
LOG_LEVEL=INFO
EOF

    chmod 600 "$PILOTE_DIR/.env"
    chown $SUDO_USER:www-data "$PILOTE_DIR/.env"

    print_success "Fichier .env créé"
}

create_database() {
    print_header "Création de la base de données"

    # Lire les credentials depuis .env
    source "$PILOTE_DIR/.env"

    # Créer la base de données
    mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

    print_success "Base de données $DB_NAME créée"
}

run_django_setup() {
    print_header "Configuration Django"

    cd "$PILOTE_DIR"
    source .venv/bin/activate

    # Migrations
    echo "Application des migrations..."
    python manage.py migrate

    # Charger la taxonomie
    echo "Chargement de la taxonomie (liste des oiseaux)..."
    python manage.py charger_lof || print_warning "Erreur lors du chargement de la taxonomie"

    # Collecter les fichiers statiques
    echo "Collection des fichiers statiques..."
    python manage.py collectstatic --noinput

    # Créer les répertoires médias
    mkdir -p media/transcription media/images
    chown -R www-data:www-data media/

    print_success "Configuration Django terminée"
}

create_superuser() {
    print_header "Création du superutilisateur"

    cd "$PILOTE_DIR"
    source .venv/bin/activate

    echo -e "${YELLOW}Veuillez créer un compte administrateur pour le pilote:${NC}"
    python manage.py createsuperuser

    print_success "Superutilisateur créé"
}

configure_nginx() {
    print_header "Configuration Nginx"

    # Créer la configuration
    cat > /etc/nginx/sites-available/observations_nids_pilote <<'EOF'
upstream django_pilote {
    server unix:/run/gunicorn-pilote/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name PILOTE_DOMAIN_PLACEHOLDER;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location /static/ {
        alias /var/www/observations_nids_pilote/staticfiles/;
    }

    location /media/ {
        alias /var/www/observations_nids_pilote/media/;
    }

    location / {
        proxy_pass http://django_pilote;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    # Remplacer le placeholder par le vrai domaine
    sed -i "s/PILOTE_DOMAIN_PLACEHOLDER/$PILOTE_DOMAIN/g" /etc/nginx/sites-available/observations_nids_pilote

    # Activer le site
    ln -sf /etc/nginx/sites-available/observations_nids_pilote /etc/nginx/sites-enabled/

    # Tester la configuration
    nginx -t

    print_success "Configuration Nginx créée"
}

configure_gunicorn() {
    print_header "Configuration Gunicorn"

    # Créer les fichiers de log
    touch /var/log/gunicorn-pilote-error.log
    touch /var/log/gunicorn-pilote-access.log
    chown www-data:www-data /var/log/gunicorn-pilote-*.log

    # Créer le service systemd
    cat > /etc/systemd/system/gunicorn-pilote.service <<EOF
[Unit]
Description=Gunicorn daemon for Observations Nids Pilote
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
RuntimeDirectory=gunicorn-pilote
WorkingDirectory=$PILOTE_DIR
Environment="PATH=$PILOTE_DIR/.venv/bin"
EnvironmentFile=$PILOTE_DIR/.env

ExecStart=$PILOTE_DIR/.venv/bin/gunicorn --workers 3 --worker-class sync --timeout 120 --bind unix:/run/gunicorn-pilote/gunicorn.sock --error-logfile /var/log/gunicorn-pilote-error.log --access-logfile /var/log/gunicorn-pilote-access.log --log-level info observations_nids.wsgi:application

ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Ajuster les permissions
    chown -R www-data:www-data "$PILOTE_DIR/staticfiles/"
    chmod -R 755 "$PILOTE_DIR/staticfiles/"

    # Recharger et démarrer
    systemctl daemon-reload
    systemctl enable gunicorn-pilote
    systemctl start gunicorn-pilote

    print_success "Gunicorn configuré et démarré"
}

configure_celery() {
    print_header "Configuration Celery"

    # Créer le fichier de log
    touch /var/log/celery-pilote-worker.log
    chown www-data:www-data /var/log/celery-pilote-worker.log

    # Créer le service systemd
    cat > /etc/systemd/system/celery-worker-pilote.service <<EOF
[Unit]
Description=Celery Worker Pilote - Observations Nids
After=network.target redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=$PILOTE_DIR
Environment="PATH=$PILOTE_DIR/.venv/bin"
EnvironmentFile=$PILOTE_DIR/.env

ExecStart=$PILOTE_DIR/.venv/bin/celery -A observations_nids worker --loglevel=info --logfile=/var/log/celery-pilote-worker.log --pidfile=/var/run/celery-pilote-worker.pid --detach --concurrency=2

ExecStop=/bin/kill -s TERM \$MAINPID
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

    # Recharger et démarrer
    systemctl daemon-reload
    systemctl enable celery-worker-pilote
    systemctl start celery-worker-pilote

    print_success "Celery configuré et démarré"
}

start_services() {
    print_header "Démarrage des services"

    systemctl start nginx
    systemctl start gunicorn-pilote
    systemctl start celery-worker-pilote

    # Vérifier les statuts
    sleep 2

    if systemctl is-active --quiet nginx; then
        print_success "Nginx actif"
    else
        print_error "Nginx n'est pas actif"
    fi

    if systemctl is-active --quiet gunicorn-pilote; then
        print_success "Gunicorn-pilote actif"
    else
        print_error "Gunicorn-pilote n'est pas actif"
    fi

    if systemctl is-active --quiet celery-worker-pilote; then
        print_success "Celery-worker-pilote actif"
    else
        print_error "Celery-worker-pilote n'est pas actif"
    fi
}

configure_ssl() {
    print_header "Configuration SSL (Let's Encrypt)"

    echo -e "${YELLOW}Installation de Certbot...${NC}"
    apt install -y certbot python3-certbot-nginx

    echo -e "${YELLOW}Obtention du certificat SSL pour $PILOTE_DOMAIN...${NC}"
    certbot --nginx -d "$PILOTE_DOMAIN" --non-interactive --agree-tos --email admin@$PILOTE_DOMAIN || {
        print_warning "Échec de la configuration SSL automatique"
        echo "Vous pouvez le faire manuellement avec : sudo certbot --nginx -d $PILOTE_DOMAIN"
        return
    }

    # Activer HTTPS dans .env
    sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' "$PILOTE_DIR/.env"
    sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' "$PILOTE_DIR/.env"
    sed -i 's/CSRF_COOKIE_SECURE=False/CSRF_COOKIE_SECURE=True/' "$PILOTE_DIR/.env"

    # Redémarrer Gunicorn
    systemctl restart gunicorn-pilote

    print_success "SSL configuré"
}

create_update_script() {
    print_header "Création du script de mise à jour"

    cat > "$PILOTE_DIR/update_pilote.sh" <<'EOFSCRIPT'
#!/bin/bash
set -e

PILOTE_DIR="/var/www/observations_nids_pilote"
VENV_DIR="$PILOTE_DIR/.venv"

echo "=== Mise à jour de l'environnement PILOTE ==="
cd $PILOTE_DIR

echo "→ Git pull..."
git fetch origin
git pull origin main

echo "→ Activation environnement virtuel..."
source $VENV_DIR/bin/activate

echo "→ Mise à jour des dépendances..."
pip install -r requirements-prod.txt --upgrade

echo "→ Application des migrations..."
python manage.py migrate

echo "→ Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "→ Vérification Django..."
python manage.py check

echo "→ Redémarrage des services..."
sudo systemctl restart gunicorn-pilote
sudo systemctl restart celery-worker-pilote
sudo systemctl reload nginx

echo "→ Vérification des services..."
sudo systemctl is-active gunicorn-pilote
sudo systemctl is-active celery-worker-pilote

echo "=== Mise à jour terminée avec succès ! ==="
echo "URL: https://PILOTE_DOMAIN_PLACEHOLDER"
EOFSCRIPT

    # Remplacer le placeholder
    sed -i "s/PILOTE_DOMAIN_PLACEHOLDER/$PILOTE_DOMAIN/g" "$PILOTE_DIR/update_pilote.sh"

    chmod +x "$PILOTE_DIR/update_pilote.sh"
    chown $SUDO_USER:www-data "$PILOTE_DIR/update_pilote.sh"

    print_success "Script de mise à jour créé : $PILOTE_DIR/update_pilote.sh"
}

print_summary() {
    print_header "Installation terminée !"

    echo -e "${GREEN}✓ Environnement PILOTE installé avec succès${NC}\n"

    echo -e "${BLUE}Informations importantes:${NC}"
    echo -e "  URL Pilote : http://$PILOTE_DOMAIN (HTTPS après config SSL)"
    echo -e "  Admin URL  : http://$PILOTE_DOMAIN/admin/"
    echo -e "  Code       : $PILOTE_DIR"
    echo -e "  Database   : $DB_NAME"
    echo -e "  Redis DB   : 1"

    echo -e "\n${BLUE}Services:${NC}"
    echo -e "  Nginx      : sudo systemctl status nginx"
    echo -e "  Gunicorn   : sudo systemctl status gunicorn-pilote"
    echo -e "  Celery     : sudo systemctl status celery-worker-pilote"

    echo -e "\n${BLUE}Logs:${NC}"
    echo -e "  Nginx      : sudo tail -f /var/log/nginx/error.log"
    echo -e "  Gunicorn   : sudo tail -f /var/log/gunicorn-pilote-error.log"
    echo -e "  Celery     : sudo tail -f /var/log/celery-pilote-worker.log"

    echo -e "\n${BLUE}Maintenance:${NC}"
    echo -e "  Mise à jour : $PILOTE_DIR/update_pilote.sh"
    echo -e "  Redémarrer  : sudo systemctl restart gunicorn-pilote celery-worker-pilote"

    echo -e "\n${YELLOW}Prochaines étapes:${NC}"
    echo -e "  1. Vérifier l'accès : http://$PILOTE_DOMAIN"
    echo -e "  2. Configurer SSL : sudo certbot --nginx -d $PILOTE_DOMAIN"
    echo -e "  3. Tester les fonctionnalités principales"
    echo -e "  4. Inviter les utilisateurs pilotes"

    echo -e "\n${GREEN}Documentation complète:${NC}"
    echo -e "  docs/developpeurs/installation/03_environnement_pilote.md"
}

# Exécution principale
main() {
    clear
    print_header "Installation Environnement PILOTE - Observations Nids"

    echo -e "${YELLOW}Ce script va installer un environnement pilote/test complet.${NC}"
    echo -e "${YELLOW}Domaine configuré: $PILOTE_DOMAIN${NC}"
    echo
    read -p "Continuer ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Installation annulée"
        exit 1
    fi

    check_prerequisites
    install_nginx
    clone_repository
    create_virtualenv
    configure_env_file
    create_database
    run_django_setup
    create_superuser
    configure_nginx
    configure_gunicorn
    configure_celery
    start_services
    create_update_script

    # SSL (optionnel)
    echo
    read -p "Configurer SSL maintenant ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        configure_ssl
    fi

    print_summary
}

# Lancer le script
main
