# Documentation du Projet : Observations Nids

## 1. Objectifs du Projet

**Observations Nids** est une application web Django conçue pour la gestion complète du cycle de vie des observations ornithologiques de nidification.

Les objectifs principaux sont :

- **Numérisation Automatisée** : Transcrire des fiches papier en données numériques via l'API Google Vision (OCR).
- **Gestion Collaborative** : Permettre la saisie, la correction et la validation des données par une équipe avec différents rôles.
- **Qualité des Données** : Assurer la cohérence et la précision des informations grâce à un workflow de validation structuré.
- **Traçabilité Complète** : Historiser chaque modification apportée aux données pour garantir l'intégrité scientifique.

---

## 2. Architecture et Workflows

Le projet est organisé en applications Django modulaires, chacune ayant une responsabilité unique (gestion des utilisateurs, taxonomie, géocodage, etc.). Les processus métier, comme la transcription OCR et la validation des données, sont conçus pour être robustes et traçables.

Pour une compréhension approfondie, consultez les guides dédiés :

- **[📄 Guide d'Architecture](./architecture.md)** : Décrit la structure des applications, les modèles de données principaux et les choix techniques.
- **[📄 Guide des Workflows](./workflows.md)** : Explique en détail les processus métier, de la transcription OCR à la validation finale des données.

---

## 3. Technologies Principales

| Catégorie | Technologie | Rôle |
|---|---|---|
| **Backend** | Django (Python) | Framework principal de l'application. |
| **Base de données** | MariaDB / MySQL | Stockage des données en production. (SQLite en développement). |
| **Tâches Asynchrones** | Celery & Redis | Traitement en arrière-plan des tâches longues (ex: transcription OCR). |
| **Frontend** | Bootstrap 5 & JavaScript | Interface utilisateur et interactions dynamiques. |
| **Tests** | Pytest | Assurance qualité et prévention des régressions. |
| **Qualité de Code** | Ruff & Mypy | Formatage, linting et analyse de type statique. |
| **API Externe** | Google Vision | Service d'OCR pour la numérisation des fiches. |

---

## 4. Démarrage Rapide

Pour installer et lancer un environnement de développement local, suivez le guide d'installation complet :

- **[🚀 Guide d'Installation](../installation/README.md)**

Les étapes clés sont :
1. Cloner le projet.
2. Créer un environnement virtuel et installer les dépendances (`requirements-dev.txt`).
3. Configurer le fichier `.env`.
4. Appliquer les migrations et créer un super-utilisateur.
5. Lancer les services (Django, Redis, Celery).
