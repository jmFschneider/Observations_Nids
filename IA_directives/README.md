# Guide d'Interaction - Assistant IA

Ce document est le guide de référence pour l'assistant IA travaillant sur le projet "Observations Nids".

**Dernière mise à jour** : Octobre 2025

## 1. Objectif du Projet

**Observations Nids** est une application Django pour la gestion d'observations ornithologiques de nidification. L'application digitalise, valide et exploite des fiches d'observations manuscrites en utilisant la transcription IA.

**Fonctionnalités clés** :
- **Transcription OCR** : Utilisation de Google Generative AI (Gemini) pour la transcription automatique de fiches manuscrites
- **Saisie manuelle** : Interface complète de saisie et modification avec formsets Django
- **Workflow de validation** : Processus de double contrôle par des utilisateurs aux rôles différents
- **Gestion des permissions** : Système de rôles avec permissions granulaires (incluant droits de transcription)
- **Traçabilité complète** : Historique de toutes les modifications avec audit trail
- **Système de tickets** : Support utilisateur intégré via django-helpdesk
- **Géocodage** : Intégration Nominatim pour la localisation des observations

## 2. Instructions Générales

1.  **Lire avant d'éditer** : Toujours lire les fichiers existants (vues, modèles, templates) avant de proposer des modifications.
2.  **Préférer l'édition** : Modifier les fichiers existants plutôt que d'en créer de nouveaux, sauf si une nouvelle fonctionnalité l'exige.
3.  **Respecter l'architecture** : Suivre la structure d'applications existante. Les nouvelles fonctionnalités doivent être placées dans l'application la plus logique.
4.  **Ajouter des tests** : Pour toute nouvelle fonctionnalité ou correction de bug, proposer d'ajouter ou de mettre à jour les tests correspondants.
5.  **Mettre à jour la documentation** : Si des changements significatifs sont apportés (modèles, API, workflow), proposer de mettre à jour la documentation pertinente dans `docs/`.

## 3. Architecture Générale

L'architecture détaillée se trouve dans `docs/docs/architecture/`. Le projet est organisé en **9 applications Django** :

### Applications principales

| Application | Rôle | Modèles clés |
|-------------|------|--------------|
| **`accounts/`** | Gestion des utilisateurs, authentification, notifications | `Utilisateur` (custom user), `Notification` |
| **`audit/`** | Historique et traçabilité de toutes les modifications | `HistoriqueModification` |
| **`core/`** | Utilitaires partagés (modèles abstraits, constantes) | Abstract: `TimeStamped`, `UUID`, `SoftDelete` |
| **`geo/`** | Géocodage Nominatim, gestion des communes françaises | `Localisation`, `CommuneFrance` |
| **`ingest/`** | Transcription OCR et importation de données JSON | `TranscriptionBrute`, `EspeceCandidate`, `ImportationEnCours` |
| **`observations/`** | **Cœur de l'application** : fiches, nids, observations | `FicheObservation`, `Nid`, `Observation`, `ResumeObservation`, `EtatCorrection`, `Remarque`, `CausesEchec` |
| **`review/`** | Workflow de validation (correction et approbation) | `Validation`, `HistoriqueValidation` |
| **`taxonomy/`** | Référentiel taxonomique des oiseaux de France | `Espece`, `Famille`, `Ordre` |
| **`helpdesk_custom/`** | Système de tickets de support (personnalisation django-helpdesk) | Customization de django-helpdesk |

### Modèles centraux

- **`FicheObservation`** : Pivot central représentant une fiche d'observation complète pour une espèce et une année
  - Crée automatiquement 5 objets liés à la sauvegarde : `Localisation`, `Nid`, `ResumeObservation`, `CausesEchec`, `EtatCorrection`
  - Relations 1:N avec `Observation`, `Remarque`, `HistoriqueModification`, `Validation`

- **`Utilisateur`** : Modèle utilisateur personnalisé (étend `AbstractUser`)
  - Champs additionnels : `role`, `est_valide`, `est_transcription`
  - 3 rôles : observateur, reviewer, administrateur

## 4. Workflows Principaux

Les workflows détaillés sont décrits dans `docs/docs/architecture/domaines/`. Les processus clés sont :

### 4.1. Workflow d'inscription et validation utilisateur

```
1. Inscription publique → compte créé (est_valide=False, is_active=False)
2. Notification envoyée à tous les administrateurs
3. Admin valide/rejette le compte
4. Si validé : est_valide=True, is_active=True + email de notification
5. Utilisateur peut se connecter
```

### 4.2. Transcription OCR & Importation

```
1. Images scannées → OCR (Google Generative AI / Gemini)
2. TranscriptionBrute créée (JSON brut stocké)
3. Extraction du nom d'espèce + matching fuzzy
4. EspeceCandidate créée (avec score de similarité)
5. Si score < 80% → validation manuelle requise
6. ImportationEnCours créée (statut: en_attente)
7. Assignation observateur + validation espèce
8. FicheObservation créée (statut: complete)
```

**Permissions** : Les vues de transcription et d'importation sont protégées par le décorateur `@transcription_required`
- Accessible uniquement si `utilisateur.est_transcription=True` OU `utilisateur.role='administrateur'`
- Lève `PermissionDenied` (403) sinon

### 4.3. Saisie et Correction d'observations

```
1. Création FicheObservation → 5 objets liés créés automatiquement
2. Statut: 'nouveau' (0% complétude)
3. Saisie données → Statut: 'en_edition' (12-87% complétude)
4. Soumission → Statut: 'en_cours' (en cours de review)
5. Validation/Rejet → Statut: 'valide' (validée)
```

**Calcul de complétude** (8 critères, 1 point chacun) :
1. Observateur présent
2. Espèce présente
3. Localisation complète (commune + département)
4. Au moins une observation datée
5. Données de ponte
6. Détails du nid
7. Hauteur du nid
8. Image associée

### 4.4. Validation (Review)

Processus de double contrôle par des utilisateurs aux rôles différents (reviewer).

### 4.5. Audit

Traçabilité automatique via des signaux Django. Chaque modification est enregistrée dans `HistoriqueModification` avec :
- Qui a modifié (utilisateur)
- Quand (date/heure)
- Quoi (ancien/nouveau contenu)
- Catégorie de modification (8 catégories)

## 5. Fichiers Critiques

Manipuler les fichiers suivants avec une précaution particulière :

### Modèles de données
-   `observations/models.py` (370 lignes) - Modèles centraux : FicheObservation, Observation, Nid, etc.
-   `accounts/models.py` (96 lignes) - Modèle Utilisateur personnalisé (AUTH_USER_MODEL)
-   `taxonomy/models.py` (35 lignes) - Référentiel taxonomique
-   `geo/models.py` (88 lignes) - Localisation et communes

### Configuration
-   `observations_nids/settings.py` (331 lignes) - Configuration complète du projet
-   `observations_nids/urls.py` (41 lignes) - Routing principal
-   Tous les fichiers dans `*/migrations/` - **NE JAMAIS modifier une migration existante**

### Vues principales
-   `observations/views/saisie_observation_view.py` (805 lignes) - Saisie et modification de fiches
-   `observations/views/view_transcription.py` (262 lignes) - Transcription OCR
-   `observations/views/views_home.py` (55 lignes) - Pages d'accueil

### Décorateurs et permissions
-   `observations/decorators.py` - Décorateur `@transcription_required`
-   `ingest/views/auth.py` - Helper `peut_transcrire(user)`

## 6. Commandes Utiles

### Développement
-   `python manage.py runserver` - Lancer le serveur de développement
-   `celery -A observations_nids worker -l info` - Lancer le worker Celery (tâches asynchrones)
-   `celery -A observations_nids flower` - Interface web de monitoring Celery

### Tests et qualité du code
-   `pytest` - Lancer la suite de tests (78 tests, 86% couverture)
-   `pytest --cov` - Tests avec rapport de couverture
-   `ruff check .` - Lancer le linter
-   `ruff format .` - Formatter le code
-   `mypy .` - Vérification des types

### Gestion des données
-   `python manage.py charger_lof` - Charger la taxonomie des oiseaux (méthode préférée)
-   `python manage.py charger_communes_france` - Charger les communes françaises
-   `python manage.py makemigrations` - Créer de nouvelles migrations
-   `python manage.py migrate` - Appliquer les migrations

### Administration
-   `python manage.py createsuperuser` - Créer un superutilisateur
-   `python manage.py shell` - Shell Django interactif (avec django-extensions)

### Documentation
-   `mkdocs serve` - Servir la documentation localement (http://127.0.0.1:8000)
-   `mkdocs build` - Construire la documentation statique

## 7. Système de Permissions et Rôles

### 7.1. Rôles utilisateurs

Le projet implémente un système de rôles à 3 niveaux :

| Rôle | Permissions |
|------|-------------|
| **Observateur** | - Créer/modifier ses propres fiches<br>- Consulter toutes les observations<br>- Créer des tickets de support |
| **Reviewer** | - Toutes permissions d'observateur<br>- Corriger toutes les fiches<br>- Accéder aux outils de transcription (si `est_transcription=True`)<br>- Valider/rejeter des fiches |
| **Administrateur** | - Toutes permissions<br>- Gestion des utilisateurs<br>- Validation des comptes<br>- Accès admin Django<br>- Accès automatique à la transcription |

### 7.2. Permission de transcription

**Nouveau depuis octobre 2025** : Le champ `est_transcription` sur le modèle `Utilisateur` contrôle l'accès aux fonctionnalités de transcription OCR et d'importation.

**Implémentation** :
- Décorateur : `@transcription_required` dans `observations/decorators.py`
- Fonction helper : `peut_transcrire(user)` dans `ingest/views/auth.py`
- Appliqué aux vues : `select_directory`, `process_images`, `importer_json`, `extraire_candidats`, etc.

**Accès** : `utilisateur.est_transcription=True` OU `utilisateur.role='administrateur'`

**UI** : Le bloc "Transcription & Importation" sur la page d'accueil est masqué pour les utilisateurs non autorisés.

### 7.3. Workflow de validation de compte

1. L'utilisateur s'inscrit → compte créé avec `est_valide=False`, `is_active=False`
2. Tous les administrateurs reçoivent une notification
3. Un administrateur valide ou rejette le compte
4. Si validé : `est_valide=True`, `is_active=True` + email de confirmation
5. L'utilisateur peut maintenant se connecter

## 8. Stack Technologique

### Framework et base de données
- **Django 5.1+** (Python 3.11+)
- **MariaDB 10.11+** - Base de données relationnelle
- **Redis 7+** - Cache et message broker pour Celery

### Bibliothèques principales
- **Celery 5+** - Traitement asynchrone des tâches (transcription OCR)
- **Google Generative AI (Gemini)** - Transcription OCR des fiches manuscrites
- **Nominatim (OpenStreetMap)** - Service de géocodage
- **django-helpdesk** - Système de tickets de support
- **pytest + coverage** - Framework de tests (86% de couverture)

### Outils de développement
- **Ruff** - Linter et formateur de code Python
- **mypy** - Vérification de types statiques
- **django-debug-toolbar** - Débogage en développement
- **Flower** - Monitoring Celery
- **MkDocs + Material theme** - Documentation technique

### Frontend
- **Bootstrap 4** - Framework CSS
- **jQuery** - Manipulation DOM et AJAX
- **django-bootstrap4form** - Intégration Bootstrap/Django

## 9. Structure de la Documentation

La documentation complète se trouve dans `docs/docs/` et est générée avec MkDocs :

```
docs/docs/
├── index.md                    # Page d'accueil documentation utilisateur
├── index-dev.md               # Page d'accueil documentation développeur
├── CHANGELOG.md               # Historique des versions
├── architecture/              # Architecture système
│   ├── domaines/             # Documentation par domaine (850+ lignes sur utilisateurs)
│   │   ├── utilisateurs.md
│   │   ├── import-transcription.md
│   │   ├── observations.md
│   │   ├── workflow-correction.md
│   │   ├── audit.md
│   │   ├── localisation.md
│   │   ├── taxonomie.md
│   │   ├── validation.md
│   │   └── nidification.md
│   └── diagrammes/           # Diagrammes ERD
├── aide_utilisateurs/         # Guides utilisateur
├── helpdesk/                  # Documentation système de tickets
│   ├── guide-utilisateur.md
│   ├── guide-developpeur.md
│   └── README.md
├── installation/              # Guides d'installation
├── testing/                   # Stratégie de tests et rapports
├── deployment/                # Guide de déploiement production (1528 lignes)
├── project/                   # Vue d'ensemble du projet
├── guides/                    # Guides divers
└── IA_directives/                    # Ce fichier
    └── README.md
```

## 10. Changements Récents (Octobre 2025)

### 10.1. Intégration django-helpdesk (commit bee0914)
- Système de tickets de support intégré
- Formulaires et templates personnalisés
- Configuration sécurisée (pas d'accès public)
- Guides utilisateur et développeur

### 10.2. Permissions de transcription (commits 386b0fb, b001022)
- Nouveau champ `est_transcription` sur `Utilisateur`
- Décorateur `@transcription_required` pour protéger les vues
- Interface admin pour gérer les droits de transcription
- Affichage conditionnel dans l'UI

### 10.3. Améliorations des tests (27 octobre)
- Couverture : 41% → **86%** (+45%)
- 78 tests (100% passing)
- Nouveaux fichiers de tests :
  - `test_transcription.py` (21 tests)
  - `test_views.py` (18 tests)
  - `test_views_home.py` (7 tests)
  - `test_json_sanitizer.py` (10 tests)
  - `audit/test_historique.py` (7 tests)

### 10.4. Corrections de bugs
- Résolution affichage des remarques supprimées dans l'historique
- Restauration JavaScript de suppression d'observations
- Contrainte d'unicité sur l'email

### 10.5. Améliorations UI
- Favicon ajouté sur toutes les pages (commit 05e33c9)
- Bannière de notification admin pour comptes en attente
- Soft delete pour utilisateurs (`is_active=False`)
- Amélioration alignement des formulaires

## 11. Bonnes Pratiques de Développement

### Avant toute modification
1. **Lire les fichiers existants** : Utiliser Read tool pour comprendre le code existant
2. **Vérifier les tests** : S'assurer que les tests passent avant de commencer
3. **Consulter la documentation** : Vérifier `docs/docs/architecture/domaines/` pour le contexte

### Pendant le développement
1. **Respecter l'architecture** : Placer le code dans l'application appropriée
2. **Suivre les conventions** : Utiliser Ruff pour le formatage
3. **Ajouter des tests** : Maintenir la couverture de code à 85%+
4. **Documenter les changements** : Mettre à jour la documentation pertinente

### Après les modifications
1. **Lancer les tests** : `pytest --cov`
2. **Vérifier le linting** : `ruff check .`
3. **Tester manuellement** : Vérifier l'UI et les workflows
4. **Mettre à jour CHANGELOG.md** : Documenter les changements significatifs

## 12. Dépannage Courant

### Problèmes de base de données
- Vérifier que MariaDB est démarré
- Vérifier les credentials dans `.env`
- Réinitialiser la base : `python manage.py migrate --run-syncdb`

### Problèmes Celery
- Vérifier que Redis est démarré : `redis-cli ping`
- Redémarrer le worker : `celery -A observations_nids worker -l info`
- Monitorer avec Flower : `celery -A observations_nids flower`

### Problèmes de transcription
- Vérifier la clé API Google dans `.env`
- Vérifier les permissions : `utilisateur.est_transcription` ou role admin
- Consulter les logs Celery pour les erreurs de tâches asynchrones

### Problèmes de tests
- Installer les dépendances de test : `pip install -r requirements-dev.txt`
- Nettoyer les `.pyc` : `find . -type f -name "*.pyc" -delete`
- Réinitialiser la DB de test : `pytest --create-db`

## 13. Ressources Additionnelles

- **Documentation complète** : `docs/docs/` (servir avec `mkdocs serve`)
- **Architecture détaillée** : `docs/docs/architecture/domaines/`
- **Guide de déploiement** : `docs/docs/deployment/` (1528 lignes)
- **Historique des changements** : `docs/docs/CHANGELOG.md`
- **Tests** : `docs/docs/testing/`

---

**Note** : Ce guide est maintenu à jour régulièrement. Pour toute question ou clarification, consulter la documentation complète dans `docs/docs/` ou créer un ticket via le système helpdesk.
