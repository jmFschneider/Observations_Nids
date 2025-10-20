# Guide d'Installation - Environnement de Développement

Ce document vous guide pour mettre en place un environnement de développement local pour le projet "Observations Nids".

## 1. Prérequis

Avant de commencer, assurez-vous d'avoir les outils suivants installés sur votre machine :

*   **Python** (version 3.11 ou supérieure recommandée)
*   **Git**
*   **Redis** : Nécessaire pour le fonctionnement des tâches de fond.
*   **MariaDB** ou **SQLite** : Le projet peut fonctionner avec l'une de ces deux bases de données.

## 2. Installation

### Étape 2.1 : Cloner le Dépôt

Ouvrez un terminal et clonez le projet depuis GitHub :

```bash
git clone https://github.com/jmFschneider/Observations_Nids.git
cd Observations_Nids
```

### Étape 2.2 : Créer et Activer l'Environnement Virtuel

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

### Étape 2.3 : Installer les Dépendances

Installez les dépendances de développement, qui incluent les outils de test et de débogage.

```bash
pip install -r requirements-dev.txt
```

### Étape 2.4 : Configurer les Variables d'Environnement

1.  **Copiez le fichier d'exemple :**
    ```bash
    # Sur Windows
    copy .env.example .env
    # Sur macOS/Linux
    cp .env.example .env
    ```

2.  **Modifiez le fichier `.env`** pour configurer votre environnement.

    *   **Base de données :**
        *   **Pour SQLite (défaut) :** Aucune configuration supplémentaire n'est nécessaire. Le fichier de base de données sera créé automatiquement.
        *   **Pour MariaDB :** Modifiez les variables `DB_*` avec les informations de votre serveur MariaDB.
          ```
          DB_ENGINE=django.db.backends.mysql
          DB_NAME=votre_db
          DB_USER=votre_user
          DB_PASSWORD=votre_mdp
          DB_HOST=localhost
          DB_PORT=3306
          ```

    *   **Autres configurations :**
        *   Générez une nouvelle `SECRET_KEY` Django.
        *   Configurez les clés d'API pour les services externes (ex: Google).

### Étape 2.5 : Préparer la Base de Données

Exécutez les migrations pour créer les tables de la base de données.

```bash
python manage.py migrate
```

### Étape 2.6 : Créer un Super-Utilisateur

Créez un compte administrateur pour accéder à l'interface d'administration.

```bash
python manage.py createsuperuser
```

## 3. Lancement des Services

Pour un fonctionnement complet, lancez les services suivants dans des terminaux distincts.

### Rôle de Redis et Celery

*   **Redis** : Agit comme un "courtier" (broker). Il reçoit les demandes de tâches de fond (ex: transcription de fichiers audio) de l'application Django et les met dans une file d'attente.
*   **Celery** : Est un "travailleur" (worker). Il surveille la file d'attente Redis, prend les tâches une par une et les exécute de manière asynchrone, sans bloquer l'application principale.

### Terminal 1 - Serveur Redis

```bash
redis-server
```

### Terminal 2 - Worker Celery

```bash
celery -A observations_nids worker --loglevel=info
```

### Terminal 3 - Serveur Django

```bash
python manage.py runserver
```

## 4. Accès à l'application

*   **Application :** [http://127.0.0.1:8000](http://127.0.0.1:8000)
*   **Admin :** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
