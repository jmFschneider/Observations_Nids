# Architecture du Système de Transcription avec Gemini

> Documentation technique complète du module de transcription OCR par IA
> Générée le : 2025-12-20
> Module : `pilot` (Application Django)

---

## Table des matières

[TOC]

---

## Vue d'ensemble

Le système de transcription des images JPG avec Gemini est implémenté dans l'application Django **"pilot"** (destinée à rester en développement/test). Il utilise une architecture **Redis + Celery** pour traiter les transcriptions en tâches asynchrones parallélisables. Le flux complet va de l'upload/sélection des répertoires d'images jusqu'à l'affichage des résultats OCR.

### Technologies utilisées

- **Django** : Framework web et gestion des données
- **Gemini API** : Reconnaissance OCR via IA multimodale
- **Celery** : Traitement asynchrone des tâches
- **Redis** : Broker de messages et stockage des résultats
- **PIL (Pillow)** : Manipulation d'images
- **PostgreSQL** : Base de données

---

## 1. Processus de préparation des images

### 1.1 Localisation et structure des images

Les images sont organisées dans une arborescence prévisible :

**Répertoire racine** : `MEDIA_ROOT/` (défini dans `settings.py` via `config.py`)

**Structure typique** :
```
media/
├── Ancienne_fiche/
│   ├── Sans_traitement/        (images brutes)
│   ├── Traitement_1/           (images optimisées)
│   └── Traitement_2/
└── Nouvelle_fiche/
    ├── Sans_traitement/
    └── Traitement_1/
```

**Fichiers impliqués** :
- `pilot/views.py:42-119` : Navigation dans les répertoires
- `observations_nids/config.py:70` : Définition de `MEDIA_ROOT`

### 1.2 Traitements appliqués aux images

**Détection du type d'image** (défini dans `pilot/tasks.py:69-83`) :
- **Images "brutes"** : Détectées si le chemin contient `Sans_traitement`
- **Images "optimisées"** : Tous les autres traitements (Traitement_1, Traitement_2, etc.)

**Traitements appliqués lors du traitement** :
- **Redimensionnement** : Non appliqué actuellement, les images sont utilisées telles quelles
- **Conversion de format** : Les images JPG/JPEG sont chargées directement via PIL
- **Encodage** : Les images sont passées directement au modèle Gemini (pas de conversion Base64 visible)

**Code de préparation** (`pilot/tasks.py:507-511`) :
```python
# Traitement de l'image avec le modèle OCR
image = Image.open(img_path_complet)  # Ouverture PIL simple
response = model.generate_content([prompt, image])  # Envoi direct au modèle
text_response = response.text.encode('utf-8').decode('utf-8')
```

**Remarque** : La préparation est **minimale** - seule l'ouverture via PIL est effectuée, sans transformation.

---

## 2. Chargement et utilisation du prompt

### 2.1 Localisation des prompts

Deux fichiers de prompts existent :

1. **Prompt générique (défaut)** :
   - `observations/json_rep/prompt_gemini_transcription.txt`
   - **Usage** : Fiches standard

2. **Prompt spécialisé (archives)** :
   - `observations/json_rep/prompt_gemini_transcription_Ancienne_Fiche.txt`
   - **Usage** : Fiches anciennes (années 70/80)

### 2.2 Chargement du prompt

**Code de chargement** (`pilot/tasks.py:382-391`) :
```python
prompt_path = os.path.join(
    settings.BASE_DIR, 'observations', 'json_rep', 'prompt_gemini_transcription.txt'
)
try:
    with open(prompt_path, encoding='utf-8') as f:
        prompt = f.read()
except Exception as e:
    logger.error(f"Erreur lors du chargement du prompt: {str(e)}")
    return {'status': 'ERROR', 'error': f"Erreur lors du chargement du prompt: {str(e)}"}
```

**Limitations actuelles** :
- Un seul prompt est chargé pour toutes les images d'une exécution batch
- Le choix du prompt n'est **pas automatisé** en fonction du type de fiche
- **À améliorer** : Détecter le type de fiche depuis le chemin et charger le prompt correspondant

### 2.3 Contenu des prompts

#### Prompt générique (observations/json_rep/prompt_gemini_transcription.txt)

Demande à Gemini de transformer l'image manuscrite en JSON structuré avec :
- `informations_generales` (n_fiche, observateur, espece, annee)
- `nid` (hauteur, couvert, etc.)
- `localisation` (commune, altitude, paysage)
- `tableau_donnees` (tableau des observations jour/mois/oeufs/poussins)
- `tableau_donnees_2` (résumé: 1er oeuf, éclosions, poussins volants)
- `causes_echec` (raisons d'échec si applicable)
- `remarque` (notes libres)

#### Prompt Ancienne Fiche (observations/json_rep/prompt_gemini_transcription_Ancienne_Fiche.txt)

Ajuste le guide pour les spécificités des fiches anciennes :
- Année écrite verticalement en marge droite
- Champs "Échec" avec cases à cocher (vs dates)
- Tableau visible au verso uniquement
- Normalisation des années (77 → 1977)

### 2.4 Utilisation du prompt dans l'appel API

**Code** (`pilot/tasks.py:510`) :
```python
response = model.generate_content([prompt, image])
```

Le prompt est passé en premier argument (texte), suivi de l'image PIL. Gemini traite les deux dans le contexte du modèle multimodal.

---

## 3. Appel à l'API Gemini

### 3.1 Configuration de l'API

**Initialisation** (`pilot/tasks.py:375-380`) :
```python
api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
if not api_key:
    logger.error("Clé API Gemini non configurée")
    return {'status': 'ERROR', 'error': "Clé API Gemini non configurée"}

genai.configure(api_key=api_key)
```

**Source de la clé API** :
- Priorité 1 : `settings.GEMINI_API_KEY` (de `config.py` → `.env`)
- Priorité 2 : Variable d'environnement `GEMINI_API_KEY`

### 3.2 Mapping des modèles

**Code** (`pilot/tasks.py:361-367`) :
```python
modeles_mapping = {
    'gemini_flash': 'gemini-1.5-flash',
    'gemini_1.5_pro': 'gemini-1.5-pro',
    'gemini_2_pro': 'gemini-2.0-pro',
    'gemini_2_flash': 'gemini-2.0-flash',
}
```

Les noms simplifiés du formulaire sont mappés vers les identifiants API officiels de Google.

### 3.3 Appel à Gemini

**Initialisation du modèle** (`pilot/tasks.py:437-438`) :
```python
model = genai.GenerativeModel(modele_api)
```

**Appel** (`pilot/tasks.py:510`) :
```python
response = model.generate_content([prompt, image])
```

**Paramètres implicites** :
- **Modèle** : Celui sélectionné (gemini-2.0-flash par défaut)
- **Température** : Non spécifiée (valeur par défaut Gemini)
- **Tokens max** : Non spécifiée (valeur par défaut)
- **Top-p, top-k** : Non spécifiés

### 3.4 Traitement de la réponse

**Étapes** (`pilot/tasks.py:511-525`) :
```python
text_response = response.text.encode('utf-8').decode('utf-8')

# Nettoyage des marqueurs markdown
if text_response.startswith("```json"):
    text_response = text_response[7:].strip()
    if text_response.endswith("```"):
        text_response = text_response[:-3].strip()

# Parsing JSON
try:
    json_data = json.loads(text_response)
    logger.debug(f"JSON correctement parsé pour {img_file}")
except json.JSONDecodeError as e:
    logger.error(f"Erreur de décodage JSON pour {img_file}: {str(e)}")
    raise ValueError(f"Réponse non JSON: {text_response[:100]}...") from e
```

**Nettoyage** :
1. Suppression des blocs markdown ` ```json ... ``` `
2. Décodage UTF-8 complet

---

## 4. Architecture Redis et Celery

### 4.1 Configuration Redis

**Broker URL** (`observations_nids/config.py:30` et `observations_nids/settings.py:69`) :
```python
broker_url: str = "redis://127.0.0.1:6379/0"
result_backend: str = "redis://127.0.0.1:6379/0"
```

**Configuration** :
- **Host** : `127.0.0.1` (localhost)
- **Port** : `6379` (défaut Redis)
- **Database** : `0` (première base de données Redis)
- **Utilisation double** : Broker (file des tâches) ET backend de résultats

**Démarrage** (`Start-DevStack.ps1:78-102`) :
```powershell
# Redis est démarré en premier
if ($redisRunning) {
    Write-Host "[1/4] Redis déjà démarré (PID: $($redisRunning.Id))."
} else {
    Write-Host "[1/4] Démarrage Redis..."
    Start-Process -FilePath $RedisExe -WorkingDirectory (Split-Path $RedisExe) | Out-Null
    Wait-PortReady -TargetHost "127.0.0.1" -Port 6379 -TimeoutSec 20 | Out-Null
}
```

### 4.2 Configuration Celery

**Configuration de base** (`observations_nids/celery.py:18-37`) :
```python
app.conf.update(
    broker_url=settings.celery.broker_url,                    # Redis URL
    result_backend=settings.celery.result_backend,            # Redis URL
    task_serializer=settings.celery.task_serializer,          # 'json'
    accept_content=settings.celery.accept_content,            # ['json']
    result_serializer=settings.celery.result_serializer,      # 'json'
    timezone=settings.celery.timezone,                        # 'Europe/Paris'
    task_track_started=settings.celery.task_track_started,    # True
    task_time_limit=settings.celery.task_time_limit,          # 30 * 60 = 1800s
    worker_hijack_root_logger=False,
    # Améliorations robustesse
    task_acks_late=True,                                      # Acquittement tardif
    task_default_retry_delay=30,                              # Retry après 30s
)
```

**Paramètres clés** :
- **task_serializer** : JSON pour compatibilité
- **task_track_started** : Permet le suivi de la progression
- **task_time_limit** : 30 minutes maximum par tâche
- **task_acks_late** : Acquittement après completion (plus sûr)

**Démarrage du worker** (`Start-DevStack.ps1:109`) :
```powershell
Start-Window -Title "Nids: Celery worker" -Command "celery -A $CeleryApp worker --loglevel=info --pool=eventlet"
```

Note : Pool `eventlet` pour Windows

### 4.3 Tâches Celery définies

#### Tâche principale : `process_batch_transcription_task`

**Signature** (`pilot/tasks.py:339-340`) :
```python
@shared_task(bind=True, name='pilot.process_batch_transcription')
def process_batch_transcription_task(self, directories: list[dict], modeles_ocr: list[str], importer_en_base: bool = False):
```

**Paramètres** :
- `directories` : Liste de dictionnaires `{'path': str, 'name': str}`
- `modeles_ocr` : Liste des noms de modèles à utiliser
- `importer_en_base` : Bool, si True importe les fiches en base de données

**Fonctionnalités** :
- Traite chaque répertoire avec chaque modèle (boucles imbriquées)
- Mise à jour de la progression via `self.update_state()`
- Création des fichiers JSON résultats
- Création d'entrées `TranscriptionOCR` en base
- Importation optionnelle de `FicheObservation` complètes

**Progression rapportée** (`pilot/tasks.py:495-505`) :
```python
self.update_state(
    state='PROGRESS',
    meta={
        'processed': processed_count,
        'total': total_images,
        'current_file': img_file,
        'current_directory': dir_path_relatif,
        'current_model': modele_ocr,
        'percent': int((processed_count / total_images) * 100),
    },
)
```

### 4.4 Déclenchement des tâches

**Code de déclenchement** (`pilot/views.py:281-282`) :
```python
task = process_batch_transcription_task.delay(directories, modeles_ocr, importer_en_base)
task_id = task.id
```

Utilisé dans la vue `lancer_transcription_batch` après réception du formulaire POST.

### 4.5 Suivi et récupération des résultats

**Vérification de progression** (`pilot/views.py:309-371`) :
```python
def check_batch_progress(request):
    task_id = request.session.get('pilot_task_id')
    if not task_id:
        return JsonResponse({'status': 'NO_TASK'})

    result = AsyncResult(task_id)

    # États gérés : PENDING, STARTED/PROGRESS, SUCCESS, FAILURE
    if result.status == 'PROGRESS':
        info: dict = cast(dict, raw_info if isinstance(raw_info, dict) else {})
        # Extraction de la progression
        ...
    elif result.status == 'SUCCESS':
        # Récupération des résultats complets
        ...
```

**Stockage en session** (`pilot/views.py:353-357`) :
```python
if result.status == 'SUCCESS':
    raw_ok: Any = result.result
    ok: dict = cast(dict, raw_ok if isinstance(raw_ok, dict) else {})
    response.update(ok)

    request.session['pilot_batch_results'] = ok
    response['redirect'] = '/pilot/optimisation-ocr/resultats/'
```

Les résultats complets sont stockés en session Django pour affichage dans `batch_results.html`.

---

## 5. Flux complet de bout en bout

### 5.1 Étape 1 : Accueil et navigation

**Vue** : `optimisation_ocr_home` → **Template** : `optimisation_ocr_home.html`

Affiche la page d'accueil du module pilot avec explications.

### 5.2 Étape 2 : Sélection des répertoires

**Vue** : `selection_repertoire_ocr` → **Template** : `selection_repertoire_ocr.html`

**Flux** :
1. Affichage des répertoires disponibles sous `MEDIA_ROOT`
2. Détection automatique du type de fiche et de traitement depuis le chemin
3. Comptage des images dans chaque répertoire
4. **Sélection multiple** par l'utilisateur (checkbox JavaScript)
5. Les sélections sont stockées dans `sessionStorage['selectedDirectories']`

**Données affichées** :
- Fil d'Ariane (navigation)
- Type de fiche détecté (ex: "Ancienne_fiche")
- Type de traitement (ex: "Traitement_1")
- Nombre d'images

### 5.3 Étape 3 : Configuration du traitement batch

**Vue** : Redirection depuis selection après sélection → **Template** : `optimisation_ocr_home.html`

**Formulaire avec** :
1. **Sélection des modèles OCR** (checkboxes multiples)
   - Gemini Flash
   - Gemini 1.5 Pro
   - Gemini 2.0 Pro
   - Gemini 2.0 Flash (défaut coché)

2. **Options** :
   - Importer les fiches en base (checkbox)
   - Analyser les correspondances avant lancement

3. **Bouton de lancement** : POST vers `lancer_transcription_batch`

### 5.4 Étape 4 : Déclenchement du traitement batch

**Vue** : `lancer_transcription_batch` (POST)

**Processus** :
1. Récupération des paramètres (directories JSON, modeles_ocr JSON, importer_en_base bool)
2. Validation des paramètres
3. **Création de la tâche Celery** : `process_batch_transcription_task.delay(...)`
4. Stockage du task_id en session
5. Réponse JSON avec `task_id` et URL de suivi

**Réponse** (exemple) :
```json
{
  "success": true,
  "task_id": "abc123def456...",
  "message": "Traitement batch démarré",
  "progress_url": "/pilot/optimisation-ocr/verifier-progression/"
}
```

### 5.5 Étape 5 : Suivi de la progression (AJAX polling)

**Vue** : `check_batch_progress` (GET, appelée via AJAX)

**Template** : `batch_results.html` avec JavaScript de polling

**Polling** (`batch_results.html:214`) :
```javascript
let progressCheckInterval = setInterval(checkProgress, 2000);  // Toutes les 2 secondes
```

**Informations rapportées** :
- Pourcentage de progression (0-100%)
- Nombre de fichiers traités / total
- Fichier en cours
- Répertoire en cours
- Modèle en cours d'utilisation
- Message de statut

**États gérés** :
- **PENDING** : En attente, 0%
- **PROGRESS** : En cours, % mis à jour
- **SUCCESS** : Terminé, redirection automatique
- **FAILURE** : Erreur, affichage du message d'erreur

### 5.6 Étape 6 : Traitement par Celery (worker)

**Code** : `pilot/tasks.py` - Fonction `process_batch_transcription_task`

**Boucles imbriquées** :
```
Pour chaque modèle OCR sélectionné :
    Initialiser le modèle Gemini
    Pour chaque répertoire sélectionné :
        Créer le répertoire de résultats
        Pour chaque image JPG du répertoire :
            1. Ouvrir l'image (PIL)
            2. Appeler Gemini avec [prompt, image]
            3. Nettoyer la réponse (supprimer markdown)
            4. Parser le JSON
            5. Valider/corriger la structure JSON
            6. Sauvegarder le JSON
            7. Créer entry TranscriptionOCR en base
            8. Optionnellement importer FicheObservation
            9. Mettre à jour la progression
```

**Durée moyenne** : 2-5 secondes par image (selon le modèle)

### 5.7 Étape 7 : Validation et correction JSON

**Validation** (`observations/json_rep/json_sanitizer.py:4-64`) :
```python
def validate_json_structure(data):
    # Vérifie la présence de toutes les clés requises
    # Retourne une liste d'erreurs (vide si conforme)
```

**Correction automatique** (`json_sanitizer.py:67-172`) :
```python
def corriger_json(data):
    # Renomme les clés incohérentes
    # Homogénéise les structures
    # Complète les champs manquants
```

**Exemples de corrections** :
- `"tableau_resume"` → `"tableau_donnees_2"`
- `"espèce"` → `"espece"`
- `"haut. nid"` → `"haut_nid"`
- Assurance que tous les sous-objets de `tableau_donnees_2` existent

### 5.8 Étape 8 : Sauvegarde des résultats

**Fichiers créés** (dans `media/transcription_results/`) :
1. **JSON final** : `{image_name}_result.json`
2. **JSON brut** (si correction nécessaire) : `{image_name}_raw.json`

**Chemin complet** :
```
media/transcription_results/{repertoire}/{type_fiche}/{type_traitement}/{modele_ocr}/{image_name}_result.json
```

**Exemple** :
```
media/transcription_results/Ancienne_fiche/Sans_traitement/gemini_2_flash/fiche_001_result.json
```

### 5.9 Étape 9 : Création des entrées en base de données

#### TranscriptionOCR (`pilot/models.py`)

**Créée automatiquement** pour chaque image réussie :
- `fiche` : Lien vers FicheObservation (peut être None)
- `chemin_json` : Chemin vers le JSON résultat
- `chemin_image` : Chemin vers l'image source
- `type_image` : 'brute' ou 'optimisee'
- `modele_ocr` : Nom du modèle utilisé
- `temps_traitement_secondes` : Durée du traitement
- `statut_evaluation` : 'non_evaluee' (par défaut)

#### FicheObservation (optionnel, si `importer_en_base=True`)

**Importée optionnellement** via `_importer_fiche_depuis_json()` (`pilot/tasks.py:113-336`)

Crée une fiche complète avec :
- Localisation (communes, coordonnées, altitude)
- Nid (hauteur, couvert)
- Observations (tableau des visites)
- Résumé (premier oeuf, éclosions, etc.)

### 5.10 Étape 10 : Affichage des résultats

**Vue** : `batch_results` → **Template** : `batch_results.html`

**Informations affichées** :

1. **Statistiques globales** (cartes colorées)
   - Total d'images traitées
   - Nombre de succès
   - Nombre d'erreurs
   - Taux de succès (%)

2. **Informations de configuration**
   - Modèles OCR utilisés
   - Nombre de répertoires
   - Durée totale
   - Durée moyenne par image

3. **Résultats détaillés par répertoire**
   - Tableau avec : Fichier | Statut | Durée | Fiche liée | Actions
   - Liens directs vers :
     - Fichier JSON (`/media/...`)
     - Admin Django (si fiche liée)
     - Entrée TranscriptionOCR

**Actions disponibles** :
- Retour à la sélection de répertoires
- Voir toutes les transcriptions (admin Django)

---

## 6. Interactions entre les composants

### 6.1 Flux de requêtes HTTP

```
[Navigateur]
    ↓
[Django]
    ├─→ selection_repertoire_ocr (GET)
    │   └─→ Affiche template + liste répertoires
    ├─→ lancer_transcription_batch (POST)
    │   └─→ Crée tâche Celery
    │       └─→ Retourne task_id
    ├─→ check_batch_progress (GET AJAX polling)
    │   ├─→ Récupère AsyncResult(task_id)
    │   └─→ Retourne JSON progression
    └─→ batch_results (GET)
        └─→ Affiche résultats stockés en session

[Celery Worker] (asynchrone)
    ↓
[process_batch_transcription_task]
    ├─→ Boucle répertoires × modèles
    │   ├─→ Pour chaque image :
    │   │   ├─→ Appel Gemini API
    │   │   ├─→ Validation/Correction JSON
    │   │   ├─→ Sauvegarde JSON
    │   │   ├─→ Création TranscriptionOCR
    │   │   ├─→ Update_state PROGRESS
    │   │   └─→ Optionnel : Importation FicheObservation
    └─→ Retourne résultats finaux

[Redis]
    ├─→ Queue des tâches Celery
    └─→ Stockage des résultats AsyncResult
```

### 6.2 Stockage des données en session

**Données de session** (`pilot/views.py:285-292`) :
```python
request.session['pilot_task_id'] = task_id
request.session['pilot_batch_config'] = {
    'directories': directories,
    'modeles_ocr': modeles_ocr,
    'importer_en_base': importer_en_base,
    'start_time': timezone.now().isoformat(),
}
```

**Durée de session** : 3600 secondes (1 heure) via `SESSION_COOKIE_AGE` dans settings.py

### 6.3 Communication JavaScript ↔ Serveur

**Sélection répertoires** (`selection_repertoire_ocr.html`) :
- Stockage local : `sessionStorage['selectedDirectories']` (JSON)
- Récupération côté serveur : POST FormData

**Suivi progression** (`batch_results.html`) :
- Polling AJAX toutes les 2 secondes
- Endpoint : `/pilot/optimisation-ocr/verifier-progression/`
- Réponse : JSON avec état, progression, infos actuelles

**Redirection automatique** (`batch_results.html:247-253`) :
```javascript
if (data.status === 'SUCCESS' || data.force_redirect) {
    clearInterval(progressCheckInterval);
    if (data.redirect) {
        window.location.href = data.redirect;
    }
}
```

---

## 7. Models de données clés

### 7.1 Model TranscriptionOCR

**Fichier** : `pilot/models.py`

**Champs** :
```python
fiche = ForeignKey(FicheObservation)  # Peut être None
chemin_json = CharField(max_length=255)
chemin_image = CharField(max_length=255)
type_image = CharField(choices=[('brute', ...), ('optimisee', ...)])
modele_ocr = CharField(choices=[('gemini_flash', ...), ...])
date_transcription = DateTimeField(auto_now_add=True)
statut_evaluation = CharField(choices=[...])
score_global = FloatField(null=True)
temps_traitement_secondes = FloatField()
# + nombreux champs pour évaluation manuelle de qualité
```

**Indices** :
- `fiche` + `modele_ocr`
- `statut_evaluation`
- `score_global`

### 7.2 Model FicheObservation

**Fichier** : `observations/models.py`

**Champs clés** :
```python
num_fiche = AutoField(primary_key=True)
observateur = ForeignKey(Utilisateur)
espece = ForeignKey(Espece)
annee = IntegerField()
chemin_image = CharField(max_length=255, blank=True)
chemin_json = CharField(max_length=255, blank=True)
transcription = BooleanField(default=False)
```

**Objets liés créés automatiquement** :
- `Localisation` (géocodage, coordonnées)
- `Nid` (hauteur, couvert, détails)
- `Observation` (tableau des visites)
- `ResumeObservation` (résumé statistiques)
- `CausesEchec` (causes d'échec)
- `EtatCorrection` (état de la correction manuelle)

---

## 8. Sécurité et gestion des erreurs

### 8.1 Gestion des erreurs dans les tâches

**Catch-all global** (`pilot/tasks.py:611-619`) :
```python
except Exception as e:
    logger.error(f"Erreur lors du traitement de {img_file}: {str(e)}")
    file_result = {
        'filename': img_file,
        'status': 'error',
        'error': str(e),
        'duration': round(time.time() - file_start, 2),
    }
    total_errors += 1
```

Les erreurs par image n'arrêtent pas le batch, elles sont comptabilisées et signalées.

### 8.2 Validation et normalisation

**Sécurité des chemins** (`pilot/views.py:48-54`) :
```python
safe_path = os.path.normpath(current_path).replace('..', '')
full_current_path = os.path.join(base_dir, safe_path)

if not full_current_path.startswith(base_dir):
    safe_path = ''
    full_current_path = base_dir
```

Prévention de directory traversal attacks.

### 8.3 Gestion des API credentials

**Récupération sécurisée** (`pilot/tasks.py:375-378`) :
```python
api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
if not api_key:
    logger.error("Clé API Gemini non configurée")
    return {'status': 'ERROR', ...}
```

La clé vient de variables d'environnement (`.env`), jamais hardcodée.

---

## 9. Limitations et points d'amélioration

### 9.1 Limitations actuelles

1. **Prompt non-adaptatif** : Un seul prompt pour tous les types de fiches, même si deux prompts existent
2. **Pas de redimensionnement d'images** : Les images très grandes pourraient être coûteuses en tokens
3. **Pas de retry sur erreurs API** : Une erreur Gemini arrête le traitement de l'image
4. **Stockage session limité** : Durée limitée à 1 heure, pas persistent après logout
5. **Pas de pagination** : Tous les résultats sont chargés en mémoire (problème pour >10k images)
6. **Pas de filtrage par modèle en résultats** : Tous les résultats mélangés

### 9.2 Améliorations possibles

#### 1. Détection auto du type de fiche et chargement du bon prompt

```python
# Dans pilot/tasks.py, ligne ~382
if 'Ancienne_fiche' in dir_path_relatif or 'Ancienne_Fiche' in dir_path_relatif:
    prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'
else:
    prompt_filename = 'prompt_gemini_transcription.txt'

prompt_path = os.path.join(
    settings.BASE_DIR, 'observations', 'json_rep', prompt_filename
)
```

#### 2. Redimensionnement adaptatif des images

```python
# Dans pilot/tasks.py, après ligne 507
image = Image.open(img_path_complet)

# Redimensionner si trop grande (optimisation coût tokens)
MAX_DIMENSION = 2000
if max(image.size) > MAX_DIMENSION:
    ratio = MAX_DIMENSION / max(image.size)
    new_size = tuple(int(dim * ratio) for dim in image.size)
    image = image.resize(new_size, Image.Resampling.LANCZOS)
    logger.info(f"Image redimensionnée de {image.size} à {new_size}")
```

#### 3. Retry avec exponential backoff

```python
# Modifier la déclaration de la tâche dans pilot/tasks.py:339
@shared_task(bind=True, name='pilot.process_batch_transcription', max_retries=3)
def process_batch_transcription_task(self, ...):
    ...
    try:
        response = model.generate_content([prompt, image])
    except Exception as exc:
        # Retry avec délai exponentiel : 2^n secondes
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### 4. Stockage des résultats en base au lieu de session

```python
# Créer un nouveau model BatchTranscription dans pilot/models.py
class BatchTranscription(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    config = models.JSONField()  # directories, modeles, options
    results = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 5. Paramètres Gemini configurables

```python
# Ajouter dans le formulaire et passer à la tâche
generation_config = {
    "temperature": 0.2,  # Faible pour plus de cohérence
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

response = model.generate_content(
    [prompt, image],
    generation_config=generation_config
)
```

---

## 10. Fichiers clés récapitulatifs

| Fichier | Rôle | Lignes clés |
|---------|------|-------------|
| `pilot/views.py` | Orchestration HTTP | 236-282 (lancer batch)<br>309-371 (progression) |
| `pilot/tasks.py` | Traitement Celery | 339-663 (tâche principale)<br>113-336 (import fiches) |
| `pilot/models.py` | Model TranscriptionOCR | 14-206 |
| `pilot/urls.py` | Routes pilot | Toutes les routes |
| `pilot/templates/optimisation_ocr_home.html` | Page accueil | Interface configuration |
| `pilot/templates/selection_repertoire_ocr.html` | Sélection répertoires | Navigation + sélection |
| `pilot/templates/batch_results.html` | Affichage résultats | Stats + tableau résultats |
| `observations/json_rep/json_sanitizer.py` | Validation/correction JSON | 4-64 (validation)<br>67-172 (correction) |
| `observations/json_rep/prompt_gemini_transcription.txt` | Prompt standard | Contenu complet |
| `observations/json_rep/prompt_gemini_transcription_Ancienne_Fiche.txt` | Prompt fiches anciennes | Contenu complet |
| `observations_nids/celery.py` | Config Celery | 18-37 (configuration) |
| `observations_nids/config.py` | Config globale | 29-42 (Celery)<br>70-71 (paths) |
| `observations_nids/settings.py` | Django settings | 69 (CELERY_BROKER_URL) |
| `Start-DevStack.ps1` | Script démarrage | Orchestration Redis/Django/Celery/Flower |

---

## Conclusion

Le système de transcription Gemini est une **architecture modulaire et scalable** reposant sur :

- **Gemini API** pour la reconnaissance OCR via IA multimodale
- **Celery + Redis** pour le traitement asynchrone batch parallélisable
- **Django** pour l'interface web et la gestion des données
- **JSON structuré** pour la représentation des fiches

### Points forts

✅ **Robustesse** : Gestion d'erreurs par image, le batch continue même en cas d'échec
✅ **Suivi temps réel** : Progression mise à jour toutes les 2 secondes
✅ **Validation automatique** : Correction des JSON malformés ou incohérents
✅ **Flexibilité** : Support de 4 modèles Gemini différents
✅ **Scalabilité** : Architecture asynchrone permettant de traiter des milliers d'images

### Prochaines améliorations prioritaires

1. **Détection automatique du type de fiche** → Chargement du bon prompt
2. **Retry sur erreurs API** → Meilleure résilience
3. **Redimensionnement d'images** → Optimisation coûts
4. **Paramètres Gemini configurables** → Meilleure qualité de transcription

---

**Dernière mise à jour** : 2025-12-20
**Mainteneur** : Équipe Observations Nids
**Contact** : [À compléter]
