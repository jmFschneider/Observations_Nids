# Plan de Réorganisation de la Documentation

Ce document suit l'avancement de la réorganisation de la documentation du projet.

## Statut Général

- [x] **Partie 1 : Documentation Utilisateur** - TERMINÉE
- [x] **Partie 2 : Documentation Développeur** - TERMINÉE

---

## Partie 2 : Plan Détaillé - Documentation Développeur

### Étape 1 : Préparation

- [x] Créer le répertoire `docs/archives/`.

### Étape 2 : Création de la nouvelle structure et des fichiers principaux

- [x] Créer le fichier `developpeurs/index.md` (fusion de `project/README.md` et `architecture/index.md`).
- [x] Déplacer `docs/docs/project/FEATURES.md` vers `developpeurs/01_features.md`.
- [x] Déplacer `docs/docs/Todo/OPTIMISATIONS_FUTURES.md` vers `developpeurs/roadmap.md`.

### Étape 3 : Réorganisation des sections

- [ ] **Section Architecture**
    - [x] Déplacer le contenu de `docs/docs/architecture/domaines/` vers `docs/developpeurs/architecture/`.
    - [x] Renommer les fichiers de domaine (ex: `01_users_and_auth.md`).
    - [x] Déplacer `docs/docs/architecture/diagrammes/` vers `docs/developpeurs/architecture/`.

- [ ] **Section Installation**
    - [x] Déplacer `docs/docs/installation/development.md` vers `developpeurs/installation/01_development_setup.md`.
    - [x] Fusionner `docs/docs/deployment/production.md` et `docs/docs/installation/production.md` dans `developpeurs/installation/02_production_deployment.md`.

- [ ] **Section Guides**
    - [x] Créer le répertoire `developpeurs/guides/`.
    - [x] Déplacer les guides fonctionnels (`taxonomie.md`, `geolocalisation.md`, `django-helpdesk.md`) dans ce répertoire.
    - [x] Créer le sous-répertoire `development_process/` et y déplacer les guides `git` et `ci-cd`.
    - [x] Créer le sous-répertoire `troubleshooting/` et y déplacer le guide de dépannage.
    - [x] Fusionner les guides GoAccess dans `developpeurs/guides/05_monitoring_with_goaccess.md`.

- [ ] **Section Qualité & Tests**
    - [x] Créer le répertoire `developpeurs/quality_and_testing/`.
    - [x] Déplacer `STRATEGIE_TESTS.md` et `TESTS_REINITIALISATION_MDP.md` dans ce répertoire.

- [ ] **Section Configuration & API**
    - [x] Créer le répertoire `developpeurs/configuration/` et y déplacer `configuration.md` et `reset_database.md`.
    - [x] Créer le répertoire `developpeurs/api_reference/` et y déplacer `API_DOCUMENTATION.md`.

### Étape 4 : Finalisation

    - [x] Mettre à jour le fichier `docs/mkdocs-dev.yml` pour refléter la nouvelle structure.- [x] Archiver tous les anciens fichiers de `docs/docs/` vers `docs/archives/`.
    - [x] Vérifier et corriger tous les liens internes dans la documentation développeur.- [x] Marquer ce plan comme terminé.
