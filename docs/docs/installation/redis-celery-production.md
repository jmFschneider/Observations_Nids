# Mise en place de Redis et Celery en Production (Raspberry Pi)

Ce document détaille l'installation, la configuration et la sécurisation de Redis et Celery pour le projet Observations Nids sur un serveur Raspberry Pi en production.

## Table des matières

1. [Introduction](#introduction)
2. [Prérequis](#prérequis)
3. [Installation de Redis](#installation-de-redis)
4. [Configuration de Redis](#configuration-de-redis)
5. [Installation et configuration de Celery](#installation-et-configuration-de-celery)
6. [Gestion des services avec systemd](#gestion-des-services-avec-systemd)
7. [Sécurisation de Redis et Celery](#sécurisation-de-redis-et-celery)
8. [Monitoring et maintenance](#monitoring-et-maintenance)
9. [Dépannage](#dépannage)

---

## Introduction

**Redis** est utilisé comme broker de messages pour Celery, permettant la gestion asynchrone des tâches longues (importation de données, traitement OCR, envoi d'emails, etc.).

**Celery** est le système de files d'attente de tâches asynchrones qui permet d'exécuter des traitements en arrière-plan sans bloquer l'interface utilisateur Django.

### Architecture

```
Django Application
       ↓
   Celery Tasks
       ↓
   Redis Broker ←→ Celery Workers
       ↓
   Task Results (Redis)
```

---

## Prérequis

- Raspberry Pi avec Raspberry Pi OS (Debian-based)
- Accès SSH au serveur
- Utilisateur avec privilèges sudo
- Python 3.12+ installé
- Projet Django déployé dans `/var/www/observations_nids/`

---

## Installation de Redis

### 1. Installation via apt

Redis est disponible dans les dépôts officiels de Raspberry Pi OS :

```bash
sudo apt update
sudo apt install redis-server -y
```

### 2. Vérification de l'installation

```bash
redis-server --version
# Devrait afficher : Redis server v=x.x.x
```

### 3. Vérification du service

```bash
sudo systemctl status redis-server
```

Redis devrait démarrer automatiquement après l'installation.

---

## Configuration de Redis

### 1. Fichier de configuration principal

Le fichier de configuration Redis se trouve dans `/etc/redis/redis.conf`. Effectuez les modifications suivantes :

```bash
sudo nano /etc/redis/redis.conf
```

### 2. Configuration de base pour la production

#### a. Limitation de l'écoute réseau (SÉCURITÉ CRITIQUE)

Par défaut, Redis écoute sur toutes les interfaces. **Limitez-le à localhost uniquement** :

```conf
# Cherchez la ligne "bind" et modifiez-la :
bind 127.0.0.1 ::1

# Assurez-vous que le mode protégé est activé :
protected-mode yes
```

Cette configuration garantit que Redis n'est accessible que depuis le serveur local, **empêchant toute connexion externe**.

#### b. Définir un mot de passe (SÉCURITÉ CRITIQUE)

Ajoutez un mot de passe fort pour authentifier les connexions :

```conf
# Cherchez la directive "requirepass" et décommentez/modifiez :
requirepass VOTRE_MOT_DE_PASSE_FORT_ICI
```

**Générez un mot de passe fort** :

```bash
openssl rand -base64 32
```

#### c. Persistance des données

Redis peut persister les données sur disque. Pour un Raspberry Pi, utilisez un mode équilibré :

```conf
# Sauvegardes RDB (snapshots)
save 900 1      # Sauvegarde après 900s si au moins 1 clé a changé
save 300 10     # Sauvegarde après 300s si au moins 10 clés ont changé
save 60 10000   # Sauvegarde après 60s si au moins 10000 clés ont changé

# Emplacement du fichier RDB
dir /var/lib/redis

# Nom du fichier
dbfilename dump.rdb

# Compression
rdbcompression yes
```

#### d. Limites mémoire (important pour Raspberry Pi)

Le Raspberry Pi a une RAM limitée. Configurez Redis pour éviter la surcharge :

```conf
# Limite mémoire maximale (ajustez selon votre RAM disponible)
maxmemory 256mb

# Politique d'éviction quand maxmemory est atteinte
maxmemory-policy allkeys-lru
```

#### e. Logging

```conf
# Niveau de log
loglevel notice

# Fichier de log
logfile /var/log/redis/redis-server.log
```

### 3. Redémarrer Redis pour appliquer les modifications

```bash
sudo systemctl restart redis-server
sudo systemctl status redis-server
```

### 4. Tester la connexion avec mot de passe

```bash
redis-cli

# Dans le CLI Redis :
AUTH VOTRE_MOT_DE_PASSE_FORT_ICI
PING
# Devrait retourner : PONG

# Quitter
exit
```

---

## Installation et configuration de Celery

### 1. Installation des dépendances Python

Celery et ses dépendances sont déjà listées dans `requirements-base.txt` :

```bash
cd /var/www/observations_nids/
source venv/bin/activate
pip install -r requirements-prod.txt
```

Les packages installés incluent :
- `celery==5.5.3`
- `redis==5.2.1`
- `django-celery-results==2.6.0`
- `flower==2.0.0` (monitoring interface)

### 2. Configuration de Celery dans Django

Le projet utilise déjà la configuration centralisée via Pydantic. Mettez à jour le fichier `.env` en production :

```bash
sudo nano /var/www/observations_nids/.env
```

Ajoutez/modifiez les lignes suivantes :

```env
# Configuration Celery
CELERY__BROKER_URL=redis://127.0.0.1:6379/0
CELERY__RESULT_BACKEND=redis://127.0.0.1:6379/0
```

**Si vous avez défini un mot de passe Redis**, utilisez ce format :

```env
CELERY__BROKER_URL=redis://:VOTRE_MOT_DE_PASSE@127.0.0.1:6379/0
CELERY__RESULT_BACKEND=redis://:VOTRE_MOT_DE_PASSE@127.0.0.1:6379/0
```

### 3. Configuration existante

Le fichier `observations_nids/celery.py` est déjà configuré correctement :

```python
# observations_nids/celery.py
app = Celery('observations_nids')

app.conf.update(
    broker_url=settings.celery.broker_url,
    result_backend=settings.celery.result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_acks_late=True,  # Robustesse
    task_default_retry_delay=30,
)
```

### 4. Test de la connexion Celery-Redis

```bash
cd /var/www/observations_nids/
source venv/bin/activate

# Test de la configuration
python -c "from observations_nids.celery import app; print(app.conf.broker_url)"

# Lancer un worker Celery en mode test
celery -A observations_nids worker --loglevel=info
```

Appuyez sur `Ctrl+C` pour arrêter après avoir vérifié que le worker démarre correctement.

---

## Gestion des services avec systemd

Pour une exécution permanente en production, créez des services systemd pour Celery.

### 1. Service Celery Worker

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

### 2. Service Celery Beat (planificateur de tâches périodiques)

Si vous avez des tâches planifiées (cron-like), créez un service Beat :

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

# Sécurité
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### 3. Créer le répertoire pour les PID files

```bash
sudo mkdir -p /var/run/celery
sudo chown www-data:www-data /var/run/celery
```

### 4. Créer le répertoire pour les logs

```bash
sudo mkdir -p /var/www/observations_nids/logs
sudo chown www-data:www-data /var/www/observations_nids/logs
```

### 5. Activer et démarrer les services

```bash
# Recharger systemd pour prendre en compte les nouveaux services
sudo systemctl daemon-reload

# Activer le démarrage automatique
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat  # Si vous l'avez créé

# Démarrer les services
sudo systemctl start celery-worker
sudo systemctl start celery-beat  # Si vous l'avez créé

# Vérifier le statut
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

### 6. Commandes de gestion

```bash
# Redémarrer le worker (après un déploiement)
sudo systemctl restart celery-worker

# Voir les logs en temps réel
sudo journalctl -u celery-worker -f

# Arrêter le service
sudo systemctl stop celery-worker
```

---

## Sécurisation de Redis et Celery

### 1. Principe de défense en profondeur

La sécurisation de Redis et Celery repose sur plusieurs couches de protection pour éviter toute intrusion ou compromission du système.

### 2. Sécurité réseau

#### a. Firewall (ufw)

Assurez-vous que Redis **n'est accessible que localement** :

```bash
# Vérifier le statut du firewall
sudo ufw status

# Si Redis écoute sur le port 6379, ne PAS ouvrir ce port :
# NE PAS FAIRE : sudo ufw allow 6379

# Vérifier que le port n'est pas ouvert
sudo ufw status | grep 6379
# Ne devrait rien retourner

# Autoriser uniquement SSH, HTTP et HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### b. Vérification de l'écoute réseau

```bash
# Vérifier que Redis écoute UNIQUEMENT sur localhost
sudo netstat -tlnp | grep redis
# Devrait afficher : 127.0.0.1:6379 ou ::1:6379

# Ou avec ss (outil plus moderne)
sudo ss -tlnp | grep redis
```

**Résultat attendu** :

```
tcp   LISTEN   0   511   127.0.0.1:6379   0.0.0.0:*   users:(("redis-server",pid=...))
```

Si vous voyez `0.0.0.0:6379` ou `:::6379`, **c'est un problème de sécurité critique** ! Retournez à la configuration Redis et corrigez la directive `bind`.

### 3. Authentification forte

#### a. Mot de passe Redis

Comme configuré précédemment, utilisez **toujours** un mot de passe fort :

```conf
# /etc/redis/redis.conf
requirepass VOTRE_MOT_DE_PASSE_FORT
```

Critères d'un mot de passe fort :
- Longueur minimale : 32 caractères
- Mélange de caractères alphanumériques et symboles
- Généré aléatoirement (pas de mots du dictionnaire)

```bash
# Génération d'un mot de passe fort
openssl rand -base64 48
```

#### b. Protection du fichier .env

Le fichier `.env` contient le mot de passe Redis. Protégez-le :

```bash
# Permissions restrictives
sudo chmod 600 /var/www/observations_nids/.env
sudo chown www-data:www-data /var/www/observations_nids/.env

# Vérification
ls -la /var/www/observations_nids/.env
# Devrait afficher : -rw------- 1 www-data www-data
```

### 4. Isolation des processus

#### a. Utilisateur dédié

Redis et Celery s'exécutent sous des utilisateurs dédiés non-privilégiés :

- Redis : utilisateur `redis` (créé automatiquement)
- Celery : utilisateur `www-data` (même que Gunicorn/Django)

Vérification :

```bash
# Vérifier l'utilisateur Redis
ps aux | grep redis-server
# Devrait montrer : redis ... redis-server

# Vérifier l'utilisateur Celery
ps aux | grep celery
# Devrait montrer : www-data ... celery
```

#### b. Restrictions systemd

Les services systemd incluent des directives de sécurité :

```ini
# Dans /etc/systemd/system/celery-worker.service
PrivateTmp=true          # Isolation du répertoire /tmp
NoNewPrivileges=true     # Empêche l'escalade de privilèges
```

Pour renforcer davantage (optionnel mais recommandé) :

```ini
[Service]
# Isolation réseau (si Celery n'a pas besoin d'accès réseau externe)
# PrivateNetwork=true  # À activer uniquement si pas d'API externes

# Restrictions d'accès au système de fichiers
ReadOnlyPaths=/
ReadWritePaths=/var/www/observations_nids/media
ReadWritePaths=/var/www/observations_nids/logs
ReadWritePaths=/var/run/celery

# Restrictions d'appels système
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

# Empêcher l'accès au kernel
ProtectKernelModules=true
ProtectKernelTunables=true
```

### 5. Chiffrement des communications

#### a. Redis local

Pour Redis en `localhost`, le chiffrement TLS n'est pas strictement nécessaire car les données ne transitent jamais sur le réseau. Cependant, si vous souhaitez une sécurité maximale :

```conf
# /etc/redis/redis.conf
# Activer TLS (nécessite des certificats)
tls-port 6380
tls-cert-file /etc/redis/certs/redis.crt
tls-key-file /etc/redis/certs/redis.key
tls-ca-cert-file /etc/redis/certs/ca.crt
```

**Note** : Pour un Raspberry Pi en production locale, cette étape est **optionnelle** si Redis reste sur `127.0.0.1`.

### 6. Monitoring et détection d'intrusion

#### a. Logs Redis

Surveillez les tentatives de connexion suspectes :

```bash
# Voir les logs Redis
sudo tail -f /var/log/redis/redis-server.log

# Rechercher les échecs d'authentification
sudo grep "Authentication" /var/log/redis/redis-server.log
```

#### b. Fail2ban (optionnel)

Installez Fail2ban pour bannir automatiquement les IPs suspectes :

```bash
sudo apt install fail2ban
```

Créez un filtre pour Redis :

```bash
sudo nano /etc/fail2ban/filter.d/redis-auth.conf
```

Contenu :

```ini
[Definition]
failregex = ^.*\[error\] WRONGPASS invalid username-password pair.*$
ignoreregex =
```

Ajoutez une jail :

```bash
sudo nano /etc/fail2ban/jail.local
```

Contenu :

```ini
[redis-auth]
enabled = true
port = 6379
filter = redis-auth
logpath = /var/log/redis/redis-server.log
maxretry = 3
bantime = 3600
```

Redémarrez Fail2ban :

```bash
sudo systemctl restart fail2ban
```

### 7. Sauvegardes sécurisées

#### a. Sauvegardes Redis automatiques

Créez un script de sauvegarde :

```bash
sudo nano /usr/local/bin/backup-redis.sh
```

Contenu :

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Déclencher une sauvegarde RDB
redis-cli -a "VOTRE_MOT_DE_PASSE" BGSAVE

# Attendre que la sauvegarde soit terminée
sleep 5

# Copier le dump.rdb
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/dump_$DATE.rdb"

# Conserver seulement les 7 dernières sauvegardes
find "$BACKUP_DIR" -name "dump_*.rdb" -mtime +7 -delete

echo "Sauvegarde Redis terminée : dump_$DATE.rdb"
```

Permissions :

```bash
sudo chmod +x /usr/local/bin/backup-redis.sh
```

Planification avec cron :

```bash
sudo crontab -e
```

Ajoutez :

```cron
# Sauvegarde Redis quotidienne à 2h du matin
0 2 * * * /usr/local/bin/backup-redis.sh >> /var/log/redis-backup.log 2>&1
```

#### b. Protection des sauvegardes

```bash
sudo chmod 700 /var/backups/redis
sudo chown redis:redis /var/backups/redis
```

### 8. Mise à jour régulière

Maintenez Redis à jour pour bénéficier des correctifs de sécurité :

```bash
# Mises à jour système
sudo apt update
sudo apt upgrade redis-server

# Redémarrer après mise à jour
sudo systemctl restart redis-server
```

### 9. Désactivation des commandes dangereuses

Redis permet de désactiver des commandes potentiellement dangereuses :

```conf
# /etc/redis/redis.conf

# Désactiver les commandes dangereuses
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
rename-command DEBUG ""
```

**Important** : Après cette modification, ces commandes ne seront plus disponibles, même pour les administrateurs. Utilisez avec précaution.

### 10. Checklist de sécurité

- [ ] Redis écoute uniquement sur `127.0.0.1` (vérifier avec `netstat`)
- [ ] Mot de passe Redis fort (32+ caractères)
- [ ] Firewall (ufw) activé, port 6379 non exposé
- [ ] Fichier `.env` avec permissions `600`
- [ ] Services Celery exécutés sous utilisateur non-privilégié (`www-data`)
- [ ] Logs Redis surveillés régulièrement
- [ ] Sauvegardes Redis automatiques configurées
- [ ] Redis et Celery à jour (dernières versions stables)
- [ ] Protected mode activé dans Redis
- [ ] Commandes Redis dangereuses désactivées (optionnel)

---

## Monitoring et maintenance

### 1. Interface de monitoring : Flower

Flower est une interface web pour surveiller Celery.

#### Installation

Déjà inclus dans `requirements-base.txt` (`flower==2.0.0`).

#### Service systemd pour Flower

```bash
sudo nano /etc/systemd/system/celery-flower.service
```

Contenu :

```ini
[Unit]
Description=Flower - Celery Monitoring Interface
After=network.target redis-server.service celery-worker.service
Wants=redis-server.service celery-worker.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/observations_nids
EnvironmentFile=/var/www/observations_nids/.env

ExecStart=/var/www/observations_nids/venv/bin/celery -A observations_nids flower \
    --port=5555 \
    --address=127.0.0.1 \
    --basic_auth=admin:VOTRE_MOT_DE_PASSE_FLOWER

Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**Sécurité importante** :
- Flower écoute sur `127.0.0.1` uniquement
- Authentification HTTP Basic activée
- Accès via reverse proxy Nginx (voir ci-dessous)

#### Activation du service

```bash
sudo systemctl enable celery-flower
sudo systemctl start celery-flower
sudo systemctl status celery-flower
```

#### Configuration Nginx pour Flower

Ajoutez dans votre configuration Nginx :

```nginx
# /etc/nginx/sites-available/observations_nids

location /flower/ {
    proxy_pass http://127.0.0.1:5555/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Authentification supplémentaire via Nginx (optionnel)
    auth_basic "Flower Monitoring";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

Rechargez Nginx :

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Accédez à Flower via : `https://votre-domaine.com/flower/`

### 2. Commandes de monitoring

#### Redis

```bash
# Connexion au CLI Redis
redis-cli -a VOTRE_MOT_DE_PASSE

# Informations générales
INFO

# Statistiques
INFO stats

# Mémoire utilisée
INFO memory

# Clients connectés
CLIENT LIST

# Nombre de clés
DBSIZE

# Quitter
exit
```

#### Celery

```bash
# Voir les workers actifs
celery -A observations_nids inspect active

# Voir les tâches planifiées
celery -A observations_nids inspect scheduled

# Statistiques des workers
celery -A observations_nids inspect stats

# Voir les tâches enregistrées
celery -A observations_nids inspect registered
```

### 3. Logs

```bash
# Logs Celery Worker
sudo tail -f /var/www/observations_nids/logs/celery-worker.log

# Logs Celery Beat
sudo tail -f /var/www/observations_nids/logs/celery-beat.log

# Logs Redis
sudo tail -f /var/log/redis/redis-server.log

# Logs systemd
sudo journalctl -u celery-worker -f
sudo journalctl -u redis-server -f
```

### 4. Rotation des logs

Créez un fichier logrotate pour Celery :

```bash
sudo nano /etc/logrotate.d/celery
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
        systemctl reload celery-worker celery-beat > /dev/null 2>&1 || true
    endscript
}
```

---

## Dépannage

### Problème : Celery ne se connecte pas à Redis

**Symptômes** : Erreur `redis.exceptions.ConnectionError` dans les logs Celery.

**Solutions** :

1. Vérifier que Redis est démarré :

```bash
sudo systemctl status redis-server
```

2. Vérifier la connexion locale :

```bash
redis-cli -a VOTRE_MOT_DE_PASSE PING
```

3. Vérifier la configuration dans `.env` :

```bash
cat /var/www/observations_nids/.env | grep CELERY
```

4. Vérifier que le mot de passe est correct :

```bash
# Test de connexion avec le mot de passe du .env
redis-cli -a "$(grep BROKER_URL /var/www/observations_nids/.env | cut -d: -f3 | cut -d@ -f1)" PING
```

### Problème : Les tâches ne s'exécutent pas

**Symptômes** : Les tâches restent en statut `PENDING`.

**Solutions** :

1. Vérifier que le worker est actif :

```bash
sudo systemctl status celery-worker
```

2. Voir les workers connectés :

```bash
celery -A observations_nids inspect active
```

3. Redémarrer le worker :

```bash
sudo systemctl restart celery-worker
```

4. Vérifier les logs :

```bash
sudo journalctl -u celery-worker -n 50
```

### Problème : Redis consomme trop de mémoire

**Symptômes** : Le Raspberry Pi devient lent ou plante.

**Solutions** :

1. Vérifier l'utilisation mémoire :

```bash
redis-cli -a VOTRE_MOT_DE_PASSE INFO memory
```

2. Réduire la limite `maxmemory` dans `/etc/redis/redis.conf` :

```conf
maxmemory 128mb
```

3. Activer la politique d'éviction :

```conf
maxmemory-policy allkeys-lru
```

4. Redémarrer Redis :

```bash
sudo systemctl restart redis-server
```

### Problème : Tâches en timeout

**Symptômes** : `TimeLimitExceeded` dans les logs.

**Solutions** :

1. Augmenter le timeout dans `observations_nids/celery.py` :

```python
task_time_limit = 60 * 60  # 60 minutes au lieu de 30
```

2. Redémarrer Celery :

```bash
sudo systemctl restart celery-worker
```

### Problème : Permissions refusées pour Celery

**Symptômes** : `PermissionError` dans les logs.

**Solutions** :

1. Vérifier les permissions des dossiers :

```bash
ls -la /var/www/observations_nids/logs/
ls -la /var/run/celery/
```

2. Corriger les permissions :

```bash
sudo chown -R www-data:www-data /var/www/observations_nids/logs/
sudo chown -R www-data:www-data /var/run/celery/
```

---

## Résumé

Cette configuration assure un déploiement sécurisé et robuste de Redis et Celery sur Raspberry Pi :

- **Redis** : Isolé sur localhost, protégé par mot de passe, limité en mémoire
- **Celery** : Géré par systemd, logs centralisés, monitoring via Flower
- **Sécurité** : Firewall, authentification forte, isolation des processus, sauvegardes automatiques
- **Monitoring** : Flower pour Celery, redis-cli et logs pour Redis

**Commandes de déploiement rapide** :

```bash
# Démarrer tous les services
sudo systemctl start redis-server celery-worker celery-beat celery-flower

# Vérifier le statut
sudo systemctl status redis-server celery-worker

# Voir les logs
sudo journalctl -u celery-worker -f
```

Pour toute question ou problème, consultez les logs et la section [Dépannage](#dépannage).
