# Documentation Développeur - Observations Nids

> **Bienvenue dans la documentation technique du projet Observations Nids.**
> Ce document est le point d'entrée pour tout développeur souhaitant comprendre, maintenir ou faire évoluer l'application.

---

## 1. Objectifs du Projet

**Observations Nids** est une application web Django conçue pour la gestion complète du cycle de vie des observations ornithologiques de nidification.

Les objectifs principaux sont :

- **Numérisation Automatisée** : Transcrire des fiches papier en données numériques via l'API Google Vision (OCR).
- **Gestion Collaborative** : Permettre la saisie, la correction et la validation des données par une équipe avec différents rôles.
- **Qualité des Données** : Assurer la cohérence et la précision des informations grâce à un workflow de validation structuré.
- **Traçabilité Complète** : Historiser chaque modification apportée aux données pour garantir l'intégrité scientifique.

---

## 2. Démarrage Rapide

Pour mettre en place un environnement de développement local, suivez le guide d'installation complet :

- **[🚀 Guide d'Installation - Développement](installation/01_development_setup.md)**

**Étapes clés :**
1. Cloner le projet.
2. Créer un environnement virtuel et installer les dépendances (`requirements-dev.txt`).
3. Configurer le fichier `.env`.
4. Appliquer les migrations et créer un super-utilisateur.
5. Lancer les services (Redis, Celery, Django runserver).

---

## 3. Architecture Générale

Le projet est organisé en **8 applications Django modulaires**, chacune ayant une responsabilité unique. Le modèle `FicheObservation` est le pivot central de l'application.

Pour une description détaillée des modèles, de leurs relations et des choix de conception, consultez la section architecture.

- **[🏗️ Documentation d'Architecture Détaillée](architecture/index.md)**

### Stack Technique Principale

| Catégorie | Technologie | Version |
|-----------|-------------|---------|
| **Backend** | Django (Python) | 5.2.7 / 3.12 |
| **Base de données** | MariaDB / MySQL | 10.x |
| **Tâches Asynchrones** | Celery & Redis | 5.x / 7.x |
| **Frontend** | Bootstrap 5 & JavaScript | 5.3 |
| **Tests** | Pytest | 8.x |
| **Qualité de Code** | Ruff & Mypy | - |
| **API Externe** | Google Vision API | v1 |
| **Documentation** | MkDocs + Material | 1.5 |

---

## 4. Naviguer dans la Documentation

Cette documentation est organisée en plusieurs sections pour vous aider à trouver rapidement l'information dont vous avez besoin.

- **[Liste des Fonctionnalités](01_features.md)**
  - Un inventaire complet de toutes les fonctionnalités de l'application, organisées par module.

- **[Feuille de Route (Roadmap)](roadmap.md)**
  - Les optimisations et améliorations futures prévues pour le projet.

- **[Architecture](architecture/index.md)**
  - La section la plus détaillée, décrivant les modèles de données, les relations et les règles métier pour chaque domaine de l'application.

- **[Installation](installation/01_development_setup.md)**
  - Guides pas à pas pour mettre en place un environnement de développement local ou de production.

- **[Guides Pratiques](guides/01_taxonomie.md)**
  - Des guides sur des sujets spécifiques comme le processus de développement (Git, CI/CD), le dépannage, la taxonomie, la géolocalisation, etc.

- **[Qualité & Tests](quality_and_testing/01_STRATEGIE_TESTS.md)**
  - La stratégie de test du projet, des exemples de tests et des guides sur la manière de contribuer à la qualité du code.

- **[Configuration](configuration/01_configuration.md)**
  - Comment configurer le projet, gérer les variables d'environnement et utiliser les commandes de gestion.

- **[Référence API](api_reference/01_API_DOCUMENTATION.md)**
  - La liste de toutes les URLs et points d'accès API du projet.
