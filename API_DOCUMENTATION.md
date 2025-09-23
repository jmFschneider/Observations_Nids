# Documentation API - Observations Nids

## Vue d'ensemble

Cette application Django permet de gérer des observations d'oiseaux avec trois modules principaux :
- **Observations** : Gestion des fiches d'observation et transcription d'images
- **Administration** : Gestion des utilisateurs
- **Importation** : Import de données JSON transcrites

---

## Base URL

```
http://localhost:8000/
```

---

## 1. Module Observations

### 1.1 Authentification

#### `POST /auth/login/`
Connexion utilisateur
- **Template** : `login.html`
- **Redirection** : Page d'accueil après connexion

#### `GET /auth/logout/`
Déconnexion utilisateur
- **Redirection** : `home`

### 1.2 Pages principales

#### `GET /`
Page d'accueil
- **Vue** : `views_home.home`
- **Template** : `home.html`
- **Authentification** : Requise
- **Contexte** :
  - `user` : Utilisateur connecté
  - `users_count` : Nombre d'utilisateurs
  - `observations_count` : Nombre d'observations

#### `GET /tableau-de-bord/`
Page de tableau de bord par défaut
- **Vue** : `views_home.default_view`
- **Template** : `access_restricted.html`

### 1.3 Gestion des observations

#### `GET /observations/`
Liste des observations / Nouvelle saisie
- **Vue** : `saisie_observation_view.saisie_observation`
- **Authentification** : Requise (`@login_required`)
- **Template** : `saisie/ajouter_observation.html`

#### `GET /observations/<int:fiche_id>/`
Détail d'une fiche d'observation
- **Vue** : `saisie_observation_view.fiche_observation_view`
- **Paramètres** :
  - `fiche_id` : ID de la fiche
- **Template** : `fiche_observation.html`

#### `GET|POST /observations/modifier/<int:fiche_id>/`
Modifier une observation existante
- **Vue** : `saisie_observation_view.saisie_observation`
- **Authentification** : Requise
- **Paramètres** :
  - `fiche_id` : ID de la fiche à modifier
- **Méthodes** :
  - `GET` : Affiche le formulaire pré-rempli
  - `POST` : Sauvegarde les modifications

#### `POST /observations/ajouter/<int:fiche_id>/`
Ajouter une observation à une fiche
- **Vue** : `saisie_observation_view.ajouter_observation`
- **Authentification** : Requise
- **Paramètres** :
  - `fiche_id` : ID de la fiche
- **Données POST** :
  - `date_observation` : DateTime
  - `nombre_oeufs` : Integer
  - `nombre_poussins` : Integer
  - `observations` : Text

#### `GET /observations/historique/<int:fiche_id>/`
Historique des modifications d'une fiche
- **Vue** : `saisie_observation_view.historique_modifications`
- **Authentification** : Requise
- **Template** : `saisie/historique_modifications.html`

### 1.4 Transcription d'images

#### `GET|POST /transcription/selection-repertoire/`
Sélection du répertoire d'images à transcrire
- **Vue** : `view_transcription.select_directory`
- **Template** : `transcription/upload_files.html`
- **Réponse POST (JSON)** :
  ```json
  {
    "success": true,
    "file_count": 15,
    "directory": "Rep1"
  }
  ```

#### `GET /transcription/traiter-images/`
Page de traitement des images
- **Vue** : `view_transcription.process_images`
- **Template** : `transcription/processing.html`
- **Note** : Lance une tâche Celery asynchrone

#### `POST /transcription/demarrer/`
API pour démarrer la transcription (AJAX)
- **Vue** : `view_transcription.start_transcription_view`
- **Réponse JSON** :
  ```json
  {
    "task_id": "uuid-task-id",
    "message": "Traitement démarré",
    "processing_url": "/transcription/verifier-progression/"
  }
  ```

#### `GET /transcription/verifier-progression/`
Vérifier la progression d'une tâche (AJAX)
- **Vue** : `view_transcription.check_progress`
- **Paramètres query** :
  - `task_id` : UUID de la tâche Celery
- **Réponse JSON** :
  ```json
  {
    "status": "PROGRESS",
    "percent": 45,
    "processed": 9,
    "total": 20,
    "current_file": "image_9.jpg"
  }
  ```

#### `GET /transcription/resultats/`
Afficher les résultats de transcription
- **Vue** : `view_transcription.transcription_results`
- **Template** : `transcription/results.html`

---

## 2. Module Administration

**Préfixe** : `/gestion/`

### 2.1 Gestion des utilisateurs

#### `GET /gestion/utilisateurs/`
Liste des utilisateurs
- **Vue** : `auth.ListeUtilisateursView` (CBV)
- **Authentification** : Admin uniquement
- **Template** : `administration/liste_utilisateurs.html`

#### `GET|POST /gestion/utilisateurs/creer/`
Créer un nouvel utilisateur
- **Vue** : `auth.creer_utilisateur`
- **Authentification** : Admin uniquement
- **Template** : `administration/creer_utilisateur.html`

#### `GET|POST /gestion/utilisateurs/<int:user_id>/modifier/`
Modifier un utilisateur
- **Vue** : `auth.modifier_utilisateur`
- **Authentification** : Admin uniquement
- **Paramètres** :
  - `user_id` : ID de l'utilisateur

#### `POST /gestion/utilisateurs/<int:user_id>/desactiver/`
Désactiver un utilisateur
- **Vue** : `auth.desactiver_utilisateur`
- **Authentification** : Admin uniquement

#### `POST /gestion/utilisateurs/<int:user_id>/activer/`
Activer un utilisateur
- **Vue** : `auth.activer_utilisateur`
- **Authentification** : Admin uniquement

#### `GET /gestion/utilisateurs/<int:user_id>/detail/`
Détail d'un utilisateur
- **Vue** : `auth.detail_utilisateur`
- **Template** : `administration/user_detail.html`

#### `POST /gestion/utilisateurs/<int:user_id>/valider/`
Valider un utilisateur en attente
- **Vue** : `auth.valider_utilisateur`
- **Authentification** : Admin uniquement

### 2.2 Profil utilisateur

#### `GET|POST /gestion/mon-profil/`
Profil de l'utilisateur connecté
- **Vue** : `auth.mon_profil`
- **Authentification** : Requise
- **Template** : `administration/mon_profil.html`

### 2.3 Inscription

#### `GET|POST /gestion/inscription-publique/`
Inscription publique (nécessite validation admin)
- **Vue** : `auth.inscription_publique`
- **Template** : `administration/inscription_publique.html`

### 2.4 Fonctionnalités d'urgence

#### `GET|POST /gestion/urgence/promouvoir-administrateur/`
Promouvoir un utilisateur en administrateur
- **Vue** : `auth.promouvoir_administrateur`
- **Authentification** : Superuser uniquement
- **Template** : `administration/promouvoir_admin.html`

---

## 3. Module Importation

**Préfixe** : `/importation/`

### 3.1 Workflow d'importation

#### `GET /importation/`
Page d'accueil de l'importation
- **Vue** : `home.accueil_importation`
- **Template** : `importation/accueil.html`

#### `POST /importation/importer-json/`
Importer des fichiers JSON depuis un répertoire
- **Vue** : `importation.importer_json`
- **Données POST** :
  - `repertoire` : Nom du répertoire
- **Réponse JSON** :
  ```json
  {
    "success": true,
    "total": 10,
    "reussis": 10,
    "ignores": 0,
    "erreurs": []
  }
  ```

#### `POST /importation/extraire-candidats/`
Extraire les espèces et observateurs candidats
- **Vue** : `importation.extraire_candidats`
- **Réponse JSON** :
  ```json
  {
    "success": true,
    "especes_ajoutees": 5,
    "utilisateurs_crees": 3
  }
  ```

#### `POST /importation/preparer/`
Préparer les importations en attente
- **Vue** : `importation.preparer_importations`
- **Réponse JSON** :
  ```json
  {
    "success": true,
    "importations_creees": 10
  }
  ```

### 3.2 Gestion des espèces

#### `GET /importation/especes/`
Liste des espèces candidates à valider
- **Vue** : `especes.liste_especes_candidates`
- **Template** : `importation/liste_especes_candidates.html`

#### `POST /importation/especes/<int:espece_id>/valider/`
Valider une correspondance d'espèce
- **Vue** : `especes.valider_espece`
- **Données POST** :
  - `espece_validee_id` : ID de l'espèce validée

#### `POST /importation/especes/valider-multiples/`
Valider plusieurs espèces en batch
- **Vue** : `especes.valider_especes_multiples`
- **Données POST** :
  ```json
  {
    "validations": [
      {"candidate_id": 1, "espece_id": 10},
      {"candidate_id": 2, "espece_id": 15}
    ]
  }
  ```

#### `POST /importation/especes/creer/`
Créer une nouvelle espèce
- **Vue** : `especes.creer_nouvelle_espece`
- **Données POST** :
  - `nom` : Nom de l'espèce
  - `nom_scientifique` : Nom scientifique (optionnel)

### 3.3 Gestion des importations

#### `GET /importation/liste/`
Liste des importations en cours
- **Vue** : `importation.liste_importations`
- **Template** : `importation/liste_importations.html`

#### `GET /importation/detail/<int:importation_id>/`
Détail d'une importation
- **Vue** : `importation.detail_importation`
- **Template** : `importation/detail_importation.html`

#### `POST /importation/finaliser/<int:importation_id>/`
Finaliser une importation (créer la fiche)
- **Vue** : `importation.finaliser_importation`
- **Réponse JSON** :
  ```json
  {
    "success": true,
    "message": "Fiche d'observation #123 créée avec succès"
  }
  ```

#### `GET /importation/resume/`
Résumé de l'importation
- **Vue** : `home.resume_importation`
- **Template** : `importation/resume_importation.html`

### 3.4 Réinitialisation

#### `POST /importation/reinitialiser/<int:importation_id>/`
Réinitialiser une importation spécifique
- **Vue** : `importation.reinitialiser_importation`

#### `POST /importation/reinitialiser-toutes/`
Réinitialiser toutes les importations
- **Vue** : `importation.reinitialiser_toutes_importations`

---

## 4. Modèles de données

### 4.1 Observations

- **FicheObservation** : Fiche principale
  - `num_fiche` (PK auto)
  - `observateur` (FK → Utilisateur)
  - `espece` (FK → Espece)
  - `annee`
  - `chemin_image`, `chemin_json`
  - `transcription` (bool)

- **Observation** : Observations individuelles
  - `fiche` (FK)
  - `date_observation`
  - `nombre_oeufs`, `nombre_poussins`
  - `observations` (text)

- **Localisation** : Données géographiques (OneToOne avec FicheObservation)
- **Nid** : Informations sur le nid (OneToOne)
- **ResumeObservation** : Résumé statistique (OneToOne)
- **CausesEchec** : Causes d'échec de la nichée (OneToOne)
- **Remarque** : Remarques liées à une fiche
- **HistoriqueModification** : Suivi des modifications

### 4.2 Administration

- **Utilisateur** : Utilisateur personnalisé
  - Hérite de `AbstractUser`
  - `role` : observateur/reviewer/administrateur
  - `est_valide` : validation par admin
  - `est_transcription` : créé par import

### 4.3 Importation

- **TranscriptionBrute** : JSON brut importé
- **EspeceCandidate** : Espèces à valider
- **ImportationEnCours** : Suivi des imports

---

## 5. Tâches asynchrones (Celery)

### `process_images_task(directory)`
Traite les images d'un répertoire via l'API Gemini
- **États** :
  - `PROGRESS` : En cours
  - `SUCCESS` : Terminé
  - `ERROR` : Erreur
- **Métadonnées** :
  - `processed`, `total`, `current_file`, `percent`

---

## 6. Permissions

- **Anonyme** : Inscription publique uniquement
- **Authentifié** : Accès aux observations, profil
- **Admin** : Gestion utilisateurs, validation
- **Superuser** : Promotion admin d'urgence

---

## 7. Notes techniques

- **Framework** : Django 5.1
- **Celery** : Traitement asynchrone avec Redis
- **Base de données** : MySQL
- **Transcription IA** : Google Gemini API
- **Authentification** : Sessions Django