# Guide de Démarrage - Développement Windows 11

## Installation effectuée

✅ Projet cloné dans `C:\projets\docker\observations_nids`
✅ Fichier `.env` créé avec configuration de développement
✅ Fichier `docker-compose.windows.yml` créé pour adapter les chemins
✅ Répertoires `logs` et `media` créés

## Prérequis

- Docker Desktop installé et démarré sur Windows 11
- WSL2 activé (recommandé pour Docker Desktop)

## Structure de l'installation

```
C:\projets\docker\observations_nids\
├── docker/
│   ├── .env                          # Configuration développement
│   ├── docker-compose.yml            # Configuration de base
│   ├── docker-compose.dev.yml        # Override développement
│   ├── docker-compose.windows.yml    # Override Windows (chemins)
│   └── ...
├── logs/                             # Logs applicatifs
├── media/                            # Fichiers uploadés
└── ...
```

## Démarrage de l'application

### 1. Première installation

Ouvrir un terminal PowerShell ou CMD dans le répertoire docker :

```powershell
cd C:\projets\docker\observations_nids\docker
```

#### a) Construire les images Docker

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml build
```

#### b) Démarrer tous les services

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml up -d
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
cd C:\projets\docker\observations_nids\docker
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml up -d
```

### 3. Arrêt de l'application

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml down
```

### 4. Arrêt complet avec suppression des volumes (⚠️ Supprime la BDD)

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml down -v
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
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml logs -f

# Un service spécifique
docker compose logs -f web
docker compose logs -f celery_worker
docker compose logs -f db
```

### Shell Django

```powershell
docker compose exec web python manage.py shell
```

### Shell Bash dans le container

```powershell
docker compose exec web bash
```

### Créer des migrations

```powershell
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Exécuter les tests

```powershell
docker compose exec web python manage.py test
```

### Reconstruire les images après modification du Dockerfile

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml up -d
```

## Alias PowerShell (optionnel)

Pour simplifier les commandes, vous pouvez créer un alias PowerShell.

Éditer votre profil PowerShell :

```powershell
notepad $PROFILE
```

Ajouter ces fonctions :

```powershell
function dcup {
    docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml up -d
}
function dcdown {
    docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml down
}
function dclogs {
    docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml logs -f
}
function dcbuild {
    docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml build
}
function dcexec {
    param($service, [Parameter(ValueFromRemainingArguments)]$cmd)
    docker compose exec $service $cmd
}
```

Ensuite, utiliser simplement :

```powershell
dcup          # Démarrer
dcdown        # Arrêter
dclogs        # Voir les logs
dcbuild       # Reconstruire
dcexec web python manage.py migrate  # Exécuter une commande
```

## Développement avec hot-reload

En mode développement (`docker-compose.dev.yml`), le code source est monté dans le container.

**Toute modification du code Python sera automatiquement rechargée** grâce à `runserver`.

## Troubleshooting

### Port déjà utilisé

Si un port est déjà utilisé (8010, 8000, 3306, 6379, 5555, 8081), modifier les ports dans `docker-compose.yml` ou `docker-compose.dev.yml`.

### Permission denied sur les volumes

Docker Desktop sur Windows gère automatiquement les permissions. Si problème, vérifier que Docker Desktop a accès au lecteur C:\ dans les paramètres.

### Base de données corrompue

```powershell
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml up -d
docker compose exec web python manage.py migrate
```

### Rebuild complet

```powershell
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml up -d
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

Éditer `docker/.env` et ajouter votre clé API :

```
GEMINI_API_KEY=votre-vraie-cle-api-ici
```

Puis redémarrer les services :

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml restart
```

### Configurer l'envoi d'emails

Éditer `docker/.env` et configurer SMTP :

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-application
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

## Support

Pour toute question, consulter :
- Documentation MkDocs : En mode développement, lancer `mkdocs serve` dans un terminal séparé
- CLAUDE.md à la racine du projet
- README.md du répertoire docker
