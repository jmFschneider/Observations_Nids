# Pilot - Gestion des chemins de fichiers

Ce document détaille la gestion des chemins de fichiers dans l'application pilot, notamment pour la navigation dans les répertoires d'images.

---

## Architecture de stockage

### Répertoire de base : `MEDIA_ROOT`

```python
# observations_nids/settings.py
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

**Chemin absolu** : `C:\Projets\observations_nids\media\` (Windows) ou `/app/media/` (Docker)

### Arborescence attendue

```
media/
├── Ancienne_fiche/           # Type de fiche (niveau 1)
│   ├── Sans_traitement/      # Type de traitement (niveau 2)
│   │   ├── fiche_001.jpg
│   │   ├── fiche_002.jpg
│   │   └── ...
│   ├── Traitement_1/         # Images avec prétraitement #1
│   │   └── ...
│   └── Traitement_2/         # Images avec prétraitement #2
│       └── ...
│
└── Nouvelle_fiche/
    ├── Sans_traitement/
    │   └── ...
    └── Traitement_1/
        └── ...
```

**Convention de nommage** :
- **Niveau 1** : Type de fiche (`Ancienne_fiche`, `Nouvelle_fiche`)
- **Niveau 2** : Type de traitement d'image (`Sans_traitement`, `Traitement_1`, `Traitement_2`, etc.)
- **Niveau 3** : Fichiers images (`.jpg`, `.jpeg`, `.png`)

---

## Navigation dans les répertoires

### Vue : `selection_repertoire_ocr`

**Fichier** : `pilot/views.py:33-151`

### Paramètres

| Paramètre GET | Type | Description | Exemple |
|---------------|------|-------------|---------|
| `path` | string | Chemin relatif depuis `MEDIA_ROOT` | `Ancienne_fiche/Sans_traitement` |

### Fonctionnement

```python
# 1. Récupérer le chemin depuis GET
current_path = request.GET.get('path', '')

# 2. Normaliser et sécuriser
safe_path = os.path.normpath(current_path).replace('..', '')

# 3. Construire le chemin complet
base_dir = settings.MEDIA_ROOT
full_current_path = os.path.join(base_dir, safe_path)

# 4. Vérifier que le chemin est dans MEDIA_ROOT
if not full_current_path.startswith(base_dir):
    safe_path = ''
    full_current_path = base_dir
```

### Sécurité : Prévention du directory traversal

**Attaque potentielle** :
```
GET /pilot/selection-repertoire/?path=../../etc/passwd
```

**Protection** :
1. `os.path.normpath()` : Résout `..` et `.`
2. `.replace('..', '')` : Supprime les `..` restants
3. `startswith(base_dir)` : Vérifie que le chemin final est dans `MEDIA_ROOT`

**Résultat** : Si chemin invalide → reset à `MEDIA_ROOT`

---

## Lister les sous-répertoires

### Code (`views.py:56-105`)

```python
directories = []
try:
    dir_list = [
        d for d in os.listdir(full_current_path)
        if os.path.isdir(os.path.join(full_current_path, d))
    ]

    for dir_name in dir_list:
        dir_path = os.path.join(full_current_path, dir_name)

        try:
            # Compter les sous-répertoires
            subdirs_count = len([
                d for d in os.listdir(dir_path)
                if os.path.isdir(os.path.join(dir_path, d))
            ])

            # Compter les fichiers images
            images_count = len([
                f for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))
                and f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ])

            directories.append({
                'name': dir_name,
                'subdirs_count': subdirs_count,
                'images_count': images_count,
            })
        except (OSError, PermissionError):
            directories.append({
                'name': dir_name,
                'subdirs_count': 0,
                'images_count': 0,
            })

    directories.sort(key=lambda x: str(x['name']).lower())
except (OSError, PermissionError):
    directories = []
    messages.error(request, "Impossible d'accéder à ce répertoire")
```

### Retour

```python
{
    'name': 'Sans_traitement',
    'subdirs_count': 0,        # Nombre de sous-répertoires
    'images_count': 42,        # Nombre d'images (.jpg, .jpeg, .png)
}
```

---

## Fil d'Ariane (Breadcrumb)

### Code (`views.py:108-115`)

```python
breadcrumb = []
if safe_path:
    parts = safe_path.split(os.sep)
    current = ''
    for part in parts:
        if part:
            current = os.path.join(current, part) if current else part
            breadcrumb.append({'name': part, 'path': current})
```

### Exemple

**Chemin** : `Ancienne_fiche/Sans_traitement`

**Résultat** :
```python
[
    {'name': 'Ancienne_fiche', 'path': 'Ancienne_fiche'},
    {'name': 'Sans_traitement', 'path': 'Ancienne_fiche/Sans_traitement'}
]
```

**Affichage** :
```
media > Ancienne_fiche > Sans_traitement
```

**Liens** :
- "Ancienne_fiche" → `?path=Ancienne_fiche`
- "Sans_traitement" → `?path=Ancienne_fiche/Sans_traitement`

---

## Construction des liens de navigation

### Template : `selection_repertoire_ocr.html`

**Code CORRECT** :
```html
<!-- Lien vers un sous-répertoire -->
<a href="?path={{ current_path }}{% if current_path %}/{% endif %}{{ directory.name }}">
    {{ directory.name }}
</a>
```

**Explication** :
- Si `current_path` est vide (`media/` racine) : `?path=Ancienne_fiche`
- Si `current_path="Ancienne_fiche"` : `?path=Ancienne_fiche/Sans_traitement`

**Code INCORRECT** (cause la perte d'accès aux sous-répertoires) :
```html
<!-- ❌ NE JAMAIS FAIRE ÇA -->
<a href="?path={{ directory.name }}">
    {{ directory.name }}
</a>
```

**Pourquoi** : On perd le chemin parent → impossible de descendre dans l'arborescence.

---

## Compter les images du répertoire actuel

### Code (`views.py:118-128`)

```python
try:
    image_count = len([
        f for f in os.listdir(full_current_path)
        if os.path.isfile(os.path.join(full_current_path, f))
        and f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
except (OSError, PermissionError):
    image_count = 0
```

**Extensions supportées** :
- `.jpg`, `.jpeg` (JPEG)
- `.png` (PNG)

**Non supporté** :
- `.tif`, `.tiff` (TIFF)
- `.bmp` (Bitmap)

---

## Déduction des métadonnées depuis le chemin

### Code (`views.py:131-139`)

```python
type_fiche = None
type_traitement = None

if safe_path:
    parts = safe_path.split(os.sep)
    if len(parts) >= 1:
        type_fiche = parts[0]  # Ex: "Ancienne_fiche"
    if len(parts) >= 2:
        type_traitement = parts[1]  # Ex: "Sans_traitement"
```

### Exemples

| Chemin | `type_fiche` | `type_traitement` |
|--------|--------------|-------------------|
| `""` (racine) | `None` | `None` |
| `Ancienne_fiche` | `"Ancienne_fiche"` | `None` |
| `Ancienne_fiche/Sans_traitement` | `"Ancienne_fiche"` | `"Sans_traitement"` |
| `Nouvelle_fiche/Traitement_1` | `"Nouvelle_fiche"` | `"Traitement_1"` |

**Usage** : Afficher le type de fiche et traitement dans l'interface pour confirmation avant lancement du batch.

---

## Analyse des correspondances image ↔ fiche

### Vue : `analyser_correspondances`

**Fichier** : `pilot/views.py:155-251`

### Fonctionnement

1. **Lister les images** du répertoire :
   ```python
   images = [
       f for f in os.listdir(full_path)
       if os.path.isfile(os.path.join(full_path, f))
       and f.lower().endswith(('.jpg', '.jpeg', '.png'))
   ]
   ```

2. **Extraire le nom de base** (sans extension) :
   ```python
   nom_base = Path(image_filename).stem
   # "fiche_042.jpg" → "fiche_042"
   ```

3. **Chercher la fiche correspondante** :
   ```python
   fiches = FicheObservation.objects.filter(chemin_image__contains=nom_base)
   ```

4. **Déterminer le statut** :
   - **1 fiche** → `trouvee`
   - **> 1 fiche** → `multiple` (conflit)
   - **0 fiche** → `non_trouvee`

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
      "fiches_possibles": [
        {"numero": 42, "espece": "Pinson des arbres", ...},
        {"numero": 142, "espece": "Mésange charbonnière", ...}
      ]
    },
    {
      "image": "fiche_999.jpg",
      "statut": "non_trouvee"
    }
  ]
}
```

---

## Gestion des chemins Windows vs Linux

### Problème

- **Windows** : Séparateur `\` (backslash)
- **Linux / Docker** : Séparateur `/` (forward slash)

### Solution

**Toujours utiliser `os.path.join()` ou `os.sep`** :

```python
# ✅ CORRECT : Portable
chemin = os.path.join(base_dir, 'Ancienne_fiche', 'Sans_traitement')

# ❌ INCORRECT : Spécifique Windows
chemin = base_dir + '\\Ancienne_fiche\\Sans_traitement'

# ❌ INCORRECT : Spécifique Linux
chemin = base_dir + '/Ancienne_fiche/Sans_traitement'
```

**Dans les templates** :
```python
# Django gère automatiquement la conversion
parts = safe_path.split(os.sep)  # Utilise le séparateur de l'OS
```

---

## Permissions de fichiers

### Gestion des erreurs

Toutes les opérations de fichiers sont protégées :

```python
try:
    files = os.listdir(directory)
except (OSError, PermissionError):
    files = []
    messages.error(request, "Impossible d'accéder à ce répertoire")
```

**Erreurs gérées** :
- `OSError` : Répertoire inexistant, disque plein, etc.
- `PermissionError` : Pas de droits de lecture

### Prévention

- **Développement** : S'assurer que l'utilisateur a accès à `media/`
- **Production / Docker** : Vérifier les permissions des volumes montés

```bash
# Docker : vérifier les permissions
docker exec observations_nids ls -la /app/media
```

---

## Tests recommandés

### Test 1 : Navigation multi-niveaux

```python
def test_navigation_sous_repertoires():
    """Vérifie la navigation dans les sous-répertoires"""
    # Niveau 1
    response = self.client.get('/pilot/selection-repertoire/')
    assert 'Ancienne_fiche' in response.content.decode()

    # Niveau 2
    response = self.client.get('/pilot/selection-repertoire/', {'path': 'Ancienne_fiche'})
    assert 'Sans_traitement' in response.content.decode()
    assert 'path=Ancienne_fiche/Sans_traitement' in response.content.decode()

    # Niveau 3 (images)
    response = self.client.get('/pilot/selection-repertoire/', {'path': 'Ancienne_fiche/Sans_traitement'})
    assert response.context['image_count'] > 0
```

### Test 2 : Sécurité (directory traversal)

```python
def test_directory_traversal_protection():
    """Vérifie la protection contre le directory traversal"""
    response = self.client.get('/pilot/selection-repertoire/', {'path': '../../etc/passwd'})
    # Devrait rediriger vers MEDIA_ROOT
    assert response.context['current_path'] == ''
```

### Test 3 : Fil d'Ariane

```python
def test_breadcrumb():
    """Vérifie le fil d'Ariane"""
    response = self.client.get('/pilot/selection-repertoire/', {'path': 'Ancienne_fiche/Sans_traitement'})
    breadcrumb = response.context['breadcrumb']
    assert len(breadcrumb) == 2
    assert breadcrumb[0] == {'name': 'Ancienne_fiche', 'path': 'Ancienne_fiche'}
    assert breadcrumb[1] == {'name': 'Sans_traitement', 'path': 'Ancienne_fiche/Sans_traitement'}
```

---

## Checklist : Modification de la navigation

Avant de modifier le code de navigation :

- [ ] Lire [gotchas.md](gotchas.md#probleme-perte-acces-sous-repertoires)
- [ ] Vérifier que les liens incluent `current_path`
- [ ] Tester la navigation sur 3 niveaux
- [ ] Vérifier le fil d'Ariane
- [ ] Tester avec un chemin contenant `..`
- [ ] Vérifier les permissions de fichiers

---

## Voir aussi

- **[Pièges à éviter](gotchas.md#probleme-perte-acces-sous-repertoires)** - Problème de perte d'accès aux sous-répertoires
- **[Vues et logique](views.md)** - Détails des vues

---

*Dernière mise à jour : 2025-12-27*
