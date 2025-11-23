# Stratégie de développement : Préparation d'images pour OCR

**Date de création** : 2025-11-23
**Auteur** : Documentation technique du projet
**Statut** : Proposition - En attente de validation

---

## Table des matières

1. [Contexte et objectifs](#1-contexte-et-objectifs)
2. [Architecture technique proposée](#2-architecture-technique-proposée)
3. [Stratégie Git et gestion des branches](#3-stratégie-git-et-gestion-des-branches)
4. [Gestion de la base de données](#4-gestion-de-la-base-de-données)
5. [Plan d'implémentation par phases](#5-plan-dimplémentation-par-phases)
6. [Workflow de traitement des images](#6-workflow-de-traitement-des-images)
7. [Portage du code Python existant](#7-portage-du-code-python-existant)
8. [Décisions à prendre](#8-décisions-à-prendre)

---

## 1. Contexte et objectifs

### Situation actuelle

- **Volume** : Plusieurs dizaines de milliers de fiches d'observation à traiter
- **Format source** : Scans JPEG (recto + verso) des fiches manuscrites
- **Processus actuel** : Traitement hors projet avec risque de perte de traçabilité
- **Code existant** : Script Python (`tmp/pdf_Conversion.py`) avec logique de fusion et prétraitement

### Objectifs

1. ✅ Intégrer le traitement d'images dans le projet Django
2. ✅ Maintenir la traçabilité complète (fichiers sources → traitements → résultats)
3. ✅ Traiter les images localement (navigateur) sans surcharger le serveur
4. ✅ Restreindre l'accès au poste de préparation local
5. ✅ Optimiser les images pour l'OCR (contraste, débruitage, binarisation)

### Contraintes

- Traitement sur poste fixe local
- Gros volume de données (50 000+ fiches)
- Besoin de continuer à travailler sur `main` en parallèle
- Éviter la duplication de la base de données si possible

---

## 2. Architecture technique proposée

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│  Poste fixe (Navigateur moderne)                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Interface Django Web                                   │  │
│  │  - Upload fichiers recto/verso                        │  │
│  │  - Prévisualisation                                   │  │
│  │  - Contrôles de traitement (rotation, contraste...)   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ JavaScript (traitement côté client)                    │  │
│  │  - Canvas API : fusion recto/verso                    │  │
│  │  - OpenCV.js : prétraitements avancés                 │  │
│  │  - Compression optimisée pour OCR                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Upload vers Django (fichier fusionné + métadonnées)   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Serveur Django                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Vue Django : Enregistrement PreparationImage          │  │
│  │  - Sauvegarde fichier fusionné                        │  │
│  │  - Stockage métadonnées JSON                          │  │
│  │  - Création enregistrement BDD                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Workflow OCR (existant)                                │  │
│  │  - Lecture PreparationImage                           │  │
│  │  - Lancement OCR                                      │  │
│  │  - Création TranscriptionBrute                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Nouveau modèle Django : `PreparationImage`

```python
# ingest/models.py

class PreparationImage(models.Model):
    """
    Stocke l'historique de préparation des images avant OCR.
    Traçabilité complète des opérations de traitement.
    """
    # Fichiers
    fichier_brut_recto = models.CharField(
        max_length=255,
        help_text="Chemin du scan brut recto"
    )
    fichier_brut_verso = models.CharField(
        max_length=255,
        help_text="Chemin du scan brut verso"
    )
    fichier_fusionne = models.ImageField(
        upload_to='prepared_images/%Y/',
        help_text="Image fusionnée recto+verso optimisée pour OCR"
    )

    # Métadonnées de traitement
    operations_effectuees = models.JSONField(
        help_text="Liste des opérations de traitement (rotation, crop, contraste, etc.)"
    )

    # Traçabilité
    operateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True
    )
    date_preparation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    # Lien vers la transcription (une fois l'OCR effectué)
    transcription = models.OneToOneField(
        'TranscriptionBrute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preparation'
    )

    class Meta:
        verbose_name = "Préparation d'image"
        verbose_name_plural = "Préparations d'images"
        ordering = ['-date_preparation']

    def __str__(self):
        return f"Préparation {self.id} - {self.date_preparation.strftime('%Y-%m-%d')}"
```

### Modification du modèle existant : `TranscriptionBrute`

```python
# Ajout optionnel d'un champ pour lien inverse (pas obligatoire grâce au related_name)
class TranscriptionBrute(models.Model):
    # Champs existants...
    fichier_source = models.CharField(max_length=255, unique=True)
    json_brut = models.JSONField()
    date_importation = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    # Nouveau champ (optionnel, pour référence bidirectionnelle explicite)
    preparation_source = models.ForeignKey(
        'ingest.PreparationImage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Préparation d'image source (si applicable)"
    )
```

### Structure JSON des métadonnées

```json
{
  "fichier_recto_original": "scans/2024/fiche_001_recto.jpg",
  "fichier_verso_original": "scans/2024/fiche_001_verso.jpg",
  "operations": [
    {
      "type": "rotation",
      "cible": "recto",
      "valeur": 90,
      "timestamp": "2024-11-23T14:30:00Z"
    },
    {
      "type": "crop_verso",
      "largeur_conservee": "55%",
      "raison": "Verso contient seulement partie gauche utile"
    },
    {
      "type": "clahe",
      "parametres": {
        "clipLimit": 2.0,
        "tileGridSize": [16, 16]
      }
    },
    {
      "type": "denoising",
      "methode": "fastNlMeansDenoising",
      "parametres": {
        "h": 20,
        "templateWindowSize": 10,
        "searchWindowSize": 30
      }
    },
    {
      "type": "binarisation",
      "methode": "adaptiveThreshold",
      "parametres": {
        "blockSize": 11,
        "C": 2
      }
    }
  ],
  "qualite_finale": {
    "poids_ko": 850,
    "dimensions": [2480, 7016],
    "format": "jpeg",
    "compression": 92
  }
}
```

### Stack technique

| Composant | Technologie | Usage |
|-----------|-------------|-------|
| **Fusion d'images** | Canvas API (natif) | Assemblage recto + verso |
| **Redimensionnement** | Pica.js | Redimensionnement haute qualité |
| **Prétraitements OCR** | OpenCV.js (WebAssembly) | CLAHE, débruitage, binarisation |
| **Interface** | Django Templates + JavaScript | Interface web de traitement |
| **Stockage** | Django ImageField + JSONField | Sauvegarde images et métadonnées |

---

## 3. Stratégie Git et gestion des branches

### Nom de branche recommandé

```bash
feature/preparation-images-ocr
```

**Justification** :
- ✅ Cohérent avec la convention existante (`feature/*`)
- ✅ Descriptif : préparation d'images avant OCR
- ✅ Différencié du module `ingest` existant

### Création de la branche

```bash
# 1. S'assurer d'être à jour sur main
git checkout main
git pull origin main

# 2. Créer la nouvelle branche
git checkout -b feature/preparation-images-ocr

# 3. Pousser la branche sur GitHub
git push -u origin feature/preparation-images-ocr
```

### Workflow : Basculer entre branches

```bash
# Travailler sur la nouvelle fonctionnalité
git checkout feature/preparation-images-ocr

# Besoin urgent de corriger un bug sur main
git stash                              # Sauvegarder le travail en cours
git checkout main
git checkout -b fix/bug-urgent
# ... corrections ...
git add .
git commit -m "fix: Correction bug urgent"
git push -u origin fix/bug-urgent
# Créer PR vers main sur GitHub

# Retourner sur la fonctionnalité en cours
git checkout feature/preparation-images-ocr
git stash pop                          # Récupérer le travail sauvegardé
```

### Synchronisation avec main

Si des modifications sont apportées à `main` pendant le développement, synchroniser régulièrement :

```bash
# Sur votre branche feature
git checkout feature/preparation-images-ocr

# Récupérer les dernières modifications de main
git fetch origin main

# Option 1 : Rebaser (recommandé, historique linéaire)
git rebase origin/main
git push --force-with-lease origin feature/preparation-images-ocr

# Option 2 : Fusionner (alternative)
git merge origin/main
git push origin feature/preparation-images-ocr
```

---

## 4. Gestion de la base de données

### Solution recommandée : Une seule BDD avec migrations additives

**Principe** : Utiliser `db_local.sqlite3` existante, avec migrations **exclusivement additives** (non destructives).

#### Règles strictes

✅ **AUTORISÉ** (compatible entre branches) :
- ✅ Ajouter un nouveau modèle (`PreparationImage`)
- ✅ Ajouter un nouveau champ avec `null=True` ou `default`
- ✅ Ajouter un index
- ✅ Créer de nouvelles tables
- ✅ Ajouter des relations optionnelles (ForeignKey avec `null=True`)

❌ **INTERDIT** (cassera l'autre branche) :
- ❌ Supprimer un modèle existant
- ❌ Renommer un champ
- ❌ Modifier un type de champ
- ❌ Ajouter un champ obligatoire sans `default`
- ❌ Supprimer un champ

#### Workflow avec une seule BDD

```bash
# Sur feature/preparation-images-ocr
python manage.py makemigrations
python manage.py migrate
# → Crée la table ingest_preparationimage

# Basculer vers main
git checkout main
python manage.py runserver
# → La table ingest_preparationimage existe toujours dans la BDD
# → Mais le modèle n'existe pas dans le code
# → Pas de problème ! Django l'ignore simplement

# Retour sur feature/preparation-images-ocr
git checkout feature/preparation-images-ocr
python manage.py runserver
# → La table est toujours là, tout fonctionne normalement
```

#### Avantages

- ✅ Simple : aucune duplication
- ✅ Pas de script de synchronisation nécessaire
- ✅ Les données de test restent disponibles entre branches
- ✅ Workflow transparent

#### Points d'attention

- ⚠️ Respecter strictement les règles de migrations additives
- ⚠️ Tables "orphelines" temporaires sur `main` (ignorées par Django)
- ⚠️ Ne pas faire de `python manage.py migrate --fake-initial` sur `main`

### Alternative : Deux BDD distinctes (si nécessaire)

Si vous avez besoin de faire des modifications incompatibles, utilisez deux BDD distinctes.

#### Configuration automatique

```python
# observations_nids/settings_local.py

import subprocess
from pathlib import Path

def get_current_branch():
    """Détecte automatiquement la branche Git courante."""
    try:
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent.parent
        ).decode('utf-8').strip()
        return branch
    except:
        return 'main'

CURRENT_BRANCH = get_current_branch()

# Choisir la BDD selon la branche
if 'preparation-images' in CURRENT_BRANCH:
    DB_NAME = 'db_preparation_images.sqlite3'
    print(f"🔧 Branche détectée: {CURRENT_BRANCH} → BDD: {DB_NAME}")
else:
    DB_NAME = 'db_local.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / DB_NAME,
    }
}
```

**Note** : Cette approche n'est recommandée que si les migrations deviennent incompatibles.

---

## 5. Plan d'implémentation par phases

### Phase 1 : Base Django (Backend)

**Durée estimée** : 1-2h

- [ ] Créer le modèle `PreparationImage` dans `ingest/models.py`
- [ ] Créer les migrations : `python manage.py makemigrations`
- [ ] Appliquer les migrations : `python manage.py migrate`
- [ ] Créer la vue Django `preparer_images_view` dans `ingest/views/preparation.py`
- [ ] Créer l'URL route dans `ingest/urls.py`
- [ ] Ajouter la restriction réseau local (décorateur `@local_network_only`)
- [ ] Enregistrer le modèle dans l'admin Django

### Phase 2 : Interface web basique (Frontend)

**Durée estimée** : 2-3h

- [ ] Créer le template HTML : `ingest/templates/ingest/preparer_images.html`
- [ ] Interface d'upload recto/verso (input file multiple)
- [ ] JavaScript : détection automatique des paires recto/verso
- [ ] JavaScript : fusion simple via Canvas API
- [ ] JavaScript : recadrage verso (5.5/10 de largeur)
- [ ] Prévisualisation de l'image fusionnée
- [ ] Upload vers Django avec métadonnées (FormData + fetch)
- [ ] Affichage de la progression (fiche N/Total)

### Phase 3 : Prétraitements avancés (Optimisation OCR)

**Durée estimée** : 3-4h + tests

- [ ] Intégrer OpenCV.js (CDN ou fichier local)
- [ ] Porter la fonction `preprocess_image()` en JavaScript :
  - [ ] CLAHE (amélioration contraste adaptatif)
  - [ ] Débruitage (fastNlMeansDenoising)
  - [ ] Binarisation adaptative (adaptiveThreshold)
- [ ] Créer des contrôles interactifs (sliders) pour ajuster les paramètres
- [ ] Afficher une comparaison avant/après traitement
- [ ] Permettre de désactiver certains traitements
- [ ] Mesurer l'impact sur la qualité OCR (tests)

### Phase 4 : Production et Optimisation

**Durée estimée** : 2-3h

- [ ] Traitement par lot avec file d'attente JavaScript
- [ ] Traitement parallèle (5-10 fiches simultanées)
- [ ] Sauvegarde automatique de l'état toutes les 100 fiches
- [ ] Gestion des erreurs et reprise sur échec
- [ ] Statistiques de progression détaillées
- [ ] Export des métadonnées pour analyse qualité OCR
- [ ] Documentation utilisateur
- [ ] Tests de charge (simuler 1000+ fiches)

---

## 6. Workflow de traitement des images

### Mode 1 : Flux continu avec validation manuelle

```
1. Accès interface : http://localhost:8000/ingest/preparer-images/

2. Sélection dossier contenant les paires recto/verso
   → Détection automatique : 001_recto.jpg + 001_verso.jpg

3. Interface affiche la première fiche :
   ┌─────────────────────────────────────┐
   │ Fiche 1/50000                       │
   │ Recto : 001_recto.jpg ✓             │
   │ Verso : 001_verso.jpg ✓             │
   │                                     │
   │ [Aperçu fusion]                     │
   │                                     │
   │ Ajustements :                       │
   │ Rotation recto : [0°] [90°] [-90°]  │
   │ Contraste      : [───●─────] +15%   │
   │                                     │
   │ [Ignorer] [Valider et suivante]     │
   └─────────────────────────────────────┘

4. Clic "Valider" :
   → Traitement + Upload vers Django
   → Sauvegarde dans PreparationImage
   → Passage automatique à la fiche 2

5. Répéter jusqu'à fiche 50 000
```

**Avantages** :
- ✅ Contrôle visuel fiche par fiche
- ✅ Ajustements manuels si nécessaire
- ✅ Flux continu sans fermer l'interface

**Vitesse** : ~1 fiche/seconde = 50 000 fiches en ~14h

### Mode 2 : Traitement automatique par lot

```
1. Sélection dossier et mode "Automatique"

2. Interface de progression :
   ┌─────────────────────────────────────┐
   │ Traitement en cours...              │
   │ ████████░░░░░░░░ 45% (22500/50000) │
   │                                     │
   │ Traitées    : 22 450               │
   │ Erreurs     : 50 (voir liste)      │
   │ Restantes   : 27 500               │
   │ Temps restant : ~6h30              │
   │                                     │
   │ [Pause] [Arrêter] [Voir erreurs]   │
   └─────────────────────────────────────┘

3. Traitement parallèle :
   → 5-10 fiches traitées simultanément
   → Sauvegarde auto toutes les 100 fiches
   → Erreurs mises de côté pour révision

4. Révision des erreurs à la fin
```

**Avantages** :
- ✅ Très rapide (5-10 fiches/seconde)
- ✅ Peut tourner sans intervention
- ✅ Reprise automatique en cas d'interruption

**Vitesse** : ~5 fiches/seconde = 50 000 fiches en ~3h

---

## 7. Portage du code Python existant

### Code source : `tmp/pdf_Conversion.py`

Le fichier contient deux fonctions principales à porter en JavaScript :

#### 7.1. Fonction `preprocess_image()` - Prétraitement OCR

**Code Python original** :

```python
def preprocess_image(image):
    """Applique un prétraitement sur l'image pour améliorer la reconnaissance de caractères."""
    img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
    img_clahe = clahe.apply(img_gray)
    img_nlm = cv2.fastNlMeansDenoising(img_clahe, None, 20, 10, 30)
    img_adaptive_gauss = cv2.adaptiveThreshold(img_nlm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY, 11, 2)
    return img_adaptive_gauss
```

**Port JavaScript avec OpenCV.js** :

```javascript
function preprocessImage(imageCanvas) {
  // 1. Charger l'image dans une matrice OpenCV
  let mat = cv.imread(imageCanvas);

  // 2. Conversion en niveaux de gris
  cv.cvtColor(mat, mat, cv.COLOR_RGBA2GRAY);

  // 3. CLAHE (amélioration contraste adaptatif)
  let clahe = new cv.CLAHE(2.0, new cv.Size(16, 16));
  clahe.apply(mat, mat);

  // 4. Débruitage
  cv.fastNlMeansDenoising(mat, mat, 20, 10, 30);

  // 5. Binarisation adaptative
  cv.adaptiveThreshold(
    mat, mat, 255,
    cv.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv.THRESH_BINARY,
    11, 2
  );

  // 6. Afficher le résultat
  cv.imshow('outputCanvas', mat);

  // 7. Nettoyer la mémoire
  mat.delete();
  clahe.delete();

  return document.getElementById('outputCanvas');
}
```

#### 7.2. Fonction `combine_recto_verso()` - Fusion recto/verso

**Code Python original** :

```python
def combine_recto_verso(processed_dir, final_dir):
    # ... lecture fichiers ...

    # Extrait la partie gauche de l'image verso (5.5/10 de la largeur)
    height_verso, width_verso = verso_img.shape[:2]
    crop_width = int(width_verso * 5.5/10)
    verso_left = verso_img[:, 0:crop_width]

    # Créer une nouvelle image verso avec la même largeur que recto
    height_recto, width_recto = recto_img.shape[:2]
    verso_resized = np.zeros((height_verso, width_recto, 3), dtype=np.uint8) + 255

    # Copier la partie gauche du verso
    copy_width = min(crop_width, width_recto)
    verso_resized[:, 0:copy_width] = verso_left[:, 0:copy_width]

    # Combine verticalement
    combined_img = np.vstack((recto_img, verso_resized))
```

**Port JavaScript avec Canvas API** :

```javascript
function fusionnerRectoVerso(rectoImg, versoImg) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  // Dimensions
  const rectoWidth = rectoImg.width;
  const rectoHeight = rectoImg.height;
  const versoWidth = versoImg.width;
  const versoHeight = versoImg.height;

  // Recadrer verso : 5.5/10 de la largeur (partie gauche)
  const cropWidth = Math.floor(versoWidth * 5.5 / 10);

  // Canvas final : largeur = recto, hauteur = recto + verso
  canvas.width = rectoWidth;
  canvas.height = rectoHeight + versoHeight;

  // Fond blanc
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Dessiner recto en haut
  ctx.drawImage(rectoImg, 0, 0);

  // Dessiner verso recadré en bas
  const copyWidth = Math.min(cropWidth, rectoWidth);
  ctx.drawImage(
    versoImg,
    0, 0, copyWidth, versoHeight,  // Source (partie gauche du verso)
    0, rectoHeight, copyWidth, versoHeight  // Destination (en bas du canvas)
  );

  return canvas;
}
```

### Points d'attention pour le portage

1. **Chargement d'OpenCV.js** : ~8 MB, préférer le chargement en CDN avec fallback local
2. **Mémoire** : Bien appeler `.delete()` sur les objets OpenCV pour éviter les fuites mémoire
3. **Performance** : OpenCV.js est compilé en WebAssembly, performance proche du natif
4. **Compatibilité** : Tester sur Chrome, Firefox et Edge (Safari peut être plus lent)

---

## 8. Décisions à prendre

### 8.1. Stratégie de branche et BDD

- [ ] **Validation** : Accepter l'approche `feature/preparation-images-ocr` + BDD unique ?
- [ ] **Alternative** : Préférer deux BDD distinctes pour isolation totale ?

### 8.2. Mode de traitement prioritaire

- [ ] **Mode 1** : Flux continu avec validation manuelle (Phase 2) ?
- [ ] **Mode 2** : Traitement automatique par lot (Phase 4) ?
- [ ] **Les deux** : Implémenter les deux modes avec sélection utilisateur ?

### 8.3. Prétraitements OCR

- [ ] **Activer par défaut** : CLAHE + Débruitage + Binarisation ?
- [ ] **Optionnel** : Laisser l'utilisateur activer/désactiver chaque traitement ?
- [ ] **Tests nécessaires** : Comparer qualité OCR avec/sans prétraitement ?

### 8.4. Restriction d'accès

- [ ] **Réseau local uniquement** : Restreindre à 127.0.0.1 et 192.168.x.x ?
- [ ] **Authentification renforcée** : Rôle spécifique "Préparateur" ?
- [ ] **Pas de restriction** : Accessible à tous les utilisateurs authentifiés ?

### 8.5. Gestion des erreurs

- [ ] **Arrêt sur erreur** : Stopper le traitement et signaler ?
- [ ] **Continuer** : Ignorer les erreurs et les lister à la fin ?
- [ ] **Intervention** : Permettre correction manuelle immédiate ?

---

## Prochaines étapes

### Commandes pour démarrer

```bash
# 1. Créer la branche
git checkout main
git pull origin main
git checkout -b feature/preparation-images-ocr
git push -u origin feature/preparation-images-ocr

# 2. Créer le modèle PreparationImage (à faire manuellement)
# Éditer : ingest/models.py

# 3. Créer les migrations
python manage.py makemigrations

# 4. Appliquer les migrations
python manage.py migrate

# 5. Commit initial
git add .
git commit -m "feat: Initialisation fonctionnalité préparation images OCR

- Ajout modèle PreparationImage
- Migrations initiales
- Architecture définie dans docs/developpeurs/guides/decision_technique/preparation_images_ocr.md"

git push origin feature/preparation-images-ocr
```

### Ordre d'implémentation recommandé

1. **Phase 1** : Base Django (modèle + migrations)
2. **Phase 2** : Interface basique (upload + fusion simple)
3. **Tests** : Valider le workflow sur 10-20 fiches
4. **Phase 3** : Prétraitements avancés (OpenCV.js)
5. **Tests OCR** : Comparer qualité avec/sans traitement
6. **Phase 4** : Optimisation (traitement parallèle)
7. **Documentation utilisateur** : Guide d'utilisation complet

---

## Références

- **Code existant** : `tmp/pdf_Conversion.py`
- **Documentation OCR** : `docs/developpeurs/architecture/domaines/03_ocr_ingestion.md`
- **Workflow Git** : `docs/developpeurs/guides/development_process/01_git.md`
- **OpenCV.js** : https://docs.opencv.org/4.x/d5/d10/tutorial_js_root.html
- **Canvas API** : https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API

---

**Document à valider et commenter avant de démarrer l'implémentation.**
