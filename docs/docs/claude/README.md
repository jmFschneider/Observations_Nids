# Guide d'Interaction - Assistant IA (Gemini)

Ce document est le guide de référence pour l'assistant IA travaillant sur le projet "Observations Nids".

## 1. Objectif du Projet

**Observations Nids** est une application Django pour la gestion d'observations ornithologiques de nidification. Les fonctionnalités clés incluent la transcription OCR de fiches, la saisie manuelle, un workflow de correction et validation, et une traçabilité complète.

## 2. Instructions Générales

1.  **Lire avant d'éditer** : Toujours lire les fichiers existants (vues, modèles, templates) avant de proposer des modifications.
2.  **Préférer l'édition** : Modifier les fichiers existants plutôt que d'en créer de nouveaux, sauf si une nouvelle fonctionnalité l'exige.
3.  **Respecter l'architecture** : Suivre la structure d'applications existante. Les nouvelles fonctionnalités doivent être placées dans l'application la plus logique.
4.  **Ajouter des tests** : Pour toute nouvelle fonctionnalité ou correction de bug, proposer d'ajouter ou de mettre à jour les tests correspondants.
5.  **Mettre à jour la documentation** : Si des changements significatifs sont apportés (modèles, API, workflow), proposer de mettre à jour la documentation pertinente dans `docs/`.

## 3. Architecture Générale

L'architecture détaillée se trouve dans `docs/project/architecture.md`. Voici un résumé :

- **`accounts/`**: Gestion des utilisateurs et des rôles.
- **`audit/`**: Historique et traçabilité.
- **`core/`**: Utilitaires partagés.
- **`geo/`**: Géocodage et gestion des communes.
- **`ingest/`**: Importation de données JSON.
- **`observations/`**: Cœur de l'application (Fiches, Observations, Transcription).
- **`review/`**: Workflow de validation.
- **`taxonomy/`**: Gestion des espèces (Ordres, Familles, Espèces).

Les modèles principaux sont `FicheObservation` et `Observation`. La logique métier est principalement dans les vues de ces applications.

## 4. Workflows Principaux

Les workflows détaillés sont décrits dans `docs/project/workflows.md`. Les processus clés sont :

1.  **Transcription OCR** : Tâches Celery asynchrones utilisant Google Vision API.
2.  **Correction & Saisie** : Formulaires complexes (Formsets) pour la saisie manuelle.
3.  **Validation** : Processus de double contrôle par des utilisateurs aux rôles différents.
4.  **Audit** : Traçabilité automatique via des signaux Django.

## 5. Fichiers Critiques

Manipuler les fichiers suivants avec une précaution particulière :

-   `observations/models.py` (modèles de données centraux)
-   `observations_nids/settings.py` (configuration du projet)
-   Tous les fichiers dans `*/migrations/` (ne jamais modifier une migration existante)
-   `observations_nids/urls.py` (routing principal)

## 6. Commandes Utiles

-   `python manage.py runserver`: Lancer le serveur de développement.
-   `celery -A observations_nids worker -l info`: Lancer le worker Celery.
-   `pytest`: Lancer la suite de tests.
-   `ruff check .`: Lancer le linter.
-   `python manage.py charger_lof`: Charger la taxonomie des oiseaux (méthode préférée).
-   `python manage.py charger_communes_france`: Charger les communes.
