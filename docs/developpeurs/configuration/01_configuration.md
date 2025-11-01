# Guide de Configuration du Projet

Ce document explique l'architecture de configuration du projet, qui repose sur une combinaison de `python-dotenv`, Pydantic, et des fichiers de settings Django.

## 1. Philosophie de Configuration

L'objectif est d'avoir une configuration :

- **Sécurisée** : Les secrets (clés d'API, mots de passe) ne sont jamais versionnés dans Git.
- **Robuste** : Les variables d'environnement sont validées et typées au démarrage de l'application grâce à Pydantic.
- **Flexible** : Permet des configurations différentes pour le développement, les tests et la production.
- **Documentée** : La configuration sert elle-même de documentation.

## 2. Fichiers de Configuration Principaux

| Fichier | Rôle |
|---|---|
| `.env` | **Stocke les secrets** et les variables spécifiques à un environnement. **Ne doit jamais être versionné.** |
| `.env.example` | **Sert de modèle** pour `.env`. Il est versionné et liste toutes les variables nécessaires. |
| `observations_nids/config.py` | **Définit la structure** de la configuration avec des modèles Pydantic. Valide et charge les variables depuis `.env`. |
| `observations_nids/settings.py` | **Fichier de settings Django principal**. Il consomme la configuration validée par `config.py`. |
| `settings_local.py` | (Optionnel) Fichier local **non versionné** pour surcharger rapidement des settings sans modifier `.env`. |
| `pyproject.toml` | **Configure les outils de développement** comme `ruff`, `black`, et `mypy`. |

---

## 3. Variables d'Environnement (dans `.env`)

Pour configurer votre environnement local, copiez `.env.example` en `.env` et modifiez les valeurs.

```bash
cp .env.example .env
```

Voici la liste des variables disponibles :

| Variable | Description |
|---|---|
| `SECRET_KEY` | **(Requis)** Clé secrète de Django pour la sécurité. Doit être unique et complexe. |
| `DEBUG` | **(Requis)** Active le mode débogage de Django (`True` ou `False`). Mettre à `False` en production. |
| `ALLOWED_HOSTS` | Liste des noms d'hôtes autorisés, séparés par des virgules (ex: `localhost,127.0.0.1`). |
| `DB_NAME` | Nom de la base de données MariaDB/MySQL. |
| `DB_USER` | Nom d'utilisateur pour la base de données. |
| `DB_PASSWORD` | Mot de passe pour la base de données. |
| `DB_HOST` | Adresse IP ou nom d'hôte du serveur de base de données. |
| `DB_PORT` | Port du serveur de base de données (défaut : `3306`). |
| `USE_DEBUG_TOOLBAR` | Active la Django Debug Toolbar (`True` ou `False`). |
| `SESSION_COOKIE_AGE` | Durée de vie des cookies de session en secondes (défaut : `3600`). |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | Expirer la session à la fermeture du navigateur (`True` ou `False`). |
| `DJANGO_LOG_DIR` | (Optionnel) Chemin absolu pour les fichiers de log en production. |
| `DJANGO_STATIC_ROOT`| (Optionnel) Chemin absolu pour les fichiers statiques collectés. |
| `DJANGO_MEDIA_ROOT` | (Optionnel) Chemin absolu pour les fichiers média uploadés. |

---

## 4. Configuration des Outils (`pyproject.toml`)

Ce fichier centralise la configuration des outils de qualité de code.

### `[tool.black]`
- **Rôle** : Formateur de code automatique.
- **Configuration** : `line-length = 100` pour autoriser des lignes légèrement plus longues.

### `[tool.ruff]`
- **Rôle** : Linter ultra-rapide qui remplace `flake8`, `isort`, et d'autres outils.
- **Configuration** : Active un ensemble de règles de qualité (`E`, `F`, `I`, `UP`, `B`, `DJ`...) et ignore certaines règles pour rester compatible avec `black`.

### `[tool.mypy]`
- **Rôle** : Analyseur de type statique.
- **Configuration** : Active des vérifications strictes (`no_implicit_optional`, `check_untyped_defs`) et utilise le plugin `mypy_django_plugin` pour comprendre le code Django.

---

## 5. Guide : Ajouter une Nouvelle Configuration

Voici les étapes pour ajouter une nouvelle variable de configuration (ex: `GOOGLE_API_KEY`).

1.  **Ajouter la variable dans `.env.example`** (avec une valeur vide ou par défaut) :
    ```env
    # .env.example
    GOOGLE_API_KEY=
    ```

2.  **Ajouter la variable dans votre `.env` local** (avec la vraie valeur) :
    ```env
    # .env
    GOOGLE_API_KEY=votre-vraie-cle-api
    ```

3.  **Ajouter le champ au modèle Pydantic** dans `observations_nids/config.py` :
    ```python
    # observations_nids/config.py
    class Settings(BaseSettings):
        # ...
        GOOGLE_API_KEY: str | None = None # Rendre optionnel si elle n'est pas toujours requise
        # ...
    ```

4.  **Utiliser la variable dans `observations_nids/settings.py`** :
    ```python
    # observations_nids/settings.py
    settings = get_settings()
    
    # ...
    GOOGLE_API_KEY = settings.GOOGLE_API_KEY
    ```

L'application aura maintenant accès à `settings.GOOGLE_API_KEY` avec la garantie qu'elle a été chargée et validée correctement.
