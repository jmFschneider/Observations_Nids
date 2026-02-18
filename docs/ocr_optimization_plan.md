# Plan d'Optimisation — Application OCR

> **Généré le** : Février 2026  
> **Contexte** : Analyse complète du pipeline OCR réalisée en session Ask mode.  
> **Usage** : Référencer ce fichier dans chaque nouveau chat (`@docs/ocr_optimization_plan.md`) pour conserver le contexte. Un chat en mode Plan par axe.

---

## Vue d'ensemble du Pipeline OCR

```
Image (media/images/)
    ↓
[Vue] selection_images → lancer_ocr (POST)
    ↓
[Celery] process_images_production_task (ocr/tasks.py)
    ├── RateLimiter (60 RPM local)
    ├── _charger_prompt_production() → prompt selon répertoire "ancien" ou standard
    ├── call_gemini_api_with_timeout() → threading.Thread + retry x3 backoff
    ├── Nettoyage Markdown (```json)
    ├── json.loads()
    ├── validate_json_structure() → corriger_json() si erreurs
    ├── Sauvegarde JSON → media/transcription_results/[structure]/gemini_3_flash/
    └── TranscriptionOCR.objects.create(statut='succes'|'erreur')
    ↓
[Ingest] ImportationService.traiter_fichier_json()
    ├── TranscriptionBrute créée
    ├── EspeceCandidate (fuzzy match SequenceMatcher seuil 80%)
    ├── creer_ou_recuperer_utilisateur()
    ├── ImportationEnCours
    └── FicheObservation + objets liés (@transaction.atomic)
```

### Fichiers clés

| Fichier | Rôle |
|---------|------|
| `ocr/tasks.py` | Tâche Celery principale + RateLimiter + retry |
| `ocr/views.py` | 4 vues : home, selection_images, lancer_ocr, verifier_progression |
| `ocr/models.py` | `TranscriptionOCR` (métadonnées + statut) |
| `ocr/urls.py` | 4 routes OCR |
| `observations/json_rep/json_sanitizer.py` | `validate_json_structure()` + `corriger_json()` |
| `observations/json_rep/prompt_gemini_transcription.txt` | Prompt standard |
| `observations/json_rep/prompt_gemini_transcription_Ancienne_Fiche.txt` | Prompt anciennes fiches |
| `ingest/tasks.py` | `process_json_batch_task` |
| `ingest/views/importation.py` | Workflow import JSON → FicheObservation |

---

## AXE 1 — Correction des Bugs Bloquants

> **Priorité : CRITIQUE — À traiter en premier**  
> **Fichier principal** : `ocr/tasks.py`

### Bug 1.1 — `return` à l'intérieur de la boucle `for` (ligne ~256)

**Impact** : La tâche ne traite **que la première image** du batch. Toutes les transcriptions en lot sont cassées.

**Code actuel** (`ocr/tasks.py`, lignes 178-256) :
```python
for index, img_rel_path in enumerate(image_paths_relatifs):
    # ... traitement ...
    self.update_state(
        state='PROGRESS',
        meta={'processed': index + 1, 'total': total, 'percent': ...},
    )
    return {'status': 'SUCCESS', ...}  # ← BUG : dans la boucle !
```

**Correction** : Désindenter le `return` d'un niveau pour qu'il soit après la boucle.

```python
    for index, img_rel_path in enumerate(image_paths_relatifs):
        # ... traitement ...
        self.update_state(...)

return {'status': 'SUCCESS', 'total': total, 'success': success_count, 'errors': errors}
```

---

### Bug 1.2 — `update_state` écrase les logs de `_log_progress`

**Impact** : Les logs de progression affichés dans `_log_progress` (stockés dans `meta['logs']`) sont effacés à chaque itération par l'`update_state` final qui ne passe que `processed/total/percent`.

**Code actuel** :
```python
# Dans _log_progress : stocke les logs dans meta
task_self.update_state(state='PROGRESS', meta={..., 'logs': logs[-100:]})

# Dans la boucle : écrase meta sans les logs
self.update_state(
    state='PROGRESS',
    meta={'processed': index + 1, 'total': total, 'percent': ...}
    # ← 'logs' absent : effacement des logs !
)
```

**Correction** : Fusionner les deux `update_state`. Accumuler les logs dans une variable locale et les inclure dans chaque mise à jour.

**Approche recommandée** :
```python
# Variable locale, pas de lecture Redis
logs = []

def log_progress(message, level='info'):
    timestamp = timezone.now().strftime('%H:%M:%S')
    logs.append({'timestamp': timestamp, 'message': message, 'level': level})
    # logs[-100:] pour limiter
    self.update_state(
        state='PROGRESS',
        meta={
            'processed': index + 1,
            'total': total,
            'percent': int(((index + 1) / total) * 100),
            'logs': logs[-100:],
        }
    )
```

Supprimer la fonction `_log_progress` (lecture Redis coûteuse) et la fonction globale indépendante.

---

### Bug 1.3 — `corriger_json` non appelé si le JSON est structurellement valide

**Impact** : `corriger_json` normalise aussi des clés avec accents/espaces (ex: `"espèce"` → `"espece"`, `"IGN/50000"` → `"IGN_50000"`). Un JSON sans erreurs de structure peut avoir des clés non normalisées qui feront échouer l'import dans `ingest`.

**Code actuel** :
```python
if validate_json_structure(json_data):  # truthy = liste d'erreurs non vide
    json_data = corriger_json(json_data)
```

**Correction** : Toujours appeler `corriger_json` pour la normalisation, indépendamment des erreurs de structure.
```python
errors = validate_json_structure(json_data)
if errors:
    logger.warning(f"Structure JSON non conforme: {errors}")
json_data = corriger_json(json_data)  # Toujours normaliser
```

---

## AXE 2 — Robustesse et Fiabilité

> **Priorité : HAUTE**  
> **Fichiers** : `ocr/tasks.py`, `ocr/views.py`, `ingest/views/importation.py`

### 2.1 — Déduplication avant transcription

**Impact** : Une image déjà transcrite avec succès est re-transcrite (et re-facturée API) si soumise à nouveau.

**Correction** : Au début du traitement de chaque image dans la boucle :
```python
if TranscriptionOCR.objects.filter(chemin_image=img_rel_path, statut='succes').exists():
    log_progress(f"⏭️ {basename} déjà transcrit, ignoré", 'warning')
    ignored_count += 1
    continue
```
Retourner aussi `ignored_count` dans le résultat final.

---

### 2.2 — Timeout via `threading.Thread` non interruptible

**Impact** : Après un timeout, le thread API Gemini continue à tourner en arrière-plan (fuite de ressources). Le timeout ne libère pas la connexion réseau.

**Correction** : Utiliser `concurrent.futures.ThreadPoolExecutor` :
```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

def call_gemini_api_with_timeout(client, model_name, prompt, image_path, timeout=120):
    def api_call():
        image = Image.open(image_path)
        try:
            response = client.models.generate_content(
                model=model_name, contents=[prompt, image]
            )
            return response.text.encode('utf-8').decode('utf-8')
        finally:
            image.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(api_call)
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError:
            future.cancel()
            raise TimeoutError(f"API call exceeded {timeout}s timeout")
```

---

### 2.3 — Normalisation de chemin fragile dans `selection_images`

**Impact** : `current_path.replace('..', '')` ne protège pas contre `....` (devient `..` après remplacement).

**Code actuel** (`ocr/views.py`, ligne 37) :
```python
safe_path = os.path.normpath(current_path).replace('..', '').replace('\\', '/')
```

**Correction** : Utiliser `Path.resolve()` et vérifier strictement le préfixe :
```python
from pathlib import Path

base_dir = Path(settings.MEDIA_ROOT) / 'images'
requested = (base_dir / current_path).resolve()
if not str(requested).startswith(str(base_dir.resolve())):
    requested = base_dir
```

---

### 2.4 — Lien `TranscriptionOCR.fiche` jamais mis à jour

**Impact** : Le champ `TranscriptionOCR.fiche` (FK vers `FicheObservation`) reste `null` même après import réussi. Le lien entre la transcription OCR et la fiche créée est perdu.

**Correction** : Dans `ImportationService` (ou `ingest/tasks.py`), après création de la `FicheObservation`, mettre à jour le `TranscriptionOCR` correspondant via le `chemin_json` :
```python
from ocr.models import TranscriptionOCR

# Dans finaliser_importation, après création de la fiche :
json_path = importation.transcription.fichier_source
TranscriptionOCR.objects.filter(
    chemin_json__endswith=json_path,
    statut='succes'
).update(fiche=fiche_creee)
```

---

## AXE 3 — Rate Limiting Distribué

> **Priorité : MOYENNE** (devient critique si plusieurs workers parallèles)  
> **Fichiers** : `ocr/tasks.py`, `observations_nids/celery.py`

### 3.1 — `RateLimiter` non partagé entre workers

**Impact** : Chaque worker Celery a son propre `RateLimiter` en mémoire. Avec N workers, le rate effectif est N × 60 = dépassement du quota Gemini.

**Correction** : Rate limiter Redis-backed avec compteur atomique :
```python
import redis
from django.conf import settings

class RedisRateLimiter:
    """Rate limiter partagé entre tous les workers via Redis."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.key = 'ocr:rate_limiter:tokens'
        self.redis = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    
    def wait_if_needed(self):
        """Acquiert un token, attend si le quota est atteint."""
        while True:
            # Compteur sur fenêtre glissante de 60s
            pipe = self.redis.pipeline()
            now = time.time()
            window_start = now - 60
            pipe.zremrangebyscore(self.key, 0, window_start)
            pipe.zcard(self.key)
            _, count = pipe.execute()
            
            if count < self.rpm:
                self.redis.zadd(self.key, {str(now): now})
                self.redis.expire(self.key, 70)
                break
            
            time.sleep(1)
```

### 3.2 — Queue dédiée non déclarée sur la tâche

**Code actuel** :
```python
@shared_task(bind=True, name='ocr.process_images_production')
def process_images_production_task(self, ...):
```

**Correction** : Ajouter `queue='ocr'` :
```python
@shared_task(bind=True, name='ocr.process_images_production', queue='ocr')
def process_images_production_task(self, ...):
```
Et vérifier que le worker OCR est lancé avec `-Q ocr`.

---

## AXE 4 — Expérience Utilisateur et Observabilité

> **Priorité : MOYENNE**  
> **Fichiers** : `ocr/views.py`, `ocr/templates/`, JS dans les templates

### 4.1 — Logs de progression non retournés au frontend

**Impact** : `verifier_progression` ne retourne que `percent/processed/total`. Les logs riches stockés dans le meta Celery (`logs`) ne sont jamais affichés.

**Correction** dans `ocr/views.py` :
```python
if result.status == 'PROGRESS':
    info = cast(dict, result.info)
    response.update({
        'percent': info.get('percent', 0),
        'processed': info.get('processed', 0),
        'total': info.get('total', 0),
        'logs': info.get('logs', []),  # ← ajouter
    })
```
Et côté JS, afficher les logs dans une zone dédiée.

### 4.2 — Pas de vue historique OCR accessible depuis l'UI

**Manque** : Seul l'admin Django donne accès à `TranscriptionOCR`. Aucune vue utilisateur pour consulter l'historique des transcriptions, re-télécharger un JSON, ou voir les erreurs passées.

**Suggestion** : Ajouter une vue `historique_ocr` listant les `TranscriptionOCR` avec filtres statut/date + lien vers le JSON si disponible.

### 4.3 — Pas de page de résultats post-OCR

**Manque** : Après la fin du batch, l'UI affiche juste le pourcentage final. Pas de synthèse des fichiers traités/en erreur ni de liens directs vers les JSONs produits pour lancer l'import.

**Suggestion** : Page de résultats exploitant le `result.result` (qui contient `errors[]` et `success_count`), avec bouton "Importer ces JSONs" pointant vers `ingest`.

### 4.4 — Modèle Gemini non sélectionnable

**Manque** : `'gemini-3-flash-preview'` est hardcodé. Pour des fiches dégradées ou ambiguës, un utilisateur pourrait vouloir relancer avec `gemini-2.5-pro`.

**Suggestion** : Paramètre optionnel `modele_ocr` dans le formulaire de sélection, transmis à la tâche.

---

## AXE 5 — Qualité et Maintenabilité

> **Priorité : BASSE** (dette technique, pas de bug)

### 5.1 — `json_sanitizer.py` mal placé

`observations/json_rep/json_sanitizer.py` appartient logiquement au pipeline OCR, pas à l'app `observations`. Déplacer vers `ocr/json_sanitizer.py` ou `core/json_sanitizer.py` + mettre à jour les imports.

### 5.2 — Prompts dans `observations/json_rep/`

Les fichiers `prompt_gemini_transcription*.txt` devraient être dans `ocr/prompts/` pour la cohérence. Mettre à jour `_charger_prompt_production()`.

### 5.3 — `test_gemini_simple.py` à la racine de l'app

Fichier de test standalone dans `ocr/`. À déplacer dans `scripts/` ou supprimer s'il est couvert par des tests unitaires.

---

## Ordre d'Intervention Recommandé

```
Nouveau chat 1 (Plan + Agent) → AXE 1 : Bugs bloquants
    Contexte : @docs/ocr_optimization_plan.md @ocr/tasks.py
    
Nouveau chat 2 (Plan + Agent) → AXE 2 : Robustesse
    Contexte : @docs/ocr_optimization_plan.md @ocr/tasks.py @ocr/views.py
    
Nouveau chat 3 (Plan + Agent) → AXE 3 : Rate Limiting distribué
    Contexte : @docs/ocr_optimization_plan.md @ocr/tasks.py
    
Nouveau chat 4 (Plan + Agent) → AXE 4 : UX / Observabilité
    Contexte : @docs/ocr_optimization_plan.md @ocr/views.py @ocr/templates/
    
Nouveau chat 5 (Plan + Agent) → AXE 5 : Maintenabilité
    Contexte : @docs/ocr_optimization_plan.md
```

---

## Notes Techniques Importantes

- **Modèle Gemini utilisé** : `gemini-3-flash-preview` (hardcodé dans `ocr/tasks.py:205`)
- **Rate limit Gemini** : 60 RPM, timeout 120s, 3 retries avec backoff exponentiel (2s→4s→8s→16s max)
- **Structure JSON attendue** : 6 clés racine (`informations_generales`, `nid`, `localisation`, `tableau_donnees`, `tableau_donnees_2`, `causes_echec`)
- **Détection prompt** : basée sur le nom du répertoire parent (`ancien`/`anciennes` → prompt Ancienne Fiche)
- **Worker Celery Windows** : pool `solo`, concurrency 1 (voir `observations_nids/celery.py`)
- **Pas de signal Django** dans l'app OCR
- **Permission OCR** : décorateur `@transcription_required` (champ `est_transcription=True` sur Utilisateur)
