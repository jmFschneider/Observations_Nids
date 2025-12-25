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

**Solution - Rebuild sélectif (recommandé)** :
```bash
# Rebuild uniquement les services concernés
# Exemple : après modification de templates HTML
docker compose build web
docker compose up -d web

# Exemple : après modification de code Python (tâches Celery)
docker compose build web celery_worker celery_beat
docker compose up -d web celery_worker celery_beat
```

**Solution - Rebuild complet** :
```bash
# Reconstruire toutes les images
docker compose down
docker compose build
docker compose up -d
```

**OU** en mode développement (hot-reload) :
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**💡 Astuce** : Voir la section [Quand reconstruire les images Docker ?](#quand-reconstruire-les-images-docker-) dans "Dépannage" pour un guide détaillé.

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

# IMPORTANT: Utiliser le format JSON avec Docker (les virgules du CSV posent problème)
ALLOWED_HOSTS='["votre-domaine.com","www.votre-domaine.com","localhost","127.0.0.1"]'

# CSRF Protection (obligatoire depuis Django 4.0+ derrière reverse proxy)
# Inclure le protocole (http:// ou https://) et le port si différent de 80/443
# Si accès direct sans reverse proxy externe:
CSRF_TRUSTED_ORIGINS='["http://localhost:8010"]'
# Si reverse proxy HTTPS externe (Apache/Nginx):
# CSRF_TRUSTED_ORIGINS='["https://votre-domaine.com","https://www.votre-domaine.com"]'

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

### 3. Architecture avec reverse proxy externe (Apache/Nginx)

Si vous utilisez un reverse proxy HTTPS externe devant Docker (par exemple Apache sur un autre serveur), suivez ces étapes :

**Architecture typique :**
```
Utilisateur (Internet)
    ↓ HTTPS (port 443)
Apache/Nginx externe
    ↓ HTTP (port 8010)
nginx Docker
    ↓ HTTP (port 8000)
Django Gunicorn
```

**Configuration Apache externe :**

Votre Apache doit transmettre les headers de proxy :

```apache
<VirtualHost *:443>
  ServerName votre-domaine.com

  ProxyPreserveHost On
  ProxyRequests Off

  # IMPORTANT: Indiquer HTTPS au backend
  RequestHeader set X-Forwarded-Proto "https"
  RequestHeader add X-Forwarded-For "%{REMOTE_ADDR}s"

  ProxyPass        / http://serveur-docker:8010/
  ProxyPassReverse / http://serveur-docker:8010/

  # SSL Configuration
  SSLEngine on
  SSLCertificateFile /path/to/cert.pem
  SSLCertificateKeyFile /path/to/key.pem
</VirtualHost>
```

**Configuration Django (.env) :**

```env
# Hosts autorisés (sans protocole)
ALLOWED_HOSTS='["votre-domaine.com","www.votre-domaine.com"]'

# CSRF avec protocole HTTPS (ce que voit l'utilisateur)
CSRF_TRUSTED_ORIGINS='["https://votre-domaine.com","https://www.votre-domaine.com"]'
```

**Note importante :** Django est configuré avec `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` pour faire confiance au header `X-Forwarded-Proto` envoyé par le reverse proxy externe. Cela permet à Django de reconnaître les requêtes HTTPS même si elles arrivent en HTTP depuis le proxy.

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

### Gestion Celery et tâches asynchrones

Celery est utilisé pour exécuter des tâches longues en arrière-plan (OCR Gemini, récupération de liens oiseaux.net, etc.) afin d'éviter les timeouts 504 Gateway Timeout.

```bash
# Voir les workers actifs
docker compose exec celery_worker celery -A observations_nids inspect active

# Voir les tâches planifiées
docker compose exec celery_beat celery -A observations_nids inspect scheduled

# Voir les tâches enregistrées
docker compose exec celery_worker celery -A observations_nids inspect registered

# Redémarrer les workers
docker compose restart celery_worker celery_beat

# Voir les logs des workers
docker compose logs -f celery_worker

# Purger toutes les tâches en attente (ATTENTION: supprime les tâches)
docker compose exec celery_worker celery -A observations_nids purge
```

### Monitoring avec Flower

**Flower** est l'interface web de monitoring pour Celery. Elle permet de suivre en temps réel l'exécution des tâches asynchrones.

#### Accès à Flower

Flower peut être accessible de deux façons selon votre configuration :

1. **Accès direct (développement local)** :
   - URL : http://localhost:5555
   - Accessible uniquement depuis le serveur

2. **Via reverse proxy Apache (production recommandée)** :
   - URL : https://votre-domaine.com/flower
   - Nécessite configuration Apache (voir ci-dessous)

#### Configuration Apache pour Flower

Pour accéder à Flower via un reverse proxy Apache (recommandé en production) :

**1. Configurer Apache :**

Ajouter dans votre VirtualHost Apache (par exemple `/etc/apache2/sites-available/pilote.observation-nids.conf`) :

```apache
# Flower monitoring (Celery)
ProxyPass /flower http://localhost:5555/flower
ProxyPassReverse /flower http://localhost:5555/flower
```

**2. Activer les modules nécessaires :**

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo systemctl restart apache2
```

**3. Important : Configuration Flower avec url-prefix**

Le fichier `docker-compose.yml` est déjà configuré avec `--url-prefix=flower` :

```yaml
flower:
  command: celery -A observations_nids flower --port=5555 --url-prefix=flower
```

**Cette option est CRITIQUE** : elle permet à Flower de générer correctement les URLs internes quand il est derrière un reverse proxy. Sans cette option, Flower génère des URLs incorrectes comme `/task/...` au lieu de `/flower/task/...`.

#### Ouverture automatique de Flower

L'application est configurée pour **ouvrir automatiquement Flower** dans un nouvel onglet lorsque vous lancez une tâche asynchrone depuis l'interface web (par exemple : récupération de liens oiseaux.net, OCR Gemini).

**Comment ça fonctionne :**

1. L'utilisateur lance une tâche via l'interface web
2. Django crée la tâche Celery et récupère son ID
3. La vue redirige vers la page d'origine avec `?task_id=XXX` dans l'URL
4. Un script JavaScript détecte le paramètre `task_id`
5. Flower s'ouvre automatiquement dans un nouvel onglet sur `/flower/task/XXX`
6. L'URL est nettoyée pour éviter de rouvrir Flower au refresh

**Exemple de code JavaScript (déjà implémenté dans les templates)** :

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const taskId = urlParams.get('task_id');

    if (taskId) {
        // Ouvrir Flower dans un nouvel onglet
        const flowerUrl = `/flower/task/${taskId}`;
        window.open(flowerUrl, '_blank', 'noopener,noreferrer');

        // Nettoyer l'URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});
```

#### États des tâches dans Flower

Flower affiche les états suivants pour les tâches :

- **PENDING** : Tâche en attente d'exécution
- **STARTED** : Tâche en cours d'exécution
- **SUCCESS** : Tâche terminée avec succès
- **FAILURE** : Tâche échouée
- **PROGRESS** : État personnalisé (mis à jour par la tâche elle-même)

#### Suivi granulaire de la progression

Les tâches peuvent mettre à jour leur progression avec `self.update_state()` :

```python
self.update_state(
    state='PROGRESS',
    meta={
        'status': 'processing',
        'message': 'Traitement de l\'image 5/20...',
        'percent': 25,
        'current': 5,
        'total': 20,
    }
)
```

Flower affiche ces informations en temps réel dans l'interface.

## Accès aux services

Une fois les conteneurs démarrés :

| Service | URL (développement local) | URL (production avec Apache) | Description |
|---------|---------------------------|------------------------------|-------------|
| **Application principale** | http://localhost:8010 | https://votre-domaine.com | Interface web Django |
| **Admin Django** | http://localhost:8010/admin | https://votre-domaine.com/admin | Interface d'administration |
| **phpMyAdmin** | http://localhost:8081 | - | Gestion de la base de données MariaDB |
| **Flower (Celery)** | http://localhost:5555 | https://votre-domaine.com/flower | Monitoring des tâches asynchrones |

**Notes importantes :**

- **Développement local** : Depuis un autre PC du réseau local, remplacez `localhost` par l'IP du serveur (exemple: `http://192.168.1.112:8081` pour phpMyAdmin)
- **Production** : Flower nécessite la configuration Apache reverse proxy (voir [Configuration Apache pour Flower](#configuration-apache-pour-flower))
- **Sécurité** : phpMyAdmin ne devrait JAMAIS être exposé sur Internet sans protection appropriée

### phpMyAdmin - Gestion de la base de données

phpMyAdmin vous permet de gérer la base de données MariaDB via une interface web conviviale.

**Accès :**
- Depuis le serveur : http://localhost:8081
- Depuis votre réseau local : http://192.168.1.112:8081 (remplacez par l'IP de votre serveur)

**Connexion :**
- **Utilisateur** : `root`
- **Mot de passe** : La valeur de `DB_ROOT_PASSWORD` dans votre fichier `.env`

**Sécurité :**
- ⚠️ phpMyAdmin est accessible **uniquement sur votre réseau local** (port 8081 non exposé sur Internet)
- ⚠️ N'exposez JAMAIS phpMyAdmin sur Internet sans protection (authentification, HTTPS, firewall)
- ✅ Pour un accès temporaire, vous pouvez arrêter le service : `docker compose stop phpmyadmin`
- ✅ Pour désactiver complètement, commentez le service dans `docker-compose.yml`

**Fonctionnalités utiles :**
- Consulter et modifier les tables
- Importer/Exporter des données (SQL, CSV, etc.)
- Exécuter des requêtes SQL personnalisées
- Gérer les utilisateurs et permissions
- Optimiser les tables

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

**Méthode recommandée (rebuild sélectif)** :

```bash
# 1. Sauvegarder la base de données (voir ci-dessus)

# 2. Récupérer les dernières modifications
git pull

# 3. Identifier les services modifiés et les reconstruire
# Si modification de code Python (models, views, tasks, etc.)
docker compose build web celery_worker celery_beat

# Si modification de templates HTML uniquement
docker compose build web

# Si modification de docker-compose.yml
# Pas de rebuild nécessaire, juste redémarrer

# 4. Redémarrer les services modifiés
docker compose up -d web celery_worker celery_beat

# 5. Vérifier les logs
docker compose logs -f web celery_worker
```

**Méthode alternative (rebuild complet)** :

Utile si vous ne savez pas exactement quels fichiers ont été modifiés.

```bash
# 1. Sauvegarder la base de données (voir ci-dessus)

# 2. Récupérer les dernières modifications
git pull

# 3. Reconstruire TOUTES les images
docker compose build --no-cache

# 4. Redémarrer TOUS les services
docker compose up -d

# 5. Vérifier les logs
docker compose logs -f
```

**⚠️ IMPORTANT** : Un simple `git pull` ne suffit PAS à mettre à jour le code dans les conteneurs. Vous DEVEZ reconstruire les images pour que les modifications soient prises en compte. Voir [Quand reconstruire les images Docker ?](#quand-reconstruire-les-images-docker-) pour plus de détails.

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

### Erreur CSRF 403 (Forbidden) - "La vérification CSRF a échoué"

Si vous obtenez une erreur **403 Forbidden** lors de la connexion ou de la soumission de formulaires :

**Cause** : Django n'arrive pas à vérifier l'origine de la requête, généralement dû à :
1. `CSRF_TRUSTED_ORIGINS` non configuré (obligatoire depuis Django 4.0+)
2. Mauvais protocole dans `CSRF_TRUSTED_ORIGINS` (HTTP vs HTTPS)
3. Reverse proxy ne transmet pas le header `X-Forwarded-Proto`

**Solution 1 - Vérifier CSRF_TRUSTED_ORIGINS dans `.env` :**

```env
# ✅ Si accès direct (sans reverse proxy externe)
CSRF_TRUSTED_ORIGINS='["http://localhost:8010"]'

# ✅ Si reverse proxy HTTPS externe (Apache/Nginx)
CSRF_TRUSTED_ORIGINS='["https://votre-domaine.com","https://www.votre-domaine.com"]'

# ❌ INCORRECT - oublier le protocole
CSRF_TRUSTED_ORIGINS='["votre-domaine.com"]'

# ❌ INCORRECT - mauvais protocole (si vous accédez en HTTPS)
CSRF_TRUSTED_ORIGINS='["http://votre-domaine.com"]'
```

**Solution 2 - Vérifier la configuration Apache (reverse proxy externe) :**

Votre Apache doit transmettre le header `X-Forwarded-Proto` :

```apache
RequestHeader set X-Forwarded-Proto "https"
```

Django est configuré avec `SECURE_PROXY_SSL_HEADER` pour faire confiance à ce header.

**Tester :**
```bash
# Redémarrer après modification
docker compose down
docker compose up -d

# Vérifier les logs
docker compose logs web --tail=50
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

### Erreur "NotRegistered" dans Flower

Si Flower affiche `NotRegistered('nom.de.la.tache')`, cela signifie que la tâche n'est pas découverte par le worker Celery.

**Cause possible 1 : Fichier de tâche manquant dans l'image Docker**

Vérifier si le fichier `tasks.py` existe dans le conteneur :

```bash
docker compose exec celery_worker ls -la taxonomy/tasks.py
docker compose exec celery_worker ls -la pilot/tasks.py
```

Si vous obtenez "No such file or directory", c'est que le fichier n'a pas été copié lors du build.

**Solution : Rebuild l'image du worker**

```bash
docker compose build celery_worker
docker compose up -d celery_worker
```

**Cause possible 2 : Tâche non enregistrée**

Vérifier que la tâche est bien décorée avec `@shared_task` :

```python
from celery import shared_task

@shared_task(bind=True, name='taxonomy.ma_tache')
def ma_tache(self):
    pass
```

Vérifier que l'application Celery découvre bien les tâches dans `observations_nids/__init__.py` :

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

Et dans `observations_nids/celery.py` :

```python
app.autodiscover_tasks()
```

**Vérification finale** :

```bash
# Voir toutes les tâches enregistrées
docker compose exec celery_worker celery -A observations_nids inspect registered

# Redémarrer le worker
docker compose restart celery_worker
```

### Template HTML non mis à jour après git pull

Si après un `git pull`, les modifications de templates HTML ne sont pas visibles dans l'application :

**Cause** : Les templates sont **copiés dans l'image Docker** lors du build, pas servis depuis le volume. Un simple `git pull` met à jour les fichiers sur l'hôte, mais pas dans le conteneur.

**Solution : Rebuild l'image web**

```bash
docker compose build web
docker compose up -d web
```

**Vérification** :

```bash
# Voir le code source dans le navigateur (Ctrl+U)
# Ou vérifier directement dans le conteneur
docker compose exec web cat taxonomy/templates/taxonomy/administration_donnees.html | grep "task_id"
```

### Flower inaccessible via reverse proxy (404 Not Found)

Si l'URL `/flower` retourne 404 Not Found :

**Cause 1 : Apache ProxyPass non configuré**

Vérifier que Apache a bien la configuration :

```apache
ProxyPass /flower http://localhost:5555/flower
ProxyPassReverse /flower http://localhost:5555/flower
```

Vérifier que les modules Apache sont activés :

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo systemctl restart apache2
```

**Cause 2 : Flower n'a pas le --url-prefix**

Vérifier dans `docker-compose.yml` :

```yaml
flower:
  command: celery -A observations_nids flower --port=5555 --url-prefix=flower
```

Si vous avez modifié le `docker-compose.yml`, **rebuild l'image flower** :

```bash
docker compose build flower
docker compose up -d flower
```

**Vérification** :

```bash
# Tester l'accès direct
curl http://localhost:5555/flower

# Tester via Apache
curl http://localhost/flower
```

### Quand reconstruire les images Docker ?

**⚠️ IMPORTANT** : Docker copie les fichiers dans l'image lors du `build`. Les modifications de code sur l'hôte ne sont PAS automatiquement reflétées dans les conteneurs.

**Vous DEVEZ reconstruire l'image quand :**

| Modification | Services à rebuild | Commande |
|--------------|-------------------|----------|
| Templates HTML (`.html`) | `web` | `docker compose build web && docker compose up -d web` |
| Code Python (`.py`) | `web`, `celery_worker`, `celery_beat` | `docker compose build web celery_worker celery_beat && docker compose up -d` |
| `docker-compose.yml` | Tous les services modifiés | `docker compose up -d` (suffit pour les changements de config) |
| `Dockerfile` | Tous | `docker compose build --no-cache && docker compose up -d` |
| Fichiers statiques (CSS/JS) | `web` | `docker compose exec web python manage.py collectstatic && docker compose restart nginx` |
| `.env` | Tous | `docker compose down && docker compose up -d` (pas de rebuild) |

**Vous N'AVEZ PAS besoin de rebuild pour :**

- Modifications des volumes montés (ex: `media/`, `logs/`)
- Modifications de `.env` (simple redémarrage suffit)
- Modifications de fichiers de configuration montés en volume

**Exemple complet après modification de code Python :**

```bash
# 1. git pull pour récupérer les modifications
git pull

# 2. Rebuild les services qui utilisent le code Python
docker compose build web celery_worker celery_beat

# 3. Redémarrer les services
docker compose up -d web celery_worker celery_beat

# 4. Vérifier les logs
docker compose logs -f web celery_worker
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
┌──────────────────────────────────────────────────────────────┐
│                  Nginx (Port 8010)                           │
│           Reverse Proxy / Static Files / SSL                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           │                           │
           ▼                           ▼
  ┌──────────────────┐       ┌──────────────────┐
  │ Django + Gunicorn│       │  Flower (5555)   │
  │   (Port 8000)    │       │ Celery Monitoring│
  └────────┬─────────┘       └──────────────────┘
           │
           │ Utilise
           │
    ┌──────┼──────┬──────────┬──────────┬──────────┐
    ▼      ▼      ▼          ▼          ▼          ▼
┌────────┐  ┌────────┐  ┌─────────┐  ┌────────┐  ┌────────┐
│MariaDB │  │ Redis  │  │ Celery  │  │ Celery │  │ Celery │
│ 10.11  │  │ Cache  │  │ Worker  │  │  Beat  │  │ Flower │
│        │  │Broker  │  │(async)  │  │(cron)  │  │(UI)    │
└────────┘  └────────┘  └─────────┘  └────────┘  └────────┘

Flux de tâches asynchrones:
1. Utilisateur lance une tâche via Django (ex: OCR, liens oiseaux.net)
2. Django envoie la tâche à Redis (broker Celery)
3. Celery Worker récupère et exécute la tâche
4. Flower affiche la progression en temps réel
5. Django affiche le résultat à l'utilisateur
```

## Support

Pour toute question ou problème :

1. Vérifier la section [Dépannage](#dépannage)
2. Consulter les logs : `docker compose logs`
3. Créer une issue sur GitHub

---

**Auteur** : Équipe Observations Nids
**Dernière mise à jour** : 2025-12-25

## Changelog récent

### 2025-12-25 : Celery et Flower
- Ajout de la documentation complète sur Celery et les tâches asynchrones
- Configuration Apache reverse proxy pour Flower (`/flower`)
- Ouverture automatique de Flower depuis l'interface web
- Guide de troubleshooting pour NotRegistered, templates non mis à jour, etc.
- Tableau détaillé : Quand reconstruire les images Docker
- Architecture mise à jour avec flux de tâches asynchrones
