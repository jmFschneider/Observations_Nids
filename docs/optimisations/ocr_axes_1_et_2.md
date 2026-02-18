# Optimisations OCR — Axes 1 et 2

> **Date** : Février 2026
> **Branche** : `optim/OCR_axe1`
> **Fichiers modifiés** : `ocr/tasks.py`, `ocr/views.py`, `ingest/importation_service.py`

---

## Axe 1 — Correction des bugs bloquants

### Bug 1.1 — `return` à l'intérieur de la boucle `for`

**Fichier** : `ocr/tasks.py` — `process_images_production_task`

**Symptôme** : Un batch de N images ne produisait qu'une seule transcription.
La tâche Celery se terminait après la première image.

**Cause** : Le `return` final était indenté au niveau de la boucle `for`,
ce qui l'exécutait à la fin de la première itération.

**Correction** : Désindentation d'un niveau — le `return` est maintenant
positionné après la boucle, au niveau de la fonction.

---

### Bug 1.2 — `update_state` écrasait les logs de progression

**Fichier** : `ocr/tasks.py` — `_log_progress` / `process_images_production_task`

**Symptôme** : Les messages de log (succès, erreurs par image) disparaissaient
à chaque itération dans l'UI de suivi.

**Cause** : `_log_progress` lisait le meta courant depuis Redis via
`AsyncResult`, y ajoutait un log, puis écrivait avec `update_state`.
En fin d'itération, un second `update_state` écrasait ce meta sans inclure
la clé `logs`.

**Correction** : Suppression de `_log_progress` et du `update_state` séparé.
Remplacement par une closure `log_progress` définie dans la tâche, qui
accumule les entrées dans une liste locale `logs: list[dict]` et effectue
**une seule écriture Redis** par appel, en fusionnant `processed`, `percent`
et `logs[-100:]` dans le même `update_state`.

Gain annexe : suppression de l'import `AsyncResult` devenu inutile, et
élimination de la lecture Redis à chaque log (coûteuse sous forte charge).

---

### Bug 1.3 — `corriger_json` non appelé sur les JSON structurellement valides

**Fichier** : `ocr/tasks.py` — `process_images_production_task`

**Symptôme** : Certaines clés JSON retournées par Gemini contenaient des
accents ou des caractères spéciaux (`"espèce"`, `"IGN/50000"`) qui faisaient
échouer l'import dans `ingest` lors du matching des champs.

**Cause** : `corriger_json` n'était appelé que si `validate_json_structure`
retournait des erreurs. Un JSON structurellement conforme mais avec des clés
non normalisées passait sans correction.

**Correction** : `corriger_json` est désormais **toujours** appelé après
le parsing, indépendamment du résultat de `validate_json_structure`.
Les erreurs de structure détectées sont loguées en `WARNING` pour la
traçabilité, sans bloquer la normalisation.

```python
# Avant
if validate_json_structure(json_data):
    json_data = corriger_json(json_data)

# Après
structure_errors = validate_json_structure(json_data)
if structure_errors:
    logger.warning(f"Structure JSON non conforme : {structure_errors}")
json_data = corriger_json(json_data)
```

---

## Axe 2 — Robustesse et fiabilité

### 2.1 — Déduplication avant transcription

**Fichier** : `ocr/tasks.py` — `process_images_production_task`

**Problème** : Une image soumise plusieurs fois était re-transcrite et
re-facturée à l'API Gemini, sans vérification de l'historique.

**Correction** : En tête de chaque itération, vérification de l'existence
d'un enregistrement `TranscriptionOCR` avec `statut='succes'` pour le
chemin d'image courant. Si trouvé, l'image est sautée via `continue` et
comptabilisée dans `ignored_count`, retourné dans le dict de résultat final.

```python
if TranscriptionOCR.objects.filter(
    chemin_image=img_rel_path, statut='succes'
).exists():
    log_progress(f"⏭️ {basename} déjà transcrit, ignoré", 'warning')
    ignored_count += 1
    continue
```

---

### 2.2 — Remplacement de `threading.Thread` par `ThreadPoolExecutor`

**Fichier** : `ocr/tasks.py` — `call_gemini_api_with_timeout`

**Problème** : Après un timeout, le thread daemon restait actif en
arrière-plan (fuite de ressources). La connexion réseau vers l'API Gemini
n'était pas libérée.

**Correction** : Utilisation de `concurrent.futures.ThreadPoolExecutor`
avec `future.result(timeout=...)`. En cas de `FutureTimeoutError`,
`future.cancel()` est appelé et le context manager `with` garantit
la libération des ressources à la sortie du bloc.

```python
with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(api_call)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        future.cancel()
        raise TimeoutError(f"API call exceeded {timeout}s timeout") from None
```

---

### 2.3 — Correction de la normalisation de chemin (`selection_images`)

**Fichier** : `ocr/views.py` — `selection_images`

**Problème** : La protection contre le path traversal reposait sur
`.replace('..', '')`, ce qui ne protège pas contre `....` (qui devient `..`
après le remplacement) ni contre les variantes encodées.

**Correction** : Utilisation de `Path.resolve()` qui résout tous les `..`
avant toute comparaison, suivi d'une vérification stricte du préfixe par
rapport au répertoire de base.

```python
base_path = Path(base_dir).resolve()
requested = (base_path / current_path).resolve()
if not str(requested).startswith(str(base_path)):
    requested = base_path
```

---

### 2.4 — Lien `TranscriptionOCR.fiche` mis à jour après import

**Fichier** : `ingest/importation_service.py` — `finaliser_importation`

**Problème** : Le champ `TranscriptionOCR.fiche` (FK vers `FicheObservation`)
restait `null` même après un import réussi, rendant impossible la traçabilité
OCR → fiche depuis l'interface d'administration.

**Correction** : Après la création de la `FicheObservation`, un `.update()`
ciblé lie la `TranscriptionOCR` correspondante à la fiche produite.

```python
TranscriptionOCR.objects.filter(
    chemin_image=chemin_image, statut='succes'
).update(fiche=fiche)
```
