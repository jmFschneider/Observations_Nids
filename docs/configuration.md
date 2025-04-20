# Configuration avec Pydantic et python-dotenv

Ce document explique comment utiliser le nouveau système de configuration basé sur Pydantic et python-dotenv pour le projet Observations_Nids.

## Aperçu

Le projet utilise maintenant Pydantic pour valider les paramètres de configuration et python-dotenv pour charger les variables d'environnement à partir d'un fichier `.env`. Cela permet de :

1. Sécuriser les informations sensibles (clés secrètes, identifiants de base de données)
2. Faciliter la configuration entre différents environnements (développement, test, production)
3. Valider les paramètres de configuration pour éviter les erreurs
4. Fournir une documentation claire des paramètres disponibles

## Fichiers de configuration

### `.env`

Ce fichier contient les variables d'environnement utilisées par l'application. Il ne doit pas être commité dans le dépôt Git car il contient des informations sensibles.

Exemple de contenu :

```
# Core Django settings
SECRET_KEY=django-insecure-^tzqm_vr2-7f#2p10rehlk4pr9!z8z^!3atbbwq@2!%h_$n2f0
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,observation-nids.meteo-poelley50.fr

# Database settings
DB_NAME=NidsObservation
DB_USER=jms
DB_PASSWORD=pointeur
DB_HOST=192.168.1.176
DB_PORT=3306

# Custom settings
USE_DEBUG_TOOLBAR=False
SESSION_COOKIE_AGE=3600
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
```

### `.env.example`

Ce fichier sert de modèle pour créer le fichier `.env`. Il contient les mêmes variables mais avec des valeurs par défaut ou des placeholders. Ce fichier peut être commité dans le dépôt Git.

### `config.py`

Ce fichier contient le modèle Pydantic pour la validation des paramètres de configuration. Il définit :

- Les types de données attendus pour chaque paramètre
- Les valeurs par défaut
- Les validateurs pour certains paramètres

## Utilisation

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration de l'environnement

1. Copiez le fichier `.env.example` vers `.env`
2. Modifiez les valeurs dans `.env` selon votre environnement

### Accès aux paramètres dans le code

Dans `settings.py`, les paramètres sont accessibles via l'objet `settings` :

```python
from .config import get_settings

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
DATABASES = settings.get_database_config()
```

## Paramètres disponibles

### Core Django settings

- `SECRET_KEY` : Clé secrète utilisée par Django pour la sécurité
- `DEBUG` : Mode de débogage (True/False)
- `ALLOWED_HOSTS` : Liste des hôtes autorisés à servir l'application

### Database settings

- `DB_NAME` : Nom de la base de données
- `DB_USER` : Nom d'utilisateur pour la connexion à la base de données
- `DB_PASSWORD` : Mot de passe pour la connexion à la base de données
- `DB_HOST` : Hôte de la base de données
- `DB_PORT` : Port de la base de données

### Custom settings

- `USE_DEBUG_TOOLBAR` : Activer la barre de débogage Django (True/False)
- `SESSION_COOKIE_AGE` : Durée de vie des cookies de session en secondes
- `SESSION_EXPIRE_AT_BROWSER_CLOSE` : Expirer la session à la fermeture du navigateur (True/False)

## Ajout de nouveaux paramètres

Pour ajouter un nouveau paramètre de configuration :

1. Ajoutez-le dans le modèle Pydantic dans `config.py`
2. Ajoutez-le dans `.env` et `.env.example`
3. Utilisez-le dans `settings.py` via l'objet `settings`

Exemple :

```python
# Dans config.py
class Settings(BaseSettings):
    # ...
    NEW_SETTING: str = "default_value"
    
# Dans .env et .env.example
NEW_SETTING=value

# Dans settings.py
NEW_SETTING = settings.NEW_SETTING
```