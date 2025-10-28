# Guide d'Installation - Environnement de Développement

Ce document vous guide pour mettre en place un environnement de développement local pour le projet "Observations Nids".

---

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Lancement des services](#lancement-des-services)
5. [Accès à l'application](#accès-à-lapplication)
6. [Commandes utiles](#commandes-utiles)
7. [Dépannage](#dépannage)

---

## 1. Prérequis

Avant de commencer, assurez-vous d'avoir les outils suivants installés sur votre machine :

- **Python** 3.11 ou supérieur (recommandé : 3.12)
- **Git** pour cloner le dépôt
- **Redis** pour les tâches asynchrones avec Celery
- **MariaDB** ou **SQLite** (le projet fonctionne avec les deux)
- Un client de base de données compatible MariaDB/MySQL (optionnel, pour accès direct)

### Installation de Redis

**Windows :**
```bash
# Télécharger depuis https://github.com/microsoftarchive/redis/releases
# Ou utiliser WSL et installer via apt
```

**macOS :**
```bash
brew install redis
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt-get install redis-server
```

---

## 2. Installation

### Étape 2.1 : Cloner le dépôt

Ouvrez un terminal et clonez le projet depuis GitHub :

```bash
git clone https://github.com/jmFschneider/Observations_Nids.git
cd Observations_Nids
```

### Étape 2.2 : Créer et activer l'environnement virtuel

Il est crucial de travailler dans un environnement virtuel pour isoler les dépendances du projet.

```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement
# Sur Windows (PowerShell/CMD)
.venv\Scripts\activate

# Sur macOS/Linux (Bash)
source .venv/bin/activate
```

Une fois activé, votre terminal devrait afficher `(.venv)` au début de la ligne de commande.

### Étape 2.3 : Installer les dépendances

Le projet utilise `requirements-dev.txt` pour le développement, qui inclut toutes les dépendances de base plus les outils de test, linting et débogage.

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

**Dépendances installées :**
- Django 5.x
- Celery (tâches asynchrones)
- Pytest (tests)
- Ruff (linting)
- MyPy (vérification de types)
- Et autres...

---

## 3. Configuration

### Étape 3.1 : Configurer les variables d'environnement

Le projet utilise un fichier `.env` pour gérer les configurations sensibles (clés d'API, secrets, etc.).

1. **Copiez le fichier d'exemple :**
   ```bash
   # Sur Windows
   copy .env.example .env

   # Sur macOS/Linux
   cp .env.example .env
   ```

2. **Modifiez le fichier `.env`** avec un éditeur de texte :

   ```env
   # Configuration Django
   SECRET_KEY=votre-cle-secrete-aleatoire-ici
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Base de données (SQLite par défaut)
   DB_ENGINE=django.db.backends.sqlite3
   DB_NAME=db.sqlite3

   # Pour MariaDB (décommenter et configurer)
   # DB_ENGINE=django.db.backends.mysql
   # DB_NAME=observations_nids
   # DB_USER=votre_user
   # DB_PASSWORD=votre_password
   # DB_HOST=localhost
   # DB_PORT=3306

   # Redis (pour Celery)
   REDIS_HOST=localhost
   REDIS_PORT=6379

   # Email (optionnel pour dev)
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

   # API Google (si vous utilisez la transcription)
   GOOGLE_API_KEY=votre-cle-api-google
   ```

3. **Générer une SECRET_KEY** :
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

### Étape 3.2 : Configuration de la base de données

**Option A - SQLite (par défaut, aucune configuration requise)**

Le fichier `db.sqlite3` sera créé automatiquement lors des migrations.

**Option B - MariaDB (recommandé pour la production)**

1. Créer la base de données :
   ```sql
   CREATE DATABASE observations_nids CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'votre_user'@'localhost' IDENTIFIED BY 'votre_password';
   GRANT ALL PRIVILEGES ON observations_nids.* TO 'votre_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. Modifier le fichier `.env` avec les paramètres MariaDB (voir ci-dessus).

### Étape 3.3 : Préparer la base de données

Exécutez les migrations Django pour créer les tables :

```bash
python manage.py migrate
```

### Étape 3.4 : Créer un super-utilisateur

Pour accéder à l'interface d'administration Django :

```bash
python manage.py createsuperuser
```

Suivez les instructions pour définir :
- Nom d'utilisateur
- Adresse e-mail
- Mot de passe

### Étape 3.5 : Charger les données initiales (optionnel)

Si vous avez des fixtures ou des données de démo :

```bash
# Charger les données taxonomiques (si disponible)
python manage.py loaddata taxonomy/fixtures/initial_data.json

# Importer TaxRef ou autres données
python manage.py charger_taxref --file chemin/vers/TAXREFv17.txt
```

---

## 4. Lancement des services

Pour un fonctionnement complet de l'application, vous devez lancer **3 services** dans 3 terminaux distincts.

### Rôle de Redis et Celery

- **Redis** : Agit comme un courtier (broker). Il reçoit les demandes de tâches de fond (ex: transcription OCR, envoi d'emails) de l'application Django et les met dans une file d'attente.
- **Celery** : Est un travailleur (worker). Il surveille la file d'attente Redis, prend les tâches une par une et les exécute de manière asynchrone, sans bloquer l'application principale.

### Terminal 1 - Serveur Redis

```bash
redis-server

# Ou sur certains systèmes
sudo systemctl start redis
```

**Vérifier que Redis fonctionne :**
```bash
redis-cli ping
# Devrait retourner: PONG
```

### Terminal 2 - Worker Celery

```bash
# Assurez-vous que l'environnement virtuel est activé
celery -A observations_nids worker --loglevel=info

# Sur Windows, utiliser :
celery -A observations_nids worker --pool=solo --loglevel=info
```

**Vous devriez voir :**
```
celery@hostname ready.
```

### Terminal 3 - Serveur Django

```bash
python manage.py runserver

# Pour écouter sur toutes les interfaces (accès depuis autre machine)
python manage.py runserver 0.0.0.0:8000
```

**Vous devriez voir :**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## 5. Accès à l'application

Félicitations ! 🎉 Votre environnement de développement est prêt.

- **Application principale** : [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interface d'administration** : [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **Documentation (si MkDocs lancé)** : [http://127.0.0.1:8001](http://127.0.0.1:8001)

### Première connexion

1. Ouvrez [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
2. Connectez-vous avec le super-utilisateur créé à l'étape 3.4
3. Explorez l'interface d'administration

---

## 6. Commandes utiles

### Tests

```bash
# Lancer tous les tests
pytest

# Lancer les tests avec couverture
pytest --cov

# Lancer un test spécifique
pytest observations/tests/test_models.py

# Lancer les tests d'une application
pytest observations/
```

### Qualité du code

```bash
# Vérifier le code avec Ruff
ruff check .

# Corriger automatiquement les problèmes
ruff check --fix .

# Vérifier le formatage
ruff format --check .

# Formater le code
ruff format .

# Vérifier le typage statique
mypy .
```

### Base de données

```bash
# Créer une nouvelle migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Afficher l'état des migrations
python manage.py showmigrations

# Revenir à une migration spécifique
python manage.py migrate app_name migration_name

# Réinitialiser la base de données (ATTENTION: perte de données)
python manage.py flush
```

### Gestion des utilisateurs

```bash
# Créer un super-utilisateur
python manage.py createsuperuser

# Changer le mot de passe d'un utilisateur
python manage.py changepassword username
```

### Fichiers statiques

```bash
# Collecter les fichiers statiques (pour production)
python manage.py collectstatic

# Nettoyer les anciens fichiers statiques
python manage.py collectstatic --clear --noinput
```

### Django shell

```bash
# Ouvrir un shell Python avec Django chargé
python manage.py shell

# Ouvrir un shell Python avec IPython
python manage.py shell_plus
```

### Celery

```bash
# Lancer le worker avec rechargement automatique
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A observations_nids worker --loglevel=info

# Purger toutes les tâches en attente
celery -A observations_nids purge

# Inspecter les workers actifs
celery -A observations_nids inspect active
```

---

## 7. Dépannage

### Problèmes courants

| Problème | Cause | Solution |
|----------|-------|----------|
| `ModuleNotFoundError` | Environnement virtuel non activé ou dépendances manquantes | 1. Vérifiez que `(.venv)` apparaît dans le terminal<br>2. Lancez `.venv\Scripts\activate`<br>3. Réinstallez : `pip install -r requirements-dev.txt` |
| Erreur de connexion à Redis | Redis non démarré | Lancez `redis-server` dans un terminal séparé |
| `redis.exceptions.ConnectionError` | Redis pas sur le port par défaut | Vérifiez `REDIS_HOST` et `REDIS_PORT` dans `.env` |
| Erreur de migration | Base de données corrompue ou migrations incohérentes | **Développement uniquement** :<br>1. Supprimez `db.sqlite3`<br>2. Relancez `python manage.py migrate`<br>**⚠️ Ne JAMAIS faire en production !** |
| Port 8000 déjà utilisé | Autre processus sur le port | Utilisez un autre port : `python manage.py runserver 8001`<br>Ou tuez le processus : `taskkill /F /IM python.exe` (Windows) |
| Tâches Celery non exécutées | Worker Celery non lancé | 1. Vérifiez que Redis fonctionne (`redis-cli ping`)<br>2. Lancez le worker : `celery -A observations_nids worker --loglevel=info` |
| `SECRET_KEY` manquante | Fichier `.env` absent ou mal configuré | 1. Copiez `.env.example` vers `.env`<br>2. Générez une clé : `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| Erreur d'encodage UTF-8 | Fichiers avec mauvais encodage | Assurez-vous que votre éditeur utilise UTF-8 sans BOM |
| `OperationalError: no such table` | Migrations non appliquées | Lancez `python manage.py migrate` |
| Fichiers statiques non chargés | Collecte des statiques manquante | En dev, Django les sert automatiquement si `DEBUG=True`<br>En prod : `python manage.py collectstatic` |

### Vérifier l'installation

Pour vérifier que tout est correctement installé :

```bash
# 1. Vérifier Python
python --version
# Devrait afficher : Python 3.11.x ou 3.12.x

# 2. Vérifier que l'environnement virtuel est activé
where python  # Windows
which python  # macOS/Linux
# Devrait pointer vers .venv

# 3. Vérifier Redis
redis-cli ping
# Devrait retourner : PONG

# 4. Vérifier les dépendances Django
python manage.py check
# Devrait retourner : System check identified no issues

# 5. Vérifier la base de données
python manage.py showmigrations
# Devrait lister toutes les migrations avec [X]

# 6. Vérifier Celery
celery -A observations_nids inspect ping
# Devrait retourner : pong
```

### Réinitialisation complète (développement uniquement)

Si vous rencontrez des problèmes persistants :

```bash
# 1. Supprimer l'environnement virtuel
rm -rf .venv  # macOS/Linux
rmdir /s .venv  # Windows

# 2. Supprimer la base de données SQLite
rm db.sqlite3  # macOS/Linux
del db.sqlite3  # Windows

# 3. Recréer l'environnement
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 4. Réinstaller les dépendances
pip install -r requirements-dev.txt

# 5. Refaire les migrations
python manage.py migrate

# 6. Recréer le super-utilisateur
python manage.py createsuperuser
```

---

## 📚 Prochaines étapes

- Consultez le [Guide de contribution](../learning/git/README.md) pour comprendre le workflow Git
- Lisez la [Stratégie de tests](../testing/STRATEGIE_TESTS.md) avant d'écrire du code
- Explorez l'[Architecture du projet](../architecture/index.md) pour comprendre la structure
- Consultez la [Documentation API](../api/API_DOCUMENTATION.md) pour les endpoints

---

## 🆘 Besoin d'aide ?

- Consultez la [section Troubleshooting](../learning/troubleshooting/README.md)
- Vérifiez les [Issues GitHub](https://github.com/jmFschneider/Observations_Nids/issues)
- Contactez l'équipe de développement

---

**Document mis à jour le** : 24/10/2025
**Version** : 2.0 (consolidé)
