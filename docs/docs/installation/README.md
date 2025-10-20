# Guide d'Installation - Observations Nids

Ce document décrit la procédure complète pour installer et lancer le projet "Observations Nids" sur un nouvel environnement.

[TOC]

---

## 1. Prérequis

Avant de commencer, assurez-vous d'avoir les outils suivants installés sur votre machine :

*   **Python** (version 3.11 ou supérieure recommandée)
*   **Git**
*   **Redis** (pour les tâches asynchrones avec Celery)
*   Un client de base de données compatible **MariaDB/MySQL** (optionnel, pour un accès direct à la BDD)

---

## 2. Installation pour le Développement

Cette section vous guide pour mettre en place un environnement de développement local.

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
Une fois activé, votre terminal devrait afficher `(.venv)` au début de la ligne de commande.

### Étape 2.3 : Installer les Dépendances

Le projet utilise des fichiers `requirements` séparés pour le développement et la production. Pour un environnement de développement, installez `requirements-dev.txt` qui inclut toutes les dépendances de base, plus les outils de test, de linting et de débogage.

```bash
pip install -r requirements-dev.txt
```

### Étape 2.4 : Configurer les Variables d'Environnement

Le projet utilise un fichier `.env` pour gérer les configurations sensibles (clés d'API, secrets, etc.).

1.  **Copiez le fichier d'exemple :**
    ```bash
    # Sur Windows
    copy .env.example .env
    # Sur macOS/Linux
    cp .env.example .env
    ```

2.  **Modifiez le fichier `.env`** avec un éditeur de texte et remplissez les valeurs, notamment pour :
    *   `SECRET_KEY` (générez une nouvelle clé secrète Django)
    *   `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` pour votre base de données locale.
    *   Les clés d'API pour Google (si vous utilisez les fonctionnalités associées).

### Étape 2.5 : Préparer la Base de Données

Exécutez les migrations Django pour créer les tables de la base de données.

```bash
python manage.py migrate
```

### Étape 2.6 : Créer un Super-Utilisateur

Pour accéder à l'interface d'administration Django, vous devez créer un compte administrateur.

```bash
python manage.py createsuperuser
```
Suivez les instructions pour définir un nom d'utilisateur, une adresse e-mail et un mot de passe.

### Étape 2.7 : Lancer les Services

Pour que toutes les fonctionnalités du projet (notamment la transcription asynchrone) fonctionnent, vous devez lancer 3 services dans 3 terminaux distincts :

**Terminal 1 - Serveur Redis (Broker Celery) :**
```bash
# Assurez-vous que Redis est installé et dans votre PATH
redis-server
```

**Terminal 2 - Worker Celery :**
```bash
# Ce terminal surveille les tâches à exécuter
celery -A observations_nids worker --loglevel=info
```

**Terminal 3 - Serveur Django :**
```bash
python manage.py runserver
```

### Étape 2.8 : Accéder à l'application

Félicitations ! Tout est prêt. Vous pouvez maintenant accéder à l'application à l'adresse [http://127.0.0.1:8000](http://127.0.0.1:8000).
L'interface d'administration est disponible à l'adresse [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

---

## 3. Installation pour la Production

L'installation en production est similaire mais utilise des dépendances optimisées et un serveur d'application WSGI comme Gunicorn.

1.  **Suivez les étapes 2.1, 2.2 et 2.4** de l'installation de développement.

2.  **Installez les dépendances de production :**
    ```bash
    pip install -r requirements-prod.txt
    ```
    Ce fichier inclut `gunicorn` et exclut les outils de débogage.

3.  **Exécutez les migrations et créez un super-utilisateur** (étapes 2.5 et 2.6) si ce n'est pas déjà fait.

4.  **Collectez les fichiers statiques :**
    ```bash
    python manage.py collectstatic
    ```

5.  **Lancez le serveur Gunicorn :**
    Assurez-vous que votre fichier `.env` est correctement configuré pour l'environnement de production (par exemple, `DEBUG=False`).

    ```bash
    gunicorn observations_nids.wsgi:application
    ```
    Pour une configuration plus robuste, il est recommandé d'utiliser Gunicorn avec un service `systemd` et un reverse proxy comme Nginx.

---

## 4. Commandes Utiles

*   **Lancer les tests :**
    ```bash
    pytest
    ```

*   **Vérifier la qualité du code (linting) :**
    ```bash
    ruff check .
    ```

*   **Vérifier le typage statique :**
    ```bash
    mypy .
    ```

---

## 5. Dépannage

| Problème | Solution |
|---|---|
| `ModuleNotFoundError` | Vérifiez que l'environnement virtuel est activé (`.venv\Scripts\activate`) et que les dépendances sont bien installées (`pip install -r requirements-dev.txt`). |
| Erreur de connexion à Redis | Assurez-vous que le serveur Redis est bien démarré (`redis-server`). Vérifiez que le port 6379 est libre. |
| Erreur de migration | Pour une nouvelle installation, vous pouvez supprimer le fichier `db.sqlite3` et relancer `python manage.py migrate`. **Ne faites jamais cela sur une base de données existante !** |
| Port 8000 déjà utilisé | Lancez le serveur sur un autre port : `python manage.py runserver 8001`. |
| Tâches de transcription non exécutées | Vérifiez que le worker Celery est bien lancé dans un terminal séparé (`celery -A observations_nids worker -l info`). |
| Erreur `SECRET_KEY` | Vérifiez que le fichier `.env` existe, qu'il est correctement rempli et que la variable `SECRET_KEY` n'est pas vide. |