# Préparation d'images pour OCR

Ce document décrit l'utilisation du script `prepare_images_local.py` pour le traitement local d'images avant import dans Django.

## 📋 Vue d'ensemble

Le workflow de traitement des images se fait en **3 étapes** :

```
1. TRAITEMENT LOCAL (ton PC puissant)
   python scripts/prepare_images_local.py

2. TRANSFERT (manuel ou automatisé)
   Copier prepared/ vers le serveur

3. IMPORT DJANGO (Raspberry Pi)
   Interface web → "Importer un lot préparé"
```

---

## 🚀 Script principal : `prepare_images_local.py`

### Installation des dépendances

```bash
pip install opencv-python numpy deskew tqdm
```

### Usage basique

```bash
python scripts/prepare_images_local.py \
    --input C:\scans_bruts \
    --output C:\prepared
```

### Options disponibles

| Option | Description | Défaut |
|--------|-------------|--------|
| `--input DIR` | Dossier contenant les scans recto/verso | *Obligatoire* |
| `--output DIR` | Dossier de sortie | *Obligatoire* |
| `--crop 55\|100` | Recadrage du verso (%) | `100` |
| `--operateur NAME` | Nom de l'opérateur | `Utilisateur` |
| `--skip-deskew` | Désactiver le redressement automatique | *Non* |
| `--skip-optimize` | Désactiver les optimisations OCR | *Non* |
| `--preview` | Mode aperçu (n'enregistre pas) | *Non* |
| `--verbose` | Logs détaillés | *Non* |

### Exemples d'utilisation

#### Exemple 1 : Traitement standard (100% verso)
```bash
python scripts/prepare_images_local.py \
    --input test_scans \
    --output prepared \
    --operateur JeanMarc
```

#### Exemple 2 : Recadrage verso 55% (instructions droite inutiles)
```bash
python scripts/prepare_images_local.py \
    --input test_scans \
    --output prepared \
    --crop 55 \
    --operateur JeanMarc
```

#### Exemple 3 : Mode debug (verbose + preview)
```bash
python scripts/prepare_images_local.py \
    --input test_scans \
    --output prepared \
    --preview \
    --verbose
```

---

## 📁 Structure des fichiers générés

```
prepared/
├── images/
│   ├── 030_prepared.jpg
│   ├── 031_prepared.jpg
│   └── ...
│
└── metadata.json  ← Métadonnées complètes
```

---

## 🔧 Algorithmes utilisés

### 1. Détection de patterns (normalisation_fichiers.py)

Détecte automatiquement les paires selon plusieurs patterns :
- `030-R.jpeg` / `030-V.jpeg`
- `030_recto.jpg` / `030_verso.jpg`
- `030_page1.jpg` / `030_page2.jpg`

### 2. Redressement automatique (image_deskew.py)

Essaie 3 méthodes dans l'ordre :
1. **Bibliothèque deskew** : Projection horizontale optimisée
2. **Contours + minAreaRect** : Détection du rectangle englobant
3. **Projection horizontale** : Maximisation de variance

Angle typique détecté : **±5°**

### 3. Optimisations OCR (image_processing.py)

- **CLAHE** : Amélioration du contraste adaptatif
- **Débruitage** : fastNlMeansDenoising
- **Sharpening** : Unsharp mask
- **Évaluation qualité** : Scores de netteté, contraste, luminosité

---

## 📊 Performance attendue

Sur un **Ryzen 9 3900X** :
- **Temps par fiche** : 5-10 secondes
- **100 fiches** : ~10 minutes
- **Taille fichier** : 1-2 MB par fiche préparée

---

## 🐛 Dépannage

### Aucune paire détectée

Vérifiez que vos fichiers suivent un pattern supporté :
```bash
# ✓ Bon
030-R.jpeg
030-V.jpeg

# ✗ Mauvais
scan_030.jpg
scan_030_back.jpg
```

### Angle détecté aberrant (>30°)

Utilisez `--skip-deskew` et vérifiez manuellement l'image.

---

Voir aussi : `scripts/README.md` pour les autres scripts du projet.
