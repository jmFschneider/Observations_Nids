# Synthèse du Projet : Observations Nids

*Ce document est une synthèse consolidée des informations trouvées dans le répertoire `Claude/`. Il a pour but de servir de document de référence principal et à jour pour le projet.*

---

## 1. Objectifs du Projet

**Observations Nids** est une application web Django conçue pour la gestion complète du cycle de vie des observations ornithologiques de nidification. 

Les objectifs principaux sont :

- **Numérisation Automatisée** : Transcrire des fiches papier en données numériques via l'API Google Vision (OCR).
- **Gestion Collaborative** : Permettre la saisie, la correction et la validation des données par une équipe avec différents rôles.
- **Qualité des Données** : Assurer la cohérence et la précision des informations grâce à un workflow de validation structuré.
- **Traçabilité Complète** : Historiser chaque modification apportée aux données pour garantir l'intégrité scientifique.

---

## 2. Architecture Générale

Le projet est modulaire, organisé en applications Django ayant chacune une responsabilité unique.

| Application | Rôle Principal |
|---|---|
| `observations` | **Cœur de l'application** : gère les fiches d'observation, les nids, etc. |
| `accounts` | Gestion des **utilisateurs** et de leurs rôles (Observateur, Correcteur, Validateur). |
| `taxonomy` | Gestion de la **classification des espèces** (Ordre, Famille, Espèce). |
| `geo` | Gestion des **données géographiques** (Communes, géocodage). |
| `review` | Gère le **workflow de validation** et les statuts des fiches. |
| `audit` | Assure la **traçabilité** en enregistrant toutes les modifications. |
| `ingest` | Import et traitement de données externes. |
| `core` | Utilitaires et code partagés par les autres applications. |

La configuration du projet (variables d'environnement) est gérée via Pydantic et un fichier `.env`, assurant une configuration validée et typée.

---

## 3. Modèles de Données Clés

L'architecture de la base de données s'articule autour de trois concepts principaux :

1.  **`FicheObservation` (`observations/models.py`)**
    - C'est le **modèle central** qui représente une observation complète pour une espèce et une année donnée.
    - Il est lié à un `observateur` et une `espece`.
    - Pour garantir l'intégrité, lors de sa création, des objets liés (OneToOne) sont **automatiquement créés** avec des valeurs par défaut : `Localisation`, `Nid`, `ResumeObservation`, `CausesEchec`, `EtatCorrection`.

2.  **`Espece` (`taxonomy/models.py`)**
    - Représente une espèce d'oiseau avec sa classification (famille, ordre) et ses informations (nom scientifique, statut, etc.).

3.  **`Utilisateur` (`accounts/models.py`)**
    - Modèle utilisateur personnalisé qui inclut un champ `role` pour gérer les permissions à travers l'application.

---

## 4. Workflows Principaux

L'application suit un processus métier clair en deux phases majeures.

### Workflow 1 : Transcription Automatique (OCR)

1.  **Lancement** : Un utilisateur sélectionne un répertoire d'images (scans de fiches papier).
2.  **Traitement Asynchrone** : Des tâches **Celery** sont lancées en arrière-plan pour chaque image, afin de ne pas bloquer l'interface.
3.  **OCR** : Chaque tâche appelle l'API **Google Vision** pour extraire le texte brut.
4.  **Parsing & Création** : Le texte est analysé pour en extraire les données structurées, qui sont ensuite utilisées pour créer une `FicheObservation` en base de données.
5.  **Suivi** : Une interface permet de suivre la progression du lot en temps réel.

### Workflow 2 : Correction et Validation Humaine

Ce workflow garantit la qualité des données via un processus de double contrôle.

1.  **Correction** :
    - Une fiche (créée par OCR ou manuellement) est à l'état `nouveau`.
    - Un **Correcteur** la prend en charge, vérifie chaque champ, et la soumet pour validation. Le statut passe à `corrige`.
    - L'interface de saisie est riche, avec autocomplétion des communes, géolocalisation GPS, et gestion dynamique de plusieurs observations pour un même nid.

2.  **Validation** :
    - Un **Validateur** (qui ne peut pas être le correcteur initial) examine la fiche corrigée.
    - Il peut soit **Valider** la fiche (statut `valide`, la donnée devient exploitable), soit la **Rejeter** avec un commentaire obligatoire (statut `rejete`, la fiche retourne en correction).

3.  **Audit** :
    - Chaque changement de statut, chaque modification de champ est **automatiquement enregistré** dans le module `audit`, garantissant une traçabilité parfaite.

---

## 5. Installation et Démarrage Rapide

Voici les étapes condensées pour lancer un environnement de développement local.

1.  **Prérequis** : Python 3.11+, Git, Redis.

2.  **Installation** :
    ```bash
    # Cloner le projet et naviguer dedans
    git clone <url-du-repo> && cd observations_nids

    # Créer et activer un environnement virtuel
    python -m venv venv
    source venv/bin/activate  # (ou venv\Scripts\activate sur Windows)

    # Installer les dépendances de développement
    pip install -r requirements-dev.txt
    ```

3.  **Configuration** :
    ```bash
    # Copier le fichier d'exemple .env
    cp .env.example .env

    # Éditer .env (générer une SECRET_KEY et vérifier la configuration DB)
    # Pour un test rapide, la configuration par défaut avec SQLite fonctionne.
    ```

4.  **Base de données** :
    ```bash
    # Appliquer les migrations
    python manage.py migrate

    # Créer un administrateur
    python manage.py createsuperuser
    ```

5.  **Démarrer les services** (dans 3 terminaux distincts) :
    ```bash
    # 1. Serveur Django
    python manage.py runserver

    # 2. Serveur Redis (pour Celery)
    redis-server

    # 3. Worker Celery
    celery -A observations_nids worker --loglevel=info
    ```

6.  **Accès** : L'application est accessible sur `http://localhost:8000`.

---

## 6. Technologies et Dépendances

- **Backend** : Django, Python 3.12+
- **Base de données** : MariaDB (ou PostgreSQL) en production, SQLite en développement.
- **Tâches Asynchrones** : Celery, Redis.
- **Frontend** : Bootstrap 5, JavaScript (vanilla).
- **Tests** : Pytest, pytest-django.
- **Qualité de code** : Ruff, Mypy.
- **API Externe** : Google Vision API (pour l'OCR).
