# Bienvenue dans la documentation Observations Nids

> **Application Django de gestion d'observations ornithologiques de nidification**
> Numérisation automatisée, correction collaborative et validation scientifique

---

## 📖 À propos du projet

**Observations Nids** est une application web Django conçue pour digitaliser et gérer le cycle de vie complet des observations ornithologiques de nidification.

**Objectifs principaux :**
- 🤖 **Numérisation automatisée** : Transcription OCR de fiches papier via Google Vision API
- 👥 **Gestion collaborative** : Workflow de correction et validation par équipe
- ✅ **Qualité des données** : Contrôles de cohérence et traçabilité complète
- 📊 **Exploitation scientifique** : Données validées prêtes pour analyses

**Statistiques du projet :**
- 7 applications Django modulaires
- 24 modèles de données
- 41 600 lignes de code Python
- 66 tests automatisés (objectif : 80% de couverture)

---

## 🚀 Démarrage rapide

### Installation

Choisissez le guide adapté à votre environnement :

| Environnement | Guide | Description |
|---------------|-------|-------------|
| **Développement** | **[Guide Installation Dev](./installation/development.md)** | SQLite, Django runserver, Redis local |
| **Production** | **[Guide Installation Production](./installation/production.md)** | MariaDB, Apache + mod_wsgi, sécurisation complète |

**Prérequis :**
- Python 3.11+ (recommandé : 3.12)
- Redis pour Celery (tâches asynchrones)
- MariaDB (production) ou SQLite (développement)
- Clé API Google Vision (transcription OCR)

### Premiers pas après installation

1. **Charger les données de référence** :
   ```bash
   # Taxonomie : Liste des Oiseaux de France (recommandé)
   python manage.py charger_lof

   # Géolocalisation : 35 000 communes françaises
   python manage.py charger_communes_france
   ```

2. **Créer des utilisateurs de test** via l'interface admin

3. **Tester la transcription OCR** : Préparer des images de fiches et lancer un lot de transcription

---

## 📚 Documentation par thème

### Pour les utilisateurs

| Section | Description |
|---------|-------------|
| **[Aide utilisateurs](./aide_utilisateurs/README.md)** | Guides pas à pas pour naviguer, saisir et corriger des observations |
| **[Workflows](./project/workflows.md)** | 5 processus métier détaillés (transcription, correction, validation, audit, consultation) |
| **[Fonctionnalités](./project/FEATURES.md)** | Inventaire complet des fonctionnalités par module (28 stables, 2 en développement) |

### Pour les développeurs

| Section | Description |
|---------|-------------|
| **[Architecture](./architecture/index.md)** | Structure des 7 applications, 24 modèles, diagrammes et choix techniques |
| **[Stratégie de tests](./testing/STRATEGIE_TESTS.md)** | Plan de tests (4 phases, 149 tests), fixtures et bonnes pratiques |
| **[API Documentation](./api/API_DOCUMENTATION.md)** | Endpoints REST pour autocomplétion et géocodage |
| **[Configuration](./configuration/configuration.md)** | Variables d'environnement, settings Django, Redis et Celery |

### Guides fonctionnels

| Guide | Description |
|-------|-------------|
| **[Taxonomie](./guides/fonctionnalites/taxonomie.md)** | Import LOF/TaxRef, gestion des espèces, enrichissement données |
| **[Géolocalisation](./guides/fonctionnalites/geolocalisation.md)** | Géocodage 2 niveaux, cache local, API Nominatim |

### Apprentissage et maintenance

| Section | Description |
|---------|-------------|
| **[Git et workflow](./learning/git/README.md)** | Branches, commits, pull requests, bonnes pratiques |
| **[Troubleshooting](./learning/troubleshooting/README.md)** | Résolution des problèmes courants |
| **[Bases de données](./learning/databases/README.md)** | Migrations, requêtes, optimisations |

---

## 🎯 Par cas d'usage

### Je veux installer l'application

- **Développement local** → [Guide Installation Dev](./installation/development.md)
- **Serveur de production** → [Guide Installation Production](./deployment/production.md)
- **Problème d'installation** → [Troubleshooting](./learning/troubleshooting/README.md)

### Je veux comprendre l'application

- **Vue d'ensemble** → [Page Projet](./project/README.md)
- **Architecture technique** → [Architecture complète](./architecture/index.md)
- **Processus métier** → [Workflows détaillés](./project/workflows.md)

### Je veux utiliser l'application

- **Premier pas** → [Navigation générale](./aide_utilisateurs/01_navigation_generale.md)
- **Saisir une observation** → [Guide de saisie](./aide_utilisateurs/02_saisie_nouvelle_observation.md)
- **Corriger des fiches** → [Guide de correction](./aide_utilisateurs/03_correction_transcription.md)

### Je veux développer sur le projet

- **Architecture et conception** → [Architecture](./architecture/index.md)
- **Écrire des tests** → [Stratégie de tests](./testing/STRATEGIE_TESTS.md)
- **Workflow Git** → [Guide Git](./learning/git/README.md)
- **APIs disponibles** → [API Documentation](./api/API_DOCUMENTATION.md)

### Je veux contribuer

- **Workflow Git** → [Guide Git](./learning/git/README.md)
- **Standards de code** → Ruff (linting) + MyPy (typage) + Pytest (tests)
- **Issues GitHub** → [https://github.com/jmFschneider/Observations_Nids/issues](https://github.com/jmFschneider/Observations_Nids/issues)

---

## 🏗️ Architecture du projet

### Applications Django

| Application | Responsabilité | Modèles principaux |
|-------------|----------------|-------------------|
| **accounts** | Authentification, utilisateurs | `Utilisateur`, `Notification` |
| **observations** | Gestion des fiches | `FicheObservation`, `Observation`, `Nid` |
| **ingest** | Transcription OCR | `TranscriptionTask` |
| **taxonomy** | Gestion des espèces | `Ordre`, `Famille`, `Espece` |
| **geo** | Géolocalisation | `Commune`, `Departement` |
| **review** | Workflow de validation | `EtatCorrection` |
| **audit** | Traçabilité | `HistoriqueModification` |

[Documentation complète →](./architecture/index.md)

### Technologies principales

- **Backend** : Django 5.2.7 + Python 3.12
- **Base de données** : MariaDB 10.x (prod) / SQLite (dev)
- **Tâches asynchrones** : Celery 5.x + Redis 7.x
- **Frontend** : Bootstrap 5.3 + JavaScript (autocomplétion, formsets)
- **Tests** : Pytest 8.x + pytest-django
- **Qualité** : Ruff + MyPy
- **OCR** : Google Vision API v1
- **Documentation** : MkDocs + Material theme

---

## 📋 Changelog et versions

- **[CHANGELOG.md](./CHANGELOG.md)** : Historique détaillé des versions
- **Version actuelle** : Voir le CHANGELOG pour la dernière version stable
- **Feuille de route** : [OPTIMISATIONS_FUTURES.md](./Todo/OPTIMISATIONS_FUTURES.md)

---

## 🆘 Besoin d'aide ?

- **Documentation** : Utilisez la recherche (en haut de cette page)
- **Troubleshooting** : [Guide de dépannage](./learning/troubleshooting/README.md)
- **Issues GitHub** : [Signaler un problème](https://github.com/jmFschneider/Observations_Nids/issues)
- **Contact** : Voir le README principal du projet

---

## 📄 Licence et crédits

**Projet** : Observations Nids
**Auteur** : Jean-Marc Schneider
**Documentation** : Générée avec MkDocs + Material theme

---

*Dernière mise à jour : 24 octobre 2025*
