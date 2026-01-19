# 🏗️ Architecture Technique

> **Vue d'ensemble de l'architecture du projet Observations Nids**

---

## 🎯 Vue d'Ensemble

```mermaid
flowchart TB
    subgraph Client["🌐 Client"]
        Browser[Navigateur Web]
    end

    subgraph Proxy["🔀 Reverse Proxy"]
        Nginx[Nginx]
    end

    subgraph App["🐍 Application Django"]
        Gunicorn[Gunicorn]
        Django[Django 6.0]
    end

    subgraph Async["⚡ Tâches Asynchrones"]
        CeleryWorker[Celery Worker]
        CeleryBeat[Celery Beat]
        Flower[Flower Monitor]
    end

    subgraph Data["💾 Données"]
        MariaDB[(MariaDB)]
        Redis[(Redis)]
    end

    subgraph External["☁️ Services Externes"]
        Gemini[Google Gemini API]
    end

    Browser --> Nginx
    Nginx --> Gunicorn
    Gunicorn --> Django
    Django --> MariaDB
    Django --> Redis
    Django --> CeleryWorker
    CeleryWorker --> Redis
    CeleryWorker --> Gemini
    CeleryBeat --> Redis
    Flower --> Redis
```

---

## 📦 Stack Technique

### Backend

| Composant | Version | Rôle |
|-----------|---------|------|
| **Python** | 3.11+ | Langage principal |
| **Django** | 6.0.1 | Framework web |
| **Gunicorn** | - | Serveur WSGI |
| **Celery** | 5.6.2 | Tâches asynchrones |

### Base de Données

| Composant | Version | Rôle |
|-----------|---------|------|
| **MariaDB** | 10.11 | Base de données principale |
| **Redis** | 7 | Cache + Broker Celery |

### Infrastructure

| Composant | Version | Rôle |
|-----------|---------|------|
| **Nginx** | Alpine | Reverse proxy + Fichiers statiques |
| **Docker** | - | Conteneurisation |
| **Docker Compose** | - | Orchestration |

### Services Externes

| Service | Rôle |
|---------|------|
| **Google Gemini** | Transcription OCR des fiches papier |

---

## 🗂️ Architecture Applicative

### Applications Django

```mermaid
flowchart TB
    subgraph Coeur["🟢 Cœur Métier"]
        OBS[observations<br/>Fiches d'observation]
        TAX[taxonomy<br/>Espèces]
        GEO[geo<br/>Communes]
        ACC[accounts<br/>Utilisateurs]
    end

    subgraph Support["🔵 Support"]
        REV[review<br/>Validation]
        AUD[audit<br/>Historique]
        ING[ingest<br/>Import JSON]
    end

    subgraph Special["🟠 Spécialisé"]
        OCR[ocr<br/>Transcription]
        CORE[core<br/>Utilitaires]
    end

    OBS -->|espèce| TAX
    OBS -->|localisation| GEO
    OBS -->|observateur| ACC
    OBS -->|historique| AUD
    OBS -->|validation| REV
    OBS -->|images| OCR

    ING -->|crée fiches| OBS
    ING -->|utilise| OCR

    CORE -.->|constantes| OBS
    CORE -.->|constantes| ACC
    CORE -.->|constantes| REV
    CORE -.->|constantes| ING
    CORE -.->|constantes| AUD
```

### Responsabilités des Applications

| Application | Responsabilité | Modèles Principaux |
|-------------|----------------|-------------------|
| **observations** | Gestion des fiches | FicheObservation, Observation, Nid, EtatCorrection |
| **taxonomy** | Référentiel espèces | Ordre, Famille, Espece |
| **geo** | Géolocalisation | CommuneFrance, AncienneCommune, Localisation |
| **accounts** | Authentification | Utilisateur, Notification |
| **review** | Workflow validation | Validation, HistoriqueValidation |
| **audit** | Traçabilité | HistoriqueModification |
| **ingest** | Import données | TranscriptionBrute, EspeceCandidate, ImportationEnCours |
| **ocr** | OCR Gemini | TranscriptionOCR |
| **core** | Utilitaires | Constantes, Modèles abstraits, Exceptions |

---

## 🔄 Flux de Données

### Flux Principal : Saisie Manuelle

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant D as Django
    participant DB as MariaDB
    participant A as Audit

    U->>D: Saisit une fiche
    D->>DB: Crée FicheObservation
    D->>DB: Crée objets liés (Localisation, Nid, etc.)
    D->>A: Enregistre dans HistoriqueModification
    D-->>U: Confirmation
```

### Flux OCR : Transcription Automatique

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant D as Django
    participant R as Redis
    participant C as Celery Worker
    participant G as Gemini API
    participant DB as MariaDB

    U->>D: Upload image + Lance transcription
    D->>R: Crée tâche Celery
    D-->>U: Redirect vers page de progression

    C->>R: Récupère tâche
    C->>G: Envoie image
    G-->>C: JSON transcrit
    C->>DB: Crée TranscriptionBrute
    C->>R: Met à jour progression

    U->>D: Polling AJAX
    D->>R: Lit état tâche
    D-->>U: Progression (%)

    C->>R: Tâche terminée
    U->>D: Consulte résultats
```

### Flux Import : JSON vers Fiche

```mermaid
flowchart LR
    A[JSON Transcrit] --> B{Espèce connue ?}
    B -->|Oui| C[Association auto]
    B -->|Non| D[EspeceCandidate]
    D --> E[Validation manuelle]
    E --> C
    C --> F[ImportationEnCours]
    F --> G[Finalisation]
    G --> H[FicheObservation]
```

---

## 🐳 Architecture Docker

### Services

```mermaid
flowchart TB
    subgraph docker["Docker Compose"]
        nginx[nginx<br/>:8010]
        web[web<br/>Gunicorn]
        worker[celery_worker]
        beat[celery_beat]
        flower[flower<br/>:5555]
        db[(db<br/>MariaDB)]
        redis[(redis)]
        pma[phpmyadmin<br/>:8081]
    end

    nginx --> web
    web --> db
    web --> redis
    worker --> db
    worker --> redis
    beat --> redis
    flower --> redis
    pma --> db
```

### Volumes

| Volume | Contenu |
|--------|---------|
| `db_data` | Données MariaDB |
| `redis_data` | Données Redis (AOF) |
| `static_volume` | Fichiers statiques Django |
| `/opt/.../media` | Fichiers uploadés (images) |

### Réseaux

| Réseau | Rôle |
|--------|------|
| `observations_network` | Communication inter-services |

---

## 🔐 Sécurité

### Authentification

- Sessions Django avec cookies sécurisés
- Tokens de réinitialisation de mot de passe
- Validation des comptes par administrateur

### Autorisations

```mermaid
flowchart TB
    subgraph Roles["Hiérarchie des Rôles"]
        Admin[Administrateur]
        Reviewer[Reviewer]
        Observateur[Observateur]
    end

    Admin --> Reviewer
    Reviewer --> Observateur

    Admin -->|Gestion utilisateurs| U[Utilisateurs]
    Admin -->|Import données| I[Import]
    Reviewer -->|Correction fiches| F[Toutes les fiches]
    Observateur -->|Saisie| M[Mes fiches]
```

### Protection des Données

- CSRF protection
- XSS protection (templates Django)
- SQL injection protection (ORM Django)
- Cookies sécurisés en production (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`)

---

## 📊 Base de Données

### Schéma Simplifié

```mermaid
erDiagram
    Utilisateur ||--o{ FicheObservation : "observateur"
    FicheObservation ||--|| Localisation : "localisation"
    FicheObservation ||--|| Nid : "nid"
    FicheObservation ||--|| EtatCorrection : "etat"
    FicheObservation ||--o{ Observation : "observations"
    FicheObservation }o--|| Espece : "espece"
    Espece }o--|| Famille : "famille"
    Famille }o--|| Ordre : "ordre"
    FicheObservation ||--o{ HistoriqueModification : "modifications"
    Localisation }o--|| CommuneFrance : "commune"
```

### Indexation

| Table | Index | Colonnes |
|-------|-------|----------|
| `FicheObservation` | PK | `num_fiche` |
| `Localisation` | Index | `code_insee` |
| `CommuneFrance` | Index | `nom`, `code_departement` |
| `Espece` | Unique | `nom` |
| `HistoriqueModification` | Index | `categorie` |

---

## ⚡ Performance

### Optimisations

| Technique | Implémentation |
|-----------|----------------|
| **Cache** | Redis pour sessions et résultats Celery |
| **Indexation** | Index sur champs fréquemment filtrés |
| **Pagination** | Listes paginées (20-50 éléments) |
| **Lazy loading** | `select_related()` et `prefetch_related()` |
| **Async** | Tâches longues via Celery |

### Limitations Redis

- Résultats Celery limités à 150-200 entrées
- TTL sur les résultats de tâches

---

## 🔧 Configuration

### Environnements

| Environnement | Fichier | Caractéristiques |
|---------------|---------|------------------|
| **Développement** | `settings_local.py` | DEBUG=True, SQLite/MySQL local |
| **Production** | `settings.py` + `.env` | DEBUG=False, MariaDB, HTTPS |
| **Docker** | `docker-compose.yml` | Services conteneurisés |

### Variables Clés

```bash
# Django
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=example.com

# Base de données
DB_NAME=observations_db
DB_USER=obs_user
DB_PASSWORD=***
DB_HOST=db
DB_PORT=3306

# Redis / Celery
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# OCR
GEMINI_API_KEY=AIza...
```

---

## 📈 Monitoring

### Outils Disponibles

| Outil | URL | Rôle |
|-------|-----|------|
| **Flower** | `:5555` | Monitoring Celery |
| **phpMyAdmin** | `:8081` | Administration BDD |
| **Django Admin** | `/admin/` | Administration Django |

### Logs

| Service | Emplacement |
|---------|-------------|
| Django | `logs/django.log` |
| Celery | `logs/celery.log` |
| Nginx | Container stdout |

---

## 🔗 Voir Aussi

- [README](../README.md) - Présentation du projet
- [Applications](../applications/) - Documentation détaillée
- [Plan Directeur](../projet/docs_todo.md) - État de la documentation
