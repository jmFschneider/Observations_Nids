# Architecture Docker - Observations Nids & Nextcloud

**Date de création** : 24 décembre 2025
**Projet** : Observations Nids - Gestion des observations ornithologiques
**Version** : 1.0

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Docker - Observations Nids](#architecture-docker---observations-nids)
3. [Architecture Nextcloud](#architecture-nextcloud)
4. [Relations et intégrations](#relations-et-intégrations)
5. [Système de surveillance inotify](#système-de-surveillance-inotify)
6. [Flux de données](#flux-de-données)
7. [Référence des commandes](#référence-des-commandes)

---

## Vue d'ensemble

Le projet **Observations Nids** est déployé dans une architecture **multi-conteneurs Docker** comprenant :

- **Application Django** (web + Celery workers) pour la gestion des observations
- **Base de données MariaDB** pour le stockage des données
- **Redis** pour le cache et le broker Celery
- **Nginx** comme reverse proxy
- **Nextcloud** (instance séparée) pour le stockage et la synchronisation des fichiers media

### Schéma de l'architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                         Serveur Ubuntu                          │
│  /opt/observations_nids_pilote/                                 │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        Docker Compose - Observations Nids              │    │
│  │                                                        │    │
│  │  ┌─────────┐  ┌─────────┐  ┌────────────┐           │    │
│  │  │  Nginx  │  │   Web   │  │   Celery   │           │    │
│  │  │  :8010  │─▶│ Django  │─▶│   Worker   │           │    │
│  │  └─────────┘  └─────────┘  └────────────┘           │    │
│  │       │           │  │            │                   │    │
│  │       │           │  │            │                   │    │
│  │       ▼           ▼  ▼            ▼                   │    │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐             │    │
│  │  │ MariaDB │  │  Redis  │  │  Flower  │             │    │
│  │  └─────────┘  └─────────┘  └──────────┘             │    │
│  │                                                        │    │
│  │  Volumes partagés:                                    │    │
│  │  • /app/media → /opt/.../media (bind mount)           │    │
│  │  • db_data (volume Docker)                            │    │
│  │  • redis_data (volume Docker)                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        Docker Compose - Nextcloud                      │    │
│  │                                                        │    │
│  │  ┌──────────────┐     ┌─────────────┐                │    │
│  │  │  Nextcloud   │────▶│  MariaDB    │                │    │
│  │  │     App      │     │ (Nextcloud) │                │    │
│  │  └──────────────┘     └─────────────┘                │    │
│  │         │                                              │    │
│  │         │ Stockage externe                            │    │
│  │         ▼                                              │    │
│  └─────────┼──────────────────────────────────────────────┘    │
│            │                                                    │
│  ┌─────────▼──────────────────────────────────────────────┐    │
│  │   /opt/observations_nids_pilote/media/                 │    │
│  │                                                        │    │
│  │   ├── jpeg/                                           │    │
│  │   ├── pdf/                                            │    │
│  │   └── transcription_results/  ◀── Surveillé par       │    │
│  │       └── [répertoires]/          inotify             │    │
│  │           └── [modèles]/                              │    │
│  │               └── *.json                              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │   Service systemd - inotify watcher                    │    │
│  │                                                        │    │
│  │   Surveille: /opt/.../media/                           │    │
│  │   Déclenche: docker exec nextcloud occ files:scan      │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Docker - Observations Nids

### Localisation

- **Chemin** : `/opt/observations_nids_pilote/`
- **Configuration Docker** : `/opt/observations_nids_pilote/docker/docker-compose.yml`

### Services Docker

#### 1. Base de données (MariaDB 10.11)

```yaml
Container: observations_db
Image: mariadb:10.11
Ports: 3306 (interne)
Volume: db_data:/var/lib/mysql
Healthcheck: mysqladmin ping
```

**Rôle** : Stockage des données de l'application (observations, utilisateurs, espèces, etc.)

#### 2. Redis

```yaml
Container: observations_redis
Image: redis:7-alpine
Ports: 6379 (interne)
Volume: redis_data:/data
```

**Rôle** :
- Cache de l'application Django
- Broker pour les tâches Celery
- Backend de résultats Celery

#### 3. Application Web (Django + Gunicorn)

```yaml
Container: observations_web
Build: Dockerfile personnalisé
Ports: 8000 (interne)
Volumes:
  - /opt/.../media:/app/media
  - static_volume:/app/staticfiles
  - ../logs:/app/logs
```

**Rôle** : Application Django principale avec Gunicorn (4 workers)

**Points clés** :
- Utilisateur dans le conteneur : `django` (UID 999, GID 999)
- MEDIA_ROOT : `/app/media` (monté depuis l'hôte)
- Configuration : Variables d'environnement depuis `.env`

#### 4. Celery Worker

```yaml
Container: observations_celery_worker
Build: Dockerfile personnalisé
Concurrency: 2 workers
Volumes:
  - /opt/.../media:/app/media
  - ../logs:/app/logs
```

**Rôle** : Traitement des tâches asynchrones
- Transcription OCR avec Gemini API
- Import de données
- Tâches planifiées

**Tâches principales** :
- `process_batch_transcription_task` : Transcription batch de fiches scannées
- Génération de fichiers JSON dans `/app/media/transcription_results/`

#### 5. Celery Beat

```yaml
Container: observations_celery_beat
Build: Dockerfile personnalisé
```

**Rôle** : Planificateur de tâches périodiques

#### 6. Flower

```yaml
Container: observations_flower
Ports: 5555:5555
```

**Rôle** : Interface de monitoring Celery (accessible sur http://serveur:5555)

#### 7. Nginx

```yaml
Container: observations_nginx
Image: nginx:alpine
Ports: 8010:80
Volumes:
  - static_volume:/app/staticfiles:ro
  - /opt/.../media:/app/media:ro
  - ./nginx/conf.d:/etc/nginx/conf.d:ro
```

**Rôle** : Reverse proxy et serveur de fichiers statiques

**Configuration importante** :
```nginx
location /media/ {
    alias /app/media/;
    expires 7d;
}
```

#### 8. phpMyAdmin

```yaml
Container: observations_phpmyadmin
Ports: 8081:80
```

**Rôle** : Interface d'administration de la base de données

### Volumes Docker

| Volume | Type | Utilisation |
|--------|------|-------------|
| `db_data` | Volume nommé | Données MariaDB (persistant) |
| `redis_data` | Volume nommé | Données Redis (persistant) |
| `static_volume` | Volume nommé | Fichiers statiques Django |
| `/opt/.../media` | Bind mount | **Fichiers media partagés avec Nextcloud** |
| `../logs` | Bind mount | Logs de l'application |

### Réseau

- **Réseau Docker** : `observations_network` (bridge)
- **Communication** : Tous les services communiquent via le réseau interne
- **Exposition externe** : Seuls Nginx (8010) et Flower (5555) sont accessibles depuis l'extérieur

---

## Architecture Nextcloud

### Localisation

- **Conteneur** : `nextcloud-app-1`
- **Installation** : Docker Compose séparé (isolation par rapport à UR Backup)

### Configuration du stockage externe

Nextcloud est configuré avec un **stockage externe** pointant vers :

```
Hôte : /opt/observations_nids_pilote/media/
Dans Nextcloud : /schneider/files/Observations Media/
```

**Type de stockage** : Stockage local externe
**Utilisateur** : schneider
**Permissions** : Lecture/Écriture

### Structure des fichiers dans Nextcloud

```
Observations Media/
├── jpeg/
│   ├── TRI_ANCIEN/
│   │   ├── FUSION_FULL/
│   │   ├── binarisation/
│   │   └── blur/
│   ├── TRI_NOUVEAU/
│   └── TRI_INCERTAIN/
├── pdf/
└── transcription_results/         ← Créé automatiquement par Celery
    └── jpeg/
        └── TRI_ANCIEN/
            └── FUSION_FULL/
                └── gemini_3_flash/
                    ├── fiche 25FINAL_result.json
                    ├── fiche 26FINAL_result.json
                    └── fiche 27FINAL_result.json
```

### Permissions critiques

Pour que Nextcloud et Django/Celery puissent accéder aux fichiers :

```bash
# Le répertoire media appartient à l'utilisateur django du conteneur
sudo chown -R 999:www-data /opt/observations_nids_pilote/media/
sudo chmod -R 775 /opt/observations_nids_pilote/media/
```

**Explication** :
- `999` : UID de l'utilisateur `django` dans le conteneur
- `www-data` : Groupe pour compatibilité avec Nextcloud
- `775` : Lecture/écriture pour propriétaire et groupe

---

## Relations et intégrations

### 1. Partage de fichiers Django ↔ Nextcloud

```
┌─────────────────┐         Bind Mount          ┌──────────────────┐
│  Django/Celery  │◀────────────────────────────▶│  Système hôte    │
│  /app/media     │   /opt/.../media:/app/media  │  /opt/.../media  │
└─────────────────┘                              └──────────────────┘
                                                          ▲
                                                          │
                                                  Stockage externe
                                                          │
                                                          ▼
                                                  ┌──────────────────┐
                                                  │    Nextcloud     │
                                                  │ Observations     │
                                                  │      Media       │
                                                  └──────────────────┘
```

### 2. Processus de transcription

```
1. Utilisateur sélectionne un répertoire dans l'interface web Django
   ↓
2. Django lance une tâche Celery (process_batch_transcription_task)
   ↓
3. Celery Worker :
   - Lit les images depuis /app/media/jpeg/...
   - Appelle Gemini API pour transcription OCR
   - Génère des fichiers JSON
   - Enregistre dans /app/media/transcription_results/...
   ↓
4. inotify détecte les nouveaux fichiers .json
   ↓
5. inotify déclenche : docker exec nextcloud occ files:scan
   ↓
6. Nextcloud détecte et indexe les nouveaux fichiers
   ↓
7. Les fichiers apparaissent dans l'interface Nextcloud
   ↓
8. Synchronisation vers les clients Nextcloud (desktop/mobile)
```

### 3. Flux des données media

```
┌──────────────────────────────────────────────────────────┐
│                    Flux des fichiers                      │
└──────────────────────────────────────────────────────────┘

Upload initial via Nextcloud
       │
       ▼
┌─────────────────┐
│  Nextcloud Web  │
└─────────────────┘
       │
       ▼ Stockage externe
┌──────────────────────────────────────┐
│  /opt/.../media/jpeg/               │
│    ├── fiche 1R.jpg                 │
│    └── fiche 1V.jpg                 │
└──────────────────────────────────────┘
       │
       │ Bind mount
       ▼
┌──────────────────────────────────────┐
│  Container: /app/media/jpeg/        │
│  (Django/Celery)                     │
└──────────────────────────────────────┘
       │
       ▼ Traitement OCR Gemini
┌──────────────────────────────────────┐
│  /app/media/transcription_results/  │
│    └── jpeg/                         │
│        └── gemini_3_flash/          │
│            └── fiche1_result.json   │
└──────────────────────────────────────┘
       │
       │ inotify watch
       ▼
┌──────────────────────────────────────┐
│  Nextcloud scan automatique          │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Synchronisation clients Nextcloud   │
└──────────────────────────────────────┘
```

---

## Système de surveillance inotify

### Présentation

**inotify** est un système Linux de surveillance du système de fichiers en temps réel. Il permet de détecter automatiquement les changements (créations, modifications, suppressions) et de déclencher des actions.

### Architecture du système de surveillance

```
┌─────────────────────────────────────────────────────────┐
│         Service systemd : nextcloud-watch-transcription │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  inotifywait -m -r -e create,moved_to          │   │
│  │  Surveille : /opt/.../media/                    │   │
│  └────────────────────────────────────────────────┘   │
│                      │                                  │
│                      │ Événement détecté               │
│                      ▼                                  │
│  ┌────────────────────────────────────────────────┐   │
│  │  Filtre : fichiers *.json uniquement           │   │
│  └────────────────────────────────────────────────┘   │
│                      │                                  │
│                      │ Fichier JSON détecté            │
│                      ▼                                  │
│  ┌────────────────────────────────────────────────┐   │
│  │  Attente 2 secondes (écriture complète)        │   │
│  └────────────────────────────────────────────────┘   │
│                      │                                  │
│                      ▼                                  │
│  ┌────────────────────────────────────────────────┐   │
│  │  docker exec -u www-data nextcloud-app-1       │   │
│  │  php occ files:scan --path="/schneider/..."    │   │
│  └────────────────────────────────────────────────┘   │
│                      │                                  │
│                      ▼                                  │
│  ┌────────────────────────────────────────────────┐   │
│  │  Nextcloud indexe les nouveaux fichiers        │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Fichiers de configuration

#### 1. Script de surveillance

**Emplacement** : `/usr/local/bin/nextcloud-watch-transcription.sh`

```bash
#!/bin/bash

WATCH_DIR="/opt/observations_nids_pilote/media"
NC_CONTAINER="nextcloud-app-1"
NC_USER="schneider"
NC_PATH="/schneider/files/Observations Media"

inotifywait -m -r -e create,moved_to --format '%w%f' "$WATCH_DIR" | while read FILE
do
    if [[ "$FILE" == *.json ]]; then
        echo "🔔 Nouveau fichier détecté: $FILE"
        sleep 2
        docker exec -u www-data "$NC_CONTAINER" php occ files:scan --path="$NC_PATH" 2>&1
        echo "✅ Scan terminé à $(date)"
    fi
done
```

#### 2. Service systemd

**Emplacement** : `/etc/systemd/system/nextcloud-watch-transcription.service`

```ini
[Unit]
Description=Nextcloud inotify watcher for transcription results
After=docker.service

[Service]
Type=simple
ExecStart=/usr/local/bin/nextcloud-watch-transcription.sh
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
```

### Personnalisation

#### Modifier le répertoire surveillé

```bash
# Surveiller seulement transcription_results
WATCH_DIR="/opt/observations_nids_pilote/media/transcription_results"

# Surveiller tout le répertoire media (actuel)
WATCH_DIR="/opt/observations_nids_pilote/media"

# Surveiller plusieurs répertoires
WATCH_DIR="/opt/.../media/jpeg /opt/.../media/pdf"
```

#### Modifier les types de fichiers

```bash
# Seulement .json (actuel)
if [[ "$FILE" == *.json ]]; then

# Tous les fichiers
if [[ -f "$FILE" ]]; then

# Images uniquement
if [[ "$FILE" == *.jpg ]] || [[ "$FILE" == *.jpeg ]] || [[ "$FILE" == *.png ]]; then

# JSON et PDF
if [[ "$FILE" == *.json ]] || [[ "$FILE" == *.pdf ]]; then
```

### Avantages vs alternatives

| Critère | inotify | Cron job | Scan manuel |
|---------|---------|----------|-------------|
| **Réactivité** | ⚡ Immédiate (< 3s) | ⏰ 15-60 min | 🐌 Sur demande |
| **Ressources CPU** | 🪶 Minimal | 📊 Pics périodiques | 💪 Ponctuel |
| **Précision** | 🎯 Exacte | 🔍 Tout scanner | 🎯 Exacte |
| **Complexité** | ⚙️ Moyenne | ✅ Simple | ✅ Simple |
| **Fiabilité** | ✅ Excellent | ⚠️ Délais | ⚠️ Oublis |

---

## Flux de données

### Diagramme de séquence - Transcription complète

```
Utilisateur     Interface Web     Celery Worker     Système fichiers     inotify     Nextcloud
    │                │                  │                   │               │            │
    │   Sélectionne  │                  │                   │               │            │
    │   répertoire   │                  │                   │               │            │
    │───────────────▶│                  │                   │               │            │
    │                │                  │                   │               │            │
    │                │  Lance tâche     │                   │               │            │
    │                │─────────────────▶│                   │               │            │
    │                │                  │                   │               │            │
    │                │                  │  Lit images       │               │            │
    │                │                  │──────────────────▶│               │            │
    │                │                  │                   │               │            │
    │                │                  │  Appelle Gemini   │               │            │
    │                │                  │  API ┄┄┄┄┄┄┄┄┄┄┄▶ │               │            │
    │                │                  │                   │               │            │
    │                │                  │  Génère JSON      │               │            │
    │                │                  │──────────────────▶│               │            │
    │                │                  │                   │               │            │
    │                │                  │                   │  Événement    │            │
    │                │                  │                   │  create       │            │
    │                │                  │                   │──────────────▶│            │
    │                │                  │                   │               │            │
    │                │                  │                   │               │  Scan      │
    │                │                  │                   │               │───────────▶│
    │                │                  │                   │               │            │
    │                │                  │                   │               │  Index     │
    │                │                  │                   │               │            │
    │                │  Résultats       │                   │               │            │
    │◀───────────────│◀─────────────────│                   │               │            │
    │                │                  │                   │               │            │
    │  Consulte      │                  │                   │               │            │
    │  sur Nextcloud │                  │                   │               │            │
    │───────────────────────────────────────────────────────────────────────────────────▶│
    │                │                  │                   │               │            │
```

### Points de synchronisation

1. **Upload de fiches** : Nextcloud → Système de fichiers → Django (lecture)
2. **Transcription** : Django/Celery → Système de fichiers → inotify → Nextcloud
3. **Consultation** : Nextcloud → Système de fichiers (lecture)

---

## Référence des commandes

### Gestion Docker - Observations Nids

#### Démarrage et arrêt

```bash
# Naviguer vers le répertoire Docker
cd /opt/observations_nids_pilote/docker

# Démarrer tous les services
docker compose up -d

# Arrêter tous les services
docker compose down

# Redémarrer tous les services
docker compose restart

# Redémarrer un service spécifique
docker compose restart celery_worker
docker compose restart web
docker compose restart nginx
```

#### Monitoring et logs

```bash
# Voir l'état de tous les conteneurs
docker compose ps

# Voir les logs en temps réel
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f celery_worker
docker compose logs -f web

# Voir les dernières 100 lignes
docker compose logs --tail=100 celery_worker

# Rechercher dans les logs
docker compose logs celery_worker | grep "transcription"
docker compose logs celery_worker | grep -i "error"
```

#### Mise à jour et maintenance

```bash
# Récupérer les dernières modifications depuis Git
cd /opt/observations_nids_pilote
git pull origin main

# Reconstruire les images si nécessaire
cd docker
docker compose build

# Reconstruire et redémarrer
docker compose up -d --build

# Nettoyer les images non utilisées
docker image prune -a

# Voir l'utilisation des volumes
docker volume ls
docker system df
```

#### Exécution de commandes dans les conteneurs

```bash
# Ouvrir un shell dans le conteneur web
docker exec -it observations_web bash

# Ouvrir un shell dans le conteneur Celery
docker exec -it observations_celery_worker bash

# Exécuter une commande Django
docker exec -it observations_web python manage.py migrate
docker exec -it observations_web python manage.py createsuperuser
docker exec -it observations_web python manage.py collectstatic --noinput

# Voir les tâches Celery en cours
docker exec -it observations_celery_worker celery -A observations_nids inspect active

# Shell Python Django
docker exec -it observations_web python manage.py shell
```

#### Accès aux bases de données

```bash
# Accès MySQL via ligne de commande
docker exec -it observations_db mysql -u root -p

# Backup de la base de données
docker exec observations_db mysqldump -u root -p${DB_ROOT_PASSWORD} observations_nids > backup_$(date +%Y%m%d).sql

# Restauration de la base de données
docker exec -i observations_db mysql -u root -p${DB_ROOT_PASSWORD} observations_nids < backup.sql

# Accès Redis
docker exec -it observations_redis redis-cli
```

### Gestion Nextcloud

#### Scan des fichiers

```bash
# Scanner tout le compte schneider
docker exec -u www-data nextcloud-app-1 php occ files:scan schneider

# Scanner seulement Observations Media
docker exec -u www-data nextcloud-app-1 php occ files:scan --path="/schneider/files/Observations Media"

# Scanner un sous-répertoire spécifique
docker exec -u www-data nextcloud-app-1 php occ files:scan --path="/schneider/files/Observations Media/transcription_results"

# Scanner tous les utilisateurs
docker exec -u www-data nextcloud-app-1 php occ files:scan --all
```

#### Maintenance Nextcloud

```bash
# Mode maintenance
docker exec -u www-data nextcloud-app-1 php occ maintenance:mode --on
docker exec -u www-data nextcloud-app-1 php occ maintenance:mode --off

# Vérifier la configuration
docker exec -u www-data nextcloud-app-1 php occ config:list

# Voir les informations système
docker exec -u www-data nextcloud-app-1 php occ status

# Nettoyer le cache
docker exec -u www-data nextcloud-app-1 php occ files:cleanup
```

### Gestion du service inotify

#### Contrôle du service

```bash
# Démarrer le service
sudo systemctl start nextcloud-watch-transcription.service

# Arrêter le service
sudo systemctl stop nextcloud-watch-transcription.service

# Redémarrer le service
sudo systemctl restart nextcloud-watch-transcription.service

# Voir le statut
sudo systemctl status nextcloud-watch-transcription.service

# Activer au démarrage
sudo systemctl enable nextcloud-watch-transcription.service

# Désactiver au démarrage
sudo systemctl disable nextcloud-watch-transcription.service
```

#### Logs et monitoring

```bash
# Voir les logs en temps réel
sudo journalctl -u nextcloud-watch-transcription.service -f

# Voir les 100 dernières lignes
sudo journalctl -u nextcloud-watch-transcription.service -n 100

# Logs depuis aujourd'hui
sudo journalctl -u nextcloud-watch-transcription.service --since today

# Logs des dernières 24h
sudo journalctl -u nextcloud-watch-transcription.service --since "24 hours ago"

# Rechercher dans les logs
sudo journalctl -u nextcloud-watch-transcription.service | grep "JSON"
sudo journalctl -u nextcloud-watch-transcription.service | grep "Scan terminé"
```

#### Modification du service

```bash
# Éditer le script de surveillance
sudo nano /usr/local/bin/nextcloud-watch-transcription.sh

# Éditer la configuration du service
sudo nano /etc/systemd/system/nextcloud-watch-transcription.service

# Recharger systemd après modification
sudo systemctl daemon-reload

# Redémarrer le service
sudo systemctl restart nextcloud-watch-transcription.service
```

### Gestion des permissions

#### Réparer les permissions du répertoire media

```bash
# Définir le propriétaire correct (utilisateur django du conteneur)
sudo chown -R 999:www-data /opt/observations_nids_pilote/media/

# Définir les permissions correctes
sudo chmod -R 775 /opt/observations_nids_pilote/media/

# Vérifier les permissions
ls -la /opt/observations_nids_pilote/media/

# Vérifier récursivement
find /opt/observations_nids_pilote/media/ -type d -ls | head -20
find /opt/observations_nids_pilote/media/ -type f -ls | head -20
```

#### Vérifier les utilisateurs dans les conteneurs

```bash
# Voir l'utilisateur dans le conteneur web
docker exec -it observations_web whoami
docker exec -it observations_web id

# Voir l'utilisateur dans le conteneur Celery
docker exec -it observations_celery_worker whoami
docker exec -it observations_celery_worker id

# Tester l'écriture dans media
docker exec -it observations_celery_worker touch /app/media/test_write.txt
docker exec -it observations_celery_worker rm /app/media/test_write.txt
```

### Recherche et diagnostic

#### Rechercher des fichiers

```bash
# Trouver tous les fichiers JSON de transcription
find /opt/observations_nids_pilote/media/transcription_results -name "*.json"

# Compter les fichiers JSON
find /opt/observations_nids_pilote/media/transcription_results -name "*.json" | wc -l

# Trouver les fichiers JSON récents (dernières 24h)
find /opt/observations_nids_pilote/media/transcription_results -name "*.json" -mtime -1

# Chercher dans les conteneurs
docker exec -it observations_celery_worker find /app -name "*_result.json"
```

#### Vérifier l'espace disque

```bash
# Espace disque global
df -h

# Taille du répertoire media
du -sh /opt/observations_nids_pilote/media/

# Taille détaillée par sous-répertoire
du -h --max-depth=2 /opt/observations_nids_pilote/media/

# Espace utilisé par Docker
docker system df
docker system df -v
```

#### Test de connectivité

```bash
# Tester la connexion entre conteneurs
docker exec -it observations_web ping db
docker exec -it observations_web ping redis

# Tester l'accès à la base de données
docker exec -it observations_web python manage.py dbshell

# Tester l'accès Redis
docker exec -it observations_web python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())"

# Tester Celery
docker exec -it observations_celery_worker celery -A observations_nids inspect ping
```

### Commandes Git

```bash
# Voir l'état des modifications
cd /opt/observations_nids_pilote
git status

# Récupérer les dernières modifications
git pull origin main

# Voir l'historique des commits
git log --oneline -10

# Voir les différences
git diff

# Annuler les modifications locales (ATTENTION: perte de données)
git reset --hard HEAD
```

### Séquence complète de mise à jour

```bash
# 1. Naviguer vers le projet
cd /opt/observations_nids_pilote

# 2. Arrêter les services
cd docker
docker compose down

# 3. Récupérer les modifications
cd ..
git pull origin main

# 4. Reconstruire et redémarrer
cd docker
docker compose up -d --build

# 5. Vérifier que tout fonctionne
docker compose ps
docker compose logs -f --tail=50

# 6. Tester l'application
curl http://localhost:8010/health/
```

---

## Annexes

### Variables d'environnement importantes

```bash
# Fichier : /opt/observations_nids_pilote/.env

# Base de données
DB_NAME=observations_nids
DB_USER=observations
DB_PASSWORD=***
DB_ROOT_PASSWORD=***

# Django
SECRET_KEY=***
DEBUG=False
ALLOWED_HOSTS=["serveur.domaine.fr"]

# Gemini API
GEMINI_API_KEY=***

# Nextcloud (si applicable)
# DJANGO_MEDIA_ROOT=/app/media (non défini = utilise défaut)
```

### Ports utilisés

| Service | Port hôte | Port conteneur | Protocole |
|---------|-----------|----------------|-----------|
| Nginx | 8010 | 80 | HTTP |
| Flower | 5555 | 5555 | HTTP |
| phpMyAdmin | 8081 | 80 | HTTP |
| MariaDB | - | 3306 | MySQL (interne) |
| Redis | - | 6379 | Redis (interne) |
| Django/Gunicorn | - | 8000 | HTTP (interne) |

### Ressources et documentation

- **Docker** : https://docs.docker.com/
- **Docker Compose** : https://docs.docker.com/compose/
- **Django** : https://docs.djangoproject.com/
- **Celery** : https://docs.celeryq.dev/
- **Nextcloud** : https://docs.nextcloud.com/
- **inotify-tools** : https://github.com/inotify-tools/inotify-tools
- **Nginx** : https://nginx.org/en/docs/

---

**Document maintenu par** : Équipe Observations Nids
**Dernière mise à jour** : 24 décembre 2025
**Version du document** : 1.0
