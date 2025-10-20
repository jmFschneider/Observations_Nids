# Liste des Fonctionnalités - Observations Nids

Ce document liste les fonctionnalités implémentées dans l'application, leur état et leurs dépendances.

**Légende :**
- ✅ **Stable :** Fonctionne correctement, testé.
- 🚧 **En développement :** Fonctionnel mais peut évoluer.
- ⚠️ **Attention :** Problèmes connus ou limitations.

---

## 🔐 Module `accounts` (Authentification)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Connexion / Déconnexion | ✅ | Basé sur le système d'authentification de Django. |
| 2 | Modèle `Utilisateur` personnalisé | ✅ | Inclut des rôles (observateur, correcteur, etc.). |
| 3 | Gestion des rôles & permissions | ✅ | Contrôle d'accès granulaire via des décorateurs. |

---

## 📝 Module `observations`

### Fonctionnalités Principales

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Liste des fiches d'observation | ✅ | Paginée et filtrable. |
| 2 | Vue détaillée d'une fiche | ✅ | Affichage complet de toutes les données liées. |
| 3 | Création / Modification de fiche | ✅ | Formulaire unifié pour la création et la modification. |
| 4 | Gestion d'observations multiples | ✅ | Utilisation de `Formsets` pour ajouter dynamiquement des observations. |
| 5 | Système de remarques | ✅ | Ajout et modification de remarques via une popup modale (AJAX). |
| 6 | Export de données | 🚧 | Fonctionnalité à implémenter (CSV, JSON). |
| 7 | Recherche avancée | 🚧 | Fonctionnalité à implémenter. |

### Interface de Saisie (UI/UX)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 8 | Auto-complétion des espèces | ✅ | Recherche asynchrone avec délai pour une meilleure expérience. |
| 9 | Auto-complétion des communes | ✅ | Interroge l'API du module `geo`. |
| 10| Auto-remplissage des données | ✅ | Remplit automatiquement le département, les coordonnées et l'altitude. |
| 11| Navigation au clavier | ✅ | Support des flèches, `Entrée` et `Echap` pour l'auto-complétion. |

---

## 🔍 Module `ingest` (Transcription & Import)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Sélection de répertoire | ✅ | Interface pour choisir le dossier d'images à transcrire. |
| 2 | Traitement asynchrone (Celery) | ✅ | Les transcriptions sont des tâches longues exécutées en arrière-plan. |
| 3 | Intégration OCR (Google Vision) | ✅ | Extraction du texte brut depuis les images. |
| 4 | Parsing intelligent | ✅ | Analyse du texte pour en extraire des données structurées. |
| 5 | Suivi de la progression | ✅ | Interface de suivi en temps réel. |

---

## 🦅 Module `taxonomy` (Gestion des Espèces)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Modèles de données | ✅ | Structure hiérarchique : `Ordre` -> `Famille` -> `Espece`. |
| 2 | Commande `charger_lof` | ✅ | **(Recommandé)** Import rapide depuis la Liste des Oiseaux de France. |
| 3 | Commande `charger_taxref` | ✅ | (Alternative) Import depuis le référentiel national TaxRef. |
| 4 | Commande `recuperer_liens_oiseaux_net` | ✅ | Enrichissement automatique des données avec des liens externes. |

---

## 🗺️ Module `geo` (Géocodage)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Base de données des communes | ✅ | Cache local de ~35 000 communes françaises pour un géocodage rapide. |
| 2 | Commande `charger_communes_france` | ✅ | Peuple la base de données des communes via une API officielle. |
| 3 | Géocodeur intelligent | ✅ | Stratégie à 2 niveaux : recherche locale d'abord, puis API externe (Nominatim). |
| 4 | API de recherche | ✅ | Point d'accès (`/geo/rechercher-communes/`) pour l'auto-complétion. |

---

## ✅ Module `review` (Validation)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Workflow de correction | ✅ | Gestion des statuts : `nouveau`, `en_cours`, `corrige`, `valide`, `rejete`. |
| 2 | Soumission pour validation | ✅ | Un observateur peut soumettre sa fiche, ce qui la verrouille pour lui. |

---

## 📜 Module `audit` (Traçabilité)

| # | Fonctionnalité | État | Notes |
|---|---|---|---|
| 1 | Historique des modifications | ✅ | Chaque changement sur une fiche est enregistré. |
| 2 | Tracking automatique | ✅ | Utilise les signaux Django (`post_save`) pour une traçabilité transparente. |
| 3 | Interface de consultation | ✅ | Page dédiée pour voir l'historique complet d'une fiche. |