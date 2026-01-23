# Architecture Globale - Observations Nids

> Documentation technique de référence du projet observations_nids

---

## 1. Vue d'Ensemble Technique

### Stack Technologique

#### Framework & Backend
- **Django** : 6.0.1
- **Python** : 3.11+ (minimum) / 3.12 (production Docker)
- **WSGI Server** : Gunicorn 23.0.0 (4 workers, timeout 120s)
- **Reverse Proxy** : Nginx (Alpine)

#### Base de Données & Cache
- **Database** : MariaDB 10.11 avec mysqlclient 2.2.7
- **Cache/Broker** : Redis 7 Alpine
- **Tâches Asynchrones** : Celery 5.6.2 avec eventlet 0.40.4

#### Intelligence Artificielle
- **OCR Engine** : Google Gemini API (google-genai 1.57.0)
- **Modèles utilisés** :
  - gemini-3-flash (principal)
  - gemini-3-pro
  - gemini-2.5-pro
  - gemini-2.5-flash-lite
- **Rate Limiting** : 60 req/min, timeout 120s, 3 retries avec exponential backoff

#### Frontend & UI
- **Formulaires** : django-crispy-forms 2.5 + crispy-bootstrap5 2025.6
- **Framework CSS** : Bootstrap 4 (django-bootstrap4-form 4.0.2)
- **JavaScript** : Vanilla JS avec AJAX pour formulaires dynamiques

#### Production & Monitoring
- **Fichiers Statiques** : WhiteNoise 6.11.0 (compression + manifest)
- **Sécurité** : django-csp 4.0 (Content Security Policy)
- **Monitoring Celery** : Flower 2.0.1 (port 5555)
- **Images** : Pillow 12.1.0

#### Services Additionnels
- **Helpdesk** : django-helpdesk 2.1.0 (customisé via helpdesk_custom)
- **API** : djangorestframework 3.16.1
- **Géolocalisation** : geopy 2.4.1 (Nominatim/OpenStreetMap)
- **Filtrage** : django-filter 25.2

---

## 2. Cartographie des Applications Django

### Applications Métier Principales

#### **observations** - Application Centrale
**Rôle** : Gestion complète du cycle de vie des fiches d'observation de nidification

**Modèles clés** :
- `FicheObservation` : Entité centrale (num_fiche, observateur, espèce, année)
- `Observation` : Événements individuels d'observation (date, heure, nombre_oeufs, nombre_poussins)
- `Nid` : Informations sur le nid (hauteur, détails, lien avec nid précédent)
- `ResumeObservation` : Synthèse des observations (dates partielles jour/mois, compteurs œufs/poussins)
- `CausesEchec` : Causes d'échec de la nidification
- `EtatCorrection` : Statut de validation (nouveau, en_edition, en_cours, valide) avec mécanisme de verrouillage
- `ConfigurationVerrouillage` : Durées de verrouillage configurables (1-10 jours ou permanent)
- `ImageSource` : Images téléchargées en attente de transcription
- `Remarque` : Commentaires horodatés

**Auto-création** : Chaque FicheObservation crée automatiquement ses objets liés (Localisation, Nid, ResumeObservation, CausesEchec, EtatCorrection)

---

#### **accounts** - Gestion Utilisateurs
**Rôle** : Workflow d'inscription avec validation admin et gestion des rôles

**Modèles** :
- `Utilisateur` : Extension de AbstractUser avec rôles (observateur, reviewer, administrateur)
- `Notification` : Notifications système (demande_compte, compte_valide, compte_refuse, info, warning)

**Workflow** : Inscription publique → Validation admin → Compte actif

---

#### **taxonomy** - Référentiel Espèces
**Rôle** : Taxonomie ornithologique basée sur TAXREF avec codes GONM personnalisés

**Modèles** :
- `Ordre` : Ordres taxonomiques
- `Famille` : Familles ornithologiques (→ Ordre)
- `Espece` : Espèces avec code_gonm unique, noms français/anglais/scientifiques, liens oiseau.net

**Source** : TAXREF + codes GONM du Groupe Ornithologique Normand

---

#### **geo** - Données Géographiques
**Rôle** : Base de données géographiques françaises avec géocodage automatique et support des fusions de communes

**Modèles** :
- `CommuneFrance` : Cache des communes françaises (code INSEE, GPS, altitude, population, superficie)
- `AncienneCommune` : Communes fusionnées avec liens vers commune actuelle
- `Localisation` : Localisation d'une fiche (commune, lieu-dit, GPS, paysage, alentours)

**Sources** : API Géoplateforme, Nominatim, saisies manuelles

---

#### **ingest** - Pipeline d'Import JSON
**Rôle** : Import des transcriptions OCR dans la base avec workflow de validation

**Modèles** :
- `PreparationImage` : Historique de préparation des images (fusion recto/verso, optimisation)
- `TranscriptionBrute` : Transcriptions JSON brutes non traitées
- `EspeceCandidate` : Espèces candidates avec score de similarité (0-100%) pour validation
- `ImportationEnCours` : Suivi d'import (en_attente, erreur, complete)

**Workflow** : JSON brut → Validation des candidats → Création de FicheObservation

---

#### **ocr** - Expérimentation OCR (Pilote uniquement)
**Rôle** : Évaluation comparative des modèles OCR et techniques de prétraitement d'images

**Modèle** :
- `TranscriptionOCR` : Métadonnées d'évaluation (score global, précision par champ, temps traitement, compteurs d'erreurs par type)

**Note** : À retirer de INSTALLED_APPS en production (environnement pilote seulement)

---

#### **audit** - Traçabilité
**Rôle** : Historique complet de toutes les modifications apportées aux données

**Modèle** :
- `HistoriqueModification` : Audit trail (fiche, champ modifié, ancienne/nouvelle valeur, utilisateur, timestamp, catégorie)

**Catégories** : fiche, observation, validation, localisation, nid, resume_observation, causes_echec, remarque

---

#### **review** - Workflow de Validation
**Rôle** : Processus de validation multi-reviewers pour les fiches transcrites

**Modèles** :
- `Validation` : Processus de review (en_cours, validee, rejete)
- `HistoriqueValidation` : Historique des changements de statut

---

### Applications Utilitaires

#### **core** - Utilitaires Partagés
**Rôle** : Constantes et utilitaires réutilisables

**Contenu** :
- `ROLE_CHOICES` : observateur, reviewer, administrateur
- `STATUT_VALIDATION_CHOICES` : en_cours, validee, rejete
- `STATUT_IMPORTATION_CHOICES` : en_attente, erreur, complete
- `CATEGORIE_MODIFICATION_CHOICES` : 8 catégories pour l'audit

---

#### **helpdesk_custom** - Support Personnalisé
**Rôle** : Extension de django-helpdesk avec formulaires personnalisés et authentification requise

---

## 3. Flux de Données Principal

### Flux de Saisie Manuelle

```
┌─────────────┐
│ Utilisateur │
└──────┬──────┘
       │ Authentification
       v
┌──────────────────┐
│ Formulaire AJAX  │  observations/templates/saisie/saisie_observation.html
│ (dynamique)      │  observations/static/Observations/js/saisie_observation.js
└──────┬───────────┘
       │ Soumission
       v
┌─────────────────────────┐
│ FicheObservation créée  │  observations/models.py
│ + Auto-création :       │
│  - Localisation         │
│  - Nid                  │
│  - ResumeObservation    │
│  - CausesEchec          │
│  - EtatCorrection       │
└──────┬──────────────────┘
       │
       v
┌──────────────────────────┐
│ Calcul automatique :     │
│ - pourcentage_completion │
│ - Statut: nouveau        │
│   puis en_edition        │
└──────────────────────────┘
```

---

### Flux de Transcription OCR

```
┌────────────────┐
│ Upload Images  │
└────┬───────────┘
     │ ImageSource (est_transcrite=False)
     v
┌──────────────────────────┐
│ Tâche Celery             │  ocr/tasks.py
│ (Queue: ocr)             │
│                          │
│ Rate Limit: 60 req/min   │
│ Timeout: 120s            │
│ Retries: 3 (exp backoff) │
└────┬─────────────────────┘
     │ Appel API
     v
┌──────────────────────────┐
│ Google Gemini API        │
│ (gemini-3-flash)         │
│                          │
│ Prompt personnalisé      │
│ Format JSON structuré    │
└────┬─────────────────────┘
     │ JSON brut
     v
┌──────────────────────────┐
│ TranscriptionBrute       │  ingest/models.py
│ (json_brut, traite)      │
└────┬─────────────────────┘
     │
     v
┌──────────────────────────┐
│ Validation Candidats     │
│ - EspeceCandidate        │
│   (score similarité)     │
│ - ObservateurCandidat    │
└────┬─────────────────────┘
     │ Validation manuelle si nécessaire
     v
┌──────────────────────────┐
│ ImportationEnCours       │
│ Statut: en_attente       │
│      → erreur            │
│      → complete          │
└────┬─────────────────────┘
     │ Import réussi
     v
┌──────────────────────────┐
│ FicheObservation créée   │
│ Statut: nouveau          │
└──────────────────────────┘
```

---

### Flux de Validation & Verrouillage

```
┌──────────────────────────┐
│ Reviewer revendique      │
│ la fiche                 │
└────┬─────────────────────┘
     │ Verrouillage
     v
┌──────────────────────────┐
│ EtatCorrection           │
│ - en_correction_par: X   │
│ - date_debut_correction  │
│ - Statut: en_cours       │
└────┬─────────────────────┘
     │ Verrouillé pour durée configurée
     │ (défaut: 5 jours)
     v
┌──────────────────────────┐
│ Correction en cours      │
│ - Autres reviewers:      │
│   lecture seule          │
└────┬─────────────────────┘
     │ Auto-unlock SI timeout
     │ OU validation manuelle
     v
┌──────────────────────────┐
│ Validation finale        │
│ - Statut: valide         │
│ - validee_par: X         │
│ - date_validation        │
└────┬─────────────────────┘
     │ Chaque modification
     v
┌──────────────────────────┐
│ HistoriqueModification   │
│ - champ_modifie          │
│ - ancienne_valeur        │
│ - nouvelle_valeur        │
│ - utilisateur, timestamp │
└──────────────────────────┘
```

---

### Flux de Géocodage

```
┌──────────────────────────┐
│ Saisie commune           │
│ (commune_saisie)         │
└────┬─────────────────────┘
     │ Recherche
     v
┌──────────────────────────┐
│ CommuneFrance lookup     │
│ - Par code INSEE         │
│ - Par nom (aliases)      │
│ - Par code postal        │
└────┬─────────────────────┘
     │ Si trouvée
     v
┌──────────────────────────┐
│ Localisation enrichie    │
│ - commune (normalisée)   │
│ - code_insee             │
│ - latitude, longitude    │
│ - altitude               │
│ - departement            │
└────┬─────────────────────┘
     │ Si non trouvée
     v
┌──────────────────────────┐
│ Géocodage Nominatim      │
│ (via geopy)              │
└────┬─────────────────────┘
     │ Création manuelle si échec
     v
┌──────────────────────────┐
│ Nouvelle CommuneFrance   │
│ source_ajout: manual     │
│ ajoutee_par: utilisateur │
└──────────────────────────┘
```

---

## 4. Infrastructure Docker

### Architecture des Conteneurs

```
┌────────────────────────────────────────────────────────┐
│                    Docker Compose                      │
│                  (observations_network)                │
└────────────────────────────────────────────────────────┘

┌─────────────┐  ┌──────────────┐  ┌─────────────────┐
│   nginx     │  │   web        │  │ celery_worker   │
│   :8010     │→ │ gunicorn     │  │ (concurrency:2) │
│             │  │ 4 workers    │  │                 │
│ Alpine      │  │ :8000        │  │ Python 3.12     │
└─────────────┘  └──────┬───────┘  └────────┬────────┘
                        │                   │
                        │  ┌────────────────┴─────┐
                        │  │   celery_beat        │
                        │  │   (scheduler)        │
                        │  └──────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
   ┌────┴─────┐                  ┌──────┴──────┐
   │    db    │                  │    redis    │
   │ MariaDB  │                  │    :6379    │
   │  10.11   │                  │  7-alpine   │
   │  :3306   │                  │             │
   └──────────┘                  └─────────────┘

┌─────────────┐  ┌──────────────┐
│   flower    │  │ phpmyadmin   │
│   :5555     │  │   :8081      │
│ monitoring  │  │ DB admin UI  │
└─────────────┘  └──────────────┘
```

---

### Services Détaillés

#### **nginx** (observations_nginx)
- **Image** : nginx:alpine
- **Port exposé** : 8010 (hôte) → 80 (conteneur)
- **Rôle** : Reverse proxy vers web:8000, servir fichiers statiques/media
- **Volumes** :
  - nginx/nginx.conf
  - nginx/conf.d
  - static_volume (read-only)
  - media (read-only)
  - nginx/ssl (certificats)
- **Healthcheck** : wget http://localhost/health/

---

#### **web** (observations_web)
- **Build** : docker/Dockerfile (Python 3.12-slim-bookworm)
- **Command** : gunicorn observations_nids.wsgi:application
  - 4 workers
  - Bind 0.0.0.0:8000
  - Timeout 120s
  - Access log vers stdout
- **Port** : 8000 (interne)
- **Volumes** :
  - static_volume (fichiers statiques collectés)
  - /opt/observations_nids_pilote/media (media partagé)
  - logs/
- **Dépendances** : db (healthy), redis (healthy)
- **Healthcheck** : curl http://localhost:8000/health/
- **Utilisateur** : django (non-root)

---

#### **db** (observations_db)
- **Image** : mariadb:10.11
- **Port** : 3306 (interne)
- **Volume** : db_data (persistant)
- **Configuration** : mariadb/conf.d
- **Healthcheck** : mysqladmin ping
- **Variables env** :
  - MYSQL_DATABASE
  - MYSQL_USER
  - MYSQL_PASSWORD
  - MYSQL_ROOT_PASSWORD

---

#### **redis** (observations_redis)
- **Image** : redis:7-alpine
- **Port** : 6379 (interne)
- **Volume** : redis_data (persistant)
- **Configuration** : appendonly yes (AOF persistence)
- **Healthcheck** : redis-cli ping

---

#### **celery_worker** (observations_celery_worker)
- **Build** : Même image que web
- **Command** : celery -A observations_nids worker --loglevel=info --concurrency=2
- **Volumes** : media, logs
- **Dépendances** : db, redis, web
- **Queues** : default, ocr (avec rate limiting)

---

#### **celery_beat** (observations_celery_beat)
- **Build** : Même image que web
- **Command** : celery -A observations_nids beat --loglevel=info
- **Rôle** : Planificateur de tâches périodiques
- **Volumes** : logs
- **Dépendances** : db, redis, web

---

#### **flower** (observations_flower)
- **Build** : Même image que web
- **Command** : celery -A observations_nids flower --port=5555 --url-prefix=flower
- **Port exposé** : 5555
- **Rôle** : Interface de monitoring Celery
- **Dépendances** : celery_worker

---

#### **phpmyadmin** (observations_phpmyadmin)
- **Image** : phpmyadmin:latest
- **Port exposé** : 8081
- **Rôle** : Interface graphique d'administration MariaDB
- **Configuration** : PMA_HOST=db

---

### Volumes Persistants

| Volume | Usage |
|--------|-------|
| `db_data` | Données MariaDB (tables, indexes) |
| `redis_data` | Données Redis (cache, broker Celery) |
| `static_volume` | Fichiers statiques Django collectés (CSS, JS, images) |
| `/opt/observations_nids_pilote/media` | Fichiers uploadés (images sources, JSON, photos nids) - **Volume externe** |

---

### Réseau

- **Nom** : observations_network
- **Driver** : bridge
- **Communication** : Tous les services peuvent se résoudre par nom (web, db, redis, etc.)

---

### Entrypoint & Démarrage

**Script** : `docker-entrypoint.sh`

**Séquence de démarrage** :
1. Attente disponibilité DB (netcat db:3306)
2. Attente disponibilité Redis (netcat redis:6379)
3. Migrations Django : `python manage.py migrate --noinput`
4. Collecte statiques : `python manage.py collectstatic --noinput`
5. Création superuser si variables env présentes
6. Exécution commande conteneur (gunicorn/celery/etc.)

**Healthchecks** :
- DB : `mysqladmin ping`
- Redis : `redis-cli ping`
- Web : `curl http://localhost:8000/health/`
- Nginx : `wget http://localhost/health/`

---

## 5. Points d'Attention Architecture

### Sécurité
- **Utilisateur non-root** : Conteneur web s'exécute avec user django
- **CSP** : Content Security Policy configurée (django-csp)
- **Secrets** : Stockés dans .env, non commités (nécessite vault en production)
- **CSRF** : CSRF_TRUSTED_ORIGINS doit correspondre exactement au domaine

### Performance
- **OCR Rate Limit** : 60 req/min Gemini, prévoir délais sur gros volumes
- **Gunicorn Workers** : 4 workers (ajuster selon RAM disponible)
- **Redis Persistence** : AOF activé (append-only file)
- **Static Files** : Compression WhiteNoise en production

### Scalabilité
- **Horizontale** : Configuration single-host actuellement
- **Celery Concurrency** : 2 workers (ajustable selon charge)
- **Media Storage** : Volume hôte `/opt/observations_nids_pilote/media` (non-portable, migrer vers S3/MinIO pour prod distribuée)

### Données
- **Sémantique NULL** : Dans ResumeObservation, NULL = "non observé" vs 0+ = "observé avec cette valeur"
- **Dates Partielles** : Support jour/mois sans année (événements de reproduction aviaire)
- **Auto-unlock** : Fiches verrouillées se débloquent automatiquement après durée configurée (défaut 5j)

### Environnements
- **Développement** : DEBUG=True, SQLite possible, pas de WhiteNoise
- **Pilote** : Configuration actuelle, app `ocr` activée pour tests
- **Production** : Retirer app `ocr`, DEBUG=False, SMTP réel, backup BDD automatique

---

## 6. Commandes de Gestion Clés

### Docker
```bash
# Démarrer
docker compose up -d

# Logs en temps réel
docker compose logs -f web

# Shell Django
docker compose exec web python manage.py shell

# Migrations
docker compose exec web python manage.py migrate

# Collecte statiques
docker compose exec web python manage.py collectstatic --noinput

# Créer superuser
docker compose exec web python manage.py createsuperuser
```

### Données Référentielles
```bash
# Charger communes françaises
python manage.py charger_communes_france

# Charger espèces TAXREF
python manage.py charger_taxref

# Importer codes GONM
python manage.py import_codes_gonm
```

### Utilisateurs
```bash
# Exporter utilisateurs
python manage.py export_users

# Importer utilisateurs
python manage.py import_users
```

### Médias
```bash
# Corriger chemins médias
python manage.py corriger_chemins_media
```

---

## Métadonnées du Document

- **Version** : 1.0.0
- **Date de création** : Janvier 2026
- **Dernière mise à jour** : Janvier 2026
- **Auteur** : Lead Architecte (Claude)
- **Statut** : Documentation de référence
