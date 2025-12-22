# Déploiement Docker - Observations Nids

Guide complet pour déployer l'application Observations Nids avec Docker.

## Table des matières

- [Prérequis](#prérequis)
- [Comment fonctionne Docker](#comment-fonctionne-docker)
- [Installation rapide](#installation-rapide)
- [Configuration](#configuration)
- [Démarrage](#démarrage)
- [Gestion des conteneurs](#gestion-des-conteneurs)
- [Accès aux services](#accès-aux-services)
- [Maintenance](#maintenance)
- [Dépannage](#dépannage)
- [Production](#production)

## Prérequis

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Système** : Ubuntu 20.04+ (recommandé) ou toute distribution Linux moderne
- **Mémoire** : 4 GB RAM minimum (8 GB recommandé)
- **Espace disque** : 20 GB minimum

### Installation Docker sur Ubuntu

```bash
# Mettre à jour les paquets
sudo apt update && sudo apt upgrade -y

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER

# Installer Docker Compose
sudo apt install docker-compose-plugin -y

# Vérifier l'installation
docker --version
docker compose version
```

**Important** : Déconnectez-vous et reconnectez-vous pour que le groupe docker soit pris en compte.

## Comment fonctionne Docker

Comprendre le processus d'installation et d'isolation Docker.

### 📦 Le processus : Clone → Build → Run

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣ CLONE sur l'hôte Ubuntu                                 │
│     git clone → /opt/observations_nids_pilote/              │
│     Le code source est maintenant sur VOTRE système         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2️⃣ BUILD de l'image Docker                                 │
│     docker compose build                                    │
│     • Docker LIT le Dockerfile                              │
│     • COPIE le code dans l'image (COPY . .)                 │
│     • Installe Python 3.12 + dépendances                    │
│     • Crée une IMAGE isolée et autonome                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3️⃣ RUN du conteneur                                        │
│     docker compose up                                       │
│     • Lance le conteneur depuis l'image                     │
│     • Le code est maintenant dans /app du conteneur         │
│     • Totalement ISOLÉ du système Ubuntu                    │
└─────────────────────────────────────────────────────────────┘
```

### 🔒 L'isolation complète

```
Système Ubuntu (Hôte)
├── /opt/observations_nids_pilote/     ← Code source original
│   ├── observations/
│   ├── docker/
│   └── ...
│
├── Conteneur "web" (Django)           ← Copie isolée
│   └── /app/
│       ├── observations/              ← Copie du code
│       ├── manage.py
│       └── Python 3.12 + Django 6.0   ← Isolé du système
│
├── Conteneur "db" (MariaDB)           ← Base de données isolée
│   └── MariaDB 10.11
│
├── Conteneur "redis"                  ← Cache isolé
│   └── Redis 7
│
└── Conteneur "nginx"                  ← Reverse proxy isolé
    └── Nginx
```

**Chaque conteneur** :
- ✅ A son propre système de fichiers
- ✅ A ses propres processus
- ✅ A son propre réseau
- ✅ Ne voit PAS le système Ubuntu
- ✅ Ne voit PAS les autres conteneurs (sauf via le réseau Docker)

### 🔗 Les volumes : ponts entre hôte et conteneurs

Certains dossiers sont **partagés** pour persister les données :

```yaml
volumes:
  - db_data:/var/lib/mysql        # Base de données persistante
  - static_volume:/app/staticfiles # Fichiers statiques
  - media_volume:/app/mediafiles   # Uploads utilisateurs
  - ../logs:/app/logs             # Logs accessibles depuis l'hôte
```

**Avantage** : Si vous supprimez les conteneurs, les données persistent !

### 🔄 Modifier le code après le build

**Question** : Si je modifie le code sur l'hôte, est-ce que c'est automatiquement dans le conteneur ?

**Réponse** : **NON** ! Le conteneur contient une **copie** faite lors du build.

**Solution** :
```bash
# Reconstruire l'image avec les modifications
docker compose down
docker compose build
docker compose up -d
```

**OU** en mode développement (hot-reload) :
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Installation rapide

### Choix de l'emplacement

Deux options recommandées pour installer la version pilote sur Ubuntu :

#### Option A : Installation dans /opt (recommandée)

Standard Linux pour les applications tierces. Nécessite sudo pour le clone initial.

```bash
# 1. Créer un utilisateur dédié
sudo useradd -m -s /bin/bash observations
sudo usermod -aG docker observations

# 2. Cloner dans /opt avec sudo
cd /opt
sudo git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids_pilote

# 3. Changer le propriétaire pour l'utilisateur observations
sudo chown -R observations:observations observations_nids_pilote

# 4. Se connecter comme utilisateur observations
sudo su - observations

# 5. Aller dans le répertoire docker
cd /opt/observations_nids_pilote/docker

# 6. Configurer
cp .env.example .env
nano .env

# 7. Construire les images (première installation)
docker compose build

# 8. Démarrer tous les services
docker compose up -d

# 9. Vérifier que tout fonctionne
docker compose ps
docker compose logs -f
```

**Emplacement final** : `/opt/observations_nids_pilote/`

#### Option B : Installation dans le home de l'utilisateur

Plus simple, pas besoin de sudo pour le clone.

```bash
# 1. Créer un utilisateur dédié
sudo useradd -m -s /bin/bash observations
sudo usermod -aG docker observations

# 2. Se connecter comme cet utilisateur
sudo su - observations

# 3. Cloner dans le home (version pilote)
git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids_pilote
cd observations_nids_pilote/docker

# 4. Configurer
cp .env.example .env
nano .env

# 5. Construire les images (première installation)
docker compose build

# 6. Démarrer tous les services
docker compose up -d

# 7. Vérifier que tout fonctionne
docker compose ps
docker compose logs -f
```

**Emplacement final** : `/home/observations/observations_nids_pilote/`

### Accès à l'application

L'application sera accessible sur http://votre-serveur

**Notes importantes** :
- ✅ Le dépôt GitHub est **public**, pas d'authentification nécessaire pour cloner
- ✅ Tous les fichiers de configuration Docker sont dans `docker/`
- ✅ Installation nommée `observations_nids_pilote` (version pilote)
- ✅ Toujours exécuter les commandes depuis le répertoire `docker/`
- ✅ Le code sur l'hôte est **copié** dans les conteneurs lors du build
- ✅ Les conteneurs sont **totalement isolés** du système Ubuntu

## Configuration

### 1. Fichier .env

Créer un fichier `.env` à la racine du projet (copier depuis `.env.example`) :

```bash
cp .env.example .env
```

**Variables essentielles à configurer :**

```env
# Django
SECRET_KEY=votre-secret-key-tres-longue-et-aleatoire
DEBUG=False
# IMPORTANT: Utiliser le format JSON pour ALLOWED_HOSTS avec Docker
ALLOWED_HOSTS='["votre-domaine.com","www.votre-domaine.com","localhost","127.0.0.1"]'

# Base de données
DB_ROOT_PASSWORD=mot-de-passe-root-tres-fort
DB_NAME=observations_nids
DB_USER=observations_user
DB_PASSWORD=mot-de-passe-utilisateur-fort

# Superuser Django
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=mot-de-passe-admin-fort

# Google API
GOOGLE_API_KEY=votre-cle-api-google
```

**Générer une SECRET_KEY aléatoire :**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Configuration SSL (optionnel, recommandé en production)

Pour activer HTTPS :

1. Placer vos certificats SSL dans `docker/nginx/ssl/` :
   - `cert.pem` (certificat)
   - `key.pem` (clé privée)

2. Décommenter les lignes SSL dans `docker/nginx/conf.d/default.conf`

3. Redémarrer Nginx :
   ```bash
   docker compose restart nginx
   ```

## Démarrage

### Premier démarrage (recommandé en deux étapes)

**Méthode recommandée** pour la première installation ou après modifications du Dockerfile :

```bash
# 1. Construire les images Docker
docker compose build

# 2. Démarrer tous les services
docker compose up -d

# 3. Suivre les logs pour vérifier
docker compose logs -f

# Attendre que tous les services soient prêts (environ 1-2 minutes)
# Ctrl+C pour quitter les logs
```

**Avantages** :
- ✅ Erreurs de build plus claires et isolées
- ✅ Meilleur pour le débogage
- ✅ Plus de contrôle sur le processus

### Méthode alternative (tout en une commande)

**Pour les mises à jour futures** ou si vous êtes pressé :

```bash
# Construire ET démarrer en une seule commande
docker compose up -d --build

# Suivre les logs
docker compose logs -f
```

**Avantages** :
- ✅ Plus rapide (une seule commande)
- ✅ Pratique pour les mises à jour

**Inconvénient** :
- ⚠️ Si le build échoue, les erreurs sont moins visibles

### Démarrages suivants (services déjà construits)

```bash
# Démarrer tous les services
docker compose up -d

# Arrêter tous les services
docker compose down

# Redémarrer un service spécifique
docker compose restart web

# Voir les logs d'un service
docker compose logs -f web
```

## Gestion des conteneurs

### Voir l'état des conteneurs

```bash
# Lister tous les conteneurs
docker compose ps

# Voir les logs
docker compose logs -f [service]

# Exemples
docker compose logs -f web        # Logs de l'application Django
docker compose logs -f celery_worker  # Logs du worker Celery
docker compose logs -f nginx      # Logs Nginx
```

### Exécuter des commandes Django

```bash
# Shell Django
docker compose exec web python manage.py shell

# Créer des migrations
docker compose exec web python manage.py makemigrations

# Appliquer les migrations
docker compose exec web python manage.py migrate

# Créer un superuser manuellement
docker compose exec web python manage.py createsuperuser

# Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic

# Shell bash dans le conteneur
docker compose exec web bash
```

### Gestion Celery

```bash
# Voir les workers actifs
docker compose exec celery_worker celery -A observations_nids inspect active

# Voir les tâches planifiées
docker compose exec celery_beat celery -A observations_nids inspect scheduled

# Redémarrer les workers
docker compose restart celery_worker celery_beat
```

## Accès aux services

Une fois les conteneurs démarrés :

| Service | URL | Description |
|---------|-----|-------------|
| **Application principale** | http://localhost | Interface web Django |
| **Admin Django** | http://localhost/admin | Interface d'administration |
| **Flower** | http://localhost:5555 | Monitoring Celery |
| **Radicale (CalDAV)** | http://localhost/radicale | Serveur CalDAV/CardDAV |

## Maintenance

### Backup de la base de données

```bash
# Créer un backup
docker compose exec db mysqldump -u root -p$DB_ROOT_PASSWORD observations_nids > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer un backup
docker compose exec -T db mysql -u root -p$DB_ROOT_PASSWORD observations_nids < backup_20250101_120000.sql
```

### Backup des volumes

```bash
# Sauvegarder tous les volumes
docker compose down
sudo tar -czf volumes_backup_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/observations_nids_*
docker compose up -d
```

### Mises à jour

```bash
# 1. Sauvegarder la base de données (voir ci-dessus)

# 2. Récupérer les dernières modifications
git pull

# 3. Reconstruire les images
docker compose build --no-cache

# 4. Redémarrer les services
docker compose up -d

# 5. Vérifier les logs
docker compose logs -f
```

### Nettoyage

```bash
# Supprimer les images inutilisées
docker image prune -a

# Supprimer les volumes non utilisés (ATTENTION: perte de données)
docker volume prune

# Nettoyer complètement (ATTENTION: supprime TOUT)
docker compose down -v  # Supprime aussi les volumes
```

## Dépannage

### Les conteneurs ne démarrent pas

```bash
# Vérifier les logs
docker compose logs

# Vérifier l'état
docker compose ps

# Reconstruire depuis zéro
docker compose down -v
docker compose up -d --build
```

### Erreur de connexion à la base de données

```bash
# Vérifier que la DB est prête
docker compose exec db mysqladmin ping -h localhost -u root -p$DB_ROOT_PASSWORD

# Redémarrer la DB
docker compose restart db

# Attendre 30 secondes et redémarrer l'app
sleep 30
docker compose restart web
```

### Erreur JSON parsing pour ALLOWED_HOSTS

Si vous obtenez une erreur `json.decoder.JSONDecodeError` au démarrage :

**Cause** : Le format CSV de ALLOWED_HOSTS peut être mal interprété par Docker Compose lors du passage des variables d'environnement (les virgules causent des problèmes).

**Solution** : Utiliser le format JSON dans le fichier `.env` :

```env
# ❌ Format CSV (peut causer des problèmes avec Docker)
ALLOWED_HOSTS=localhost,127.0.0.1,domaine.com

# ✅ Format JSON (recommandé pour Docker)
ALLOWED_HOSTS='["localhost","127.0.0.1","domaine.com"]'
```

Après modification, redémarrer les conteneurs :
```bash
docker compose down
docker compose up -d
```

### Problèmes de permissions

```bash
# Fixer les permissions des volumes
docker compose exec web chown -R django:django /app/staticfiles /app/mediafiles
```

### Fichiers statiques non chargés

```bash
# Recollector les fichiers statiques
docker compose exec web python manage.py collectstatic --clear --noinput

# Redémarrer Nginx
docker compose restart nginx
```

### Celery ne traite pas les tâches

```bash
# Vérifier les workers
docker compose logs celery_worker

# Redémarrer Celery
docker compose restart celery_worker celery_beat

# Vérifier Redis
docker compose exec redis redis-cli ping
```

## Production

### Checklist de déploiement en production

- [ ] Configurer `.env` avec des valeurs de production
  - [ ] `DEBUG=False`
  - [ ] `SECRET_KEY` unique et aléatoire
  - [ ] Mots de passe forts partout
  - [ ] `ALLOWED_HOSTS` correct
- [ ] Configurer SSL/HTTPS
  - [ ] Certificats SSL en place
  - [ ] Configuration Nginx décommentée
- [ ] Configurer les backups automatiques
- [ ] Configurer un monitoring (logs, alertes)
- [ ] Tester le redémarrage complet
- [ ] Documenter l'architecture pour votre équipe

### Monitoring et logs

```bash
# Suivre tous les logs en temps réel
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f web

# Logs depuis les 10 dernières minutes
docker compose logs --since 10m

# Sauvegarder les logs
docker compose logs > logs_$(date +%Y%m%d_%H%M%S).txt
```

### Performance

Pour améliorer les performances en production :

1. **Augmenter les workers Gunicorn** :
   Modifier dans `docker-compose.yml` :
   ```yaml
   command: gunicorn ... --workers 8  # Ajuster selon CPU disponibles
   ```

2. **Augmenter les workers Celery** :
   ```yaml
   command: celery -A observations_nids worker --concurrency=4
   ```

3. **Activer le cache Redis** dans Django

4. **Optimiser Nginx** pour vos besoins spécifiques

## Architecture Docker

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Port 80/443)                  │
│                   Reverse Proxy / SSL                   │
└─────────┬─────────────────────────────┬─────────────────┘
          │                             │
          ▼                             ▼
┌─────────────────────┐       ┌──────────────────────┐
│   Django + Gunicorn │       │      Radicale        │
│      (Port 8000)    │       │   CalDAV (5232)      │
└──────────┬──────────┘       └──────────────────────┘
           │
           │
    ┌──────┴───────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
│ MariaDB │  │  Redis   │  │  Celery  │  │  Flower │
│  10.11  │  │  Cache   │  │  Worker  │  │  (5555) │
└─────────┘  └──────────┘  └──────────┘  └─────────┘
```

## Support

Pour toute question ou problème :

1. Vérifier la section [Dépannage](#dépannage)
2. Consulter les logs : `docker compose logs`
3. Créer une issue sur GitHub

---

**Auteur** : Équipe Observations Nids
**Dernière mise à jour** : 2025-12-21
