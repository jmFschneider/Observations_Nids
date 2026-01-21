# Guide de Démarrage - Développement Windows 11

> **Dernière mise à jour** : Janvier 2026
> **Version** : 2.0 - Mise à jour avec corrections et script PowerShell

## Notes importantes

⚠️ **Points clés à retenir** :

1. Le fichier `.env` est à la **racine du projet** (`C:\Projets\docker\observations_nids\.env`), **PAS** dans `docker/`
2. Utiliser le script `docker-dev.ps1` pour simplifier les commandes
3. Par défaut, `USE_DEBUG_TOOLBAR=False` car le module n'est pas installé dans Docker
4. Les commandes `docker compose` doivent être exécutées depuis le répertoire `docker/`

## Installation effectuée

✅ Projet cloné dans `C:\Projets\docker\observations_nids`
✅ Fichier `.env` créé à la racine avec configuration de développement
✅ Fichier `docker-compose.windows.yml` créé pour adapter les chemins Windows
✅ Script `docker-dev.ps1` disponible pour simplifier les commandes
✅ Répertoires `logs` et `media` créés

## Prérequis

- Docker Desktop installé et démarré sur Windows 11
- WSL2 activé (recommandé pour Docker Desktop)

## Structure de l'installation

```
C:\Projets\docker\observations_nids\
├── .env                              # Configuration développement (RACINE)
├── docker/
│   ├── docker-compose.yml            # Configuration de base
│   ├── docker-compose.dev.yml        # Override développement
│   ├── docker-compose.windows.yml    # Override Windows (chemins)
│   ├── docker-dev.ps1                # Script PowerShell pour simplifier
│   └── ...
├── logs/                             # Logs applicatifs
├── media/                            # Fichiers uploadés
└── ...
```

**Important** : Le fichier `.env` est à la **racine du projet**, pas dans le répertoire `docker/`.

## Démarrage de l'application

### Méthode simplifiée avec le script PowerShell

Un script `docker-dev.ps1` est disponible dans le répertoire `docker/` pour simplifier les commandes.

```powershell
cd C:\Projets\docker\observations_nids\docker

# Afficher l'aide
.\docker-dev.ps1

# Commandes principales
.\docker-dev.ps1 up           # Démarrer les services
.\docker-dev.ps1 down         # Arrêter les services
.\docker-dev.ps1 logs         # Voir les logs
.\docker-dev.ps1 build        # Reconstruire les images
.\docker-dev.ps1 shell        # Ouvrir un shell Django
.\docker-dev.ps1 migrate      # Appliquer les migrations
```

### 1. Première installation

Ouvrir un terminal PowerShell ou CMD dans le répertoire docker :

```powershell
cd C:\Projets\docker\observations_nids\docker
```

#### a) Construire les images Docker

```powershell
docker compose build
# OU avec le script
.\docker-dev.ps1 build
```

#### b) Démarrer tous les services

```powershell
docker compose up -d
# OU avec le script
.\docker-dev.ps1 up
```

#### c) Appliquer les migrations de base de données

```powershell
docker compose exec web python manage.py migrate
```

#### d) Créer le superutilisateur (si pas créé automatiquement)

```powershell
docker compose exec web python manage.py createsuperuser
```

Ou utiliser les credentials du fichier .env :
- Username: `admin`
- Password: `admin123`

#### e) Charger les données de référence

```powershell
# Communes françaises
docker compose exec web python manage.py charger_communes_france

# Espèces TAXREF (optionnel, peut être long)
docker compose exec web python manage.py charger_taxref

# Codes GONM
docker compose exec web python manage.py import_codes_gonm
```

#### f) Collecter les fichiers statiques

```powershell
docker compose exec web python manage.py collectstatic --noinput
```

### 2. Démarrage quotidien

```powershell
cd C:\Projets\docker\observations_nids\docker
docker compose up -d
# OU avec le script
.\docker-dev.ps1 up
```

### 3. Arrêt de l'application

```powershell
docker compose down
# OU avec le script
.\docker-dev.ps1 down
```

### 4. Arrêt complet avec suppression des volumes (⚠️ Supprime la BDD)

```powershell
docker compose down -v
```

## Accès aux services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Application Django** | http://localhost:8010 | admin / admin123 |
| **Application directe** | http://localhost:8000 | admin / admin123 |
| **phpMyAdmin** | http://localhost:8081 | root / root_dev_password_123 |
| **Flower (Celery)** | http://localhost:5555 | - |

## Commandes utiles

### Logs des services

```powershell
# Tous les services
docker compose logs -f
# OU avec le script
.\docker-dev.ps1 logs

# Un service spécifique
docker compose logs -f web
docker compose logs -f celery_worker
docker compose logs -f db
```

### Shell Django

```powershell
docker compose exec web python manage.py shell
# OU avec le script
.\docker-dev.ps1 shell
```

### Shell Bash dans le container

```powershell
docker compose exec web bash
# OU avec le script
.\docker-dev.ps1 bash
```

### Créer des migrations

```powershell
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
# OU avec le script pour migrate uniquement
.\docker-dev.ps1 migrate
```

### Exécuter les tests

```powershell
docker compose exec web python manage.py test
# OU avec le script
.\docker-dev.ps1 test
```

### Reconstruire les images après modification du Dockerfile

```powershell
docker compose build --no-cache
docker compose up -d
# OU avec le script
.\docker-dev.ps1 build
.\docker-dev.ps1 up
```

## Script PowerShell docker-dev.ps1

Le projet inclut déjà un script PowerShell `docker-dev.ps1` qui simplifie toutes les commandes Docker.

**Commandes disponibles** :

| Commande | Description |
|----------|-------------|
| `.\docker-dev.ps1 up` | Démarrer les services |
| `.\docker-dev.ps1 down` | Arrêter les services |
| `.\docker-dev.ps1 restart` | Redémarrer les services |
| `.\docker-dev.ps1 logs` | Afficher les logs |
| `.\docker-dev.ps1 build` | Reconstruire les images |
| `.\docker-dev.ps1 shell` | Ouvrir un shell Django |
| `.\docker-dev.ps1 bash` | Ouvrir un shell Bash |
| `.\docker-dev.ps1 migrate` | Appliquer les migrations |
| `.\docker-dev.ps1 test` | Exécuter les tests |
| `.\docker-dev.ps1 collectstatic` | Collecter les fichiers statiques |

**Avantages** :
- Messages colorés et informatifs
- Vérification des erreurs
- Affichage des URLs des services au démarrage
- Plus simple que les commandes docker compose complètes

## Développement avec hot-reload

En mode développement (`docker-compose.dev.yml`), le code source est monté dans le container.

**Toute modification du code Python sera automatiquement rechargée** grâce à `runserver`.

## Troubleshooting

### Erreur 502 Bad Gateway

**Symptôme** : Erreur 502 lors de l'accès à http://localhost:8010

**Cause possible** : Les services web/celery crashent au démarrage

**Diagnostic** :
```powershell
docker compose ps
docker compose logs web
```

**Solutions courantes** :

1. **ModuleNotFoundError: No module named 'debug_toolbar'**

   Éditer le fichier `.env` **à la racine du projet** et vérifier :
   ```
   USE_DEBUG_TOOLBAR=False
   ```

   Puis redémarrer :
   ```powershell
   docker compose down
   docker compose up -d
   ```

2. **Autres erreurs Python**

   Vérifier les logs pour identifier le module manquant ou l'erreur de configuration.

### Services en état "Restarting"

Si certains services (web, celery_worker, celery_beat, flower) sont en état "Restarting" :

1. Vérifier les logs du service problématique :
   ```powershell
   docker compose logs --tail=50 web
   docker compose logs --tail=50 celery_worker
   ```

2. Vérifier que toutes les variables d'environnement nécessaires sont définies dans `.env`

3. Si le problème persiste, reconstruire les images :
   ```powershell
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

### Port déjà utilisé

Si un port est déjà utilisé (8010, 8000, 3306, 6379, 5555, 8081), modifier les ports dans `docker-compose.yml` ou `docker-compose.dev.yml`.

### Permission denied sur les volumes

Docker Desktop sur Windows gère automatiquement les permissions. Si problème, vérifier que Docker Desktop a accès au lecteur C:\ dans les paramètres.

### Base de données corrompue

```powershell
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
```

### Rebuild complet (réinitialisation totale)

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## Différences avec l'environnement Pilote

| Aspect | Pilote (Ubuntu) | Développement (Windows) |
|--------|-----------------|------------------------|
| OS | Ubuntu Server | Windows 11 + Docker Desktop |
| IP | 192.168.1.112 | localhost uniquement |
| DEBUG | False | True |
| Base de données | observations_nids | observations_nids_dev |
| Serveur web | Gunicorn | Django runserver |
| Hot-reload | Non | Oui |
| HTTPS | Oui | Non |
| Email | SMTP Brevo | Console backend |

## Configuration avancée

### Activer l'OCR Gemini

Éditer le fichier `.env` **à la racine du projet** (`C:\Projets\docker\observations_nids\.env`) et ajouter votre clé API :

```
GEMINI_API_KEY=votre-vraie-cle-api-ici
```

Puis redémarrer les services :

```powershell
cd C:\Projets\docker\observations_nids\docker
docker compose restart
# OU avec le script
.\docker-dev.ps1 restart
```

### Configurer l'envoi d'emails

Éditer le fichier `.env` **à la racine du projet** et configurer SMTP :

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-application
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

Puis redémarrer les services pour appliquer les changements.

### Variables d'environnement importantes

Le fichier `.env` à la racine contient toutes les variables de configuration :

| Variable | Description | Valeur par défaut dev |
|----------|-------------|-----------------------|
| `DEBUG` | Mode debug Django | `True` |
| `SECRET_KEY` | Clé secrète Django | `dev-secret-key-change-me-in-production-only` |
| `DB_NAME` | Nom de la base de données | `observations_nids_dev` |
| `DB_USER` | Utilisateur MySQL | `observations_user` |
| `DB_PASSWORD` | Mot de passe MySQL | `dev_password_123` |
| `USE_DEBUG_TOOLBAR` | Activer Django Debug Toolbar | `False` (module non installé) |
| `GEMINI_API_KEY` | Clé API Google Gemini pour OCR | (vide par défaut) |
| `ENVIRONMENT` | Environnement (development/pilote/production) | `development` |

## Support

Pour toute question, consulter :
- Documentation MkDocs : En mode développement, lancer `mkdocs serve` dans un terminal séparé
- CLAUDE.md à la racine du projet
- README.md du répertoire docker
