# Pilot - Vues et logique métier

Ce fichier documente les vues de l'application pilot.

**Fichier source** : `pilot/views.py`

---

## Décorateur : `@transcription_required`

Toutes les vues pilot sont protégées par ce décorateur :

```python
from observations.decorators import transcription_required

@transcription_required
def ma_vue(request):
    # ...
```

**Rôle** : Restreindre l'accès aux utilisateurs autorisés (permissions transcription).

---

## Vue : `optimisation_ocr_home`

**Fichier** : `views.py:28-30`

### Responsabilité
Page d'accueil de l'optimisation OCR.

### Route
```
GET /pilot/optimisation-ocr/
```

### Template
`pilot/optimisation_ocr_home.html`

### Logique
Vue simple sans logique métier.

---

## Vue : `selection_repertoire_ocr`

**Fichier** : `views.py:33-151`

### Responsabilité
Navigation dans les répertoires d'images (`media/`) avec :
- Affichage des sous-répertoires et statistiques
- Fil d'Ariane (breadcrumb)
- Comptage des images
- Déduction automatique du type de fiche et traitement

### Route
```
GET /pilot/optimisation-ocr/selection-repertoire/
```

### Paramètres GET

| Paramètre | Type | Description | Défaut |
|-----------|------|-------------|--------|
| `path` | string | Chemin relatif depuis `MEDIA_ROOT` | `""` (racine) |

### Template
`pilot/selection_repertoire_ocr.html`

### Contexte retourné

```python
{
    'directories': [  # Liste des sous-répertoires
        {
            'name': 'Sans_traitement',
            'subdirs_count': 0,
            'images_count': 42,
        },
        # ...
    ],
    'current_path': 'Ancienne_fiche',  # Chemin actuel (relatif)
    'breadcrumb': [  # Fil d'Ariane
        {'name': 'Ancienne_fiche', 'path': 'Ancienne_fiche'},
    ],
    'image_count': 0,  # Nombre d'images dans le répertoire actuel
    'parent_path': None,  # Chemin du répertoire parent (pour "Retour")
    'type_fiche': 'Ancienne_fiche',  # Type déduit (niveau 1)
    'type_traitement': None,  # Type déduit (niveau 2)
}
```

### Logique détaillée

Voir **[Gestion des fichiers](file_handling.md)** pour tous les détails.

#### 1. Sécurisation du chemin
```python
safe_path = os.path.normpath(current_path).replace('..', '')
full_current_path = os.path.join(base_dir, safe_path)

if not full_current_path.startswith(base_dir):
    safe_path = ''
    full_current_path = base_dir
```

#### 2. Listage des sous-répertoires
```python
directories = []
for dir_name in os.listdir(full_current_path):
    if os.path.isdir(os.path.join(full_current_path, dir_name)):
        # Compter sous-répertoires et images
        directories.append({
            'name': dir_name,
            'subdirs_count': ...,
            'images_count': ...,
        })
```

#### 3. Construction du fil d'Ariane
```python
breadcrumb = []
parts = safe_path.split(os.sep)
current = ''
for part in parts:
    current = os.path.join(current, part) if current else part
    breadcrumb.append({'name': part, 'path': current})
```

### Points d'attention

⚠️ **Critique** : Ne jamais modifier sans lire [gotchas.md](gotchas.md#probleme-perte-acces-sous-repertoires)

---

## Vue : `analyser_correspondances`

**Fichier** : `views.py:155-251`

### Responsabilité
Analyse les images d'un répertoire et trouve les fiches FicheObservation correspondantes.

### Route
```
POST /pilot/optimisation-ocr/analyser-correspondances/
```

### Paramètres POST

| Paramètre | Type | Description |
|-----------|------|-------------|
| `repertoire` | string | Chemin relatif du répertoire à analyser |

### Retour JSON

```json
{
  "success": true,
  "total_images": 42,
  "nb_trouvees": 38,
  "nb_multiples": 2,
  "nb_non_trouvees": 2,
  "correspondances": [
    {
      "image": "fiche_001.jpg",
      "statut": "trouvee",
      "fiche_id": 123,
      "fiche_info": {
        "numero": 123,
        "espece": "Mésange bleue",
        "annee": 2023,
        "observateur": "jean.dupont",
        "chemin_image": "/media/Ancienne_fiche/Sans_traitement/fiche_001.jpg"
      }
    },
    {
      "image": "fiche_042.jpg",
      "statut": "multiple",
      "fiches_possibles": [...]
    },
    {
      "image": "fiche_999.jpg",
      "statut": "non_trouvee"
    }
  ]
}
```

### Logique

1. **Lister les images** (`.jpg`, `.jpeg`, `.png`)
2. **Extraire le nom de base** (sans extension)
3. **Chercher les fiches** avec `chemin_image__contains=nom_base`
4. **Déterminer le statut** :
   - 1 fiche → `trouvee`
   - Plusieurs fiches → `multiple`
   - Aucune fiche → `non_trouvee`

### Exemple d'utilisation (JavaScript)

```javascript
fetch('/pilot/optimisation-ocr/analyser-correspondances/', {
    method: 'POST',
    body: new FormData([['repertoire', 'Ancienne_fiche/Sans_traitement']])
})
.then(response => response.json())
.then(data => {
    console.log(`${data.nb_trouvees} images correspondantes trouvées`);
});
```

---

## Vue : `lancer_transcription_batch`

**Fichier** : `views.py:255-328`

### Responsabilité
Lance une tâche Celery pour transcrire en batch les images d'un ou plusieurs répertoires avec un ou plusieurs modèles OCR.

### Route
```
POST /pilot/optimisation-ocr/lancer-batch/
```

### Paramètres POST

| Paramètre | Type | Description |
|-----------|------|-------------|
| `directories` | JSON array | Liste des répertoires à traiter (objets `{path, name}`) |
| `modeles_ocr` | JSON array | Liste des modèles OCR à utiliser (ex: `["gemini_2.5_pro", "gemini_3_flash"]`) |

### Exemple de requête

```javascript
const formData = new FormData();
formData.append('directories', JSON.stringify([
    {path: 'Ancienne_fiche/Sans_traitement', name: 'Sans_traitement'}
]));
formData.append('modeles_ocr', JSON.stringify(['gemini_2.5_pro', 'gemini_3_flash']));

fetch('/pilot/optimisation-ocr/lancer-batch/', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Tâche lancée:', data.task_id);
});
```

### Retour JSON (succès)

```json
{
  "success": true,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Traitement batch démarré",
  "progress_url": "/pilot/optimisation-ocr/verifier-progression/"
}
```

### Logique

1. **Valider les paramètres** (directories et modeles_ocr)
2. **Parser les JSON**
3. **Lancer la tâche Celery** :
   ```python
   task = process_batch_transcription_task.delay(directories, modeles_ocr)
   ```
4. **Stocker l'ID en session** pour le suivi de progression
5. **Retourner l'ID de tâche**

### Gestion d'erreurs

```python
# Paramètres manquants
{'error': 'Paramètres manquants (directories ou modeles_ocr)'}  # 400

# JSON invalide
{'error': 'Format JSON invalide pour directories'}  # 400

# Liste vide
{'error': 'La liste des répertoires est vide ou invalide'}  # 400

# Erreur serveur
{'error': 'Erreur serveur: [message]'}  # 500
```

---

## Vue : `check_batch_progress`

**Fichier** : `views.py:332-394`

### Responsabilité
Endpoint AJAX pour vérifier la progression du traitement batch en temps réel.

### Route
```
GET /pilot/optimisation-ocr/verifier-progression/
```

### Retour JSON

Dépend du statut de la tâche Celery :

#### PENDING (en attente)
```json
{
  "status": "PENDING",
  "task_id": "...",
  "message": "Tâche en attente de démarrage...",
  "percent": 0
}
```

#### STARTED / PROGRESS (en cours)
```json
{
  "status": "PROGRESS",
  "task_id": "...",
  "percent": 65,
  "processed": 26,
  "total": 40,
  "current_file": "fiche_026.jpg",
  "current_directory": "Ancienne_fiche/Sans_traitement",
  "message": "Traitement en cours... (26/40)"
}
```

#### SUCCESS (terminé)
```json
{
  "status": "SUCCESS",
  "task_id": "...",
  "percent": 100,
  "message": "Traitement terminé avec succès",
  "redirect": "/pilot/optimisation-ocr/resultats/",
  "force_redirect": true,
  "total_images": 40,
  "total_success": 38,
  "total_errors": 2,
  "duration": 245.3
}
```

#### FAILURE (échec)
```json
{
  "status": "FAILURE",
  "task_id": "...",
  "percent": 0,
  "error": "Message d'erreur détaillé",
  "message": "Une erreur s'est produite lors du traitement batch."
}
```

### Logique

1. **Récupérer l'ID de tâche** depuis la session
2. **Interroger Celery** via `AsyncResult(task_id)`
3. **Retourner le statut et les infos de progression**

### Polling JavaScript (exemple)

```javascript
function pollProgress() {
    fetch('/pilot/optimisation-ocr/verifier-progression/')
        .then(response => response.json())
        .then(data => {
            updateProgressBar(data.percent);

            if (data.status === 'SUCCESS') {
                window.location.href = data.redirect;
            } else if (data.status !== 'FAILURE') {
                setTimeout(pollProgress, 2000);  // Re-poll après 2s
            }
        });
}
```

---

## Vue : `batch_results`

**Fichier** : `views.py:398-445`

### Responsabilité
Affiche les résultats du traitement batch.

### Route
```
GET /pilot/optimisation-ocr/resultats/
GET /pilot/optimisation-ocr/resultats/?tracking=true
```

### Paramètres GET

| Paramètre | Type | Description |
|-----------|------|-------------|
| `tracking` | bool | `true` si mode suivi en temps réel (avant fin de tâche) |

### Template
`pilot/batch_results.html`

### Contexte retourné

```python
{
    'results': {  # Résultats stockés en session
        'total_directories': 1,
        'total_models': 2,
        'total_images': 40,
        'total_success': 38,
        'total_errors': 2,
        'success_rate': 95.0,
        'duration': 245.3,
        'modeles_ocr': ['gemini_2.5_pro', 'gemini_3_flash'],
        'results': [  # Détails par répertoire
            {
                'directory': 'Ancienne_fiche/Sans_traitement',
                'images_processed': 40,
                'success': 38,
                'errors': 2,
            }
        ]
    },
    'config': {  # Configuration du batch
        'directories': [...],
        'modeles_ocr': [...],
        'start_time': '2025-12-27T10:30:00',
    },
    'modeles_ocr': ['gemini_2.5_pro', 'gemini_3_flash'],
    'modeles_ocr_display': 'gemini_2.5_pro, gemini_3_flash',
    'total_directories': 1,
    'total_models': 2,
    'total_images': 40,
    'total_success': 38,
    'total_errors': 2,
    'success_rate': 95.0,
    'duration': 245.3,
    'duration_per_image': 6.1,
    'directory_results': [...]
}
```

### Logique

1. **Vérifier si mode tracking** (`?tracking=true`)
2. **Récupérer les résultats** depuis la session
3. **Afficher le template** avec les résultats ou un message de suivi

---

## Résumé des vues

| Vue | Route | Méthode | Rôle |
|-----|-------|---------|------|
| `optimisation_ocr_home` | `/pilot/optimisation-ocr/` | GET | Page d'accueil |
| `selection_repertoire_ocr` | `/pilot/optimisation-ocr/selection-repertoire/` | GET | Navigation dans `media/` |
| `analyser_correspondances` | `/pilot/optimisation-ocr/analyser-correspondances/` | POST | Matching image ↔ fiche |
| `lancer_transcription_batch` | `/pilot/optimisation-ocr/lancer-batch/` | POST | Lance la tâche Celery |
| `check_batch_progress` | `/pilot/optimisation-ocr/verifier-progression/` | GET | Polling de progression (AJAX) |
| `batch_results` | `/pilot/optimisation-ocr/resultats/` | GET | Affichage des résultats |

---

## Voir aussi

- **[Gestion des fichiers](file_handling.md)** - Détails sur `selection_repertoire_ocr`
- **[Workflow OCR](ocr_workflow.md)** - Pipeline complet
- **[Pièges à éviter](gotchas.md)** - Erreurs courantes

---

*Dernière mise à jour : 2025-12-27*
