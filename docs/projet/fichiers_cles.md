# 📁 Index des Fichiers Clés

> **Résumé** : Inventaire des fichiers importants du projet, classés par catégorie.

---

## 🎨 JavaScript

| Fichier | Description |
|---------|-------------|
| `observations/static/Observations/js/main.js` | Fonctionnalités JavaScript principales |
| `observations/static/Observations/js/saisie_observation.js` | Interactions du formulaire de saisie |
| `observations/static/Observations/js/sidebar.js` | Toggle et interactions du menu latéral |
| `ingest/static/ingest/js/preparation_images.js` | Interface de préparation des images |

---

## 🎨 CSS / Feuilles de Style

| Fichier | Description |
|---------|-------------|
| `observations/static/Observations/css/styles.css` | Styles personnalisés de l'application |
| `observations/static/Observations/css/sidebar.css` | Styles du menu latéral |
| `observations/static/Observations/css/normalize.css` | Normalisation CSS |
| `geo/static/geo/css/commune_autocomplete.css` | Styles du widget d'autocomplétion |

---

## 📄 Templates HTML

### Base et Composants Partagés

| Fichier | Description |
|---------|-------------|
| `templates/base.html` | Template de base pour toutes les pages |
| `observations/templates/components/navbar.html` | Barre de navigation |
| `observations/templates/components/footer.html` | Pied de page |
| `observations/templates/components/messages.html` | Affichage des messages flash |
| `observations/templates/components/pagination.html` | Contrôles de pagination |
| `observations/templates/components/user_card.html` | Carte profil utilisateur |

### Observations (Application Principale)

| Fichier | Description |
|---------|-------------|
| `observations/templates/home.html` | Page d'accueil / tableau de bord |
| `observations/templates/login.html` | Page de connexion |
| `observations/templates/liste_fiches_observations.html` | Liste des fiches d'observation |
| `observations/templates/fiche_observation.html` | Détail d'une fiche |
| `observations/templates/observations/statistiques.html` | Page de statistiques |
| `observations/templates/saisie/saisie_observation.html` | Formulaire principal de saisie |
| `observations/templates/saisie/ajouter_observation.html` | Sous-formulaire ajout observation |
| `observations/templates/saisie/historique_modifications.html` | Historique des modifications |
| `observations/templates/transcription/upload_files.html` | Upload pour transcription |
| `observations/templates/transcription/processing.html` | Suivi du traitement |
| `observations/templates/transcription/results.html` | Résultats de transcription |

### Accounts (Gestion Utilisateurs)

| Fichier | Description |
|---------|-------------|
| `accounts/templates/accounts/inscription_publique.html` | Formulaire d'inscription publique |
| `accounts/templates/accounts/liste_utilisateurs.html` | Liste des utilisateurs |
| `accounts/templates/accounts/mon_profil.html` | Page de profil |
| `accounts/templates/accounts/valider_utilisateur.html` | Validation admin |
| `accounts/templates/accounts/mot_de_passe_oublie.html` | Réinitialisation mot de passe |

### Geo (Données Géographiques)

| Fichier | Description |
|---------|-------------|
| `geo/templates/geo/liste_communes.html` | Liste des communes |
| `geo/templates/geo/detail_commune.html` | Détail d'une commune |
| `geo/templates/geo/administration_donnees.html` | Administration des données |
| `geo/templates/geo/rechercher_nominatim.html` | Recherche Nominatim |

### Ingest (Import de Données)

| Fichier | Description |
|---------|-------------|
| `ingest/templates/ingest/accueil.html` | Accueil module ingest |
| `ingest/templates/ingest/importer_json.html` | Import JSON unitaire |
| `ingest/templates/ingest/importer_json_batch.html` | Import JSON en lot |
| `ingest/templates/ingest/preparer_images.html` | Préparation des images |
| `ingest/templates/ingest/batch_progress.html` | Progression des traitements |

### Taxonomy (Espèces)

| Fichier | Description |
|---------|-------------|
| `taxonomy/templates/taxonomy/liste_especes.html` | Liste des espèces |
| `taxonomy/templates/taxonomy/detail_espece.html` | Détail d'une espèce |
| `taxonomy/templates/taxonomy/importer_especes.html` | Import d'espèces |

### OCR

| Fichier | Description |
|---------|-------------|
| `ocr/templates/ocr/selection_repertoire_ocr.html` | Sélection des répertoires |
| `ocr/templates/ocr/batch_results.html` | Résultats des lots OCR |

---

## 🐍 Python - Modèles

| Fichier | Description |
|---------|-------------|
| `observations/models.py` | Modèles principaux : FicheObservation, Observation, Nid |
| `accounts/models.py` | Modèle Utilisateur et comptes |
| `geo/models.py` | Modèles géographiques : Localisation, CommuneFrance |
| `taxonomy/models.py` | Modèle Espece et taxonomie |
| `ingest/models.py` | Modèles d'import : Importation, EspeceCandidate |
| `audit/models.py` | Modèle HistoriqueModification |
| `review/models.py` | Modèles de validation |
| `ocr/models.py` | Modèle TranscriptionOCR |

---

## 🐍 Python - Vues

### Observations

| Fichier | Description |
|---------|-------------|
| `observations/views/views_home.py` | Vues tableau de bord et accueil |
| `observations/views/views_observation.py` | Vues détail et liste des fiches |
| `observations/views/saisie_observation_view.py` | Vues du formulaire de saisie |
| `observations/views/upload_views.py` | Gestion des uploads |
| `observations/views/view_transcription.py` | Vues de transcription |
| `observations/views/api_observateurs.py` | API REST observateurs |

### Autres Applications

| Fichier | Description |
|---------|-------------|
| `accounts/views/auth.py` | Authentification et connexion |
| `accounts/views/admin_views.py` | Administration utilisateurs |
| `geo/views.py` | Vues données géographiques |
| `geo/views_admin.py` | Administration géographie |
| `ingest/views/home.py` | Accueil module ingest |
| `ingest/views/importation.py` | Vues d'importation |
| `taxonomy/views.py` | Liste et détail espèces |
| `ocr/views.py` | Traitement OCR |

---

## 🐍 Python - Formulaires

| Fichier | Description |
|---------|-------------|
| `accounts/forms.py` | Formulaires inscription, connexion, profil |
| `observations/forms.py` | Formulaires de saisie d'observation |

---

## 🐍 Python - Tâches Celery

| Fichier | Description |
|---------|-------------|
| `observations/tasks.py` | Tâches asynchrones observations |
| `ingest/tasks.py` | Tâches workflow d'ingestion |
| `ocr/tasks.py` | Tâches batch OCR Gemini |
| `taxonomy/tasks.py` | Tâches maintenance taxonomie |

---

## 🐍 Python - Administration Django

| Fichier | Description |
|---------|-------------|
| `observations/admin.py` | Admin fiches et observations |
| `accounts/admin.py` | Admin utilisateurs |
| `geo/admin.py` | Admin données géographiques |
| `taxonomy/admin.py` | Admin espèces |
| `ingest/admin.py` | Admin importations |
| `audit/admin.py` | Admin historique |
| `ocr/admin.py` | Admin transcriptions OCR |

---

## 🐍 Python - URLs / Routage

| Fichier | Description |
|---------|-------------|
| `observations_nids/urls.py` | Configuration racine des URLs |
| `observations/urls.py` | Routes observations (accueil, listes, formulaires) |
| `accounts/urls.py` | Routes authentification et profil |
| `geo/urls.py` | Routes données géographiques |
| `ingest/urls.py` | Routes ingestion |
| `taxonomy/urls.py` | Routes espèces |
| `ocr/urls.py` | Routes OCR |

---

## 🐍 Python - Configuration Projet

| Fichier | Description |
|---------|-------------|
| `observations_nids/settings.py` | Configuration Django principale |
| `observations_nids/config.py` | Configuration Pydantic (variables d'environnement) |
| `observations_nids/celery.py` | Configuration Celery |
| `observations_nids/urls.py` | Configuration racine des URLs |
| `observations_nids/wsgi.py` | Point d'entrée WSGI (production) |
| `observations_nids/asgi.py` | Point d'entrée ASGI |
| `observations_nids/context_processors.py` | Processeurs de contexte template |
| `observations_nids/health.py` | Endpoint health check |

---

## 🐍 Python - Utilitaires et Services

| Fichier | Description |
|---------|-------------|
| `accounts/utils/email_service.py` | Service d'envoi d'emails |
| `geo/utils/geocoding.py` | Utilitaires de géocodage |
| `geo/services/geocodeur.py` | Service de géocodage |
| `ingest/importation_service.py` | Logique d'importation |
| `ingest/utils/image_processing.py` | Traitement d'images |
| `ingest/utils/image_deskew.py` | Redressement d'images |
| `observations/json_rep/json_sanitizer.py` | Nettoyage JSON OCR |
| `observations/filters.py` | Filtres de requête observations |
| `core/constants.py` | Constantes de l'application |
| `core/exceptions.py` | Exceptions personnalisées |

---

## 🐍 Python - Commandes de Gestion

### Données Géographiques

| Fichier | Description |
|---------|-------------|
| `geo/management/commands/charger_communes_france.py` | Charger les communes |
| `geo/management/commands/charger_altitudes.py` | Charger les altitudes |
| `geo/management/commands/importer_anciennes_communes.py` | Importer communes obsolètes |

### Taxonomie

| Fichier | Description |
|---------|-------------|
| `taxonomy/management/commands/charger_taxref.py` | Charger données TAXREF |
| `taxonomy/management/commands/charger_lof.py` | Charger espèces LOF |
| `taxonomy/management/commands/import_codes_gonm.py` | Importer codes GONM |

### Utilisateurs

| Fichier | Description |
|---------|-------------|
| `accounts/management/commands/export_users.py` | Exporter utilisateurs |
| `accounts/management/commands/import_users.py` | Importer utilisateurs |

### Maintenance

| Fichier | Description |
|---------|-------------|
| `observations/management/commands/corriger_chemins_media.py` | Corriger chemins médias |
| `geo/management/commands/reset_importations.py` | Réinitialiser importations |
| `geo/management/commands/reset_transcriptions.py` | Réinitialiser transcriptions |

---

## 📊 Résumé

| Catégorie | Nombre de fichiers |
|-----------|-------------------|
| JavaScript | 4 |
| CSS | 4 |
| Templates HTML | ~70 |
| Modèles Python | 8 |
| Vues Python | ~12 modules |
| Formulaires | 2 |
| Tâches Celery | 4 |
| Admin Django | 7 |
| Configuration URLs | 7 |
| Configuration projet | 8 |
| Utilitaires | ~10 |
| Commandes gestion | ~15 |

---

## 🔗 Voir Aussi

- [Architecture](../guides/architecture.md) - Vue d'ensemble technique
- [Plan directeur](./docs_todo.md) - État de la documentation
