# Guide de Déploiement - Environnement Pilote/Test

> **Guide complet pour déployer un environnement de test/pilote sur le même serveur que la production**
>
> Permet de tester les nouvelles fonctionnalités avec de vrais utilisateurs avant le déploiement en production.

**Dernière mise à jour** : 3 novembre 2025

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

### Architecture choisie : Option A (Sous-domaine) avec Apache → Gunicorn

> **📝 Note importante** : L'architecture déployée utilise **Apache en proxy direct vers Gunicorn** (sans Nginx intermédiaire).
>
> **Raison** : Architecture simplifiée où Apache gère SSL, les fichiers statiques/media, et proxie vers Gunicorn via socket Unix. Plus simple à maintenir qu'une chaîne Apache → Nginx → Gunicorn.

```
📦 Raspberry Pi (même machine)
│
├── 🟢 PRODUCTION (ne pas modifier)
│   ├── URL : observations-nids.votre-domaine.fr
│   ├── Serveur : Apache + mod_wsgi (port 80/443)
│   ├── Code : /var/www/observations_nids/
│   ├── Base : observations_nids_prod
│   ├── Redis : DB 0
│   └── Branch Git : production
│
└── 🔵 PILOTE/TEST (nouveau)
    ├── URL : pilote.observation-nids.votre-domaine.fr
    ├── Architecture : Apache (80/443) → Gunicorn (socket Unix)
    ├── Serveur Web : Apache (SSL + proxy + statiques) + Gunicorn
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
| **Serveur Web** | Apache (port 80/443) | Apache (port 80/443, proxy vers socket) |
| **App Server** | mod_wsgi | Gunicorn (socket Unix) |
| **Base de données** | `observations_nids_prod` | `observations_nids_pilote` |
| **Redis DB** | 0 | 1 |
| **Répertoire** | `/var/www/observations_nids/` | `/var/www/observations_nids_pilote/` |
| **Service Gunicorn** | N/A | `gunicorn-pilote.service` |
| **Service Celery** | `celery-worker.service` | `celery-worker-pilote.service` |
| **Logs Apache** | `/var/log/apache2/` | `/var/log/apache2/pilote_proxy_*.log` |
| **Logs Django/Celery** | `/var/www/observations_nids/logs/` | `/var/www/observations_nids_pilote/logs/` |
| **SSL** | Certbot Apache | Certbot Apache (pilote-proxy.conf) |
| **Fichiers statiques** | Servis par Apache | Servis par Apache (`Alias /static/`) |

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

> **📝 Note** : Cette installation n'utilise **pas Nginx**. Apache proxy directement vers Gunicorn via socket Unix.

### Phase 1 : Création du répertoire et clonage (10 min)

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

### Phase 2 : Environnement virtuel Python (10 min)

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

### Phase 3 : Configuration Django (.env) (15 min)

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
# IMPORTANT : Format JSON obligatoire pour ALLOWED_HOSTS (requis par Pydantic)
ALLOWED_HOSTS=["localhost","127.0.0.1","pilote.observation-nids.votre-domaine.fr","88.177.71.193"]

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
DJANGO_LOG_DIR=/var/www/observations_nids_pilote/logs
```

> **⚠️ Notes importantes sur le .env** :
> - **ALLOWED_HOSTS** doit être au format **JSON** (avec crochets et guillemets doubles) car Pydantic ne supporte pas le format CSV simple
> - **DJANGO_LOG_DIR** doit pointer vers `/var/www/observations_nids_pilote/logs` (à la racine du projet, PAS dans le sous-répertoire `observations/`)
> - Remplacez `votre-domaine.fr` par votre vrai domaine
> - Remplacez `88.177.71.193` par votre vraie IP publique


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

### Phase 4 : Création de la base de données (10 min)

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

### Phase 5 : Migrations et données initiales (15 min)

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

### Phase 6 : Configuration Apache (20 min)

> **📝 Note** : Apache proxy **directement** vers Gunicorn via socket Unix (pas de Nginx intermédiaire).
> Apache gère également le SSL et sert les fichiers statiques/media.

#### 6.1 Activer les modules proxy Apache

```bash
# Activer les modules proxy nécessaires
sudo a2enmod proxy
sudo a2enmod proxy_http

# Vérifier l'activation
apache2ctl -M | grep proxy
# Devrait afficher proxy_module et proxy_http_module
```

#### 6.2 Créer le VirtualHost HTTP (port 80)

```bash
sudo nano /etc/apache2/sites-available/pilote-proxy.conf
```

**Contenu** :

```apache
<VirtualHost *:80>
    ServerName pilote.observation-nids.votre-domaine.fr

    # Servir les fichiers statiques et media directement par Apache
    Alias /static/ /var/www/observations_nids_pilote/staticfiles/
    <Directory /var/www/observations_nids_pilote/staticfiles>
        Require all granted
    </Directory>

    Alias /media/ /var/www/observations_nids_pilote/media/
    <Directory /var/www/observations_nids_pilote/media>
        Require all granted
    </Directory>

    # Exclure les chemins statiques et media du proxy
    ProxyPass /static/ !
    ProxyPass /media/ !

    # Proxy vers Gunicorn via socket Unix
    # Note : le socket sera créé par Gunicorn dans /run/gunicorn-pilote/
    ProxyPreserveHost On
    ProxyPass / unix:/run/gunicorn-pilote/gunicorn.sock|http://localhost/
    ProxyPassReverse / unix:/run/gunicorn-pilote/gunicorn.sock|http://localhost/

    ErrorLog ${APACHE_LOG_DIR}/pilote_proxy_error.log
    CustomLog ${APACHE_LOG_DIR}/pilote_proxy_access.log combined
</VirtualHost>
```

**Explications** :
- `Alias /static/` : Apache sert directement les fichiers statiques (CSS, JS) sans passer par Django
- `Alias /media/` : Apache sert directement les fichiers media (uploads utilisateurs)
- `ProxyPass /static/ !` et `/media/ !` : Exclut ces chemins du proxy
- `ProxyPass ... unix:...` : Proxy vers le socket Unix de Gunicorn
- `ProxyPreserveHost On` : Transmet le nom de domaine original à Django

#### 6.3 Activer le site et tester

```bash
# Activer le site
sudo a2ensite pilote-proxy.conf

# Tester la configuration
sudo apache2ctl configtest
# Devrait afficher "Syntax OK"

# Redémarrer Apache
sudo systemctl restart apache2

# Vérifier le statut
sudo systemctl status apache2
```

**Note** : Le site retournera une erreur 503 pour l'instant car Gunicorn n'est pas encore configuré. C'est normal.

### Phase 7 : Configuration Gunicorn (20 min)

#### 7.1 Créer le service systemd

```bash
sudo nano /etc/systemd/system/gunicorn-pilote.service
```

> **⚠️ ATTENTION - Problème de copier-coller :**
>
> **Certains éditeurs (nano, vim) peuvent mal interpréter les retours à la ligne avec `\` (backslash) lorsque vous copiez-collez le contenu ci-dessous.**
>
> **Si le service ne démarre pas avec l'erreur "No application module specified", vérifiez que la ligne `ExecStart` est bien sur UNE SEULE ligne continue, SANS retour à la ligne physique.**
>
> **Le backslash `\` dans la documentation ci-dessous est uniquement pour la lisibilité dans ce document. Dans le fichier réel, tout doit être sur une seule ligne.**

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

ExecStart=/var/www/observations_nids_pilote/.venv/bin/gunicorn --workers 3 --worker-class sync --timeout 120 --bind unix:/run/gunicorn-pilote/gunicorn.sock --error-logfile /var/log/gunicorn-pilote-error.log --access-logfile /var/log/gunicorn-pilote-access.log --log-level info observations_nids.wsgi:application

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

#### 7.2 Créer les logs et ajuster les permissions

```bash
# Créer les fichiers de log Gunicorn
sudo touch /var/log/gunicorn-pilote-error.log
sudo touch /var/log/gunicorn-pilote-access.log
sudo chown www-data:www-data /var/log/gunicorn-pilote-*.log

# ⚠️ IMPORTANT : Créer le répertoire de logs Django
# Django utilise DJANGO_LOG_DIR=/var/www/observations_nids_pilote/logs (défini dans .env)
# Ne PAS créer dans /var/www/observations_nids_pilote/observations/logs !
sudo mkdir -p /var/www/observations_nids_pilote/logs
sudo chown www-data:www-data /var/www/observations_nids_pilote/logs
sudo chmod 755 /var/www/observations_nids_pilote/logs

# Créer le fichier de log Django
sudo touch /var/www/observations_nids_pilote/logs/django_debug.log
sudo chown www-data:www-data /var/www/observations_nids_pilote/logs/django_debug.log
sudo chmod 644 /var/www/observations_nids_pilote/logs/django_debug.log

# Ajuster les permissions du répertoire pilote
sudo chown -R www-data:www-data /var/www/observations_nids_pilote/media/
sudo chown -R www-data:www-data /var/www/observations_nids_pilote/staticfiles/
sudo chmod -R 755 /var/www/observations_nids_pilote/media/
sudo chmod -R 755 /var/www/observations_nids_pilote/staticfiles/
```

#### 7.3 Démarrer Gunicorn

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

#### 7.4 Vérifier la socket Gunicorn et tester

```bash
# La socket devrait être créée par RuntimeDirectory
ls -l /run/gunicorn-pilote/gunicorn.sock
# Devrait afficher un fichier socket (type srwxrwxrwx)

# Redémarrer Nginx pour prendre en compte la socket
sudo systemctl restart nginx
```

### Phase 8 : Configuration Celery (20 min)

#### 8.1 Créer le service Celery Worker

```bash
sudo nano /etc/systemd/system/celery-worker-pilote.service
```

> **⚠️ ATTENTION - Problème de copier-coller :**
>
> **Comme pour Gunicorn, certains éditeurs peuvent mal interpréter les retours à la ligne avec `\` (backslash).**
>
> **La ligne `ExecStart` doit être sur UNE SEULE ligne continue dans le fichier réel, SANS retour à la ligne physique.**

**Contenu** (adapté depuis la configuration production robuste) :

```ini
[Unit]
Description=Celery Worker Pilote - Observations Nids
After=network.target redis-server.service mariadb.service
Wants=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids_pilote

# Charger les variables d'environnement depuis .env
EnvironmentFile=/var/www/observations_nids_pilote/.env

# Configuration Python et Django
Environment="PYTHONPATH=/var/www/observations_nids_pilote"
Environment="DJANGO_SETTINGS_MODULE=observations_nids.settings"
Environment="C_FORCE_ROOT=true"
Environment="DJANGO_LOG_DIR=/var/www/observations_nids_pilote/logs"

# Créer automatiquement le répertoire runtime pour les PID
RuntimeDirectory=celery-pilote
RuntimeDirectoryMode=0755

# Commande de démarrage (sans --detach car systemd gère le processus)
ExecStart=/var/www/observations_nids_pilote/.venv/bin/celery -A observations_nids worker --loglevel=info --concurrency=2 --max-tasks-per-child=100 --logfile=/var/www/observations_nids_pilote/logs/celery-worker.log --pidfile=/run/celery-pilote/worker.pid

# Signaux pour l'arrêt et le rechargement
ExecStop=/bin/kill -s TERM $MAINPID
ExecReload=/bin/kill -s HUP $MAINPID

# Redémarrage automatique en cas d'échec
Restart=always
RestartSec=10s

# Limites de ressources pour Raspberry Pi
LimitNOFILE=65536
MemoryLimit=512M
CPUQuota=150%

# Sécurité
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/observations_nids_pilote/logs /var/www/observations_nids_pilote/media

# Logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=celery-worker-pilote

[Install]
WantedBy=multi-user.target
```

**📝 Explications des améliorations par rapport à une config basique** :

- **`Type=simple`** : Systemd suit directement le processus principal (pas de fork/detach)
- **`RuntimeDirectory=celery-pilote`** : Crée automatiquement `/run/celery-pilote/` avec les bonnes permissions
- **`--max-tasks-per-child=100`** : Redémarre les workers après 100 tâches pour éviter les fuites mémoire
- **`Restart=always`** : Redémarrage automatique même en cas d'arrêt normal (robustesse)
- **Limites de ressources** : Protection du Raspberry Pi contre la surcharge
- **`ProtectSystem=strict`** : Sécurité renforcée - Celery ne peut écrire que dans les chemins autorisés
- **`StandardOutput=journal`** : Logs intégrés à journald pour une meilleure traçabilité

#### 8.2 Créer le fichier de log Celery

```bash
# Le répertoire logs existe déjà (créé en Phase 7.2)
# Créer juste le fichier de log Celery
sudo touch /var/www/observations_nids_pilote/logs/celery-worker.log
sudo chown www-data:www-data /var/www/observations_nids_pilote/logs/celery-worker.log
sudo chmod 644 /var/www/observations_nids_pilote/logs/celery-worker.log
```

#### 8.3 Démarrer Celery

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer Celery
sudo systemctl enable celery-worker-pilote
sudo systemctl start celery-worker-pilote

# Vérifier le statut
sudo systemctl status celery-worker-pilote

# Vérifier les logs (dans journald et dans le fichier)
sudo journalctl -u celery-worker-pilote -f
# Ou consulter le fichier de log directement
sudo tail -f /var/www/observations_nids_pilote/logs/celery-worker.log
```

### Phase 9 : Test initial (sans SSL) (10 min)

```bash
# Tester l'accès HTTP (temporaire)
curl -I http://pilote.observation-nids.votre-domaine.fr

# Devrait retourner un code 200 ou une redirection

# Ouvrir dans un navigateur
# http://pilote.observation-nids.votre-domaine.fr
# Devrait afficher la page d'accueil (sans style si pas de SSL)
```

### Phase 10 : Configuration SSL avec Let's Encrypt (15 min)

> **📝 Note** : Le certificat SSL est installé sur **Apache** car Apache gère directement les connexions sur les ports 80/443.

```bash
# Installer Certbot pour Apache (si pas déjà fait)
sudo apt install -y certbot python3-certbot-apache

# Obtenir le certificat SSL pour le sous-domaine pilote
sudo certbot --apache -d pilote.observation-nids.votre-domaine.fr

# Suivre les instructions interactives :
# Email: votre-email@domaine.fr
# Accepter les CGU: Oui (A)
# Partager email avec EFF: Optionnel (Y/N)
# Redirection HTTPS automatique: Oui (2)

# Vérifier le certificat
sudo certbot certificates
# Devrait lister le certificat pour pilote.observation-nids.votre-domaine.fr

# Tester le renouvellement automatique
sudo certbot renew --dry-run
```

**Certbot va automatiquement :**
- ✅ Créer le certificat SSL pour le sous-domaine pilote
- ✅ Modifier `pilote-proxy.conf` pour ajouter un VirtualHost HTTPS:443
- ✅ Configurer la redirection HTTP → HTTPS
- ✅ Mettre en place le renouvellement automatique (cron)

**Architecture finale après SSL** :
```
Internet (HTTPS:443)
    ↓
Apache (SSL termination + proxy + fichiers statiques)
    ↓ Socket Unix
Gunicorn/Django
```

> **📝 Note sur CSRF_TRUSTED_ORIGINS** : Pour que Django accepte les requêtes HTTPS via le proxy Apache, ajoutez dans `/var/www/observations_nids_pilote/observations_nids/settings_local.py` :
> ```python
> CSRF_TRUSTED_ORIGINS = [
>     'https://pilote.observation-nids.votre-domaine.fr',
> ]
> ```

#### 10.2 Activer HTTPS dans Django

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

### Phase 11 : Validation finale (15 min)

#### 11.1 Tests de connectivité

```bash
# Test HTTPS
curl -I https://pilote.observation-nids.votre-domaine.fr
# Devrait retourner 200 OK

# Test redirection HTTP → HTTPS
curl -I http://pilote.observation-nids.votre-domaine.fr
# Devrait retourner 301 et rediriger vers https://
```

#### 11.2 Tests fonctionnels

Ouvrir dans un navigateur : `https://pilote.observation-nids.votre-domaine.fr`

Vérifier :
- ✅ Page d'accueil s'affiche correctement
- ✅ CSS chargé (styles visibles)
- ✅ Connexion admin : `/admin/`
- ✅ Aucune erreur dans la console navigateur (F12)

#### 11.3 Vérifier les services

```bash
# Tous les services doivent être actifs
sudo systemctl status apache2
sudo systemctl status gunicorn-pilote
sudo systemctl status celery-worker-pilote
sudo systemctl status redis-server
sudo systemctl status mariadb

# Vérifier les logs
sudo tail -n 50 /var/log/apache2/pilote_proxy_error.log
sudo tail -n 50 /var/log/gunicorn-pilote-error.log
sudo tail -n 50 /var/www/observations_nids_pilote/logs/celery-worker.log
```

#### 11.4 Désactiver Nginx (si installé)

> **📝 Note** : Nginx n'est **pas utilisé** dans cette architecture. Si vous l'aviez installé lors d'un test précédent, désactivez-le.

```bash
# Arrêter et désactiver Nginx
sudo systemctl stop nginx
sudo systemctl disable nginx

# Vérifier qu'il est bien arrêté
sudo systemctl status nginx
# Devrait afficher "inactive (dead)"
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
sudo systemctl reload apache2

# Voir les logs en temps réel
sudo journalctl -u gunicorn-pilote -f
sudo tail -f /var/log/gunicorn-pilote-error.log
sudo tail -f /var/log/apache2/pilote_proxy_error.log

# Vérifier l'état des services
sudo systemctl status gunicorn-pilote celery-worker-pilote apache2

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

/var/www/observations_nids_pilote/logs/celery-worker.log {
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

/var/www/observations_nids_pilote/logs/django_debug.log {
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
```

---

## Dépannage

### Nginx ne démarre pas avec "bind() failed"

**Symptôme** : `nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)`

**Cause** : Apache et Nginx ne peuvent pas écouter simultanément sur le même port 80.

**Solution** : Nginx doit écouter sur le port **8080** et Apache fait le reverse proxy.

```bash
# Vérifier que Nginx écoute bien sur 8080 (pas 80)
sudo nano /etc/nginx/sites-available/observations_nids_pilote
# Vérifier les lignes :
#   listen 8080;
#   listen [::]:8080;

# Tester la configuration
sudo nginx -t

# Redémarrer
sudo systemctl restart nginx

# Vérifier qu'Apache écoute sur 80 et Nginx sur 8080
sudo ss -tlnp | grep -E ':(80|8080)'
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

### Erreur "Unable to configure handler 'file'" au démarrage

**Symptôme** : Gunicorn fonctionne en manuel mais échoue en service avec l'erreur :
```
ValueError: Unable to configure handler 'file'
Worker exiting (pid: XXXXX) with code 3
```

**Cause** : Le répertoire de logs Django n'existe pas ou n'est pas accessible par `www-data`.

**Solution** :

```bash
# Vérifier où Django cherche à écrire les logs
cd /var/www/observations_nids_pilote
source .venv/bin/activate
python -c "from observations_nids.settings import LOGGING; print(LOGGING['handlers']['file']['filename'])"
# Devrait afficher : /var/www/observations_nids_pilote/logs/django_debug.log

# Créer le répertoire et le fichier avec les bonnes permissions
sudo mkdir -p /var/www/observations_nids_pilote/logs
sudo chown www-data:www-data /var/www/observations_nids_pilote/logs
sudo touch /var/www/observations_nids_pilote/logs/django_debug.log
sudo chown www-data:www-data /var/www/observations_nids_pilote/logs/django_debug.log
sudo chmod 644 /var/www/observations_nids_pilote/logs/django_debug.log

# Redémarrer le service
sudo systemctl restart gunicorn-pilote
sudo systemctl status gunicorn-pilote
```

**Note importante** : Le chemin est `/var/www/observations_nids_pilote/logs/` (à la racine du projet), **PAS** `/var/www/observations_nids_pilote/observations/logs/` (dans le sous-répertoire).

### Erreur 502 Bad Gateway

```bash
# Vérifier que Gunicorn tourne
sudo systemctl status gunicorn-pilote

# Vérifier que la socket existe
ls -l /run/gunicorn-pilote/gunicorn.sock

# Vérifier les logs Apache
sudo tail -f /var/log/apache2/pilote_proxy_error.log

# Redémarrer dans l'ordre
sudo systemctl restart gunicorn-pilote
sudo systemctl reload apache2
```

### Erreur 400 Bad Request ou DisallowedHost

**Symptôme** : `django.core.exceptions.DisallowedHost: Invalid HTTP_HOST header`

**Cause** : Le nom de domaine reçu par Django n'est pas dans ALLOWED_HOSTS du `.env`.

**Solutions** :

```bash
# 1. Vérifier les logs pour voir quel host est reçu
sudo tail -30 /var/www/observations_nids_pilote/logs/django_debug.log
# ou
sudo journalctl -u gunicorn-pilote -n 30

# 2. Éditer le .env
sudo nano /var/www/observations_nids_pilote/.env

# 3. Ajouter le host manquant (format JSON obligatoire !)
# Exemple :
ALLOWED_HOSTS=["localhost","127.0.0.1","pilote.observation-nids.votre-domaine.fr","88.177.71.193"]

# 4. Redémarrer
sudo systemctl restart gunicorn-pilote
```

**Note importante** : Le format doit être **JSON** avec crochets `[]` et guillemets doubles `""`. Le format CSV simple ne fonctionne pas avec Pydantic.

**Erreur courante** :
- ❌ `ALLOWED_HOSTS=localhost,127.0.0.1` (mauvais format)
- ✅ `ALLOWED_HOSTS=["localhost","127.0.0.1"]` (bon format)

### Erreur "SettingsError: error parsing value for field ALLOWED_HOSTS"

**Symptôme** : Gunicorn ne démarre pas avec l'erreur Pydantic sur ALLOWED_HOSTS

**Cause** : Format incorrect dans le `.env` (pas du JSON valide)

**Solution** : Utilisez le format JSON avec crochets et guillemets doubles :
```bash
ALLOWED_HOSTS=["localhost","127.0.0.1","pilote.observation-nids.votre-domaine.fr"]
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

# Voir les logs (journald ou fichier)
sudo journalctl -u celery-worker-pilote -n 50
# Ou
sudo tail -f /var/www/observations_nids_pilote/logs/celery-worker.log

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

### Le domaine racine pointe vers le pilote au lieu du site attendu

**Symptôme** : `http://votredomaineracine.fr` affiche le site pilote au lieu du site prévu (ex: WeeWX, site vitrine, etc.)

**Cause** : Apache n'a pas de VirtualHost pour le domaine racine et utilise par défaut le premier disponible (pilote-proxy.conf).

**Solution** : Créer un VirtualHost pour le domaine racine.

Exemple pour WeeWX :
```bash
sudo nano /etc/apache2/sites-available/domaineracine.conf
```

```apache
<VirtualHost *:80>
    ServerName votredomaineracine.fr
    DocumentRoot /var/www/html/weewx

    <Directory /var/www/html/weewx>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/domaine_error.log
    CustomLog ${APACHE_LOG_DIR}/domaine_access.log combined
</VirtualHost>
```

```bash
# Activer et redémarrer
sudo a2ensite domaineracine.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
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
/etc/apache2/sites-available/pilote-proxy.conf
/etc/apache2/sites-available/pilote-proxy-le-ssl.conf
/etc/systemd/system/gunicorn-pilote.service
/etc/systemd/system/celery-worker-pilote.service
/var/www/observations_nids_pilote/.env
/var/www/observations_nids_pilote/update_pilote.sh
```

### Logs à surveiller

```
# Logs Apache (reverse proxy)
/var/log/apache2/pilote_proxy_access.log
/var/log/apache2/pilote_proxy_error.log

# Logs Gunicorn
/var/log/gunicorn-pilote-error.log
/var/log/gunicorn-pilote-access.log

# Logs Django et Celery (dans le projet)
/var/www/observations_nids_pilote/logs/django_debug.log
/var/www/observations_nids_pilote/logs/celery-worker.log

# Logs systemd (journald)
# Utiliser: sudo journalctl -u gunicorn-pilote
# Utiliser: sudo journalctl -u celery-worker-pilote
```

### Commandes rapides

```bash
# Tout redémarrer
sudo systemctl restart gunicorn-pilote celery-worker-pilote && sudo systemctl reload apache2

# Voir tous les logs en temps réel
sudo tail -f /var/log/apache2/pilote_proxy_error.log \
            /var/log/gunicorn-pilote-error.log \
            /var/www/observations_nids_pilote/logs/django_debug.log \
            /var/www/observations_nids_pilote/logs/celery-worker.log

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
**Dernière révision** : 3 novembre 2025
**Version** : 1.3

**Changelog** :
- **v1.3 (3 nov 2025)** : Architecture simplifiée - suppression de Nginx, Apache connecté directement à Gunicorn via socket Unix
- **v1.2 (3 nov 2025)** : Architecture finale avec Apache reverse proxy + corrections format ALLOWED_HOSTS JSON
- **v1.1 (2 nov 2025)** : Configuration Celery robuste + corrections chemins logs
- **v1.0 (1 nov 2025)** : Version initiale
