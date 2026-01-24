# CLAUDE.md - Référence Projet observations_nids

> Document de référence pour accélérer les futures interventions sur ce projet.

---

## Identité du Projet

**Nom** : Observations Nids
**But** : Application web de gestion des fiches d'observation de nidification d'oiseaux pour le GONM (Groupe Ornithologique Normand)
**Fonctionnalités clés** :
- Saisie manuelle de fiches d'observation
- Transcription OCR de fiches papier via Google Gemini
- Workflow de validation/correction des fiches
- Gestion des espèces (taxonomie GONM)
- Gestion des communes françaises

---

## Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | Django | 6.0 |
| Python | | 3.11+ |
| Base de données | MariaDB | 10.11 |
| Cache/Broker | Redis | 7 |
| Tâches async | Celery | 5.6 |
| OCR | Google Gemini API | |
| Serveur prod | Gunicorn + Nginx | |
| Conteneurisation | Docker Compose | |

---

## Structure du Projet

```
observations_nids/
├── observations/          # App principale - fiches d'observation
├── accounts/              # Utilisateurs et authentification
├── taxonomy/              # Espèces et codes GONM
├── geo/                   # Communes et géolocalisation
├── review/                # Workflow de validation
├── audit/                 # Historique des modifications
├── ingest/                # Import JSON des transcriptions
├── ocr/                   # Pipeline OCR Gemini
├── core/                  # Utilitaires partagés
├── observations_nids/     # Configuration Django (settings, urls, celery)
├── templates/             # Templates de base
├── docker/                # Configuration Docker Compose
├── docs/                  # Documentation MkDocs
└── scripts/               # Scripts utilitaires
```

---

## Applications Django - Résumé

### observations (App Principale)
- **Modèles** : `FicheObservation`, `Observation`, `Nid`, `ImageSource`
- **Vues clés** : `views_home.py`, `views_observation.py`, `saisie_observation_view.py`
- **Templates** : `home.html`, `fiche_observation.html`, `saisie/saisie_observation.html`
- **JS important** : `saisie_observation.js` (formulaire dynamique)
- **Fonctionnalité spéciale** : Notation d'incertitude "5?" pour les comptages

#### Gestion de l'Incertitude
Les observateurs peuvent marquer un comptage comme incertain en ajoutant "?" (ex: `5?`)
- **Champs** : `nombre_oeufs_incertain`, `nombre_poussins_incertain` (BooleanField)
- **Format** : Le nombre et le flag sont stockés séparément en BDD
- **Saisie** : `ObservationForm` utilise un `CharField` qui parse "5?" → nombre=5, flag=True
- **Affichage** : Icône jaune "?" affichée dynamiquement par JavaScript
- **Migration** : `0016_add_incertitude_fields.py`

### accounts
- **Modèle** : `Utilisateur` (extension de AbstractUser)
- **Rôles** : Observateur, Reviewer, Administrateur
- **Workflow** : Inscription publique → Validation admin → Compte actif

### taxonomy
- **Modèle** : `Espece` avec `code_gonm` (identifiant GONM unique)
- **Source** : TAXREF + codes GONM personnalisés
- **API** : Autocomplétion espèces

### geo
- **Modèles** : `CommuneFrance`, `Localisation`
- **Source** : INSEE + Nominatim pour géocodage
- **API** : Autocomplétion communes avec widget dédié

### ingest
- **Modèles** : `Importation`, `EspeceCandidate`, `ObservateurCandidat`
- **Rôle** : Importer les JSON issus de l'OCR vers les fiches
- **Workflow** : JSON → Validation candidats → Création fiche

### ocr
- **Modèle** : `TranscriptionOCR`
- **API** : Google Gemini (gemini-3-flash, gemini-2.5-pro)
- **Prompts** : `observations/json_rep/prompt_gemini_transcription*.txt`
- **Rate limit** : 60 req/min, timeout 120s, 3 retries

### audit
- **Modèle** : `HistoriqueModification`
- **Rôle** : Traçabilité complète des modifications

### review
- **Rôle** : Workflow de validation des fiches transcrites
- **Statuts** : Nouveau → En édition → En correction → Validé

---

## Fichiers de Configuration Clés

| Fichier | Rôle |
|---------|------|
| `observations_nids/settings.py` | Configuration Django principale |
| `observations_nids/config.py` | Variables d'environnement (Pydantic) |
| `observations_nids/celery.py` | Configuration Celery |
| `docker/.env` | Variables d'environnement Docker |
| `docker/docker-compose.yml` | Services Docker |

---

## Patterns et Conventions

### Nommage
- **Vues** : `views_*.py` ou répertoire `views/` avec modules séparés
- **Templates** : snake_case, organisés par app
- **URLs** : kebab-case dans les chemins, snake_case pour les noms
- **Modèles** : PascalCase, singulier français

### Architecture Vues
```python
# Pattern commun pour les vues
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

@login_required
def ma_vue(request, pk):
    obj = get_object_or_404(MonModele, pk=pk)
    return render(request, 'app/template.html', {'obj': obj})
```

### Tâches Celery
```python
# Pattern tâche async
from celery import shared_task

@shared_task(bind=True)
def ma_tache(self, param):
    # self.update_state() pour progression
    pass
```

### Formulaires Dynamiques (JS)
- Le formulaire de saisie utilise AJAX pour ajouter/supprimer des observations
- Widget d'autocomplétion personnalisé pour espèces et communes

---

## Points d'Entrée Importants

### URLs Racine (`observations_nids/urls.py`)
```python
urlpatterns = [
    path('', include('observations.urls')),
    path('accounts/', include('accounts.urls')),
    path('geo/', include('geo.urls')),
    path('taxonomy/', include('taxonomy.urls')),
    path('ingest/', include('ingest.urls')),
    path('ocr/', include('ocr.urls')),
    path('admin/', admin.site.urls),
]
```

### Vues Principales
| URL | Vue | Description |
|-----|-----|-------------|
| `/` | `home_view` | Tableau de bord |
| `/fiches/` | `liste_fiches` | Liste des fiches |
| `/fiche/<pk>/` | `fiche_observation` | Détail fiche |
| `/saisie/` | `saisie_observation` | Formulaire saisie |
| `/ocr/selection-repertoire/` | `selection_repertoire_ocr` | Lancer OCR |
| `/ingest/` | `accueil_ingest` | Import JSON |

---

## Base de Données

### Modèles Principaux (relations)
```
FicheObservation
├── Observation (1:N) ──→ Espece
├── Nid (1:1)
├── Localisation (1:1) ──→ CommuneFrance
├── ImageSource (1:N)
└── Utilisateur (observateur, createur)

TranscriptionOCR
└── FicheObservation (FK optionnelle)
```

### Champs Récurrents
- `date_creation`, `date_modification` : timestamps auto
- `createur` : FK vers Utilisateur
- `statut` : choix prédéfinis (nouveau, en_edition, valide...)

---

## Celery et Redis

### Queues
- **default** : tâches générales
- **ocr** : transcription Gemini (rate limited)

### Tâches Importantes
| Tâche | Fichier | Description |
|-------|---------|-------------|
| `process_ocr_batch` | `ocr/tasks.py` | Batch OCR Gemini |
| `importer_json_batch` | `ingest/tasks.py` | Import JSON en lot |

### Commandes
```bash
# Démarrer worker
celery -A observations_nids worker -l INFO

# Démarrer beat (tâches planifiées)
celery -A observations_nids beat -l INFO

# Monitoring Flower
celery -A observations_nids flower
```

---

## Docker

### Services
| Service | Port | Description |
|---------|------|-------------|
| nginx | 8010 | Reverse proxy |
| web | 8000 (interne) | Django/Gunicorn |
| celery_worker | - | Workers Celery |
| celery_beat | - | Scheduler |
| flower | 5555 | Monitoring |
| db | 3306 (interne) | MariaDB |
| redis | 6379 (interne) | Cache/Broker |
| phpmyadmin | 8081 | Admin BDD |

### Commandes Utiles
```bash
cd docker

# Démarrer
docker compose up -d

# Logs
docker compose logs -f web

# Shell Django
docker compose exec web python manage.py shell

# Migrations
docker compose exec web python manage.py migrate

# Collecter statiques
docker compose exec web python manage.py collectstatic --noinput
```

---

## Tests

```bash
# Tous les tests
python manage.py test

# Une application
python manage.py test observations

# Avec couverture
coverage run manage.py test && coverage report
```

### Fixtures
- `conftest.py` à la racine et dans chaque app
- Factories avec `factory_boy` (si utilisé)

---

## Documentation

### MkDocs
```bash
# Serveur dev (port 8001)
mkdocs serve -f docs/mkdocs.yml

# Build pour production
mkdocs build -f docs/mkdocs.yml
python manage.py collectstatic --noinput
```

### Structure docs/
```
docs/
├── README.md                    # Page d'accueil
├── mkdocs.yml                   # Configuration MkDocs
├── guides/
│   ├── architecture.md          # Architecture technique
│   ├── workflow_fiche.md        # Cycle de vie fiche
│   ├── permissions.md           # Rôles et droits
│   ├── ocr_gemini.md           # Pipeline OCR
│   └── utilisateur/
│       └── saisie_observation.md  # Guide utilisateur
├── applications/                # Doc par application
├── deploiement/                 # Guides déploiement
└── projet/                      # Suivi projet
```

---

## Variables d'Environnement Clés

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Django |
| `DEBUG` | Mode debug (False en prod) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Connexion MariaDB |
| `REDIS_HOST` | Hôte Redis |
| `GEMINI_API_KEY` | Clé API Google Gemini |
| `ENVIRONMENT` | development/pilote/production |
| `ALLOWED_HOSTS` | Hôtes autorisés (JSON) |
| `CSRF_TRUSTED_ORIGINS` | Origins CSRF (JSON) |

---

## Commandes de Gestion Utiles

```bash
# Charger les communes françaises
python manage.py charger_communes_france

# Charger les espèces TAXREF
python manage.py charger_taxref

# Importer les codes GONM
python manage.py import_codes_gonm

# Exporter/importer utilisateurs
python manage.py export_users
python manage.py import_users

# Corriger chemins médias
python manage.py corriger_chemins_media
```

---

## Points d'Attention

### Sécurité
- Ne jamais commiter `.env` ou clés API
- `CSRF_TRUSTED_ORIGINS` doit inclure le domaine exact
- Toujours utiliser `@login_required` sur les vues sensibles

### Performance
- OCR Gemini : rate limit 60 req/min, prévoir délais
- Images : compression JPEG recommandée avant upload
- Redis : surveiller la mémoire sur gros volumes

### Migrations
- Toujours créer une sauvegarde avant migration en prod
- Tester les migrations sur environnement pilote d'abord

---

## Environnements

| Env | URL | Description |
|-----|-----|-------------|
| Local | http://localhost:8000 | Développement |
| Docker local | http://localhost:8010 | Test Docker |
| Pilote | https://pilote.observation-nids.meteo-poelley50.fr | Pré-production |
| Production | (à définir) | Production |

---

## Contacts et Ressources

- **Organisation** : GONM (Groupe Ornithologique Normand)
- **Documentation** : `/static/docs/index.html` (en prod)
- **API Gemini** : https://ai.google.dev/

---

*Dernière mise à jour : Janvier 2026*
