# Guide d'Installation - Environnement de Production

Ce document décrit la procédure complète pour déployer le projet "Observations Nids" sur un serveur de production Linux (Raspberry Pi ou serveur Debian/Ubuntu).

---

## 📋 Table des matières

1. [Prérequis](#1-prérequis)
2. [Installation système](#2-installation-système)
3. [Configuration Redis](#3-configuration-redis)
4. [Configuration Celery](#4-configuration-celery)
5. [Déploiement Django avec Gunicorn](#5-déploiement-django-avec-gunicorn)
6. [Configuration Apache/Nginx](#6-configuration-apachenginx)
7. [Sécurisation](#7-sécurisation)
8. [Monitoring et maintenance](#8-monitoring-et-maintenance)
9. [Dépannage](#9-dépannage)

---

## 1. Prérequis

### Matériel et système

- **Serveur** : Raspberry Pi 4 (4GB RAM min) ou serveur Linux Debian/Ubuntu
- **OS** : Raspberry Pi OS (Debian-based) ou Ubuntu Server 22.04+
- **Accès** : SSH avec privilèges sudo
- **Stockage** : 32GB minimum (recommandé : 64GB+)

### Logiciels requis

- Python 3.11 ou supérieur (recommandé : 3.12)
- Git
- Redis
- MariaDB ou MySQL
- Apache2 ou Nginx
- mod_wsgi (Apache) ou Gunicorn (Nginx)

---

## 2. Installation système

### 2.1. Mise à jour du système

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

### 2.2. Installation des dépendances système

```bash
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    redis-server \
    mariadb-server \
    apache2 \
    libapache2-mod-wsgi-py3 \
    build-essential \
    libmariadb-dev \
    pkg-config
```

**Note** : Pour Nginx au lieu d'Apache, installez `nginx` et `gunicorn`.

### 2.3. Sécurisation du serveur MariaDB

```bash
sudo mysql_secure_installation
```

Répondez aux questions :
- Set root password? **Yes**
- Remove anonymous users? **Yes**
- Disallow root login remotely? **Yes**
- Remove test database? **Yes**
- Reload privilege tables? **Yes**

### 2.4. Création de la base de données

```bash
sudo mysql -u root -p
```

Dans le prompt MySQL :

```sql
CREATE DATABASE observations_nids CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'obs_user'@'localhost' IDENTIFIED BY 'VOTRE_MOT_DE_PASSE_FORT';
GRANT ALL PRIVILEGES ON observations_nids.* TO 'obs_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2.5. Clonage du projet

```bash
# Créer le répertoire de déploiement
sudo mkdir -p /var/www/observations_nids
sudo chown $USER:$USER /var/www/observations_nids

# Cloner le projet
cd /var/www
git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids
cd observations_nids
```

### 2.6. Création de l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### 2.7. Configuration du fichier .env

```bash
cp .env.example .env
nano .env
```

Configuration minimale :

```env
# Django
SECRET_KEY=GÉNÉRER_UNE_CLÉ_ALÉATOIRE_ICI
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# Base de données
DB_ENGINE=django.db.backends.mysql
DB_NAME=observations_nids
DB_USER=obs_user
DB_PASSWORD=VOTRE_MOT_DE_PASSE_FORT
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Celery
CELERY__BROKER_URL=redis://127.0.0.1:6379/0
CELERY__RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email (configurer selon votre SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
ADMIN_EMAIL=admin@votre-domaine.com

# Sécurité
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**Générer une SECRET_KEY** :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2.8. Préparation de Django

```bash
# Migrations
python manage.py migrate

# Créer un super-utilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Créer les dossiers nécessaires
mkdir -p logs media
```

### 2.9. Permissions

```bash
sudo chown -R www-data:www-data /var/www/observations_nids
sudo chmod 600 /var/www/observations_nids/.env
```

---

## 3. Configuration Redis

### 3.1. Installation

Redis devrait déjà être installé (étape 2.2). Vérification :

```bash
redis-server --version
sudo systemctl status redis-server
```

### 3.2. Configuration sécurisée

Éditez le fichier de configuration :

```bash
sudo nano /etc/redis/redis.conf
```

**Modifications critiques pour la sécurité** :

```conf
# 1. Limitation réseau (CRITIQUE)
bind 127.0.0.1 ::1
protected-mode yes

# 2. Mot de passe (CRITIQUE)
requirepass VOTRE_MOT_DE_PASSE_REDIS_FORT

# 3. Limites mémoire (important pour Raspberry Pi)
maxmemory 256mb
maxmemory-policy allkeys-lru

# 4. Persistance
save 900 1
save 300 10
save 60 10000
dir /var/lib/redis
dbfilename dump.rdb
rdbcompression yes

# 5. Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# 6. Désactivation commandes dangereuses (optionnel)
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

**Générer un mot de passe Redis fort** :

```bash
openssl rand -base64 48
```

### 3.3. Mise à jour du .env avec le mot de passe Redis

```bash
nano /var/www/observations_nids/.env
```

Modifiez :

```env
CELERY__BROKER_URL=redis://:VOTRE_MOT_DE_PASSE_REDIS@127.0.0.1:6379/0
CELERY__RESULT_BACKEND=redis://:VOTRE_MOT_DE_PASSE_REDIS@127.0.0.1:6379/0
```

### 3.4. Redémarrage et vérification

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server

# Test de connexion
redis-cli -a "VOTRE_MOT_DE_PASSE_REDIS" PING
# Devrait retourner : PONG
```

### 3.5. Vérification de la sécurité

```bash
# Vérifier que Redis écoute UNIQUEMENT sur localhost
sudo ss -tlnp | grep redis
# Devrait afficher : 127.0.0.1:6379 (et NON 0.0.0.0:6379)
```

---

## 4. Configuration Celery

### 4.1. Création des répertoires

```bash
sudo mkdir -p /var/run/celery /var/www/observations_nids/logs
sudo chown www-data:www-data /var/run/celery
sudo chown www-data:www-data /var/www/observations_nids/logs
```

### 4.2. Service Celery Worker

Créez le fichier de service :

```bash
sudo nano /etc/systemd/system/celery-worker.service
```

Contenu :

```ini
[Unit]
Description=Celery Worker pour Observations Nids
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids
EnvironmentFile=/var/www/observations_nids/.env

ExecStart=/var/www/observations_nids/venv/bin/celery -A observations_nids worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=100 \
    --logfile=/var/www/observations_nids/logs/celery-worker.log \
    --pidfile=/var/run/celery/worker.pid \
    --detach

ExecStop=/bin/kill -s TERM $MAINPID
ExecReload=/bin/kill -s HUP $MAINPID

Restart=always
RestartSec=10s

# Sécurité
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### 4.3. Service Celery Beat (optionnel - tâches planifiées)

```bash
sudo nano /etc/systemd/system/celery-beat.service
```

Contenu :

```ini
[Unit]
Description=Celery Beat Scheduler pour Observations Nids
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids
EnvironmentFile=/var/www/observations_nids/.env

ExecStart=/var/www/observations_nids/venv/bin/celery -A observations_nids beat \
    --loglevel=info \
    --logfile=/var/www/observations_nids/logs/celery-beat.log \
    --pidfile=/var/run/celery/beat.pid

Restart=always
RestartSec=10s

PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### 4.4. Activation des services

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl status celery-worker

# Si vous avez créé Beat
sudo systemctl enable celery-beat
sudo systemctl start celery-beat
```

### 4.5. Commandes de gestion Celery

```bash
# Redémarrer après un déploiement
sudo systemctl restart celery-worker

# Voir les logs en temps réel
sudo journalctl -u celery-worker -f

# Voir le statut
sudo systemctl status celery-worker

# Inspecter les workers
cd /var/www/observations_nids
source venv/bin/activate
celery -A observations_nids inspect active
```

---

## 5. Déploiement Django avec Gunicorn

### 5.1. Installation Gunicorn

```bash
cd /var/www/observations_nids
source venv/bin/activate
pip install gunicorn
```

### 5.2. Service Gunicorn

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Contenu :

```ini
[Unit]
Description=Gunicorn daemon for Observations Nids
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids
EnvironmentFile=/var/www/observations_nids/.env

ExecStart=/var/www/observations_nids/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/observations_nids/gunicorn.sock \
    --timeout 120 \
    --log-level info \
    --access-logfile /var/www/observations_nids/logs/gunicorn-access.log \
    --error-logfile /var/www/observations_nids/logs/gunicorn-error.log \
    observations_nids.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

### 5.3. Activation Gunicorn

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

---

## 6. Configuration Apache/Nginx

### Option A : Apache avec mod_wsgi

#### 6.1. Activation des modules

```bash
sudo a2enmod wsgi
sudo a2enmod rewrite
sudo a2enmod ssl
sudo a2enmod headers
```

#### 6.2. Configuration VirtualHost

```bash
sudo nano /etc/apache2/sites-available/observations_nids.conf
```

Contenu :

```apache
<VirtualHost *:80>
    ServerName votre-domaine.com
    ServerAlias www.votre-domaine.com

    # Redirection HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName votre-domaine.com
    ServerAlias www.votre-domaine.com

    # SSL (à configurer avec Let's Encrypt)
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/votre-domaine.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/votre-domaine.com/privkey.pem

    # Chemins
    DocumentRoot /var/www/observations_nids

    # WSGI
    WSGIDaemonProcess observations_nids python-home=/var/www/observations_nids/venv python-path=/var/www/observations_nids
    WSGIProcessGroup observations_nids
    WSGIScriptAlias / /var/www/observations_nids/observations_nids/wsgi.py

    <Directory /var/www/observations_nids/observations_nids>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    # Fichiers statiques
    Alias /static /var/www/observations_nids/static
    <Directory /var/www/observations_nids/static>
        Require all granted
    </Directory>

    # Fichiers média
    Alias /media /var/www/observations_nids/media
    <Directory /var/www/observations_nids/media>
        Require all granted
    </Directory>

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/observations_nids_error.log
    CustomLog ${APACHE_LOG_DIR}/observations_nids_access.log combined
</VirtualHost>
```

#### 6.3. Activation et redémarrage

```bash
sudo a2ensite observations_nids
sudo a2dissite 000-default
sudo systemctl restart apache2
```

### Option B : Nginx avec Gunicorn

#### 6.1. Configuration Nginx

```bash
sudo nano /etc/nginx/sites-available/observations_nids
```

Contenu :

```nginx
upstream django {
    server unix:/var/www/observations_nids/gunicorn.sock;
}

server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;

    # Sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    # Logs
    access_log /var/log/nginx/observations_nids_access.log;
    error_log /var/log/nginx/observations_nids_error.log;

    # Fichiers statiques
    location /static/ {
        alias /var/www/observations_nids/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers média
    location /media/ {
        alias /var/www/observations_nids/media/;
    }

    # Application Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Limite taille upload
    client_max_body_size 100M;
}
```

#### 6.2. Activation

```bash
sudo ln -s /etc/nginx/sites-available/observations_nids /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. Sécurisation

### 7.1. Firewall (UFW)

```bash
# Activer UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Vérifier
sudo ufw status
```

**IMPORTANT** : Ne PAS ouvrir le port 6379 (Redis) !

### 7.2. SSL avec Let's Encrypt

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-apache  # Pour Apache
# OU
sudo apt install certbot python3-certbot-nginx   # Pour Nginx

# Obtenir un certificat
sudo certbot --apache -d votre-domaine.com -d www.votre-domaine.com
# OU
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique (test)
sudo certbot renew --dry-run
```

### 7.3. Fail2ban

```bash
sudo apt install fail2ban

# Configuration pour SSH
sudo nano /etc/fail2ban/jail.local
```

Contenu :

```ini
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

Redémarrer :

```bash
sudo systemctl restart fail2ban
```

### 7.4. Checklist de sécurité

- [ ] Redis écoute sur 127.0.0.1 uniquement
- [ ] Mot de passe Redis fort configuré
- [ ] Fichier `.env` avec permissions 600
- [ ] Firewall UFW activé
- [ ] SSL/HTTPS configuré avec Let's Encrypt
- [ ] DEBUG=False dans .env
- [ ] ALLOWED_HOSTS configuré
- [ ] SECRET_KEY unique et aléatoire
- [ ] Fail2ban activé
- [ ] Sauvegardes automatiques configurées

---

## 8. Monitoring et maintenance

### 8.1. Interface Flower pour Celery

```bash
sudo nano /etc/systemd/system/celery-flower.service
```

Contenu :

```ini
[Unit]
Description=Flower - Celery Monitoring
After=network.target redis-server.service celery-worker.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids
EnvironmentFile=/var/www/observations_nids/.env

ExecStart=/var/www/observations_nids/venv/bin/celery -A observations_nids flower \
    --port=5555 \
    --address=127.0.0.1 \
    --basic_auth=admin:MOT_DE_PASSE_FLOWER

Restart=always

[Install]
WantedBy=multi-user.target
```

Activation :

```bash
sudo systemctl enable celery-flower
sudo systemctl start celery-flower
```

Accès : `https://votre-domaine.com/flower/` (via reverse proxy)

### 8.2. Rotation des logs

```bash
sudo nano /etc/logrotate.d/observations_nids
```

Contenu :

```
/var/www/observations_nids/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload celery-worker gunicorn > /dev/null 2>&1 || true
    endscript
}
```

### 8.3. Sauvegardes automatiques

Créez un script de sauvegarde :

```bash
sudo nano /usr/local/bin/backup-observations.sh
```

Contenu :

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/observations_nids"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Sauvegarde base de données
mysqldump -u obs_user -p'VOTRE_MDP' observations_nids | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Sauvegarde Redis
redis-cli -a "VOTRE_MDP_REDIS" BGSAVE
sleep 5
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Sauvegarde fichiers média
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /var/www/observations_nids/media/

# Conservation 7 jours
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete

echo "Sauvegarde terminée : $DATE"
```

Permissions et planification :

```bash
sudo chmod +x /usr/local/bin/backup-observations.sh
sudo crontab -e
```

Ajoutez :

```cron
# Sauvegarde quotidienne à 2h du matin
0 2 * * * /usr/local/bin/backup-observations.sh >> /var/log/backup-observations.log 2>&1
```

---

## 9. Dépannage

### 9.1. Vérifications essentielles

```bash
# Services actifs
sudo systemctl status redis-server
sudo systemctl status celery-worker
sudo systemctl status gunicorn
sudo systemctl status apache2  # ou nginx

# Logs
sudo journalctl -u celery-worker -n 50
sudo journalctl -u gunicorn -n 50
tail -f /var/www/observations_nids/logs/celery-worker.log
tail -f /var/log/apache2/observations_nids_error.log
```

### 9.2. Problèmes courants

| Problème | Cause | Solution |
|----------|-------|----------|
| 502 Bad Gateway | Gunicorn non démarré | `sudo systemctl start gunicorn` |
| Tâches Celery non exécutées | Worker arrêté | `sudo systemctl start celery-worker` |
| Erreur Redis connexion | Redis arrêté ou mauvais MDP | Vérifier Redis : `systemctl status redis-server` |
| Static files 404 | Collectstatic non fait | `python manage.py collectstatic` |
| Permission denied | Mauvaises permissions | `sudo chown -R www-data:www-data /var/www/observations_nids` |

### 9.3. Redéploiement après mise à jour

```bash
cd /var/www/observations_nids
git pull origin main
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart celery-worker gunicorn
```

---

## 📚 Ressources supplémentaires

- [Guide de développement](./development.md)
- [Architecture du projet](../architecture/index.md)
- [Sécurité Raspberry Pi](../deployment/DEPLOIEMENT_PI.md)
- [Guide Git](../learning/git/README.md)

---

**Document mis à jour le** : 24/10/2025
**Version** : 2.0 (consolidé avec redis-celery-production.md)
