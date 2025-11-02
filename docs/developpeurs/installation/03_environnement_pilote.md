# Guide de Déploiement - Environnement Pilote/Test

> **Guide complet pour déployer un environnement de test/pilote sur le même serveur que la production**
>
> Permet de tester les nouvelles fonctionnalités avec de vrais utilisateurs avant le déploiement en production.

**Dernière mise à jour** : 1er novembre 2025

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Prérequis](#prérequis)
4. [Installation étape par étape](#installation-étape-par-étape)
5. [Configuration des services](#configuration-des-services)
6. [Workflow de déploiement](#workflow-de-déploiement)
7. [Maintenance](#maintenance)
8. [Dépannage](#dépannage)

---

## Vue d'ensemble

### Objectif

Créer un **environnement de test/pilote** séparé de la production sur le même Raspberry Pi, permettant de :
- ✅ Tester les nouvelles fonctionnalités sans risque
- ✅ Valider avec des utilisateurs pilotes
- ✅ Tester Nginx comme alternative à Apache
- ✅ Déployer en continu depuis la branche `main`

### Architecture choisie : Option A (Sous-domaine)

```
📦 Raspberry Pi (même machine)
│
├── 🟢 PRODUCTION (ne pas modifier)
│   ├── URL : observations-nids.votre-domaine.fr
│   ├── Serveur : Apache + mod_wsgi
│   ├── Code : /var/www/observations_nids/
│   ├── Base : observations_nids_prod
│   ├── Redis : DB 0
│   └── Branch Git : production
│
└── 🔵 PILOTE/TEST (nouveau)
    ├── URL : pilote.observation-nids.votre-domaine.fr
    ├── Serveur : Nginx + Gunicorn
    ├── Code : /var/www/observations_nids_pilote/
    ├── Base : observations_nids_pilote
    ├── Redis : DB 1
    └── Branch Git : main
```

### Durée estimée

- **Installation initiale** : 1h30 - 2h
- **Configuration SSL** : 10 minutes
- **Tests de validation** : 30 minutes

---

## Architecture

### Séparation des environnements

| Composant | Production | Pilote/Test |
|-----------|-----------|-------------|
| **URL** | observations-nids.domaine.fr | pilote.observation-nids.domaine.fr |
| **Serveur Web** | Apache (port 80/443) | Nginx (port 80/443, virtual host) |
| **App Server** | mod_wsgi | Gunicorn |
| **Base de données** | `observations_nids_prod` | `observations_nids_pilote` |
| **Redis DB** | 0 | 1 |
| **Répertoire** | `/var/www/observations_nids/` | `/var/www/observations_nids_pilote/` |
| **Service Gunicorn** | N/A | `gunicorn-pilote.service` |
| **Service Celery** | `celery-worker.service` | `celery-worker-pilote.service` |
| **Logs** | `/var/log/apache2/` | `/var/log/nginx/observations_pilote_*.log` |
| **SSL** | Certbot Apache | Certbot Nginx |

### Isolation des données

- ✅ **Bases de données séparées** : Aucun risque de conflit
- ✅ **Fichiers séparés** : Code et médias isolés
- ✅ **Redis DB différent** : Pas de collision dans le cache
- ✅ **Services systemd différents** : Gestion indépendante
- ✅ **Logs séparés** : Facilite le débogage

---

## Prérequis

### ☑ Côté serveur (Raspberry Pi)

- ✅ Production déjà installée et fonctionnelle
- ✅ Accès SSH avec droits sudo
- ✅ Au moins **1.5 GB RAM disponible** (vérifier avec `free -h`)
- ✅ Au moins **5 GB espace disque** (vérifier avec `df -h`)
- ✅ Python 3.11+, MariaDB, Redis déjà installés

### ☑ Côté DNS

- ✅ Sous-domaine `pilote.observation-nids.votre-domaine.fr` créé
- ✅ Enregistrement A pointant vers l'IP du Raspberry Pi
- ✅ Propagation DNS effective (vérifier avec `nslookup pilote.observation-nids.votre-domaine.fr`)

### ☑ Vérifications préalables

```bash
# Vérifier que le sous-domaine résout bien
nslookup pilote.observation-nids.votre-domaine.fr

# Vérifier la mémoire disponible
free -h
# Attendu : Au moins 1.5 GB disponible

# Vérifier l'espace disque
df -h /var/www
# Attendu : Au moins 5 GB disponible

# Vérifier les services existants
sudo systemctl status apache2 mariadb redis-server
# Tous doivent être actifs
```

---

## Installation étape par étape

### Phase 1 : Installation de Nginx (10 min)

```bash
# Se connecter au Raspberry Pi
ssh utilisateur@raspberry-pi-ip

# Mettre à jour les paquets
sudo apt update

# Installer Nginx et Gunicorn
sudo apt install -y nginx gunicorn3

# Vérifier l'installation
nginx -v
gunicorn3 --version

# Nginx sera configuré plus tard, le laisser arrêté pour l'instant
sudo systemctl stop nginx
```

### Phase 2 : Création du répertoire et clonage (10 min)

```bash
# Créer le répertoire pilote
sudo mkdir -p /var/www/observations_nids_pilote
sudo chown $USER:www-data /var/www/observations_nids_pilote

# Se déplacer dans le répertoire
cd /var/www/observations_nids_pilote

# Cloner le repository
git clone https://github.com/jmFschneider/Observations_Nids.git .

# Vérifier la branche actuelle
git branch
# Devrait être sur 'main'

# Si besoin, basculer sur main
git checkout main
git pull origin main

# Vérifier les fichiers
ls -la
```

### Phase 3 : Environnement virtuel Python (10 min)

```bash
# Toujours dans /var/www/observations_nids_pilote

# Créer l'environnement virtuel
python3 -m venv .venv

# Activer l'environnement
source .venv/bin/activate

# Vérifier que le prompt change (devrait afficher (.venv))

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances (production uniquement, pas les outils de dev)
pip install -r requirements-prod.txt

# Vérifier l'installation Django
python -c "import django; print(django.get_version())"
# Devrait afficher 5.2.x
```

### Phase 4 : Configuration Django (.env) (15 min)

```bash
# Copier le fichier .env de la production comme base
sudo cp /var/www/observations_nids/.env /var/www/observations_nids_pilote/.env.example

# Créer et éditer le nouveau .env
nano /var/www/observations_nids_pilote/.env
```

**Contenu du fichier `.env` pour le pilote** :

```bash
# === CONFIGURATION PILOTE/TEST ===

# Django
SECRET_KEY=GENERER_UNE_NOUVELLE_CLE_ICI
DEBUG=False
ALLOWED_HOSTS=pilote.observation-nids.votre-domaine.fr

# Base de données (NOM DIFFERENT)
DB_NAME=observations_nids_pilote
DB_USER=votre_user_mysql
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=3306

# Redis (DB DIFFERENT - utiliser 1 au lieu de 0)
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Email (copier depuis prod ou laisser vide pour tests)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
DEFAULT_FROM_EMAIL=votre-email@gmail.com
ADMIN_EMAIL=admin@votre-domaine.fr

# Google Generative AI (copier depuis prod)
GOOGLE_API_KEY=votre_cle_api_google

# Environnement
ENVIRONMENT=pilote
VERSION=pilote-main

# Sécurité (pour HTTPS après configuration SSL)
SECURE_SSL_REDIRECT=False  # Mettre True après config SSL
SESSION_COOKIE_SECURE=False  # Mettre True après config SSL
CSRF_COOKIE_SECURE=False  # Mettre True après config SSL

# Logging
LOG_LEVEL=INFO
```

**Générer une nouvelle SECRET_KEY** :

```bash
# Dans l'environnement virtuel activé
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Copier le résultat dans SECRET_KEY du .env
```

**Sécuriser le fichier .env** :

```bash
chmod 600 /var/www/observations_nids_pilote/.env
```

### Phase 5 : Création de la base de données (10 min)

```bash
# Se connecter à MariaDB
sudo mysql -u root -p

# Dans le prompt MySQL
CREATE DATABASE observations_nids_pilote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Donner les droits à l'utilisateur existant
GRANT ALL PRIVILEGES ON observations_nids_pilote.* TO 'votre_user'@'localhost';
FLUSH PRIVILEGES;

# Vérifier la création
SHOW DATABASES;
# Devrait lister observations_nids_pilote

# Quitter MySQL
EXIT;

# Vérifier la connexion depuis Django
cd /var/www/observations_nids_pilote
source .venv/bin/activate
python manage.py check --database default
# Devrait afficher "System check identified no issues"
```

### Phase 6 : Migrations et données initiales (15 min)

```bash
# Toujours dans /var/www/observations_nids_pilote avec .venv activé

# Appliquer les migrations
python manage.py migrate

# Charger les données de référence (taxonomie)
python manage.py charger_lof
# Cela va télécharger et charger la liste des oiseaux de France

# Charger les communes françaises (optionnel mais recommandé)
python manage.py charger_communes_france

# Créer un superutilisateur pour le pilote
python manage.py createsuperuser
# Email: admin-pilote@votre-domaine.fr
# Mot de passe: [choisir un mot de passe fort]

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Vérifier que tout est OK
python manage.py check
# Devrait afficher "System check identified no issues (0 silenced)"
```

### Phase 7 : Configuration Nginx (20 min)

#### 7.1 Créer la configuration du site pilote

```bash
sudo nano /etc/nginx/sites-available/observations_nids_pilote
```

**Contenu du fichier** :

```nginx
# Configuration Nginx pour l'environnement pilote
# /etc/nginx/sites-available/observations_nids_pilote

upstream django_pilote {
    server unix:/run/gunicorn-pilote/gunicorn.sock fail_timeout=0;
}

# Redirection HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name pilote.observation-nids.votre-domaine.fr;

    # Permettre Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirection HTTPS (sera décommentée après config SSL)
    # return 301 https://$server_name$request_uri;

    # Temporaire : proxy vers Gunicorn (pour tester avant SSL)
    location / {
        proxy_pass http://django_pilote;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/observations_nids_pilote/staticfiles/;
    }

    location /media/ {
        alias /var/www/observations_nids_pilote/media/;
    }
}

# Configuration HTTPS (sera ajoutée automatiquement par Certbot)
# Ne pas remplir manuellement, Certbot s'en charge
```

#### 7.2 Activer le site

```bash
# Créer le lien symbolique
sudo ln -s /etc/nginx/sites-available/observations_nids_pilote /etc/nginx/sites-enabled/

# Vérifier la configuration
sudo nginx -t
# Devrait afficher "syntax is ok" et "test is successful"

# Démarrer Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Vérifier le statut
sudo systemctl status nginx
```

### Phase 8 : Configuration Gunicorn (20 min)

#### 8.1 Créer le service systemd

```bash
sudo nano /etc/systemd/system/gunicorn-pilote.service
```

**Contenu du fichier** :

```ini
[Unit]
Description=Gunicorn daemon for Observations Nids Pilote
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
RuntimeDirectory=gunicorn-pilote
WorkingDirectory=/var/www/observations_nids_pilote
Environment="PATH=/var/www/observations_nids_pilote/.venv/bin"
EnvironmentFile=/var/www/observations_nids_pilote/.env

ExecStart=/var/www/observations_nids_pilote/.venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --timeout 120 \
    --bind unix:/run/gunicorn-pilote/gunicorn.sock \
    --error-logfile /var/log/gunicorn-pilote-error.log \
    --access-logfile /var/log/gunicorn-pilote-access.log \
    --log-level info \
    observations_nids.wsgi:application

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**📝 Explications des choix techniques** :

- **`Type=exec`** (au lieu de `notify`) : Systemd considère le service démarré dès le lancement. Plus simple et fiable pour Gunicorn qui n'émet pas toujours le signal "ready" attendu par `Type=notify`.

- **`RuntimeDirectory=gunicorn-pilote`** : Crée automatiquement `/run/gunicorn-pilote/` au démarrage avec `www-data` comme propriétaire. `/run/` est un tmpfs (en RAM) : propre, rapide, sécurisé, et se nettoie au redémarrage.

- **Socket dans `/run/`** : Évite les conflits de permissions avec le code source dans `/var/www/` (propriétaire `schneider`) et la socket (propriétaire `www-data`). Chaque composant a son répertoire dédié.

#### 8.2 Créer les logs et ajuster les permissions

```bash
# Créer les fichiers de log
sudo touch /var/log/gunicorn-pilote-error.log
sudo touch /var/log/gunicorn-pilote-access.log
sudo chown www-data:www-data /var/log/gunicorn-pilote-*.log

# Ajuster les permissions du répertoire pilote
sudo chown -R www-data:www-data /var/www/observations_nids_pilote/media/
sudo chown -R www-data:www-data /var/www/observations_nids_pilote/staticfiles/
sudo chmod -R 755 /var/www/observations_nids_pilote/media/
sudo chmod -R 755 /var/www/observations_nids_pilote/staticfiles/
```

#### 8.3 Démarrer Gunicorn

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer Gunicorn
sudo systemctl enable gunicorn-pilote
sudo systemctl start gunicorn-pilote

# Vérifier le statut
sudo systemctl status gunicorn-pilote
# Devrait afficher "active (running)"

# Vérifier les logs
sudo tail -f /var/log/gunicorn-pilote-error.log
# Ctrl+C pour arrêter
```

#### 8.4 Vérifier la socket Gunicorn

```bash
# La socket devrait être créée par RuntimeDirectory
ls -l /run/gunicorn-pilote/gunicorn.sock
# Devrait afficher un fichier socket (type srwxrwxrwx)

# Redémarrer Nginx pour prendre en compte la socket
sudo systemctl restart nginx
```

### Phase 9 : Configuration Celery (20 min)

#### 9.1 Créer le service Celery Worker

```bash
sudo nano /etc/systemd/system/celery-worker-pilote.service
```

**Contenu** :

```ini
[Unit]
Description=Celery Worker Pilote - Observations Nids
After=network.target redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids_pilote
Environment="PATH=/var/www/observations_nids_pilote/.venv/bin"
EnvironmentFile=/var/www/observations_nids_pilote/.env

ExecStart=/var/www/observations_nids_pilote/.venv/bin/celery -A observations_nids worker \
    --loglevel=info \
    --logfile=/var/log/celery-pilote-worker.log \
    --pidfile=/var/run/celery-pilote-worker.pid \
    --detach \
    --concurrency=2

ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

#### 9.2 Créer les logs Celery

```bash
sudo touch /var/log/celery-pilote-worker.log
sudo chown www-data:www-data /var/log/celery-pilote-worker.log
```

#### 9.3 Démarrer Celery

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer Celery
sudo systemctl enable celery-worker-pilote
sudo systemctl start celery-worker-pilote

# Vérifier le statut
sudo systemctl status celery-worker-pilote

# Vérifier les logs
sudo tail -f /var/log/celery-pilote-worker.log
```

### Phase 10 : Test initial (sans SSL) (10 min)

```bash
# Tester l'accès HTTP (temporaire)
curl -I http://pilote.observation-nids.votre-domaine.fr

# Devrait retourner un code 200 ou une redirection

# Ouvrir dans un navigateur
# http://pilote.observation-nids.votre-domaine.fr
# Devrait afficher la page d'accueil (sans style si pas de SSL)
```

### Phase 11 : Configuration SSL avec Let's Encrypt (15 min)

```bash
# Installer Certbot pour Nginx
sudo apt install -y certbot python3-certbot-nginx

# Obtenir le certificat SSL
sudo certbot --nginx -d pilote.observation-nids.votre-domaine.fr

# Suivre les instructions interactives
# Email: votre-email@domaine.fr
# Accepter les CGU: Oui
# Partager email avec EFF: Optionnel
# Redirection HTTPS automatique: Oui

# Vérifier le certificat
sudo certbot certificates

# Tester le renouvellement automatique
sudo certbot renew --dry-run
```

**Certbot va automatiquement :**
- ✅ Créer les certificats SSL
- ✅ Modifier la config Nginx pour ajouter HTTPS
- ✅ Configurer la redirection HTTP → HTTPS
- ✅ Mettre en place le renouvellement automatique

#### 11.2 Activer HTTPS dans Django

```bash
nano /var/www/observations_nids_pilote/.env
```

**Modifier ces lignes** :

```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**Redémarrer Gunicorn** :

```bash
sudo systemctl restart gunicorn-pilote
```

### Phase 12 : Validation finale (15 min)

#### 12.1 Tests de connectivité

```bash
# Test HTTPS
curl -I https://pilote.observation-nids.votre-domaine.fr
# Devrait retourner 200 OK

# Test redirection HTTP → HTTPS
curl -I http://pilote.observation-nids.votre-domaine.fr
# Devrait retourner 301 et rediriger vers https://
```

#### 12.2 Tests fonctionnels

Ouvrir dans un navigateur : `https://pilote.observation-nids.votre-domaine.fr`

Vérifier :
- ✅ Page d'accueil s'affiche correctement
- ✅ CSS chargé (styles visibles)
- ✅ Connexion admin : `/admin/`
- ✅ Aucune erreur dans la console navigateur (F12)

#### 12.3 Vérifier les services

```bash
# Tous les services doivent être actifs
sudo systemctl status nginx
sudo systemctl status gunicorn-pilote
sudo systemctl status celery-worker-pilote
sudo systemctl status redis-server
sudo systemctl status mariadb

# Vérifier les logs
sudo tail -n 50 /var/log/nginx/observations_pilote_error.log
sudo tail -n 50 /var/log/gunicorn-pilote-error.log
sudo tail -n 50 /var/log/celery-pilote-worker.log
```

---

## Configuration des services

### Script de mise à jour du pilote

Créer un script pour faciliter les mises à jour :

```bash
nano /var/www/observations_nids_pilote/update_pilote.sh
```

**Contenu** :

```bash
#!/bin/bash
# Script de mise à jour de l'environnement pilote
# /var/www/observations_nids_pilote/update_pilote.sh

set -e

PILOTE_DIR="/var/www/observations_nids_pilote"
VENV_DIR="$PILOTE_DIR/.venv"

echo "=== Mise à jour de l'environnement PILOTE ==="
cd $PILOTE_DIR

# 1. Récupérer les derniers changements
echo "→ Git pull..."
git fetch origin
git pull origin main

# 2. Activer l'environnement virtuel
echo "→ Activation environnement virtuel..."
source $VENV_DIR/bin/activate

# 3. Mettre à jour les dépendances
echo "→ Mise à jour des dépendances..."
pip install -r requirements-prod.txt --upgrade

# 4. Appliquer les migrations
echo "→ Application des migrations..."
python manage.py migrate

# 5. Collecter les fichiers statiques
echo "→ Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 6. Vérifier la configuration
echo "→ Vérification Django..."
python manage.py check

# 7. Redémarrer les services
echo "→ Redémarrage des services..."
sudo systemctl restart gunicorn-pilote
sudo systemctl restart celery-worker-pilote
sudo systemctl reload nginx

# 8. Vérifier les statuts
echo "→ Vérification des services..."
sudo systemctl is-active gunicorn-pilote
sudo systemctl is-active celery-worker-pilote

echo "=== Mise à jour terminée avec succès ! ==="
echo "URL: https://pilote.observation-nids.votre-domaine.fr"
```

**Rendre exécutable** :

```bash
chmod +x /var/www/observations_nids_pilote/update_pilote.sh
```

**Utilisation** :

```bash
/var/www/observations_nids_pilote/update_pilote.sh
```

---

## Workflow de déploiement

### Flux recommandé

```
1. Développement local
   ↓ (git push vers main)

2. GitHub (branche main)
   ↓ (déploiement manuel ou automatique)

3. 🔵 Environnement PILOTE
   ├─ Tests fonctionnels
   ├─ Tests utilisateurs pilotes
   └─ Validation métier
   ↓ (si validation OK)

4. Merge main → production
   ↓ (déploiement sur production)

5. 🟢 Environnement PRODUCTION
```

### Déploiement sur le pilote

```bash
# Sur le Raspberry Pi
ssh utilisateur@raspberry-pi

# Exécuter le script de mise à jour
/var/www/observations_nids_pilote/update_pilote.sh
```

### Déploiement vers la production

**Uniquement après validation complète sur le pilote** :

```bash
# 1. Sur votre machine locale, merger main vers production
git checkout production
git pull origin production
git merge main
git push origin production

# 2. Sur le Raspberry Pi, mettre à jour la production
ssh utilisateur@raspberry-pi
cd /var/www/observations_nids
git pull origin production
# ... suivre le processus habituel de mise à jour prod
```

---

## Maintenance

### Commandes utiles

```bash
# Redémarrer tous les services pilote
sudo systemctl restart gunicorn-pilote celery-worker-pilote
sudo systemctl reload nginx

# Voir les logs en temps réel
sudo journalctl -u gunicorn-pilote -f
sudo tail -f /var/log/gunicorn-pilote-error.log
sudo tail -f /var/log/nginx/observations_pilote_error.log

# Vérifier l'état des services
sudo systemctl status gunicorn-pilote celery-worker-pilote nginx

# Mettre à jour le code
cd /var/www/observations_nids_pilote
git pull origin main
./update_pilote.sh
```

### Bannière visuelle d'identification

Pour éviter toute confusion, ajouter une bannière dans `base.html` :

```bash
nano /var/www/observations_nids_pilote/observations/templates/base.html
```

Ajouter après `<body>` :

```html
<!-- Bannière environnement PILOTE -->
{% if request.get_host == 'pilote.observation-nids.votre-domaine.fr' %}
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 12px;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            position: sticky;
            top: 0;
            z-index: 9999;">
    🧪 ENVIRONNEMENT PILOTE/TEST - Version de développement - Ne pas utiliser pour les données réelles
</div>
{% endif %}
```

**Appliquer les modifications** :

```bash
cd /var/www/observations_nids_pilote
source .venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn-pilote
```

### Monitoring des ressources

```bash
# Surveiller la mémoire et CPU
htop

# Voir la consommation par service
sudo systemd-cgtop

# Espace disque
df -h

# Taille des bases de données
sudo du -sh /var/lib/mysql/observations_nids_*
```

### Rotation des logs

Créer `/etc/logrotate.d/observations_nids_pilote` :

```bash
sudo nano /etc/logrotate.d/observations_nids_pilote
```

**Contenu** :

```
/var/log/nginx/observations_pilote*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}

/var/log/gunicorn-pilote*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl restart gunicorn-pilote > /dev/null 2>&1 || true
    endscript
}

/var/log/celery-pilote*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl restart celery-worker-pilote > /dev/null 2>&1 || true
    endscript
}
```

---

## Dépannage

### Nginx ne démarre pas

```bash
# Vérifier la configuration
sudo nginx -t

# Voir les erreurs détaillées
sudo journalctl -u nginx -n 50

# Vérifier les ports
sudo netstat -tuln | grep :80
sudo netstat -tuln | grep :443

# S'assurer qu'Apache n'écoute pas sur les mêmes ports
sudo ss -tulpn | grep :80
```

### Gunicorn ne démarre pas

```bash
# Voir les logs
sudo journalctl -u gunicorn-pilote -n 100

# Vérifier les permissions
ls -la /var/www/observations_nids_pilote/

# Tester Gunicorn manuellement
cd /var/www/observations_nids_pilote
source .venv/bin/activate
gunicorn observations_nids.wsgi:application --bind 127.0.0.1:8001
# Ctrl+C pour arrêter
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que Gunicorn tourne
sudo systemctl status gunicorn-pilote

# Vérifier que la socket existe
ls -l /run/gunicorn-pilote/gunicorn.sock

# Vérifier les logs Nginx
sudo tail -f /var/log/nginx/observations_pilote_error.log

# Redémarrer dans l'ordre
sudo systemctl restart gunicorn-pilote
sudo systemctl reload nginx
```

### Fichiers statiques non chargés (CSS manquant)

```bash
# Re-collecter les fichiers statiques
cd /var/www/observations_nids_pilote
source .venv/bin/activate
python manage.py collectstatic --noinput

# Vérifier les permissions
sudo chown -R www-data:www-data staticfiles/
sudo chmod -R 755 staticfiles/

# Vérifier la config Nginx
sudo nano /etc/nginx/sites-available/observations_nids_pilote
# Vérifier que le chemin /static/ est correct

# Redémarrer Nginx
sudo systemctl reload nginx
```

### Celery ne traite pas les tâches

```bash
# Vérifier Celery
sudo systemctl status celery-worker-pilote

# Voir les logs
sudo tail -f /var/log/celery-pilote-worker.log

# Vérifier Redis (DB 1 pour le pilote)
redis-cli
> SELECT 1
> KEYS *
> EXIT

# Redémarrer Celery
sudo systemctl restart celery-worker-pilote
```

### Base de données inaccessible

```bash
# Vérifier que la base existe
sudo mysql -u root -p
> SHOW DATABASES;
> USE observations_nids_pilote;
> SHOW TABLES;
> EXIT;

# Tester depuis Django
cd /var/www/observations_nids_pilote
source .venv/bin/activate
python manage.py dbshell
# Devrait ouvrir le prompt MySQL
```

---

## Checklist de validation finale

Avant de considérer l'environnement pilote comme opérationnel :

### ☑ Services

- [ ] Nginx actif : `sudo systemctl is-active nginx`
- [ ] Gunicorn-pilote actif : `sudo systemctl is-active gunicorn-pilote`
- [ ] Celery-pilote actif : `sudo systemctl is-active celery-worker-pilote`
- [ ] Redis actif : `sudo systemctl is-active redis-server`
- [ ] MariaDB actif : `sudo systemctl is-active mariadb`

### ☑ SSL et sécurité

- [ ] HTTPS fonctionne : `curl -I https://pilote.observation-nids.votre-domaine.fr`
- [ ] Redirection HTTP → HTTPS active
- [ ] Certificat SSL valide : `sudo certbot certificates`
- [ ] Renouvellement auto configuré : `sudo certbot renew --dry-run`

### ☑ Fonctionnalités

- [ ] Page d'accueil accessible
- [ ] Admin accessible : `/admin/`
- [ ] Connexion utilisateur fonctionne
- [ ] Fichiers statiques chargés (CSS visible)
- [ ] Upload de fichiers fonctionne (médias)
- [ ] Transcription OCR fonctionne (Celery)
- [ ] Bannière "ENVIRONNEMENT PILOTE" visible

### ☑ Isolation

- [ ] Base de données séparée confirmée
- [ ] Redis DB 1 utilisé (pas DB 0)
- [ ] Logs séparés et accessibles
- [ ] Pas d'interférence avec la production

### ☑ Maintenance

- [ ] Script `update_pilote.sh` fonctionnel
- [ ] Rotation des logs configurée
- [ ] Monitoring en place (htop, logs)

---

## Ressources

### Fichiers de configuration importants

```
/etc/nginx/sites-available/observations_nids_pilote
/etc/systemd/system/gunicorn-pilote.service
/etc/systemd/system/celery-worker-pilote.service
/var/www/observations_nids_pilote/.env
/var/www/observations_nids_pilote/update_pilote.sh
```

### Logs à surveiller

```
/var/log/nginx/observations_pilote_access.log
/var/log/nginx/observations_pilote_error.log
/var/log/gunicorn-pilote-error.log
/var/log/gunicorn-pilote-access.log
/var/log/celery-pilote-worker.log
```

### Commandes rapides

```bash
# Tout redémarrer
sudo systemctl restart gunicorn-pilote celery-worker-pilote && sudo systemctl reload nginx

# Voir tous les logs en temps réel
sudo tail -f /var/log/nginx/observations_pilote_error.log \
            /var/log/gunicorn-pilote-error.log \
            /var/log/celery-pilote-worker.log

# Mettre à jour rapidement
/var/www/observations_nids_pilote/update_pilote.sh
```

---

## Conclusion

Vous disposez maintenant d'un **environnement pilote/test totalement isolé** de la production, permettant de :

- ✅ Tester les nouvelles fonctionnalités en conditions réelles
- ✅ Valider avec des utilisateurs pilotes
- ✅ Déployer en continu depuis `main`
- ✅ Tester Nginx/Gunicorn comme alternative à Apache
- ✅ Garantir la stabilité de la production

**Prochain déploiement** : Utilisez le workflow recommandé (dev → pilote → validation → production).

**Support** : En cas de problème, consulter la section [Dépannage](#dépannage) ou les logs détaillés.

---

**Document maintenu par** : Équipe développement Observations Nids
**Dernière révision** : 1er novembre 2025
**Version** : 1.0
