# Documentation du Projet : Observations Nids

> **Page d'accueil de la documentation projet**
> Vue d'ensemble, objectifs, architecture, technologies et liens vers les ressources clés.

---

## 📋 Navigation dans cette section

| Document | Description |
|----------|-------------|
| **[FEATURES.md](./FEATURES.md)** | Inventaire complet des fonctionnalités par module avec leur état de développement (✅ Stable, 🚧 En développement, ⚠️ Attention). |
| **[workflows.md](./workflows.md)** | Documentation détaillée des 5 workflows majeurs : transcription OCR, correction, validation, audit et consultation. |
| **[Architecture complète](../architecture/index.md)** | Structure technique du projet : 7 domaines, 24 modèles, diagrammes et choix techniques. |

---

## 1. Objectifs du Projet

**Observations Nids** est une application web Django conçue pour la gestion complète du cycle de vie des observations ornithologiques de nidification.

Les objectifs principaux sont :

- **Numérisation Automatisée** : Transcrire des fiches papier en données numériques via l'API Google Vision (OCR).
- **Gestion Collaborative** : Permettre la saisie, la correction et la validation des données par une équipe avec différents rôles.
- **Qualité des Données** : Assurer la cohérence et la précision des informations grâce à un workflow de validation structuré.
- **Traçabilité Complète** : Historiser chaque modification apportée aux données pour garantir l'intégrité scientifique.

---

## 2. Architecture et Workflows

Le projet est organisé en **7 applications Django modulaires**, chacune ayant une responsabilité unique :

| Application | Responsabilité | Modèles principaux |
|-------------|----------------|-------------------|
| **accounts** | Authentification, utilisateurs, notifications | `Utilisateur`, `Notification` |
| **observations** | Gestion des fiches et observations | `FicheObservation`, `Observation`, `Localisation`, `Nid` |
| **ingest** | Transcription OCR et import de données | `TranscriptionTask` |
| **taxonomy** | Gestion des espèces et référentiels | `Ordre`, `Famille`, `Espece` |
| **geo** | Géocodage et localisation | `Commune`, `Departement` |
| **review** | Workflow de validation | `EtatCorrection` |
| **audit** | Traçabilité des modifications | `HistoriqueModification` |

**Statistiques du projet :**
- 24 modèles de données
- 41 600 lignes de code Python
- 66 tests automatisés (41% de couverture, objectif : 80%)

### Ressources détaillées

- **[📐 Architecture complète](../architecture/index.md)** : Structure des applications, modèles de données, diagrammes et choix techniques.
- **[⚙️ Workflows](./workflows.md)** : 5 processus métier détaillés (transcription OCR, correction, validation, audit, consultation).
- **[📋 Fonctionnalités](./FEATURES.md)** : Inventaire complet par module avec états de développement.

---

## 3. Technologies Principales

| Catégorie | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| **Backend** | Django (Python) | 5.2.7 / Python 3.12 | Framework principal de l'application. |
| **Base de données** | MariaDB / MySQL | 10.x | Stockage des données en production. (SQLite en développement). |
| **Tâches Asynchrones** | Celery & Redis | Celery 5.x / Redis 7.x | Traitement en arrière-plan des tâches longues (ex: transcription OCR). |
| **Frontend** | Bootstrap 5 & JavaScript | Bootstrap 5.3 | Interface utilisateur responsive et interactions dynamiques (autocomplétion, formsets). |
| **Tests** | Pytest | pytest 8.x + pytest-django | Assurance qualité et prévention des régressions (66 tests, 41% couverture). |
| **Qualité de Code** | Ruff & Mypy | Ruff 0.x / Mypy 1.x | Formatage, linting (PEP 8) et analyse de type statique. |
| **API Externe** | Google Vision API | v1 | Service d'OCR pour la numérisation des fiches papier (85-95% succès). |
| **Documentation** | MkDocs + Material | MkDocs 1.5 | Documentation technique et guides utilisateurs. |

**Choix techniques clés :**
- **Formsets Django** : gestion des observations multiples par fiche
- **Signaux Django** : traçabilité automatique des modifications (audit)
- **API REST légère** : endpoints pour autocomplétion et géocodage
- **Stratégie de géocodage à 2 niveaux** : cache local (35 000 communes) + API Nominatim

---

## 4. Fonctionnalités

**Résumé par statut :** (voir [FEATURES.md](./FEATURES.md) pour le détail)

| Statut | Nombre | Description |
|--------|--------|-------------|
| ✅ **Stable** | 28 | Fonctionnalités testées et en production |
| 🚧 **En développement** | 2 | Fonctionnalités à implémenter (export de données, recherche avancée) |
| ⚠️ **Attention** | 0 | Fonctionnalités avec problèmes connus |

**Fonctionnalités principales :**
- Authentification et gestion des rôles (observateur, correcteur, validateur, admin)
- Transcription OCR automatique avec suivi en temps réel
- Interface de saisie/correction avec autocomplétion (espèces, communes)
- Workflow de validation avec notifications
- Géocodage automatique (35 000 communes françaises)
- Historique complet des modifications (audit)
- Base taxonomique complète (Liste des Oiseaux de France - LOF)

Pour le détail complet, consultez **[FEATURES.md](./FEATURES.md)**.

---

## 5. Démarrage Rapide

Pour installer et lancer un environnement de développement local, suivez le guide d'installation complet :

- **[🚀 Guide d'Installation - Développement](../installation/development.md)**
- **[📦 Guide d'Installation - Production](../installation/production.md)**

**Étapes clés (développement) :**
1. Cloner le projet
2. Créer un environnement virtuel et installer les dépendances (`requirements-dev.txt`)
3. Configurer le fichier `.env` (SECRET_KEY, base de données, Redis, Google API)
4. Appliquer les migrations et créer un super-utilisateur
5. Lancer les 3 services : Redis, Celery worker, Django runserver

**Prérequis :**
- Python 3.11+ (recommandé : 3.12)
- Redis pour Celery
- MariaDB (ou SQLite en développement)
- Clé API Google Vision pour la transcription OCR

---

## 6. Documentation complémentaire

**Guides d'installation :**
- [Installation - Développement](../installation/development.md)
- [Installation - Production](../installation/production.md)

**Architecture et conception :**
- [Architecture complète](../architecture/index.md)
- [Domaines métier](../architecture/domaines/)
- [Diagrammes](../architecture/diagrammes/)

**Guides fonctionnels :**
- [Guide Taxonomie](../guides/fonctionnalites/taxonomie.md)
- [Guide Géolocalisation](../guides/fonctionnalites/geolocalisation.md)

**Tests et qualité :**
- [Stratégie de tests](../testing/STRATEGIE_TESTS.md)
- [Exemple de tests : Réinitialisation de mot de passe](../testing/TESTS_REINITIALISATION_MDP.md)

---

**Document créé le** : Janvier 2025
**Dernière mise à jour** : 24 octobre 2025
**Version** : 2.0 (consolidé JOUR 3)
