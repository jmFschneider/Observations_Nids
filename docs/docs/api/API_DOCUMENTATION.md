# Guide des URLs et des APIs - Observations Nids

*Dernière mise à jour : 2025-10-13*

## 1. Vue d'ensemble

Ce document décrit l'ensemble des URLs du projet, en distinguant les **pages web** (qui retournent du HTML) et les **points d'accès API** (qui retournent du JSON).

- **Framework** : Django 5.2.7
- **Base de données** : MySQL/MariaDB
- **Tâches asynchrones** : Celery avec Redis
- **APIs IA** : Google Gemini

---

## 2. Structure des URLs par module

L'application est découpée en plusieurs modules, chacun ayant son propre préfixe d'URL :

- `/` : Module principal **Observations**
- `/accounts/` : Module de **Gestion des comptes**
- `/geo/` : Module de **Géocodage**
- `/ingest/` : Module d'**Importation de données**
- `/taxonomy/` : Module de **Gestion des espèces**
- `/admin/` : Interface d'administration Django
- `/__debug__/` : Barre d'outils Django Debug Toolbar (en mode DEBUG)

---

## 3. Module `observations`

**Préfixe d'URL :** `/`

### Pages Web (HTML)

- **`GET /`** (`home`)
  - **Description** : Page d'accueil après connexion.
  - **Vue** : `observations.views.views_home.home`
  - **Template** : `home.html`

- **`GET /tableau-de-bord/`** (`default`)
  - **Description** : Page par défaut, actuellement une page de restriction d'accès.
  - **Vue** : `observations.views.views_home.default_view`
  - **Template** : `access_restricted.html`

- **`GET /auth/login/`** (`login`)
  - **Description** : Page de connexion.
  - **Vue** : `django.contrib.auth.views.LoginView`
  - **Template** : `login.html`

- **`GET /auth/logout/`** (`logout`)
  - **Description** : Déconnexion de l'utilisateur.
  - **Vue** : `django.contrib.auth.views.LogoutView`

- **`GET /observations/`** (`observations_list`)
  - **Description** : Page de saisie d'une nouvelle observation.
  - **Vue** : `observations.views.saisie_observation_view.saisie_observation`
  - **Template** : `saisie/ajouter_observation.html`

- **`GET /observations/liste/`** (`liste_fiches_observations`)
  - **Description** : Affiche la liste de toutes les fiches d'observation.
  - **Vue** : `observations.views.views_observation.liste_fiches_observations`

- **`GET /observations/<int:fiche_id>/`** (`fiche_observation`)
  - **Description** : Affiche le détail d'une fiche d'observation.
  - **Vue** : `observations.views.saisie_observation_view.fiche_observation_view`
  - **Template** : `fiche_observation.html`

- **`GET|POST /observations/modifier/<int:fiche_id>/`** (`modifier_observation`)
  - **Description** : Modifie une fiche d'observation existante.
  - **Vue** : `observations.views.saisie_observation_view.saisie_observation`

- **`GET /observations/historique/<int:fiche_id>/`** (`historique_modifications`)
  - **Description** : Affiche l'historique des modifications d'une fiche.
  - **Vue** : `observations.views.saisie_observation_view.historique_modifications`
  - **Template** : `saisie/historique_modifications.html`

- **`GET /transcription/selection-repertoire/`** (`select_directory`)
  - **Description** : Page pour sélectionner un répertoire d'images à transcrire.
  - **Vue** : `observations.views.view_transcription.select_directory`
  - **Template** : `transcription/upload_files.html`

- **`GET /transcription/traiter-images/`** (`process_images`)
  - **Description** : Page affichant la progression du traitement des images.
  - **Vue** : `observations.views.view_transcription.process_images`
  - **Template** : `transcription/processing.html`

- **`GET /transcription/resultats/`** (`transcription_results`)
  - **Description** : Affiche les résultats de la transcription.
  - **Vue** : `observations.views.view_transcription.transcription_results`
  - **Template** : `transcription/results.html`

### Points d'accès API (JSON)

- **`POST /observations/ajouter/<int:fiche_id>/`** (`ajouter_observation`)
  - **Description** : Ajoute une nouvelle ligne d'observation à une fiche existante.
  - **Vue** : `saisie_observation_view.ajouter_observation`

- **`POST /observations/soumettre/<int:fiche_id>/`** (`soumettre_pour_correction`)
  - **Description** : Soumet une fiche pour correction.
  - **Vue** : `saisie_observation_view.soumettre_pour_correction`

- **`POST /transcription/demarrer/`** (`start_transcription`)
  - **Description** : Démarre la tâche de transcription asynchrone (Celery).
  - **Vue** : `view_transcription.start_transcription_view`
  - **Réponse** : `{ "task_id": "...", "message": "...", "processing_url": "..." }`

- **`GET /transcription/verifier-progression/`** (`check_progress`)
  - **Description** : Interroge l'état d'une tâche de transcription.
  - **Vue** : `view_transcription.check_progress`
  - **Paramètres URL** : `?task_id=<uuid>`
  - **Réponse** : `{ "status": "...", "percent": 0-100, ... }`

---

## 4. Module `accounts`

**Préfixe d'URL :** `/accounts/`

### Pages Web (HTML)

- **`GET /accounts/utilisateurs/`** (`liste_utilisateurs`)
  - **Description** : Liste tous les utilisateurs. (Admin)
  - **Vue** : `accounts.views.auth.ListeUtilisateursView`

- **`GET|POST /accounts/utilisateurs/creer/`** (`creer_utilisateur`)
  - **Description** : Crée un nouvel utilisateur. (Admin)
  - **Vue** : `accounts.views.auth.creer_utilisateur`

- **`GET|POST /accounts/utilisateurs/<int:user_id>/modifier/`** (`modifier_utilisateur`)
  - **Description** : Modifie un utilisateur. (Admin)
  - **Vue** : `accounts.views.auth.modifier_utilisateur`

- **`GET /accounts/utilisateurs/<int:user_id>/detail/`** (`detail_utilisateur`)
  - **Description** : Affiche les détails d'un utilisateur. (Admin)
  - **Vue** : `accounts.views.auth.detail_utilisateur`

- **`GET|POST /accounts/mon-profil/`** (`mon_profil`)
  - **Description** : Page de profil de l'utilisateur connecté.
  - **Vue** : `accounts.views.auth.mon_profil`

- **`GET|POST /accounts/inscription-publique/`** (`inscription_publique`)
  - **Description** : Formulaire d'inscription publique.
  - **Vue** : `accounts.views.auth.inscription_publique`

- **`GET|POST /accounts/urgence/promouvoir-administrateur/`** (`promouvoir_administrateur`)
  - **Description** : Permet à un super-utilisateur de promouvoir un autre utilisateur admin. (Superuser)
  - **Vue** : `accounts.views.auth.promouvoir_administrateur`

### Points d'accès API (JSON)

- **`POST /accounts/utilisateurs/<int:user_id>/desactiver/`** (`desactiver_utilisateur`)
  - **Description** : Désactive un compte utilisateur. (Admin)
  - **Vue** : `accounts.views.auth.desactiver_utilisateur`

- **`POST /accounts/utilisateurs/<int:user_id>/activer/`** (`activer_utilisateur`)
  - **Description** : Active un compte utilisateur. (Admin)
  - **Vue** : `accounts.views.auth.activer_utilisateur`

- **`POST /accounts/utilisateurs/<int:user_id>/valider/`** (`valider_utilisateur`)
  - **Description** : Valide un utilisateur en attente. (Admin)
  - **Vue** : `accounts.views.auth.valider_utilisateur`

---

## 5. Module `geo`

**Préfixe d'URL :** `/geo/`

### Points d'accès API (JSON)

- **`POST /geo/geocoder/`** (`geocoder_commune`)
  - **Description** : Géocode manuellement une commune pour une fiche et sauvegarde les coordonnées.
  - **Vue** : `geo.views.geocoder_commune_manuelle`
  - **Données POST** : `fiche_id`, `commune`, `departement` (opt.), `lieu_dit` (opt.)
  - **Réponse** : `{ "success": true/false, "coords": {...}, "message": "..." }`

- **`GET /geo/rechercher-communes/`** (`rechercher_communes`)
  - **Description** : Recherche des communes pour l'auto-complétion.
  - **Vue** : `geo.views.rechercher_communes`
  - **Paramètres URL** : `?q=<terme>&lat=<lat>&lon=<lon>&limit=<N>`
  - **Réponse** : `{ "communes": [ { "nom": "...", "code_insee": "...", ... } ] }`

---

## 6. Module `ingest`

**Préfixe d'URL :** `/ingest/`

### Pages Web (HTML)

- **`GET /ingest/`** (`accueil_importation`)
  - **Description** : Page d'accueil du workflow d'importation.
  - **Vue** : `ingest.views.home.accueil_importation`

- **`GET /ingest/especes/`** (`liste_especes_candidates`)
  - **Description** : Affiche les espèces candidates à valider.
  - **Vue** : `ingest.views.especes.liste_especes_candidates`

- **`GET /ingest/liste/`** (`liste_importations`)
  - **Description** : Liste les importations en cours de validation.
  - **Vue** : `ingest.views.importation.liste_importations`

- **`GET /ingest/detail/<int:importation_id>/`** (`detail_importation`)
  - **Description** : Affiche le détail d'une importation.
  - **Vue** : `ingest.views.importation.detail_importation`

- **`GET /ingest/resume/`** (`resume_importation`)
  - **Description** : Affiche un résumé des dernières importations.
  - **Vue** : `ingest.views.home.resume_importation`

### Points d'accès API (JSON)

- **`POST /ingest/importer-json/`** (`importer_json`)
  - **Description** : Importe les fichiers JSON depuis un répertoire.
  - **Vue** : `ingest.views.importation.importer_json`

- **`POST /ingest/extraire-candidats/`** (`extraire_candidats`)
  - **Description** : Extrait les espèces et observateurs depuis les données brutes.
  - **Vue** : `ingest.views.importation.extraire_candidats`

- **`POST /ingest/preparer/`** (`preparer_importations`)
  - **Description** : Prépare les fiches d'importation en attente.
  - **Vue** : `ingest.views.importation.preparer_importations`

- **`POST /ingest/especes/<int:espece_id>/valider/`** (`valider_espece`)
  - **Description** : Valide la correspondance pour une espèce candidate.
  - **Vue** : `ingest.views.especes.valider_espece`

- **`POST /ingest/especes/valider-multiples/`** (`valider_especes_multiples`)
  - **Description** : Valide plusieurs espèces en une seule requête.
  - **Vue** : `ingest.views.especes.valider_especes_multiples`

- **`POST /ingest/especes/creer/`** (`creer_nouvelle_espece`)
  - **Description** : Crée une nouvelle espèce depuis le workflow d'import.
  - **Vue** : `ingest.views.especes.creer_nouvelle_espece`

- **`POST /ingest/finaliser/<int:importation_id>/`** (`finaliser_importation`)
  - **Description** : Finalise une importation et crée la fiche d'observation.
  - **Vue** : `ingest.views.importation.finaliser_importation`

- **`POST /ingest/finaliser-multiples/`** (`finaliser_importations_multiples`)
  - **Description** : Finalise plusieurs importations en une seule requête.
  - **Vue** : `ingest.views.importation.finaliser_importations_multiples`

- **`POST /ingest/reinitialiser/<int:importation_id>/`** (`reinitialiser_importation`)
  - **Description** : Réinitialise une importation spécifique.
  - **Vue** : `ingest.views.importation.reinitialiser_importation`

- **`POST /ingest/reinitialiser-toutes/`** (`reinitialiser_toutes_importations`)
  - **Description** : Réinitialise toutes les données du workflow d'importation.
  - **Vue** : `ingest.views.importation.reinitialiser_toutes_importations`

---

## 7. Module `taxonomy`

**Préfixe d'URL :** `/taxonomy/`

### Pages Web (HTML)

- **`GET /taxonomy/especes/`** (`liste_especes`)
  - **Description** : Affiche la liste de toutes les espèces gérées.
  - **Vue** : `taxonomy.views.liste_especes`

- **`GET /taxonomy/especes/<int:espece_id>/`** (`detail_espece`)
  - **Description** : Affiche les détails d'une espèce.
  - **Vue** : `taxonomy.views.detail_espece`

- **`GET|POST /taxonomy/especes/creer/`** (`creer_espece`)
  - **Description** : Formulaire pour créer une nouvelle espèce.
  - **Vue** : `taxonomy.views.creer_espece`

- **`GET|POST /taxonomy/especes/<int:espece_id>/modifier/`** (`modifier_espece`)
  - **Description** : Formulaire pour modifier une espèce.
  - **Vue** : `taxonomy.views.modifier_espece`

- **`GET|POST /taxonomy/especes/<int:espece_id>/supprimer/`** (`supprimer_espece`)
  - **Description** : Page de confirmation pour supprimer une espèce.
  - **Vue** : `taxonomy.views.supprimer_espece`

- **`GET /taxonomy/importer/`** (`importer_especes`)
  - **Description** : Page expliquant comment lancer les commandes d'import en masse.
  - **Vue** : `taxonomy.views.importer_especes`

---

## 8. Modèles de données

*(Cette section sera validée après une analyse détaillée des fichiers `models.py`)*

- **FicheObservation**: Fiche principale d'une observation.
- **Observation**: Observation individuelle liée à une fiche.
- **Localisation**: Données géographiques d'une fiche.
- **Utilisateur**: Modèle utilisateur personnalisé.
- **Espece**: Modèle principal pour une espèce d'oiseau.
- **Famille, Ordre**: Taxonomie supérieure.
- **ImportationEnCours**: Modèle de suivi pour le workflow d'importation.

---

## 9. Permissions

- **Anonyme** : Accès à la page de connexion et d'inscription publique.
- **Utilisateur authentifié** : Accès à son profil, aux fiches d'observation.
- **Admin (`is_staff`)** : Accès à la gestion des utilisateurs et à la gestion de la taxonomie.
- **Superuser** : Accès à toutes les fonctionnalités, y compris les commandes d'urgence.
