# Possibilités d'amélioration de la documentation

Ce document recense les redondances, erreurs et imprécisions identifiées lors de l'analyse de la documentation du projet.

## 1. Redondances

- **Réinitialisation du mot de passe** : Le fichier `docs/docs/account/REINITIALISATION_MOT_DE_PASSE.md` est un doublon quasi-identique du contenu déjà présent dans `docs/docs/account/GESTION_UTILISATEURS.md`.
  - **Suggestion** : Supprimer `REINITIALISATION_MOT_DE_PASSE.md` et s'assurer que `GESTION_UTILISATEURS.md` est la seule source de vérité.

- **Changelog** : Les fichiers `CHANGELOG.md` et `CHANGELOG-2.md` sont présents. `CHANGELOG-2.md` semble être une version plus récente.
  - **Suggestion** : Fusionner les deux fichiers en un seul `CHANGELOG.md` pour éviter la confusion.

- **Stratégie de tests** : Les fichiers `docs/docs/testing/INDEX.md` et `docs/docs/testing/STRATEGIE_TESTS.md` traitent du même sujet. `INDEX.md` semble être une analyse plus récente et détaillée.
  - **Suggestion** : Consolider les informations pertinentes dans un seul fichier (probablement `STRATEGIE_TESTS.md`) et supprimer l'autre.

## 2. Liens manquants ou incorrects

- **Lien vers le fichier de CI/CD** : Le document `learning/git/README.md` pointe vers le fichier brut `.github/workflows/ci.yml`.
  - **Suggestion** : Il serait plus pertinent de pointer vers le guide `learning/ci-cd/README.md` qui explique le fonctionnement de la CI.

## 3. Améliorations structurelles

- **Organisation des tests** : Les fichiers de test `test_remarques_popup.py`, `test_geocoding.py`, `test_database_fallback.py` se trouvent à la racine du projet.
  - **Suggestion (hors périmètre doc)** : Déplacer ces tests dans les répertoires `tests/` des applications Django correspondantes pour une meilleure organisation.

- **Navigation `mkdocs.yml`** : Le fichier de configuration de la navigation peut être amélioré pour inclure tous les documents et offrir une structure plus logique, notamment pour les guides utilisateurs et les documentations techniques.

