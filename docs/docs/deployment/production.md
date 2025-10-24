# Guide de Déploiement Production - Raspberry Pi

> **Guide complet de déploiement et sécurisation**
> Ce document couvre l'ensemble du processus : de la sécurisation initiale au déploiement, puis la maintenance en production.

**Navigation rapide :**
- [Étape 1 : Sécurisation préalable](#étape-1--sécurisation-préalable-obligatoire) ⚠️ **À faire en premier**
- [Étape 2 : Déploiement initial](#étape-2--déploiement-initial)
- [Étape 3 : Vérification post-déploiement](#étape-3--vérification-post-déploiement)
- [Mises à jour futures](#mises-à-jour-futures-non-destructives)
- [Sécurité avancée](#sécurité-avancée-phases-2-et-3)
- [Annexes](#annexes)

---

## Vue d'ensemble

Ce guide vous accompagne pour déployer l'application **Observations Nids** sur un Raspberry Pi en production. Le processus se déroule en 3 étapes principales :

1. **Sécurisation du serveur** (obligatoire avant tout déploiement)
2. **Déploiement de l'application** (automatisé ou manuel)
3. **Configuration avancée** (HTTPS, monitoring, backups)

**Durée estimée :**
- Sécurisation Phase 1 : 30-45 minutes
- Déploiement initial : 15-30 minutes
- Configuration avancée : 2-4 heures (réparties sur plusieurs jours)

---

## Prérequis

### Matériel et système
- ✅ Raspberry Pi 3B+ ou supérieur (recommandé : Pi 4 avec 4GB RAM)
- ✅ Carte SD de qualité (32GB minimum, classe A1 ou A2)
- ✅ Raspberry Pi OS 64-bit (Debian Bookworm) à jour
- ✅ Accès physique au Pi en cas de problème SSH
- ✅ Alimentation stable (éviter les coupures)

### Réseau et domaine
- ✅ IP fixe (via DHCP statique ou configuration réseau)
- ✅ Nom de domaine pointant vers le Pi (requis pour HTTPS)
- ✅ Ports 80 et 443 accessibles depuis Internet (si hébergement public)

### Accès et droits
- ✅ Accès SSH avec utilisateur ayant droits `sudo`
- ✅ Git, Python 3.11+, et `virtualenv` installés
- ✅ Serveur web Apache2 installé

### Installation des outils de base

```bash
# Mise à jour initiale
sudo apt update && sudo apt upgrade -y

# Outils essentiels
sudo apt install -y git python3-full python3-pip python3-venv \
  apache2 libapache2-mod-wsgi-py3 mariadb-server mariadb-client \
  redis-server build-essential libssl-dev libffi-dev python3-dev
```

---

## Étape 1 : Sécurisation préalable (OBLIGATOIRE)

⚠️ **IMPORTANT** : Ne déployez JAMAIS une application sans avoir complété au minimum la Phase 1 de sécurisation. Un serveur non sécurisé sera compromis en quelques heures.

### Sauvegarde initiale (obligatoire)

Avant toute modification, créez une sauvegarde complète :

```bash
# Sauvegarde du système (si base de données existante)
sudo mysqldump --all-databases --single-transaction --routines --events \
  > /root/backup_initial_$(date +%F).sql

# Sauvegarde des fichiers de configuration
sudo tar -czf /root/backup_config_$(date +%F).tar.gz \
  /etc/ssh /etc/apache2 /etc/mysql
```

**Vérification :** `ls -lh /root/backup_*` doit afficher les fichiers créés.

---

### Phase 1 : Actions immédiates

Cette phase doit être complétée **avant le déploiement**. Comptez 30-45 minutes.

#### ☑ 1.1 Mise à jour du système

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install unattended-upgrades apt-listchanges -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

**Vérification :** `sudo apt list --upgradable` doit retourner une liste vide.

**Explication :** Les mises à jour automatiques (`unattended-upgrades`) installent les correctifs de sécurité sans intervention manuelle.

---

#### ☑ 1.2 Gestion des utilisateurs & SSH

**Étape A : Créer un utilisateur admin**

```bash
# Créer l'utilisateur (remplacer 'jmadmin' par votre nom)
sudo adduser jmadmin
sudo usermod -aG sudo jmadmin
```

**Étape B : Configurer l'accès par clé SSH**

Sur **votre machine locale** :

```bash
# Générer une paire de clés (si pas déjà fait)
ssh-keygen -t ed25519 -C "admin@observations-nids"

# Copier la clé publique sur le Pi
ssh-copy-id -i ~/.ssh/id_ed25519.pub jmadmin@<IP_DU_PI>
```

**Étape C : Tester la connexion par clé**

```bash
# Tester SANS fermer la session actuelle
ssh jmadmin@<IP_DU_PI>
```

**Étape D : Sécuriser SSH**

Une fois la connexion par clé vérifiée, modifier `/etc/ssh/sshd_config` :

```bash
sudo nano /etc/ssh/sshd_config
```

Modifier ou ajouter ces lignes :

```
# Désactiver connexion root
PermitRootLogin no

# Désactiver authentification par mot de passe
PasswordAuthentication no

# (Optionnel) Changer le port SSH
# Port 2222

# Autoriser seulement certains utilisateurs
AllowUsers jmadmin
```

Redémarrer SSH :

```bash
sudo systemctl restart ssh
```

**Vérification :**
- ✅ Connexion par clé fonctionne : `ssh jmadmin@<IP_DU_PI>`
- ✅ Connexion par mot de passe refusée (tester depuis une autre machine)

⚠️ **CRITIQUE** : Ne fermez pas votre session SSH actuelle tant que vous n'avez pas vérifié que la connexion par clé fonctionne !

---

#### ☑ 1.3 Sécurisation MariaDB

```bash
sudo mysql_secure_installation
```

Répondre **OUI** à toutes les questions :
- ✅ Définir un mot de passe root fort
- ✅ Supprimer les utilisateurs anonymes
- ✅ Désactiver la connexion root distante
- ✅ Supprimer la base de données de test
- ✅ Recharger les privilèges

**Vérification :**

```bash
sudo mysql -u root -p
```

Puis dans MariaDB :

```sql
SELECT user, host FROM mysql.user;
-- Vérifier qu'aucun utilisateur root n'a host='%'
EXIT;
```

---

#### ☑ 1.4 Pare-feu (UFW)

```bash
# Installer et configurer UFW
sudo apt install ufw -y

# Politique par défaut
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Autoriser SSH (port 22 ou personnalisé)
sudo ufw allow 22/tcp

# Autoriser HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activer le pare-feu
sudo ufw enable

# Vérifier l'état
sudo ufw status verbose
```

**Vérification :** `sudo ufw status` doit afficher les règles actives.

⚠️ **ATTENTION** : Si vous avez changé le port SSH, remplacez `22` par votre port personnalisé AVANT d'activer UFW !

---

#### ☑ 1.5 Fail2Ban

Protection contre les attaques par force brute :

```bash
sudo apt install fail2ban -y
```

Créer `/etc/fail2ban/jail.d/local.conf` :

```bash
sudo nano /etc/fail2ban/jail.d/local.conf
```

Contenu :

```ini
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = /var/log/auth.log
maxretry = 5

[apache-auth]
enabled = true
filter = apache-auth
logpath = /var/log/apache2/*error.log
maxretry = 6

[apache-badbots]
enabled  = true
port     = http,https
filter   = apache-badbots
logpath  = /var/log/apache2/*access.log
maxretry = 2
```

Redémarrer Fail2Ban :

```bash
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

**Vérification :**

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

---

#### ☑ 1.6 Fichier `.env` et SECRET_KEY

⚠️ **CRITIQUE** : La `SECRET_KEY` Django NE doit JAMAIS être dans Git.

**Étape A : Générer une SECRET_KEY**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Étape B : Créer le fichier `.env`**

Dans le répertoire du projet (ex: `/var/www/observations_nids/`) :

```bash
nano .env
```

Contenu minimal :

```env
# Django
SECRET_KEY=<votre_secret_key_générée>
DEBUG=False
ALLOWED_HOSTS=votre-domaine.fr,www.votre-domaine.fr

# Base de données
DB_ENGINE=django.db.backends.mysql
DB_NAME=observations_nids
DB_USER=django_app
DB_PASSWORD=<mot_de_passe_fort>
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Email (production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.votre-fournisseur.fr
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@votre-domaine.fr
EMAIL_HOST_PASSWORD=<mot_de_passe_email>

# Google Vision API (transcription OCR)
GOOGLE_API_KEY=<votre_clé_api_google>
```

**Étape C : Protéger le fichier**

```bash
chmod 600 .env
chown www-data:www-data .env
```

**Vérification :** `ls -l .env` doit afficher `-rw-------` (permissions 600).

---

### Checkpoint Phase 1 ✅

Avant de passer au déploiement, vérifiez :

- [ ] Système à jour et mises à jour automatiques activées
- [ ] Utilisateur admin créé avec accès SSH par clé
- [ ] SSH sécurisé (pas de root, pas de mot de passe)
- [ ] MariaDB sécurisé avec `mysql_secure_installation`
- [ ] Pare-feu UFW actif avec règles appropriées
- [ ] Fail2Ban installé et configuré
- [ ] Fichier `.env` créé avec SECRET_KEY et permissions correctes

**Si toutes les cases sont cochées, vous pouvez passer au déploiement. Sinon, retournez compléter les étapes manquantes.**

---

## Étape 2 : Déploiement initial

Maintenant que le serveur est sécurisé, vous pouvez déployer l'application. Deux méthodes sont disponibles :

- **Méthode 1 (recommandée)** : Script automatisé `deploy_pi.sh`
- **Méthode 2** : Déploiement manuel étape par étape

---

### Méthode 1 : Déploiement automatisé (recommandé)

Le script `deploy_pi.sh` automatise toutes les étapes de déploiement.

#### ⚠️ AVERTISSEMENT IMPORTANT

Dans sa version actuelle, le script est **DESTRUCTIF** : il **supprime et recrée la base de données** à chaque exécution.

**Utilisation appropriée :**
- ✅ **Première installation** sur un serveur vierge
- ❌ **Mise à jour** d'une application avec données (voir [Mises à jour futures](#mises-à-jour-futures-non-destructives))

#### Étapes du déploiement automatisé

**1. Cloner le dépôt**

```bash
# Se placer dans le répertoire web
cd /var/www/

# Cloner le projet
sudo git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids
cd observations_nids

# Basculer sur la branche production
sudo git checkout production
```

**2. Configurer les permissions**

```bash
# Changer le propriétaire
sudo chown -R www-data:www-data /var/www/observations_nids

# Rendre le script exécutable
sudo chmod +x deploy_pi.sh
```

**3. Créer le fichier `.env`**

Si ce n'est pas déjà fait (voir section 1.6), créez le fichier `.env` avec les bonnes valeurs.

**4. Exécuter le script de déploiement**

```bash
sudo ./deploy_pi.sh
```

Le script va effectuer automatiquement :
1. Sauvegarde des configurations existantes
2. Arrêt du serveur Apache
3. Mise à jour du code (git pull)
4. Création de l'environnement virtuel Python
5. Installation des dépendances (`requirements-prod.txt`)
6. Configuration de la base de données MariaDB
7. Application des migrations Django
8. Collecte des fichiers statiques
9. Configuration Apache (VirtualHost + mod_wsgi)
10. Redémarrage du serveur

**Durée estimée :** 10-15 minutes selon la connexion Internet.

**5. Créer un super-utilisateur**

```bash
cd /var/www/observations_nids
source .venv/bin/activate
python manage.py createsuperuser
```

**6. Vérifier le déploiement**

Ouvrez votre navigateur et accédez à `http://<IP_DU_PI>` ou `http://votre-domaine.fr`.

Vous devriez voir la page d'accueil de l'application.

---

### Méthode 2 : Déploiement manuel

Pour un contrôle total du processus, suivez ces étapes :

#### 2.1 Cloner le projet

```bash
cd /var/www/
sudo git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids
cd observations_nids
sudo git checkout production
```

#### 2.2 Créer l'environnement virtuel

```bash
sudo python3 -m venv .venv
sudo chown -R www-data:www-data .venv
```

#### 2.3 Installer les dépendances

```bash
sudo -u www-data .venv/bin/pip install --upgrade pip
sudo -u www-data .venv/bin/pip install -r requirements-prod.txt
```

#### 2.4 Créer la base de données MariaDB

```bash
sudo mysql -u root -p
```

Dans MariaDB :

```sql
CREATE DATABASE observations_nids CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'django_app'@'localhost' IDENTIFIED BY '<mot_de_passe_fort>';
GRANT ALL PRIVILEGES ON observations_nids.* TO 'django_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 2.5 Configurer le fichier `.env`

Voir section 1.6 pour le contenu du fichier.

#### 2.6 Appliquer les migrations

```bash
cd /var/www/observations_nids
sudo -u www-data .venv/bin/python manage.py migrate
```

#### 2.7 Collecter les fichiers statiques

```bash
sudo -u www-data .venv/bin/python manage.py collectstatic --noinput
```

#### 2.8 Configurer Apache

**A. Créer le fichier WSGI**

Créer `/var/www/observations_nids/observations_nids.wsgi` :

```python
import os
import sys

# Ajouter le chemin du projet
path = '/var/www/observations_nids'
if path not in sys.path:
    sys.path.insert(0, path)

# Environnement virtuel
activate_this = '/var/www/observations_nids/.venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Configuration Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'observations_nids.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**B. Créer le VirtualHost Apache**

Créer `/etc/apache2/sites-available/observations_nids.conf` :

```apache
<VirtualHost *:80>
    ServerName votre-domaine.fr
    ServerAlias www.votre-domaine.fr
    ServerAdmin admin@votre-domaine.fr

    DocumentRoot /var/www/observations_nids

    # WSGI Configuration
    WSGIDaemonProcess observations_nids python-home=/var/www/observations_nids/.venv python-path=/var/www/observations_nids
    WSGIProcessGroup observations_nids
    WSGIScriptAlias / /var/www/observations_nids/observations_nids.wsgi

    <Directory /var/www/observations_nids>
        <Files observations_nids.wsgi>
            Require all granted
        </Files>
    </Directory>

    # Fichiers statiques
    Alias /static/ /var/www/observations_nids/staticfiles/
    <Directory /var/www/observations_nids/staticfiles>
        Require all granted
    </Directory>

    # Fichiers médias
    Alias /media/ /var/www/observations_nids/media/
    <Directory /var/www/observations_nids/media>
        Require all granted
    </Directory>

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/observations_nids_error.log
    CustomLog ${APACHE_LOG_DIR}/observations_nids_access.log combined
</VirtualHost>
```

**C. Activer le site et les modules**

```bash
sudo a2enmod wsgi
sudo a2ensite observations_nids.conf
sudo a2dissite 000-default.conf
sudo apachectl configtest
sudo systemctl restart apache2
```

#### 2.9 Créer un super-utilisateur

```bash
cd /var/www/observations_nids
sudo -u www-data .venv/bin/python manage.py createsuperuser
```

---

## Étape 3 : Vérification post-déploiement

Après le déploiement, effectuez ces vérifications :

### ☑ 3.1 Vérifier l'accès web

```bash
# Test local
curl -I http://localhost

# Test depuis l'extérieur (remplacer par votre domaine)
curl -I http://votre-domaine.fr
```

Attendu : `HTTP/1.1 200 OK` ou `HTTP/1.1 302 Found` (redirection)

### ☑ 3.2 Vérifier la base de données

```bash
sudo -u www-data /var/www/observations_nids/.venv/bin/python manage.py check
```

Attendu : `System check identified no issues (0 silenced).`

### ☑ 3.3 Vérifier les logs Apache

```bash
sudo tail -f /var/log/apache2/observations_nids_error.log
```

Ne devrait pas contenir d'erreurs récentes.

### ☑ 3.4 Vérifier Redis et Celery

```bash
# Tester Redis
redis-cli ping
# Attendu : PONG

# Lancer le worker Celery (pour les tâches asynchrones)
cd /var/www/observations_nids
sudo -u www-data .venv/bin/celery -A observations_nids worker --loglevel=info
```

### ☑ 3.5 Tester l'interface admin

Accédez à `http://votre-domaine.fr/admin` et connectez-vous avec le super-utilisateur créé.

### ☑ 3.6 Vérifier la sécurité

```bash
# Ports ouverts
sudo nmap -sS localhost

# Services actifs
sudo systemctl status apache2
sudo systemctl status redis-server
sudo systemctl status fail2ban
sudo systemctl status ufw

# Fail2Ban status
sudo fail2ban-client status
```

---

## Mises à jour futures (non-destructives)

Une fois que l'application est en production avec des **données réelles**, vous ne devez **PLUS utiliser le script `deploy_pi.sh`** dans sa version actuelle (qui supprime la base de données).

### Option 1 : Modifier le script pour le rendre non-destructif

Ouvrir `deploy_pi.sh` et commenter/supprimer les lignes qui suppriment la base de données (étape 7 du script) :

```bash
# ÉTAPE 7 : commenter ou supprimer ces lignes
# echo -e "${YELLOW}[7/10]${NC} Suppression de l'ancienne base de données..."
# if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
#     mv "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_old_$(date +%Y%m%d_%H%M%S).sqlite3"
#     echo -e "${GREEN}✓${NC} Ancienne base sauvegardée\n"
# else
#     echo -e "${YELLOW}!${NC} Aucune base de données trouvée\n"
# fi
```

Le script se contentera alors d'appliquer les nouvelles migrations sans effacer les données.

### Option 2 : Procédure de mise à jour manuelle

**Workflow recommandé pour les mises à jour :**

```bash
# 1. Se connecter au Pi
ssh jmadmin@<IP_DU_PI>

# 2. Naviguer vers le projet
cd /var/www/observations_nids

# 3. Sauvegarder la base de données (OBLIGATOIRE)
sudo mysqldump -u django_app -p observations_nids \
  > ~/backup_db_$(date +%F_%H%M).sql

# 4. Mettre à jour le code
sudo git fetch origin
sudo git pull origin production

# 5. Activer l'environnement virtuel
source .venv/bin/activate

# 6. Mettre à jour les dépendances Python
sudo -u www-data .venv/bin/pip install -r requirements-prod.txt

# 7. Appliquer les migrations (NON-DESTRUCTIF)
sudo -u www-data .venv/bin/python manage.py migrate

# 8. Collecter les fichiers statiques
sudo -u www-data .venv/bin/python manage.py collectstatic --noinput

# 9. Redémarrer Apache
sudo systemctl restart apache2

# 10. Vérifier les logs
sudo tail -f /var/log/apache2/observations_nids_error.log
```

**Durée estimée :** 5-10 minutes

### Gestion des conflits de migration

Si les migrations échouent :

```bash
# Voir l'état des migrations
sudo -u www-data .venv/bin/python manage.py showmigrations

# Revenir en arrière si nécessaire
sudo -u www-data .venv/bin/python manage.py migrate <app_name> <migration_name>

# Forcer une migration (DANGER : comprendre pourquoi avant)
sudo -u www-data .venv/bin/python manage.py migrate --fake <app_name> <migration_name>
```

---

## Sécurité avancée (Phases 2 et 3)

Une fois le déploiement initial effectué, poursuivez le durcissement du serveur.

---

### Phase 2 : Renforcement (jours suivants)

Cette phase améliore la sécurité et ajoute HTTPS. Comptez 2-4 heures réparties sur plusieurs jours.

#### ☑ 2.1 HTTPS avec Let's Encrypt

⚠️ **Prérequis** : Votre domaine doit pointer vers l'IP publique du Pi.

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-apache -y

# Obtenir un certificat SSL
sudo certbot --apache -d votre-domaine.fr -d www.votre-domaine.fr

# Tester le renouvellement automatique
sudo certbot renew --dry-run
```

**Vérification :**

```bash
# Vérifier les certificats
sudo certbot certificates

# Tester HTTPS
curl -I https://votre-domaine.fr
```

Le certificat se renouvellera automatiquement tous les 90 jours.

---

#### ☑ 2.2 Hardening Apache

**A. Désactiver modules inutiles**

```bash
sudo a2dismod status cgi autoindex
sudo systemctl restart apache2
```

**B. Protéger les en-têtes HTTP**

Modifier `/etc/apache2/sites-available/observations_nids-le-ssl.conf` (créé par Certbot) :

```apache
<VirtualHost *:443>
    ServerName votre-domaine.fr

    # Configuration SSL par Certbot
    Include /etc/letsencrypt/options-ssl-apache.conf
    SSLCertificateFile /etc/letsencrypt/live/votre-domaine.fr/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/votre-domaine.fr/privkey.pem

    # En-têtes de sécurité
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"

    # HSTS (activer seulement si HTTPS stable)
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"

    # CSP (Content Security Policy) - à adapter selon vos besoins
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"

    # Limiter la taille des uploads
    LimitRequestBody 10485760

    # Cacher la signature du serveur
    ServerSignature Off
    ServerTokens Prod

    # ... reste de la configuration WSGI ...
</VirtualHost>
```

Activer le module `headers` et redémarrer :

```bash
sudo a2enmod headers
sudo apachectl configtest
sudo systemctl restart apache2
```

**Vérification :**

```bash
curl -I https://votre-domaine.fr
# Vérifier la présence des en-têtes de sécurité
```

---

#### ☑ 2.3 Sécuriser MariaDB - Configuration réseau

**A. Forcer l'écoute locale uniquement**

Modifier `/etc/mysql/mariadb.conf.d/50-server.cnf` :

```ini
[mysqld]
bind-address = 127.0.0.1
```

Redémarrer MariaDB :

```bash
sudo systemctl restart mariadb
```

**B. Créer un utilisateur Django avec privilèges minimaux**

```sql
-- Supprimer l'ancien utilisateur si nécessaire
DROP USER IF EXISTS 'django_app'@'localhost';

-- Créer un utilisateur avec privilèges limités
CREATE USER 'django_app'@'localhost' IDENTIFIED BY '<mot_de_passe_fort>';

-- Accorder uniquement les privilèges nécessaires (pas de DROP DATABASE, etc.)
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON observations_nids.* TO 'django_app'@'localhost';

FLUSH PRIVILEGES;
```

**Vérification :**

```bash
sudo mysql -u django_app -p observations_nids
# Tester une requête SELECT
```

---

#### ☑ 2.4 Logs et rotation

**A. Configurer la rotation des logs Apache**

Créer `/etc/logrotate.d/observations_nids` :

```
/var/log/apache2/observations_nids*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 root adm
    sharedscripts
    postrotate
        systemctl reload apache2 > /dev/null 2>&1 || true
    endscript
}
```

**B. Configurer les logs Django**

Ajouter dans `settings.py` (si pas déjà fait) :

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/observations_nids/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

Créer le répertoire de logs :

```bash
sudo mkdir -p /var/log/observations_nids
sudo chown www-data:www-data /var/log/observations_nids
```

**Vérification :**

```bash
sudo logrotate --debug /etc/logrotate.conf
```

---

#### ☑ 2.5 Sécurité des dépendances Python

```bash
# Installer pip-audit
cd /var/www/observations_nids
source .venv/bin/activate
pip install pip-audit

# Auditer les dépendances
pip-audit
```

Si des vulnérabilités sont trouvées :

```bash
# Mettre à jour les packages vulnérables
pip install --upgrade <package_name>

# Régénérer requirements-prod.txt
pip freeze > requirements-prod.txt
```

**Automatiser l'audit (optionnel)** :

```bash
# Crontab hebdomadaire
sudo crontab -e
```

Ajouter :

```
0 3 * * 1 cd /var/www/observations_nids && .venv/bin/pip-audit > /var/log/pip-audit.log 2>&1
```

---

### Phase 3 : Opérations et surveillance (long terme)

Cette phase met en place la surveillance continue et les backups automatisés.

#### ☑ 3.1 Surveillance système avec AIDE

AIDE (Advanced Intrusion Detection Environment) détecte les modifications non autorisées de fichiers système.

```bash
# Installer AIDE
sudo apt install aide aide-common -y

# Initialiser la base de données (peut prendre 10-20 min)
sudo aideinit

# Déplacer la base de données
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Tester
sudo aide --check
```

**Automatiser les vérifications** :

```bash
sudo crontab -e
```

Ajouter :

```
0 4 * * * /usr/bin/aide --check | mail -s "AIDE Report $(hostname)" admin@votre-domaine.fr
```

---

#### ☑ 3.2 Backups automatisés et chiffrés

**A. Créer un script de backup**

Créer `/root/backup_observations.sh` :

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/root/backups"
PROJECT_DIR="/var/www/observations_nids"
DB_NAME="observations_nids"
DB_USER="django_app"
DB_PASS="<mot_de_passe>"
DATE=$(date +%F_%H%M)

# Créer le répertoire de backup
mkdir -p $BACKUP_DIR

# Backup base de données
echo "Backup de la base de données..."
mysqldump -u $DB_USER -p"$DB_PASS" $DB_NAME --single-transaction --routines --events \
  | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup fichiers médias
echo "Backup des fichiers médias..."
tar -czf $BACKUP_DIR/media_$DATE.tar.gz $PROJECT_DIR/media/

# Backup fichiers de configuration
echo "Backup des fichiers de configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  $PROJECT_DIR/.env \
  $PROJECT_DIR/observations_nids.wsgi \
  /etc/apache2/sites-available/observations_nids*.conf

# Chiffrement (optionnel mais recommandé)
echo "Chiffrement des backups..."
for file in $BACKUP_DIR/*_$DATE.*; do
  gpg --symmetric --cipher-algo AES256 --batch --yes --passphrase "<passphrase_forte>" "$file"
  rm "$file"  # Supprimer la version non chiffrée
done

# Nettoyage (garder 30 jours)
echo "Nettoyage des anciens backups..."
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete

echo "Backup terminé : $BACKUP_DIR"
```

Rendre exécutable :

```bash
sudo chmod 700 /root/backup_observations.sh
```

**B. Automatiser avec cron**

```bash
sudo crontab -e
```

Ajouter (backup quotidien à 3h du matin) :

```
0 3 * * * /root/backup_observations.sh >> /var/log/backup.log 2>&1
```

**C. Sauvegarder hors-site**

**Option 1 : Rsync vers un serveur distant**

```bash
# Ajouter à la fin du script de backup
rsync -avz --delete $BACKUP_DIR/ user@serveur-distant:/backups/observations_nids/
```

**Option 2 : Cloud (exemple avec rclone)**

```bash
# Installer rclone
sudo apt install rclone -y

# Configurer (suivre l'assistant)
rclone config

# Ajouter à la fin du script de backup
rclone sync $BACKUP_DIR remote:observations_nids_backups
```

**Vérification :**

```bash
# Exécuter manuellement
sudo /root/backup_observations.sh

# Vérifier les backups
ls -lh /root/backups/

# Tester la restauration (sur environnement de test)
gunzip -c /root/backups/db_<DATE>.sql.gz | mysql -u django_app -p observations_nids
```

---

#### ☑ 3.3 Accès admin via VPN (WireGuard)

Pour sécuriser davantage l'accès SSH, utilisez WireGuard pour créer un VPN.

**A. Installer WireGuard sur le Pi**

```bash
sudo apt install wireguard -y
```

**B. Générer les clés**

```bash
cd /etc/wireguard
umask 077
wg genkey | tee server_private.key | wg pubkey > server_public.key
```

**C. Configurer le serveur**

Créer `/etc/wireguard/wg0.conf` :

```ini
[Interface]
PrivateKey = <contenu_de_server_private.key>
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Client 1 (votre machine)
PublicKey = <clé_publique_du_client>
AllowedIPs = 10.0.0.2/32
```

**D. Démarrer WireGuard**

```bash
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

**E. Autoriser le port WireGuard dans UFW**

```bash
sudo ufw allow 51820/udp
```

**F. Restreindre SSH au VPN uniquement**

Modifier `/etc/ssh/sshd_config` :

```
ListenAddress 10.0.0.1
```

Redémarrer SSH :

```bash
sudo systemctl restart ssh
```

**Configuration client (votre machine) :**

- Installer WireGuard sur votre machine
- Générer une paire de clés client
- Configurer le fichier `wg0.conf` client
- Se connecter au VPN avant d'accéder au Pi en SSH

**Documentation complète :** [WireGuard Quick Start](https://www.wireguard.com/quickstart/)

---

#### ☑ 3.4 Tests de vulnérabilité

**A. Scan de ports avec Nmap**

```bash
# Installer Nmap
sudo apt install nmap -y

# Scanner les ports ouverts (depuis l'extérieur si possible)
sudo nmap -sS -sV -O votre-domaine.fr
```

Attendu : Seulement les ports 80, 443, et éventuellement 51820 (WireGuard) doivent être ouverts.

**B. Audit web avec Nikto**

```bash
# Installer Nikto
sudo apt install nikto -y

# Scanner
nikto -h https://votre-domaine.fr
```

Corriger les vulnérabilités détectées (en-têtes manquants, versions exposées, etc.).

**C. Test SSL avec SSLLabs**

Tester votre configuration SSL sur : [https://www.ssllabs.com/ssltest/](https://www.ssllabs.com/ssltest/)

Objectif : Note **A** ou **A+**.

**D. OWASP ZAP (optionnel)**

Pour un audit complet de sécurité applicative, utiliser OWASP ZAP :

```bash
# Installer via Docker
docker run -u zap -p 8080:8080 -p 8090:8090 \
  -i owasp/zap2docker-stable zap-webswing.sh
```

---

## Maintenance régulière

### Checklist hebdomadaire

- [ ] Vérifier les logs d'erreur Apache : `sudo tail -n 100 /var/log/apache2/observations_nids_error.log`
- [ ] Vérifier les logs Django : `sudo tail -n 100 /var/log/observations_nids/django.log`
- [ ] Vérifier Fail2Ban : `sudo fail2ban-client status`
- [ ] Vérifier l'espace disque : `df -h`
- [ ] Vérifier les mises à jour disponibles : `sudo apt list --upgradable`

### Checklist mensuelle

- [ ] Vérifier les backups : tester une restauration sur environnement de test
- [ ] Audit de sécurité des dépendances : `pip-audit`
- [ ] Vérifier les certificats SSL : `sudo certbot certificates`
- [ ] Analyser les logs d'accès Apache pour détecter des comportements suspects
- [ ] Vérifier AIDE : `sudo aide --check`

### Checklist trimestrielle

- [ ] Scan de vulnérabilité complet (Nmap, Nikto, OWASP ZAP)
- [ ] Révision des permissions et utilisateurs système
- [ ] Mise à jour majeure de Django et des dépendances (après tests)
- [ ] Audit de performance (temps de réponse, utilisation CPU/RAM)

---

## Annexes

### A. Checklist complète de déploiement

**Phase 1 - Sécurisation (obligatoire) :**
- [ ] Sauvegarde initiale effectuée
- [ ] Système à jour + mises à jour automatiques
- [ ] Utilisateur admin créé avec accès SSH par clé
- [ ] SSH sécurisé (no root, no password)
- [ ] MariaDB sécurisé (`mysql_secure_installation`)
- [ ] Pare-feu UFW configuré et actif
- [ ] Fail2Ban installé et configuré
- [ ] Fichier `.env` créé avec SECRET_KEY

**Phase 2 - Déploiement :**
- [ ] Code cloné depuis Git (branche `production`)
- [ ] Environnement virtuel Python créé
- [ ] Dépendances installées (`requirements-prod.txt`)
- [ ] Base de données MariaDB créée
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Apache configuré (VirtualHost + mod_wsgi)
- [ ] Super-utilisateur créé

**Phase 3 - Vérification :**
- [ ] Accès web fonctionnel (HTTP)
- [ ] Interface admin accessible
- [ ] Redis et Celery fonctionnels
- [ ] Logs Apache sans erreurs
- [ ] Commande `manage.py check` sans erreurs

**Phase 4 - Sécurité avancée :**
- [ ] HTTPS configuré (Let's Encrypt)
- [ ] En-têtes de sécurité HTTP activés
- [ ] MariaDB en écoute locale uniquement
- [ ] Logs rotatifs configurés
- [ ] Dépendances auditées (pip-audit)

**Phase 5 - Opérations :**
- [ ] AIDE installé et initialisé
- [ ] Backups automatisés configurés
- [ ] Backup testé (restauration)
- [ ] VPN WireGuard configuré (optionnel)
- [ ] Tests de vulnérabilité effectués

---

### B. Scripts utiles

#### Script de vérification santé système

Créer `/root/check_health.sh` :

```bash
#!/bin/bash

echo "=== État des services ==="
systemctl is-active apache2 redis-server mariadb fail2ban ufw

echo -e "\n=== Espace disque ==="
df -h / /var

echo -e "\n=== Utilisation mémoire ==="
free -h

echo -e "\n=== Charge CPU ==="
uptime

echo -e "\n=== Fail2Ban ==="
fail2ban-client status | grep "Jail list"

echo -e "\n=== Certificats SSL ==="
certbot certificates 2>/dev/null | grep -E "Certificate Name|Expiry Date"

echo -e "\n=== Mises à jour disponibles ==="
apt list --upgradable 2>/dev/null | grep -v "Listing"

echo -e "\n=== Logs Apache (dernières erreurs) ==="
tail -n 5 /var/log/apache2/observations_nids_error.log
```

Rendre exécutable :

```bash
sudo chmod +x /root/check_health.sh
```

Exécuter :

```bash
sudo /root/check_health.sh
```

---

### C. Commandes de dépannage

#### Apache ne démarre pas

```bash
# Vérifier la configuration
sudo apachectl configtest

# Vérifier les logs
sudo tail -n 50 /var/log/apache2/error.log

# Vérifier les ports occupés
sudo netstat -tuln | grep :80
sudo netstat -tuln | grep :443

# Redémarrer Apache
sudo systemctl restart apache2
```

#### Erreur 500 (Internal Server Error)

```bash
# Vérifier les logs Django
sudo tail -n 100 /var/log/observations_nids/django.log

# Vérifier les logs Apache
sudo tail -n 100 /var/log/apache2/observations_nids_error.log

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/observations_nids
sudo chmod -R 755 /var/www/observations_nids
sudo chmod 600 /var/www/observations_nids/.env

# Tester Django directement
cd /var/www/observations_nids
sudo -u www-data .venv/bin/python manage.py check
sudo -u www-data .venv/bin/python manage.py runserver 0.0.0.0:8001
```

#### Base de données corrompue

```bash
# Vérifier l'intégrité de MariaDB
sudo mysqlcheck -u root -p --all-databases

# Réparer une base
sudo mysqlcheck -u root -p --repair observations_nids

# Restaurer depuis backup
sudo mysql -u root -p observations_nids < /root/backups/db_<DATE>.sql
```

#### Celery ne traite pas les tâches

```bash
# Vérifier Redis
redis-cli ping

# Vérifier les workers Celery
ps aux | grep celery

# Redémarrer Celery (si systemd service configuré)
sudo systemctl restart celery

# Voir les tâches en attente
cd /var/www/observations_nids
source .venv/bin/activate
celery -A observations_nids inspect active
celery -A observations_nids inspect scheduled
```

---

### D. Configuration Celery en tant que service systemd

Pour que Celery démarre automatiquement au boot, créer un service systemd.

**Créer `/etc/systemd/system/celery.service` :**

```ini
[Unit]
Description=Celery Worker pour Observations Nids
After=network.target redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids
Environment="PATH=/var/www/observations_nids/.venv/bin"
ExecStart=/var/www/observations_nids/.venv/bin/celery -A observations_nids worker --loglevel=info --logfile=/var/log/observations_nids/celery.log --pidfile=/var/run/celery.pid --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Activer et démarrer le service :**

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

---

### E. Ressources et liens utiles

**Documentation officielle :**
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Apache mod_wsgi Documentation](https://modwsgi.readthedocs.io/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Fail2Ban Manual](https://www.fail2ban.org/wiki/index.php/MANUAL_0_8)
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/)

**Outils de sécurité :**
- [SSL Server Test (Qualys)](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

**Communautés :**
- [Django Forum](https://forum.djangoproject.com/)
- [Stack Overflow - Django Tag](https://stackoverflow.com/questions/tagged/django)
- [Reddit - r/django](https://www.reddit.com/r/django/)

---

## Conclusion

Ce guide vous a accompagné pour :

1. ✅ Sécuriser votre Raspberry Pi (Phase 1 obligatoire)
2. ✅ Déployer l'application Observations Nids (automatisé ou manuel)
3. ✅ Vérifier le bon fonctionnement (checklist post-déploiement)
4. ✅ Mettre en place HTTPS et le renforcement avancé (Phase 2)
5. ✅ Configurer la surveillance et les backups (Phase 3)

**Prochaines étapes :**

- Charger les données taxonomiques : `python manage.py charger_lof`
- Charger les communes françaises : `python manage.py charger_communes_france`
- Créer des utilisateurs de test
- Tester le workflow de transcription OCR
- Consulter la [documentation fonctionnelle](../guides/fonctionnalites/)

**Support :**

- Documentation du projet : `/docs/`
- Issues GitHub : [https://github.com/jmFschneider/Observations_Nids/issues](https://github.com/jmFschneider/Observations_Nids/issues)

---

**Document créé le** : 11 octobre 2025
**Dernière mise à jour** : 24 octobre 2025
**Version** : 2.0 (consolidé JOUR 3 - sécurité + déploiement)
**Auteurs** : Jean-Marc Schneider, Claude Code
