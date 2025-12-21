# ANALYSE DÉTAILLÉE DU FLUX DE TRANSCRIPTION PURE - APPLICATION PILOT

> **Périmètre** : Transcription pure (images → JSON) **SANS** importation en base de données
>
> **Date** : 2025-12-20
>
> **Objectif** : Analyser et optimiser le flux de transcription OCR batch avec Gemini

---

## TABLE DES MATIÈRES

[TOC]

---

## SYNTHÈSE EXÉCUTIVE

Le flux de transcription OCR batch dans l'application pilot traite les images à travers une tâche Celery asynchrone. Le flux actuel fonctionne mais présente **plusieurs problèmes critiques** :

### Problèmes identifiés

| Priorité | Problème | Impact |
|----------|----------|--------|
| 🔴 CRITIQUE | Import timezone manquant | **Application crash** |
| 🔴 CRITIQUE | TranscriptionOCR.fiche non nullable | **Impossible de créer TranscriptionOCR sans fiche** |
| 🔴 CRITIQUE | Pas de détection automatique du prompt | **Anciennes fiches mal transcrites** |
| 🔴 CRITIQUE | Pas de retry sur erreurs API | **Images perdues sur erreur réseau** |
| 🔴 CRITIQUE | Pas de rate limiting | **Risque de ban Google API** |
| 🟡 HAUTE | Pas de timeout API | **Gelage du batch possible** |
| 🟡 HAUTE | Validation JSON insuffisante | **Erreurs de parsing** |
| 🟢 MOYENNE | Arborescence JSON trop profonde | **Maintenance difficile** |
| 🟢 MOYENNE | update_state() trop fréquent | **Surcharge Redis** |
| 🔵 BASSE | sessionStorage pour paramètres | **Perte de données possible** |

### Quick Wins recommandés

1. **Import timezone** (1 min) → Évite crash
2. **Fiche nullable** (10 min + migration) → Permet création TranscriptionOCR
3. **Détection prompt** (30 min) → Améliore qualité transcription
4. **Retry avec backoff** (1h) → Robustesse réseau
5. **Rate limiting** (30 min) → Évite ban API

**Total estimé** : 2h15 pour corriger les 5 problèmes critiques

---

## 1. DÉTECTION DU TYPE DE FICHE ET SÉLECTION DU PROMPT

### 1.1 État actuel

**Détection du type de fiche** (`pilot/tasks.py:86-110`)

```python
def _determiner_type_fiche_et_traitement(chemin_relatif: str) -> tuple[str, str]:
    """
    Détermine le type de fiche et de traitement à partir du chemin.

    Args:
        chemin_relatif: Chemin comme "Ancienne_fiche/Traitement_1"

    Returns:
        (type_fiche, type_traitement)
    """
    parts = chemin_relatif.split(os.sep)
    type_fiche = "Inconnu"
    type_traitement = "Inconnu"

    if len(parts) >= 1:
        type_fiche = parts[0]  # Ex: "Ancienne_fiche"
    if len(parts) >= 2:
        type_traitement = parts[1]  # Ex: "Traitement_1"

    return type_fiche, type_traitement
```

**Chargement du prompt** (`pilot/tasks.py:382-391`)

```python
# ❌ PROBLÈME : Toujours le même prompt, quelle que soit la fiche
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

### 1.2 Prompts disponibles

Deux prompts existent dans `observations/json_rep/` :

#### `prompt_gemini_transcription.txt` (Standard)
- **Usage** : Fiches modernes standard
- **Format** : Tableau au recto, informations structurées
- **Taille** : 52 lignes

#### `prompt_gemini_transcription_Ancienne_Fiche.txt` (Archives)
- **Usage** : Fiches années 70/80
- **Particularités** :
  - Année écrite **VERTICALEMENT** en marge droite
  - Feuille IGN en haut à droite
  - Cases à cocher pour bilan (Succès/Échec)
  - Tableau de données sur le **VERSO uniquement**
  - Normalisation années (77 → 1977)
- **Taille** : 91 lignes

### 1.3 Problèmes identifiés

| Problème | Severity | Impact |
|----------|----------|--------|
| Pas de détection automatique du prompt | 🔴 CRITIQUE | Anciennes fiches transcrites avec mauvais prompt = erreurs structurelles |
| Type fiche détecté mais non utilisé | 🟡 HAUTE | La logique existe (`_determiner_type_fiche_et_traitement`) mais inutilisée |
| Pas de fallback | 🟢 MOYENNE | Erreur non gracieuse si prompt inexistant |
| Pas de logging de sélection | 🟢 MOYENNE | Impossible de tracer quel prompt utilisé |

### 1.4 Solution proposée

#### Fonction de chargement automatique

**Créer dans `pilot/tasks.py`** (après `_determiner_type_fiche_et_traitement`) :

```python
def _charger_prompt_selon_type_fiche(chemin_relatif: str) -> str:
    """
    Charge le bon prompt selon le type de fiche détecté dans le chemin.

    Règle de détection :
    - Si le chemin contient "ancien" ou "Ancien" → prompt anciennes fiches
    - Sinon → prompt standard

    Args:
        chemin_relatif: Chemin du répertoire (ex: "Ancienne_fiche/Traitement_1")

    Returns:
        Contenu du prompt en string

    Raises:
        ValueError: Si le prompt n'est pas trouvé

    Example:
        >>> _charger_prompt_selon_type_fiche("Ancienne_fiche/Sans_traitement")
        # Retourne le contenu de prompt_gemini_transcription_Ancienne_Fiche.txt
    """
    type_fiche, _ = _determiner_type_fiche_et_traitement(chemin_relatif)

    # Déterminer quel prompt utiliser (insensible à la casse)
    if 'ancien' in type_fiche.lower():
        prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'
        logger.info(f"📄 Prompt ANCIENNES FICHES sélectionné pour: {type_fiche}")
    else:
        prompt_filename = 'prompt_gemini_transcription.txt'
        logger.info(f"📄 Prompt STANDARD sélectionné pour: {type_fiche}")

    prompt_path = os.path.join(
        settings.BASE_DIR, 'observations', 'json_rep', prompt_filename
    )

    try:
        with open(prompt_path, encoding='utf-8') as f:
            prompt_content = f.read()
            logger.debug(f"✓ Prompt chargé: {prompt_filename} ({len(prompt_content)} chars)")
            return prompt_content
    except FileNotFoundError as e:
        logger.error(f"❌ Prompt introuvable: {prompt_path}")
        raise ValueError(f"Prompt {prompt_filename} non trouvé dans observations/json_rep/") from e
```

#### Intégration dans la tâche principale

**Modifier `process_batch_transcription_task()`** :

**AVANT** (lignes 382-391) - **À SUPPRIMER** :
```python
# Charger le prompt
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

**APRÈS** (dans la boucle des répertoires, après ligne 465) :

```python
# Boucle sur les répertoires
for dir_index, dir_info in enumerate(directories):
    dir_path_relatif = dir_info['path']
    dir_name = dir_info['name']

    logger.info(f"📁 Traitement du répertoire {dir_index + 1}/{len(directories)}: {dir_path_relatif}")

    # ✨ NOUVEAU : Charger le prompt approprié selon le type de fiche
    try:
        prompt = _charger_prompt_selon_type_fiche(dir_path_relatif)
    except ValueError as e:
        logger.error(f"❌ Erreur chargement prompt pour {dir_path_relatif}: {e}")
        all_results.append({
            'directory': dir_path_relatif,
            'modele_ocr': modele_ocr,
            'status': 'error',
            'error': f"Prompt introuvable: {str(e)}",
            'files': [],
        })
        continue  # Passer au répertoire suivant

    # Déterminer le type de fiche et de traitement
    type_fiche, type_traitement = _determiner_type_fiche_et_traitement(dir_path_relatif)

    # ... reste du code
```

### 1.5 Tests recommandés

```python
# test_pilot_tasks.py

def test_charger_prompt_ancienne_fiche():
    """Vérifie que les anciennes fiches utilisent le bon prompt"""
    prompt = _charger_prompt_selon_type_fiche("Ancienne_fiche/Sans_traitement")
    assert "VERTICALEMENT" in prompt
    assert "années 70" in prompt.lower()

def test_charger_prompt_standard():
    """Vérifie que les nouvelles fiches utilisent le prompt standard"""
    prompt = _charger_prompt_selon_type_fiche("Nouvelle_fiche/Traitement_1")
    assert "VERTICALEMENT" not in prompt

def test_charger_prompt_case_insensitive():
    """Vérifie que la détection est insensible à la casse"""
    prompt1 = _charger_prompt_selon_type_fiche("ANCIENNE_fiche/test")
    prompt2 = _charger_prompt_selon_type_fiche("ancienne_FICHE/test")
    assert prompt1 == prompt2
```

### 1.6 Priorité

**🔴 PRIORITÉ CRITIQUE** - Impact direct sur la qualité des transcriptions

---

## 2. ORGANISATION DES FICHIERS JSON RÉSULTATS

### 2.1 État actuel

**Structure réelle** (`pilot/tasks.py:461, 544-545`)

```
media/
└── transcription_results/
    └── {dir_path_relatif}/           # Ex: Ancienne_fiche/Sans_traitement
        └── {modele_ocr}/              # Ex: gemini_2_flash
            ├── {image_name}_result.json
            └── {image_name}_raw.json  # Si erreur détectée
```

**Exemple concret** :
```
media/transcription_results/
├── Ancienne_fiche/
│   └── Sans_traitement/
│       ├── gemini_2_flash/
│       │   ├── scan_001_result.json
│       │   ├── scan_001_raw.json
│       │   └── scan_002_result.json
│       └── gemini_1.5_pro/
│           ├── scan_001_result.json
│           └── scan_002_result.json
└── Nouvelle_fiche/
    └── Traitement_1/
        └── gemini_2_flash/
            └── scan_050_result.json
```

### 2.2 Problèmes identifiés

| Problème | Severity | Impact |
|----------|----------|--------|
| Modèle dans le chemin | 🟢 MOYENNE | Arborescence profonde (4 niveaux), instable si modèles renommés |
| Pas de métadonnées | 🟢 MOYENNE | Impossible de savoir : date, durée, modèle utilisé |
| Pas d'horodatage | 🔵 BASSE | Impossible de distinguer 2 exécutions du même batch |
| Pas d'index global | 🔵 BASSE | Difficile de retrouver tous les résultats d'un batch |

### 2.3 Solutions proposées

#### Solution 1 : Ajouter métadonnées en en-tête JSON (RECOMMANDÉE)

**Format du fichier JSON avec métadonnées** :

```json
{
  "_metadata": {
    "date_transcription": "2025-01-20T14:30:52+01:00",
    "modele_ocr": "gemini_2_flash",
    "duree_secondes": 2.34,
    "type_image": "brute",
    "type_fiche": "Ancienne_fiche",
    "type_traitement": "Sans_traitement",
    "version_prompt": "ancienne",
    "image_source": "scan_001.jpg",
    "chemin_image": "Ancienne_fiche/Sans_traitement/scan_001.jpg",
    "transcription_ocr_id": 12345
  },
  "informations_generales": {
    "n_fiche": "001",
    "observateur": "Jean Dupont",
    ...
  },
  "nid": { ... },
  "localisation": { ... },
  ...
}
```

**Code pour implémenter** (dans la boucle image, remplacer lignes 542-548) :

```python
# Construire le JSON final avec métadonnées
json_data_with_metadata = {
    "_metadata": {
        "date_transcription": timezone.now().isoformat(),
        "modele_ocr": modele_ocr,
        "duree_secondes": round(duration, 2),
        "type_image": type_image,
        "type_fiche": type_fiche,
        "type_traitement": type_traitement,
        "version_prompt": "ancienne" if "ancien" in type_fiche.lower() else "standard",
        "image_source": img_file,
        "chemin_image": img_path_relatif,
        "transcription_ocr_id": transcription_ocr.pk if transcription_ocr else None,
    },
    **json_data  # Fusionner les données de transcription
}

# Enregistrement du JSON final
with open(json_path_complet, 'w', encoding='utf-8') as f:
    json.dump(json_data_with_metadata, f, indent=2, ensure_ascii=False)

logger.info(f"✓ JSON sauvegardé avec métadonnées: {json_path_relatif}")
```

#### Solution 2 : Simplifier l'arborescence (Optionnel)

**Nouvelle structure plus plate** :

```
media/transcription_results/
└── {type_fiche}/
    └── {type_traitement}/
        └── {image_name}_{modele}_{timestamp}.json
```

**Avantages** :
- 3 niveaux au lieu de 4
- Modèle dans le nom (pas dans le chemin)
- Timestamp pour distinguer les exécutions

**Inconvénient** : Tous les modèles mélangés dans le même dossier

### 2.4 Priorité

**🟢 PRIORITÉ MOYENNE** - Amélioration de traçabilité et maintenance

---

## 3. BOUCLES DE TRAITEMENT ET OPTIMISATION

### 3.1 État actuel

**Structure des boucles** (`pilot/tasks.py:429-632`)

```python
# Boucle 1 : Pour chaque modèle OCR
for modele_index, modele_ocr in enumerate(modeles_ocr):
    modele_api = modeles_mapping.get(modele_ocr)
    model = genai.GenerativeModel(modele_api)  # Initialisation du modèle

    # Boucle 2 : Pour chaque répertoire
    for dir_index, dir_info in enumerate(directories):

        # Boucle 3 : Pour chaque image
        for img_file in image_files:
            # Traitement (40s par image en moyenne)
            response = model.generate_content([prompt, image])
            # ...

            # ❌ PROBLÈME : update_state() à CHAQUE image
            self.update_state(state='PROGRESS', meta={...})
```

**Calcul de progression** (`pilot/tasks.py:399-411`)

```python
# Total images = somme des images par répertoire × nombre de modèles
total_images = images_par_repertoire * len(modeles_ocr)
```

### 3.2 Problèmes identifiés

| Problème | Type | Severity | Impact |
|----------|------|----------|--------|
| Exécution 100% séquentielle | Performance | 🟡 HAUTE | 600 images × 40s = **6h40** de traitement |
| Pas de retry sur erreur réseau | Robustesse | 🔴 CRITIQUE | Une erreur API = image perdue définitivement |
| Pas de timeout | Robustesse | 🟡 HAUTE | Un appel gelé = tout le batch gelé |
| Pas de rate limiting | Robustesse | 🔴 CRITIQUE | Risque de ban Google API (quota dépassé) |
| update_state() trop fréquent | Performance | 🟢 MOYENNE | 600 écritures Redis = surcharge |
| Pas de gestion mémoire | Performance | 🔵 BASSE | Images PIL non fermées explicitement |

### 3.3 Solutions proposées

#### Solution 1 : Retry avec exponential backoff (CRITIQUE)

**Créer une fonction utilitaire** dans `pilot/tasks.py` :

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, initial_delay=2, max_delay=16):
    """
    Décorateur pour retry avec exponential backoff.

    Délais progressifs : 2s → 4s → 8s → 16s (max)

    Args:
        max_retries: Nombre maximum de tentatives (défaut: 3)
        initial_delay: Délai initial en secondes (défaut: 2)
        max_delay: Délai maximum en secondes (défaut: 16)

    Returns:
        Décorateur de fonction

    Example:
        @retry_with_backoff(max_retries=3)
        def call_api():
            # Code qui peut échouer
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_error = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"⚠️ Tentative {attempt + 1}/{max_retries} échouée pour {func.__name__}: {str(e)}. "
                            f"Retry dans {delay}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)  # Exponential backoff
                    else:
                        logger.error(
                            f"❌ Toutes les tentatives échouées pour {func.__name__} après {max_retries} essais"
                        )

            raise last_error
        return wrapper
    return decorator
```

**Utilisation** :

```python
@retry_with_backoff(max_retries=3, initial_delay=2)
def call_gemini_api(model, prompt, image_path):
    """Appel API Gemini avec retry automatique"""
    image = Image.open(image_path)
    try:
        response = model.generate_content([prompt, image])
        return response.text.encode('utf-8').decode('utf-8')
    finally:
        image.close()  # Libérer la mémoire
```

**Intégration dans la boucle** (remplacer lignes 507-526) :

```python
try:
    # Appel API avec retry automatique
    text_response = call_gemini_api(model, prompt, img_path_complet)

    # Nettoyage markdown
    if text_response.startswith("```json"):
        text_response = text_response[7:].strip()
        if text_response.endswith("```"):
            text_response = text_response[:-3].strip()

    # Parsing JSON
    json_data = json.loads(text_response)

except Exception as e:
    logger.error(f"❌ Échec définitif pour {img_file} après retries: {str(e)}")
    file_result = {
        'filename': img_file,
        'status': 'error',
        'error': str(e),
        'duration': round(time.time() - file_start, 2),
    }
    total_errors += 1
    continue  # Passer à l'image suivante
```

#### Solution 2 : Rate limiting (CRITIQUE)

**Ajouter au début de `process_batch_transcription_task()`** :

```python
# Configuration rate limiting pour Google Gemini API
GEMINI_REQUESTS_PER_MINUTE = 60  # Limite Google
MIN_DELAY_BETWEEN_REQUESTS = 60.0 / GEMINI_REQUESTS_PER_MINUTE  # 1 req/sec

last_request_time = time.time()

def apply_rate_limit():
    """Applique un délai minimum entre les requêtes API"""
    global last_request_time

    now = time.time()
    elapsed = now - last_request_time

    if elapsed < MIN_DELAY_BETWEEN_REQUESTS:
        delay = MIN_DELAY_BETWEEN_REQUESTS - elapsed
        logger.debug(f"⏱️ Rate limit: attente de {delay:.2f}s")
        time.sleep(delay)

    last_request_time = time.time()
```

**Utilisation dans la boucle image** (avant l'appel API) :

```python
# Respecter le rate limiting
apply_rate_limit()

# Appel API
text_response = call_gemini_api(model, prompt, img_path_complet)
```

#### Solution 3 : Timeout (HAUTE)

**Ajouter timeout à l'appel API** :

```python
@retry_with_backoff(max_retries=3)
def call_gemini_api(model, prompt, image_path, timeout=120):
    """
    Appel API Gemini avec timeout.

    Args:
        timeout: Timeout en secondes (défaut: 120s = 2 minutes)
    """
    image = Image.open(image_path)
    try:
        # Gemini SDK ne supporte pas timeout natif, utiliser threading
        import threading

        result = [None]
        exception = [None]

        def api_call():
            try:
                response = model.generate_content([prompt, image])
                result[0] = response.text.encode('utf-8').decode('utf-8')
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=api_call)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            raise TimeoutError(f"API call exceeded {timeout}s timeout")

        if exception[0]:
            raise exception[0]

        return result[0]

    finally:
        image.close()
```

#### Solution 4 : Optimiser update_state (MOYENNE)

**Réduire la fréquence des updates** :

```python
# Au début de la tâche
UPDATE_PROGRESS_EVERY_N_IMAGES = 5  # Mettre à jour tous les 5 fichiers

# Dans la boucle image
if processed_count % UPDATE_PROGRESS_EVERY_N_IMAGES == 0 or processed_count == total_images:
    self.update_state(
        state='PROGRESS',
        meta={
            'processed': processed_count,
            'total': total_images,
            'current_file': img_file,
            'current_directory': dir_path_relatif,
            'current_model': modele_ocr,
            'percent': int((processed_count / total_images) * 100),
        }
    )
```

### 3.4 Priorité par solution

| Solution | Priorité | Effort | Impact |
|----------|----------|--------|--------|
| Retry + backoff | 🔴 CRITIQUE | 1h | Évite perte d'images |
| Rate limiting | 🔴 CRITIQUE | 30 min | Évite ban API |
| Timeout | 🟡 HAUTE | 30 min | Évite gelage |
| Optimiser update_state | 🟢 MOYENNE | 15 min | Améliore performance |

---

## 4. GESTION DES ERREURS DE TRANSCRIPTION

### 4.1 État actuel

**Flux de traitement** (`pilot/tasks.py:507-619`)

```python
try:
    # 1. Ouverture image
    image = Image.open(img_path_complet)

    # 2. Appel API (❌ PAS DE RETRY, PAS DE TIMEOUT)
    response = model.generate_content([prompt, image])
    text_response = response.text.encode('utf-8').decode('utf-8')

    # 3. Nettoyage markdown
    if text_response.startswith("```json"):
        text_response = text_response[7:].strip()
        if text_response.endswith("```"):
            text_response = text_response[:-3].strip()

    # 4. Parsing JSON
    try:
        json_data = json.loads(text_response)
    except json.JSONDecodeError as e:
        logger.error(f"Erreur décodage JSON: {str(e)}")
        raise ValueError(f"Réponse non JSON: {text_response[:100]}...")

    # 5. Validation et correction
    if json_data:
        erreurs = validate_json_structure(json_data)
        if erreurs:
            logger.warning(f"JSON invalide, correction en cours")
            json_data = corriger_json(copy.deepcopy(json_data))
            # Sauvegarder le raw
            with open(raw_path, 'w') as f:
                json.dump(json_data_raw, f, indent=2, ensure_ascii=False)

except Exception as e:
    logger.error(f"Erreur: {str(e)}")
    total_errors += 1
```

### 4.2 Problèmes identifiés

| Problème | Catégorie | Severity | Impact |
|----------|-----------|----------|--------|
| Pas de retry | Robustesse | 🔴 CRITIQUE | Perte d'image sur erreur réseau temporaire |
| Pas de timeout | Robustesse | 🔴 CRITIQUE | Gelage du batch |
| raw.json seulement si erreur | Traçabilité | 🟢 MOYENNE | Impossible de comparer réponse brute vs corrigée |
| Pas de fallback JSON | Robustesse | 🟡 HAUTE | Si Gemini retourne du texte, image perdue |

### 4.3 Solution proposée

**Fonction robuste de validation/correction** :

```python
def valider_et_corriger_json(json_data, img_file, results_dir):
    """
    Valide un JSON et le corrige si nécessaire.

    Args:
        json_data: Données JSON à valider
        img_file: Nom du fichier image (pour logging)
        results_dir: Répertoire pour sauvegarder raw.json

    Returns:
        (json_corrige, était_invalide, erreurs)
    """
    from observations.json_rep.json_sanitizer import validate_json_structure, corriger_json

    erreurs = validate_json_structure(json_data)

    if not erreurs:
        logger.info(f"✓ JSON valide pour {img_file}")
        return json_data, False, []

    # JSON invalide
    logger.warning(f"⚠️ JSON invalide pour {img_file}. Erreurs: {erreurs}")

    # Toujours sauvegarder le JSON brut
    raw_filename = f"{os.path.splitext(img_file)[0]}_raw.json"
    raw_path = os.path.join(results_dir, raw_filename)
    json_data_raw = copy.deepcopy(json_data)

    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(json_data_raw, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 JSON brut sauvegardé: {raw_filename}")

    # Corriger le JSON
    json_corrige = corriger_json(json_data_raw)

    # Revalider après correction
    erreurs_apres = validate_json_structure(json_corrige)

    if erreurs_apres:
        logger.error(f"❌ JSON reste invalide après correction: {erreurs_apres}")
        return None, True, erreurs_apres

    logger.info(f"✓ JSON corrigé avec succès pour {img_file}")
    return json_corrige, True, []
```

### 4.4 Priorité

**🟡 PRIORITÉ HAUTE** - Robustesse du système

---

## 5. CRÉATION DES ENTRÉES TRANSCRIPTIONOCR

### 5.1 État actuel

**Création de TranscriptionOCR** (`pilot/tasks.py:575-597`)

```python
# Créer l'entrée TranscriptionOCR
nom_base = _extraire_nom_base_fichier(img_path_relatif)

# Utiliser la fiche importée si disponible
if fiche_importee:
    fiche = fiche_importee
else:
    fiche = _trouver_fiche_correspondante(nom_base)

transcription_ocr = TranscriptionOCR.objects.create(
    fiche=fiche,  # ❌ PROBLÈME : Peut être None, mais le champ n'est pas nullable !
    chemin_json=json_path_relatif,
    chemin_image=img_path_relatif,
    type_image=type_image,
    modele_ocr=modele_ocr,
    temps_traitement_secondes=duration,
    statut_evaluation='non_evaluee',
)
```

### 5.2 Problèmes identifiés

#### Problème 1 : Import timezone manquant (CRITIQUE)

**Lignes concernées** :
- `pilot/tasks.py:271` (dans `_importer_fiche_depuis_json`)
- `pilot/tasks.py:557` (dans `process_batch_transcription_task`)

```python
# ❌ ERREUR : timezone utilisé mais jamais importé
date_obs = timezone.make_aware(datetime.datetime(annee, mois, jour, heure, 0))
annee = timezone.now().year
```

**Impact** : **Application crash** avec `NameError: name 'timezone' is not defined`

**Solution** :

```python
# En haut du fichier pilot/tasks.py (après les autres imports Django)
from django.utils import timezone
```

#### Problème 2 : Champ fiche non nullable (CRITIQUE)

**Définition du modèle** (`pilot/models.py:26-32`) :

```python
class TranscriptionOCR(models.Model):
    fiche = models.ForeignKey(
        FicheObservation,
        on_delete=models.CASCADE,
        related_name="transcriptions_ocr_pilot",
        verbose_name="Fiche de référence",
        help_text="Fiche d'observation corrigée manuellement (vérité terrain)",
        # ❌ MANQUE : null=True, blank=True
    )
```

**Problème** : Le flux demandé **exclut** l'importation de fiches, donc `fiche` sera toujours `None`.

**Impact** : **Impossible de créer TranscriptionOCR** sans fiche → Erreur Django `IntegrityError`

**Solution** :

```python
# Modifier pilot/models.py
fiche = models.ForeignKey(
    FicheObservation,
    on_delete=models.CASCADE,
    related_name="transcriptions_ocr_pilot",
    verbose_name="Fiche de référence",
    help_text="Fiche d'observation corrigée manuellement (vérité terrain)",
    null=True,   # ✅ AJOUTER
    blank=True,  # ✅ AJOUTER
)
```

**Migration nécessaire** :

```bash
python manage.py makemigrations pilot
python manage.py migrate
```

### 5.3 Champs remplis dans TranscriptionOCR

**Actuellement** (`pilot/tasks.py:584-592`) :

| Champ | Valeur | Source |
|-------|--------|--------|
| `fiche` | Foreign Key (peut être None) | `fiche_importee` ou `_trouver_fiche_correspondante()` |
| `chemin_json` | Chemin relatif | Calculé |
| `chemin_image` | Chemin relatif | Depuis répertoire |
| `type_image` | 'brute' ou 'optimisee' | Détecté depuis chemin |
| `modele_ocr` | Nom du modèle | Depuis paramètre |
| `temps_traitement_secondes` | Float | Chronomètre |
| `statut_evaluation` | 'non_evaluee' | Défaut |
| `date_transcription` | Auto | `auto_now_add=True` |

**Non remplis** (mais pertinents pour évaluation future) :
- `score_global`, `nombre_champs_corrects`, `nombre_champs_total`
- `nombre_erreurs_*` (tous à 0)
- `details_comparaison`, `notes_evaluation`

### 5.4 Priorité

| Problème | Priorité | Effort |
|----------|----------|--------|
| Import timezone manquant | 🔴 CRITIQUE | 1 min |
| Fiche nullable | 🔴 CRITIQUE | 10 min + migration |

---

## 6. PASSAGE DES PARAMÈTRES ENTRE LES VUES

### 6.1 État actuel

**Stockage côté client** (`pilot/templates/pilot/selection_repertoire_ocr.html:311-321`)

```javascript
// Stockage dans sessionStorage (navigateur)
const selectedDirs = checked.map(cb => ({
    name: cb.value,
    path: cb.dataset.path
}));

sessionStorage.setItem('selectedDirectories', JSON.stringify(selectedDirs));

window.location = '{% url "pilot:optimisation_ocr_home" %}';
```

**Récupération côté client** (`pilot/templates/pilot/optimisation_ocr_home.html:132-148`)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const selectedDirsJSON = sessionStorage.getItem('selectedDirectories');

    if (!selectedDirsJSON) {
        // Erreur : pas de sélection
        return;
    }

    const selectedDirs = JSON.parse(selectedDirsJSON);
    // Afficher...
});
```

**Envoi au serveur** (`pilot/templates/pilot/optimisation_ocr_home.html:234-251`)

```javascript
function lancerTranscriptionBatch(directories, modeles, importerEnBase) {
    const formData = new FormData();
    formData.append('directories', JSON.stringify(directories));
    formData.append('modeles_ocr', JSON.stringify(modeles));
    formData.append('importer_en_base', importerEnBase ? 'true' : 'false');

    fetch('{% url "pilot:lancer_transcription_batch" %}', {
        method: 'POST',
        body: formData
    })
}
```

### 6.2 Problèmes identifiés

| Problème | Severity | Impact |
|----------|----------|--------|
| sessionStorage volatile | 🔵 BASSE | Perte si tab fermée, mais POST fonctionne |
| Pas de validation client-side | 🔵 BASSE | Données invalides → erreur serveur |
| Perte de contexte en crash | 🟢 MOYENNE | Impossible de savoir ce qui était lancé |

### 6.3 Solution proposée (optionnelle)

**Ajouter logging avec batch_id** :

```python
def lancer_transcription_batch(request):
    # Générer un ID unique pour le batch
    batch_id = f"{request.user.id}_{int(timezone.now().timestamp())}"

    logger.info(
        f"🚀 [BATCH {batch_id}] Lancement par {request.user.username}: "
        f"{len(directories)} répertoires, {len(modeles_ocr)} modèles"
    )

    # Stocker en session
    request.session['pilot_batch_id'] = batch_id

    return JsonResponse({
        'success': True,
        'task_id': task_id,
        'batch_id': batch_id,
    })
```

### 6.4 Priorité

**🔵 PRIORITÉ BASSE** - Le système actuel fonctionne

---

## RÉCAPITULATIF GLOBAL - PRIORITÉS

### Corrections par ordre de priorité

| # | Problème | Fichiers à modifier | Priorité | Effort | Impact |
|---|----------|---------------------|----------|--------|--------|
| 1 | **Import timezone manquant** | `pilot/tasks.py` | 🔴 CRITIQUE | 1 min | Évite crash application |
| 2 | **Fiche nullable** | `pilot/models.py` | 🔴 CRITIQUE | 10 min + migration | Permet création TranscriptionOCR |
| 3 | **Détection prompt auto** | `pilot/tasks.py` | 🔴 CRITIQUE | 30 min | Améliore qualité transcription |
| 4 | **Retry avec backoff** | `pilot/tasks.py` | 🔴 CRITIQUE | 1h | Évite perte d'images |
| 5 | **Rate limiting** | `pilot/tasks.py` | 🔴 CRITIQUE | 30 min | Évite ban Google API |
| 6 | **Timeout API** | `pilot/tasks.py` | 🟡 HAUTE | 30 min | Évite gelage batch |
| 7 | **Validation JSON robuste** | `pilot/tasks.py` | 🟡 HAUTE | 1h | Meilleure gestion erreurs |
| 8 | **Métadonnées JSON** | `pilot/tasks.py` | 🟢 MOYENNE | 30 min | Traçabilité |
| 9 | **Optimiser update_state** | `pilot/tasks.py` | 🟢 MOYENNE | 15 min | Performance |
| 10 | **Logging batch** | `pilot/views.py` | 🔵 BASSE | 30 min | Debug |

### Quick Wins (priorité maximale, effort minimal)

**Total : 2h15 pour les 5 problèmes critiques**

1. ✅ **Import timezone** (1 min)
2. ✅ **Fiche nullable** (10 min + migration)
3. ✅ **Détection prompt** (30 min)
4. ✅ **Retry backoff** (1h)
5. ✅ **Rate limiting** (30 min)

---

## FICHIERS À MODIFIER - CHECKLIST

### Modifications critiques

- [x] `pilot/tasks.py`
  - [ ] Ajouter `from django.utils import timezone`
  - [ ] Créer `_charger_prompt_selon_type_fiche()`
  - [ ] Créer `retry_with_backoff()`
  - [ ] Créer `apply_rate_limit()`
  - [ ] Modifier boucle répertoires (charger prompt par répertoire)
  - [ ] Ajouter retry à l'appel API
  - [ ] Ajouter rate limiting
  - [ ] Réduire fréquence update_state

- [x] `pilot/models.py`
  - [ ] Rendre `TranscriptionOCR.fiche` nullable (`null=True, blank=True`)

- [x] `pilot/migrations/`
  - [ ] Générer migration pour fiche nullable

### Modifications optionnelles

- [ ] `pilot/tasks.py`
  - [ ] Ajouter métadonnées dans JSON
  - [ ] Améliorer validation JSON
  - [ ] Ajouter timeout

- [ ] `pilot/views.py`
  - [ ] Ajouter logging avec batch_id

### Exclusions (hors périmètre)

- ❌ Pas de modification de `_importer_fiche_depuis_json()` (importation en base exclue)
- ❌ Pas de modification des modèles FicheObservation, Localisation, Nid, etc.

---

## TESTS RECOMMANDÉS

```python
# tests/test_pilot_tasks.py

def test_charger_prompt_ancienne_fiche():
    """Anciennes fiches utilisent le bon prompt"""
    prompt = _charger_prompt_selon_type_fiche("Ancienne_fiche/Sans_traitement")
    assert "VERTICALEMENT" in prompt

def test_charger_prompt_standard():
    """Nouvelles fiches utilisent le prompt standard"""
    prompt = _charger_prompt_selon_type_fiche("Nouvelle_fiche/Traitement_1")
    assert "VERTICALEMENT" not in prompt

def test_retry_backoff_success_first_try():
    """Retry réussit au premier essai"""
    @retry_with_backoff(max_retries=3)
    def func():
        return "success"

    assert func() == "success"

def test_retry_backoff_fails_then_succeeds():
    """Retry réussit après échec"""
    attempts = [0]

    @retry_with_backoff(max_retries=3)
    def func():
        attempts[0] += 1
        if attempts[0] < 2:
            raise Exception("Fail")
        return "success"

    assert func() == "success"
    assert attempts[0] == 2

def test_transcription_ocr_without_fiche():
    """TranscriptionOCR peut être créé sans fiche"""
    transcription = TranscriptionOCR.objects.create(
        fiche=None,  # Doit fonctionner après migration
        chemin_json="test.json",
        chemin_image="test.jpg",
        type_image="brute",
        modele_ocr="gemini_2_flash",
        temps_traitement_secondes=2.5,
    )
    assert transcription.pk is not None
```

---

## CONCLUSION

Le flux de transcription pure nécessite **5 corrections critiques** pour être opérationnel :

1. ✅ **Import timezone** → Évite crash
2. ✅ **Fiche nullable** → Permet création TranscriptionOCR sans importation
3. ✅ **Détection prompt** → Améliore qualité (anciennes fiches)
4. ✅ **Retry API** → Robustesse réseau
5. ✅ **Rate limiting** → Évite ban Google

**Effort total estimé** : 2h15

Une fois ces corrections appliquées, le système sera **robuste et fonctionnel** pour la transcription batch multi-répertoires/multi-modèles.

---

**Dernière mise à jour** : 2025-12-20
**Auteur** : Analyse automatisée
**Statut** : Prêt pour implémentation
