# Pilot - Pièges et points d'attention

Ce fichier documente les **erreurs récurrentes** et **pièges** rencontrés lors du développement de l'application pilot.

---

## ⚠️ Problème : Perte d'accès aux sous-répertoires

### Contexte
Lors de la navigation dans les répertoires d'images via la vue `selection_repertoire_ocr`, l'utilisateur peut soudainement perdre la capacité d'accéder aux sous-répertoires.

### Symptôme
- L'interface affiche le répertoire actuel et le fil d'Ariane
- Les sous-répertoires sont listés avec `subdirs_count > 0`
- **Mais** : cliquer sur un sous-répertoire ne fonctionne plus
- L'URL reste la même ou affiche une erreur

### Cause
Modification accidentelle de la logique de construction des liens dans le template `selection_repertoire_ocr.html`.

**Code problématique** :
```html
<!-- ❌ INCORRECT : Lien cassé -->
<a href="?path={{ directory.name }}">
    {{ directory.name }}
</a>
```

**Pourquoi ça casse** :
- `directory.name` contient seulement le nom du répertoire (ex: `"Traitement_1"`)
- Il **manque le chemin parent** (`current_path`)
- Résultat : on essaie d'accéder à `/media/Traitement_1` au lieu de `/media/Ancienne_fiche/Traitement_1`

### Solution

**Code correct** :
```html
<!-- ✅ CORRECT : Concaténation du chemin parent -->
<a href="?path={{ current_path }}{% if current_path %}/{% endif %}{{ directory.name }}">
    {{ directory.name }}
</a>
```

**Explication** :
- `current_path` : chemin actuel (ex: `"Ancienne_fiche"`)
- Si `current_path` existe, ajouter `/` comme séparateur
- `directory.name` : nom du sous-répertoire (ex: `"Traitement_1"`)
- Résultat : `"Ancienne_fiche/Traitement_1"` ✅

### Prévention

1. **Tester systématiquement** la navigation multi-niveaux :
   ```
   media/ → Ancienne_fiche/ → Sans_traitement/ → (retour)
   ```

2. **Vérifier le template** après toute modification de `selection_repertoire_ocr.html` :
   - Chercher toutes les occurrences de `href="?path=`
   - S'assurer que `current_path` est inclus

3. **Tests automatisés** à ajouter (TODO) :
   ```python
   def test_navigation_sous_repertoires():
       """Vérifie que la navigation dans les sous-répertoires fonctionne"""
       response = self.client.get('/pilot/selection-repertoire/', {'path': 'Ancienne_fiche'})
       assert 'Sans_traitement' in response.content.decode()
       assert 'path=Ancienne_fiche/Sans_traitement' in response.content.decode()
   ```

### Fichiers concernés
- `pilot/templates/pilot/selection_repertoire_ocr.html` (lignes de liens `<a href="?path=..."`)
- `pilot/views.py:selection_repertoire_ocr` (ligne 44-55 : calcul de `current_path`)

---

## ⚠️ Problème : Fil d'Ariane (breadcrumb) incorrect

### Contexte
Le fil d'Ariane permet de naviguer rapidement vers un répertoire parent.

### Symptôme
Les liens du fil d'Ariane ne fonctionnent pas ou pointent vers de mauvais répertoires.

### Cause
Erreur dans la construction des chemins cumulés dans `views.py:selection_repertoire_ocr`.

**Code problématique** :
```python
# ❌ INCORRECT : Chaque lien pointe vers le même chemin
for part in parts:
    breadcrumb.append({'name': part, 'path': part})
```

**Résultat** :
```
media > Ancienne_fiche (path="Ancienne_fiche") > Sans_traitement (path="Sans_traitement")
                                                                    └─ ❌ Devrait être "Ancienne_fiche/Sans_traitement"
```

### Solution

**Code correct** (déjà implémenté dans `views.py:108-115`) :
```python
# ✅ CORRECT : Chemin cumulatif
breadcrumb = []
if safe_path:
    parts = safe_path.split(os.sep)
    current = ''
    for part in parts:
        if part:
            current = os.path.join(current, part) if current else part
            breadcrumb.append({'name': part, 'path': current})
```

**Explication** :
- `current` accumule les parties du chemin au fur et à mesure
- Premier item : `{'name': 'Ancienne_fiche', 'path': 'Ancienne_fiche'}`
- Deuxième item : `{'name': 'Sans_traitement', 'path': 'Ancienne_fiche/Sans_traitement'}`

### Prévention
Ne **jamais** simplifier la logique de construction du fil d'Ariane sans tests.

### Fichiers concernés
- `pilot/views.py:108-115` (calcul du breadcrumb)
- `pilot/templates/pilot/selection_repertoire_ocr.html` (affichage du breadcrumb)

---

## ⚠️ Problème : Tâche Celery bloquée en PENDING

### Contexte
Après avoir lancé un traitement batch, la progression reste bloquée à "Tâche en attente de démarrage...".

### Symptôme
- Le worker Celery est lancé
- La tâche apparaît avec `status='PENDING'` indéfiniment
- Aucun traitement ne démarre

### Causes possibles

**1. Worker Celery non démarré**
```bash
# Vérifier si le worker tourne
celery -A observations_nids worker --loglevel=info
```

**2. Mauvaise configuration Redis**
```python
# settings.py
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'  # ← Vérifier IP/port
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
```

**3. Nom de tâche incorrect**
```python
# ❌ INCORRECT
from pilot.tasks import process_batch_transcription_task
task = process_batch_transcription_task.delay(...)  # Nom de tâche peut être incorrect

# ✅ VÉRIFIER dans le worker log
[tasks]
  . pilot.tasks.process_batch_transcription_task  # ← Nom réel de la tâche
```

### Solution

1. **Redémarrer le worker Celery** :
   ```bash
   pkill -f "celery worker"
   celery -A observations_nids worker --loglevel=info
   ```

2. **Vérifier Redis** :
   ```bash
   redis-cli ping  # Doit retourner PONG
   ```

3. **Vérifier les logs** :
   ```bash
   tail -f logs/celery.log
   ```

### Prévention
- Toujours vérifier que le worker Celery est lancé avant de tester
- Ajouter un health check dans l'interface pour vérifier la connexion Redis

### Fichiers concernés
- `pilot/tasks.py:process_batch_transcription_task`
- `pilot/views.py:lancer_transcription_batch` (ligne 304 : `.delay()`)
- `observations_nids/settings.py:73-82` (configuration Celery)

---

## ⚠️ Problème : Timeout API Gemini

### Contexte
Lors d'un traitement batch, certaines images prennent trop de temps à transcrire et provoquent un timeout.

### Symptôme
```
Erreur : TimeoutError: API Gemini timeout après 120 secondes
```

### Cause
Images de grande taille ou complexes, ralentissant l'API Gemini.

### Solution

**1. Augmenter le timeout** (déjà implémenté dans `tasks.py:87-88`) :
```python
@retry_with_backoff(max_retries=3, initial_delay=2)
def call_gemini_api_with_timeout(client, model_name, prompt, image_path, timeout=120):
    # ✅ timeout=120s (2 minutes)
```

**2. Pré-redimensionner les images** :
```python
# tasks.py (ajout possible)
def resize_image_if_needed(image_path, max_width=2048):
    """Redimensionne l'image si trop grande"""
    img = Image.open(image_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(image_path)
```

**3. Utiliser un modèle plus rapide** :
- `gemini_2.5_flash_lite` au lieu de `gemini_2.5_pro`

### Prévention
- Tester avec des images de différentes tailles
- Ajouter une métrique `taille_image_mo` dans `TranscriptionOCR`

### Fichiers concernés
- `pilot/tasks.py:87-145` (appel API Gemini)

---

## ⚠️ Problème : JSON de transcription invalide

### Contexte
Après une transcription OCR, le JSON retourné par Gemini est invalide.

### Symptôme
```python
json.JSONDecodeError: Expecting property name enclosed in double quotes
```

### Cause
Gemini peut retourner du texte **avant** ou **après** le JSON valide :
```
Voici la transcription de la fiche :

{
  "espece": "Mésange bleue",
  ...
}

J'ai détecté quelques incertitudes...
```

### Solution

**Utiliser le sanitizer** (déjà implémenté dans `tasks.py`) :
```python
from observations.json_rep.json_sanitizer import corriger_json, validate_json_structure

# 1. Nettoyer le JSON brut
json_corrige = corriger_json(raw_response)

# 2. Valider la structure
is_valid, errors = validate_json_structure(json_corrige)

if not is_valid:
    logger.error(f"JSON invalide : {errors}")
```

**Le sanitizer fait** :
- Extraction du bloc JSON entre `{` et `}`
- Suppression des markdown code fences (` ```json `)
- Validation des champs obligatoires

### Prévention
- **Toujours** utiliser `corriger_json()` après un appel API
- Ne **jamais** faire `json.loads(raw_response)` directement

### Fichiers concernés
- `observations/json_rep/json_sanitizer.py` (utilitaire de nettoyage)
- `pilot/tasks.py` (utilise le sanitizer)

---

## ⚠️ Problème : Correspondances multiples (image ↔ fiche)

### Contexte
Lors de l'analyse des correspondances, une image peut matcher plusieurs fiches.

### Symptôme
```json
{
  "image": "fiche_042.jpg",
  "statut": "multiple",
  "fiches_possibles": [
    {"numero": 42, "annee": 2023, ...},
    {"numero": 142, "annee": 2024, ...}
  ]
}
```

### Cause
Plusieurs fiches ont un `chemin_image` contenant le même nom de base.

**Exemple** :
- Fiche #42 : `chemin_image="/media/2023/fiche_042.jpg"`
- Fiche #142 : `chemin_image="/media/2024/fiche_042.jpg"`

Le code recherche avec `contains` :
```python
# views.py:194
fiches = FicheObservation.objects.filter(chemin_image__contains=nom_base)
```

**Résultat** : Les 2 fiches matchent sur `"fiche_042"`.

### Solution

**Option 1** : Matching plus strict (chemin complet)
```python
# Construire le chemin relatif complet
chemin_relatif = os.path.join(repertoire, image_filename)
fiches = FicheObservation.objects.filter(chemin_image=chemin_relatif)
```

**Option 2** : Laisser l'utilisateur choisir (comportement actuel)
- L'interface affiche les fiches multiples
- L'utilisateur sélectionne manuellement

### Prévention
- Utiliser des **noms de fichiers uniques** (inclure année ou timestamp)
- Documenter la convention de nommage

### Fichiers concernés
- `pilot/views.py:188-235` (analyse des correspondances)

---

## ✅ Bonnes pratiques

### 1. Toujours tester la navigation complète
```
media/ → Ancienne_fiche/ → Sans_traitement/ → Retour → Nouvelle_fiche/ → Traitement_1/
```

### 2. Vérifier les logs Celery en développement
```bash
tail -f logs/celery.log
```

### 3. Utiliser le retry avec backoff pour les appels API
```python
@retry_with_backoff(max_retries=3)
def call_external_api():
    # ...
```

### 4. Valider tout JSON externe
```python
from observations.json_rep.json_sanitizer import corriger_json

json_safe = corriger_json(external_json)
```

### 5. Sécuriser les chemins de fichiers
```python
safe_path = os.path.normpath(user_input).replace('..', '')
if not full_path.startswith(base_dir):
    raise ValueError("Chemin invalide")
```

---

## 🔥 Checklist avant modification de pilot

Avant de modifier l'app pilot, vérifier :

- [ ] Les liens de navigation dans `selection_repertoire_ocr.html` incluent `current_path`
- [ ] Le fil d'Ariane utilise des chemins cumulatifs
- [ ] Les appels API Gemini utilisent `retry_with_backoff`
- [ ] Le JSON est nettoyé avec `corriger_json()` avant `json.loads()`
- [ ] Les chemins de fichiers sont validés (pas de `..` ou de sortie de `MEDIA_ROOT`)
- [ ] Le worker Celery est lancé pour tester les tâches
- [ ] Les logs sont vérifiés après modification

---

*Dernière mise à jour : 2025-12-27*
