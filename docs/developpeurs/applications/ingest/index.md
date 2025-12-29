# Ingest - Vue d'ensemble

> Pipeline d'import et transcription OCR pour créer des FicheObservation depuis des scans

## Responsabilité

L'application **ingest** gère le **pipeline complet d'import** des fiches scannées :

1. **Préparation des images** (fusion recto/verso, prétraitement)
2. **Stockage des transcriptions OCR** (JSON brut)
3. **Matching fuzzy des espèces** transcrites avec le référentiel
4. **Création automatique des utilisateurs** depuis les noms transcrits
5. **Géocodage des communes**
6. **Création contrôlée des FicheObservation** depuis les transcriptions

## Position dans l'architecture

```
pilot/ (Interface Pilote - Test uniquement)
  ↓ génère des JSON OCR
ingest/ (Pipeline OCR - Production)
  ├─ PreparationImage → Fusion recto/verso
  ├─ TranscriptionBrute → JSON brut OCR
  ├─ EspeceCandidate → Matching fuzzy
  ├─ ImportationEnCours → Workflow d'import
  └─ ImportationService → Logique métier
  ↓ crée
observations/FicheObservation (Fiche finale)
```

**Différence clé** :
- **pilot** : Expérimentation, comparaison de modèles OCR (génère du JSON uniquement)
- **ingest** : Pipeline production pour créer réellement des FicheObservation

---

## Modèles principaux

| Modèle | Description | Fichier |
|--------|-------------|---------|
| **[PreparationImage](models.md#modele-preparationimage)** | Historique de préparation des images (fusion, rotation, etc.) | `ingest/models.py:8-59` |
| **[TranscriptionBrute](models.md#modele-transcriptionbrute)** | JSON brut produit par l'OCR | `ingest/models.py:62-69` |
| **[EspeceCandidate](models.md#modele-espececandidate)** | Nom d'espèce transcrit + matching avec Espece | `ingest/models.py:72-81` |
| **[ImportationEnCours](models.md#modele-importationencours)** | Workflow d'importation (en_attente / erreur / complete) | `ingest/models.py:84-101` |

---

## Service principal

### ImportationService

**Fichier** : `ingest/importation_service.py`

Classe de service qui centralise toute la logique métier d'import.

**Méthodes principales** :

| Méthode | Description |
|---------|-------------|
| `importer_fichiers_json(repertoire)` | Importe tous les fichiers JSON d'un répertoire → TranscriptionBrute |
| `extraire_donnees_candidats()` | Extrait espèces et crée utilisateurs depuis transcriptions |
| `creer_fiche_depuis_importation(importation)` | Crée une FicheObservation depuis une ImportationEnCours |

**Voir** : [importation_service.md](importation_service.md) pour tous les détails

---

## Utilitaires de traitement d'image

### `ingest/utils/`

| Fichier | Description |
|---------|-------------|
| `image_processing.py` | Fusion recto/verso, contraste, dé bruitage |
| `image_deskew.py` | Détection et correction d'inclinaison |
| `normalisation_fichiers.py` | Normalisation des noms de fichiers |

---

## Vues principales

### Organisation (`ingest/views/`)

| Fichier | Description | Routes principales |
|---------|-------------|--------------------|
| `home.py` | Page d'accueil ingest | `/ingest/` |
| `importation.py` | Import de fichiers JSON | `/ingest/importer-json/` |
| `preparation.py` | Préparation des images | `/ingest/preparation/` |
| `especes.py` | Validation des espèces candidates | `/ingest/especes/` |
| `auth.py` | Permissions (décorateur `peut_transcrire`) | - |

---

## Workflow complet

### Étape 1 : Préparation des images

```
scan_001_r.jpg + scan_001_v.jpg
         ↓
[image_processing.py]
         ↓
scan_001_fusionne.jpg → PreparationImage
```

**Opérations** :
- Fusion recto/verso
- Rotation (deskew)
- Contraste
- Débruitage

### Étape 2 : Transcription OCR

```
scan_001_fusionne.jpg
         ↓
[Gemini OCR - via pilot ou autre]
         ↓
scan_001_gemini_2.5_pro_result.json
```

### Étape 3 : Import JSON

```
scan_001_result.json
         ↓
[ImportationService.importer_fichiers_json()]
         ↓
TranscriptionBrute (JSON stocké en base)
```

### Étape 4 : Extraction et matching

```
TranscriptionBrute
         ↓
[ImportationService.extraire_donnees_candidats()]
         ↓
EspeceCandidate (matching fuzzy avec Espece)
+ Utilisateur (création automatique si n'existe pas)
+ Commune (géocodage)
```

### Étape 5 : Validation manuelle (si nécessaire)

```
EspeceCandidate (espece_validee=NULL)
         ↓
[Interface admin - validation manuelle]
         ↓
EspeceCandidate (espece_validee=Espece, validation_manuelle=True)
```

### Étape 6 : Création de la fiche

```
ImportationEnCours (statut='en_attente')
         ↓
[ImportationService.creer_fiche_depuis_importation()]
         ↓
FicheObservation + tous les objets liés (1:1, 1:N)
         ↓
ImportationEnCours (statut='complete')
```

---

## Dépendances

### Applications Django
- **observations** - Création de FicheObservation
- **taxonomy** - Matching d'espèces (Espece)
- **accounts** - Création/assignation d'observateurs (Utilisateur)
- **geo** - Géocodage de communes (Localisation)
- **core** - Constantes (STATUT_IMPORTATION_CHOICES)

### Services externes
- **Google Gemini API** - Transcription OCR (génération du JSON)
- **Geocodeur** - Géolocalisation des communes

### Bibliothèques Python
- **Pillow (PIL)** - Traitement d'images
- **difflib.SequenceMatcher** - Matching fuzzy d'espèces

---

## Points d'entrée clés

### URLs principales
- `/ingest/` - Page d'accueil
- `/ingest/importer-json/` - Import de fichiers JSON
- `/ingest/importer-json/?path=2025/batch_001` - Navigation dans les répertoires
- `/ingest/preparation/` - Préparation des images
- `/ingest/especes/` - Validation des espèces candidates

### Permissions

Toutes les vues ingest sont protégées par le décorateur `@user_passes_test(peut_transcrire)`.

**Fichier** : `ingest/views/auth.py`

```python
def peut_transcrire(user):
    """Vérifie si l'utilisateur peut accéder aux fonctionnalités de transcription"""
    return user.is_staff or user.role in ['administrateur', 'reviewer']
```

---

## Configuration

### Répertoires

**Définis dans `settings.py`** :

```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Structure attendue :
media/
├── scans_bruts/             # Scans originaux (recto/verso)
│   └── 2025/
├── prepared_images/         # Images fusionnées et prétraitées
│   └── 2025/
└── transcription_results/   # JSON OCR
    └── 2025/
        └── batch_001/
```

### Paramètres du service

**`ImportationService.__init__()`** :

```python
self.seuil_similarite = 0.8  # Seuil matching fuzzy (80%)
```

---

## Fichiers critiques

| Fichier | Sensibilité | Raison |
|---------|-------------|--------|
| `importation_service.py` | 🔥 **Critique** | Logique métier centrale - création de fiches |
| `models.py` | ⚠️ Sensible | Workflow d'import |
| `utils/image_processing.py` | ⚠️ Sensible | Préparation des images |
| `views/importation.py` | ⚠️ Sensible | Navigation dans les fichiers (sécurité chemins) |

---

## Statuts et workflow

### Statuts de TranscriptionBrute

| Champ `traite` | Signification |
|----------------|---------------|
| `False` | Transcription importée, pas encore traitée |
| `True` | Transcription traitée (ImportationEnCours créé) |

### Statuts d'ImportationEnCours

| Statut | Signification | Action suivante |
|--------|---------------|-----------------|
| `en_attente` | Import en cours, en attente de validation | Valider espèce ou assigner observateur |
| `erreur` | Erreur détectée (données manquantes/incohérentes) | Intervention manuelle |
| `complete` | Fiche créée avec succès | Aucune |

---

## Documentation existante

- **[Architecture détaillée](../../architecture/domaines/03_ocr_ingestion.md)** - Version longue avec exemples
- **[Application pilot](../pilot/index.md)** - Environnement de test OCR

---

## Voir aussi

- **[Modèles détaillés](models.md)** - Documentation complète des modèles
- **[Service d'importation](importation_service.md)** - Logique métier
- **[Pièges à éviter](gotchas.md)** - Erreurs courantes

---

*Dernière mise à jour : 2025-12-27*
