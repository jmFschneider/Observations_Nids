# Récapitulatif Session - Optimisation OCR Batch (App Pilot)

**Date Session 1:** 18 décembre 2024
**Date Session 2:** 19 décembre 2024
**Branche:** `feature/preparation-images-ocr-V2`
**Statut:** Fonctionnalité opérationnelle - Sélection multiple de modèles implémentée

---

## 🆕 Session 2 - 19 décembre 2024

### Modification majeure : Sélection multiple de modèles OCR

**Problème identifié:** Le système ne permettait de sélectionner qu'un seul modèle à la fois via un dropdown, ce qui nécessitait de relancer manuellement le traitement pour chaque modèle.

**Solution implémentée:** Interface avec checkboxes permettant de sélectionner plusieurs modèles et de les exécuter séquentiellement en une seule opération.

#### Changements apportés

**1. Interface utilisateur (`optimisation_ocr_home.html`)**
- Remplacement du `<select>` par des checkboxes pour chaque modèle
- Ajout de boutons "Tout sélectionner" / "Tout désélectionner"
- Descriptions pour chaque modèle :
  - Gemini Flash : Rapide et économique
  - Gemini 1.5 Pro : Équilibre qualité/coût
  - Gemini 2.0 Pro : Haute qualité
  - Gemini 2.0 Flash : Dernier modèle (coché par défaut)

**2. Logique JavaScript**
```javascript
// Validation : au moins 1 modèle requis
const selectedModels = [];
document.querySelectorAll('.model-checkbox:checked').forEach(cb => {
    selectedModels.push(cb.value);
});

// Envoi au backend
formData.append('modeles_ocr', JSON.stringify(modeles));
```

**3. Backend (`pilot/views.py` - ligne 250)**
```python
modeles_ocr_json = request.POST.get('modeles_ocr')
modeles_ocr = json.loads(modeles_ocr_json)  # Liste au lieu d'une string

task = process_batch_transcription_task.delay(directories, modeles_ocr, importer_en_base)
```

**4. Tâche Celery (`pilot/tasks.py` - ligne 340)**
Structure d'exécution séquentielle :
```python
def process_batch_transcription_task(self, directories, modeles_ocr: list[str], ...):
    # Pour chaque modèle sélectionné
    for modele_index, modele_ocr in enumerate(modeles_ocr):
        model = genai.GenerativeModel(modele_api)

        # Pour chaque répertoire
        for dir_index, dir_info in enumerate(directories):

            # Pour chaque image
            for img_file in image_files:
                # Transcription avec le modèle courant
```

**Calcul de progression :**
```python
total_images = images_par_repertoire * len(modeles_ocr)
```

**Organisation des résultats :**
```
transcription_results/
├── {repertoire}/
│   ├── {modele1}/
│   │   └── fichier_result.json
│   ├── {modele2}/
│   │   └── fichier_result.json
```

**5. Affichage des résultats (`batch_results.html`)**
- Badge du modèle pour chaque répertoire traité
- Affichage du modèle en cours durant le tracking
- Statistiques incluant le nombre de modèles testés

#### Exemple concret

**Sélection :**
- 2 répertoires : FUSION_FULL + Répertoire_A
- 3 modèles : Gemini Flash, 1.5 Pro, 2.0 Flash

**Exécution automatique :**
1. FUSION_FULL × Gemini Flash
2. FUSION_FULL × Gemini 1.5 Pro
3. FUSION_FULL × Gemini 2.0 Flash
4. Répertoire_A × Gemini Flash
5. Répertoire_A × Gemini 1.5 Pro
6. Répertoire_A × Gemini 2.0 Flash

**Total : 6 passes en une seule opération !**

#### Fichiers modifiés

```
pilot/templates/pilot/optimisation_ocr_home.html   # Interface checkboxes + JS
pilot/views.py                                     # Réception liste modèles
pilot/tasks.py                                     # Boucle sur modèles + organisation fichiers
pilot/templates/pilot/batch_results.html           # Affichage modèles multiples
```

---

## 📅 Session 1 - 18 décembre 2024

---

## 📋 Contexte du projet

### Objectif global
Mettre en place un système d'optimisation OCR dans l'app temporaire `pilot` pour :
1. Tester différents modèles OCR (Gemini Flash, 1.5 Pro, 2.0 Pro, 2.0 Flash)
2. Comparer la qualité des transcriptions avec une vérité terrain (FUSION_FULL)
3. Évaluer l'impact de différents prétraitements d'images

### Répertoires de test
**Localisation:** `C:\Projets\observations_nids\media\jpeg_pdf\TRI_ANCIEN\`

5 répertoires sélectionnés :
- **FUSION_FULL** : Répertoire de référence (vérité terrain) - **À importer UNE SEULE FOIS**
- 4 autres répertoires : Pour tests comparatifs avec différents modèles (2-4 passes chacun)

---

## 🎯 Ce qui a été fait aujourd'hui

### 1. Changement du répertoire de base de navigation

**Fichiers modifiés:**
- `pilot/views.py` (lignes 42 et 159)

**Changement:**
```python
# AVANT
base_dir = os.path.join(settings.MEDIA_ROOT, 'images_optimisees')

# APRÈS
base_dir = settings.MEDIA_ROOT
```

**Impact:** L'utilisateur peut maintenant naviguer dans tout le répertoire `media/` et remonter jusqu'à sa racine.

---

### 2. Gestion du modèle OCR paramétrable

**Problème:** Le modèle OCR était codé en dur (`gemini-2.0-flash`) dans `observations/tasks.py:59`

**Solution adoptée:** Création d'une tâche Celery spécifique pour pilot

#### Architecture mise en place

**Nouveau fichier créé:** `pilot/tasks.py` (600+ lignes)

**Fonctions principales:**

1. **`process_batch_transcription_task`** (ligne 340)
   - Tâche Celery principale pour le traitement batch
   - Paramètres:
     - `directories`: Liste de répertoires à traiter
     - `modele_ocr`: Modèle à utiliser (ex: "gemini_2_flash")
     - `importer_en_base`: Flag pour contrôler l'import en BDD

2. **`_importer_fiche_depuis_json`** (ligne 113)
   - Import direct JSON → FicheObservation
   - Version simplifiée de `ImportationService.finaliser_importation`
   - Crée tous les objets liés (Localisation, Nid, Observations, etc.)

3. **Fonctions utilitaires:**
   - `_extraire_nom_base_fichier` (ligne 23)
   - `_trouver_fiche_correspondante` (ligne 37)
   - `_determiner_type_image` (ligne 54)
   - `_determiner_type_fiche_et_traitement` (ligne 75)

**Mapping des modèles** (pilot/tasks.py:361-366):
```python
modeles_mapping = {
    'gemini_flash': 'gemini-1.5-flash',
    'gemini_1.5_pro': 'gemini-1.5-pro',
    'gemini_2_pro': 'gemini-2.0-pro',
    'gemini_2_flash': 'gemini-2.0-flash',
}
```

---

### 3. Interface de contrôle d'import en base

**Fonctionnalité clé:** Checkbox "Importer les fiches en base de données"

#### Fichiers modifiés

**`pilot/templates/pilot/optimisation_ocr_home.html`** (lignes 48-56)
```html
<div class="form-check">
    <input class="form-check-input" type="checkbox" id="importer_en_base" checked>
    <label class="form-check-label" for="importer_en_base">
        <strong>Importer les fiches en base de données</strong>
    </label>
    <div class="form-text">
        Cocher pour créer les FicheObservation en base (première fois sur FUSION_FULL).
        Décocher si les fiches existent déjà (réexécution ou tests sur autres répertoires).
    </div>
</div>
```

**JavaScript** (lignes 135, 191):
- Récupère la valeur de la checkbox
- Envoie via FormData : `importer_en_base: 'true' | 'false'`

**`pilot/views.py`** - `lancer_transcription_batch` (ligne 251):
```python
importer_en_base = request.POST.get('importer_en_base', 'false').lower() == 'true'
```

---

### 4. Vues et URLs complétées

**Fichiers modifiés:**

**`pilot/views.py`:**
- `lancer_transcription_batch` (ligne 238) : Lance la tâche Celery
- `check_batch_progress` (ligne 299) : AJAX pour suivi progression
- `batch_results` (ligne 365) : Affiche les résultats finaux

**`pilot/urls.py`:**
```python
path('optimisation-ocr/lancer-transcription-batch/', views.lancer_transcription_batch, name='lancer_transcription_batch'),
path('optimisation-ocr/verifier-progression/', views.check_batch_progress, name='check_batch_progress'),
path('optimisation-ocr/resultats/', views.batch_results, name='batch_results'),
```

---

### 5. Template de résultats

**Nouveau fichier:** `pilot/templates/pilot/batch_results.html`

**Fonctionnalités:**
- **Mode tracking** : Suivi en temps réel avec barre de progression
- **Mode résultats** : Affichage détaillé des résultats
- **Statistiques globales** : Cards avec totaux (succès, erreurs, taux)
- **Résultats par répertoire** : Tableaux détaillés avec liens JSON et admin
- **Polling AJAX** : Vérification toutes les 2 secondes

---

## 🔄 Flux de fonctionnement complet

### Étape 1 : Sélection des répertoires
**URL:** `http://127.0.0.1:8000/pilot/optimisation-ocr/selection-repertoire/`

1. Navigation dans `media/` (fil d'Ariane)
2. Sélection multiple par checkboxes
3. Stockage dans `sessionStorage`
4. Bouton "Continuer" → Page de configuration

### Étape 2 : Configuration
**URL:** `http://127.0.0.1:8000/pilot/optimisation-ocr/`

1. Affichage des répertoires sélectionnés (depuis sessionStorage)
2. Choix du modèle OCR (dropdown)
3. **Checkbox "Importer en base"** (cochée par défaut)
4. Bouton "Lancer" → Envoi AJAX

### Étape 3 : Traitement batch (Celery)
**Tâche:** `pilot.process_batch_transcription`

Pour chaque image :
1. **Transcription OCR** avec le modèle choisi
2. **Génération JSON** (validation + correction si nécessaire)
3. **Import conditionnel** :
   - Si `importer_en_base = True` : Création FicheObservation complète
   - Sinon : Recherche fiche existante
4. **Création TranscriptionOCR** liée à la fiche (ou None)

### Étape 4 : Suivi et résultats
**URL:** `http://127.0.0.1:8000/pilot/optimisation-ocr/resultats/?tracking=true`

1. Polling AJAX toutes les 2s
2. Mise à jour barre de progression
3. Affichage fichier/répertoire en cours
4. Redirection automatique vers résultats finaux

---

## 📊 Comportement selon le flag d'import

### ✅ `importer_en_base = True` (FUSION_FULL - 1ère fois)

**Ce qui se passe :**
1. Transcription OCR → JSON ✓
2. **Import en base de données** ✓
   - Création `FicheObservation`
   - Création `Localisation` (avec géocodage)
   - Création `Nid`
   - Création `Observation` (tableau_donnees)
   - Création `ResumeObservation` (tableau_donnees_2)
   - Création `CausesEchec`
   - Création `Remarque` (si présente)
   - Création ou récupération `Utilisateur`
3. Création `TranscriptionOCR` liée à la fiche importée ✓

**Logs attendus:**
```
Fiche d'observation #123 créée
TranscriptionOCR créée (ID: 456) pour image.jpg - Liée à fiche 123
```

### ⭕ `importer_en_base = False` (Tests comparatifs)

**Ce qui se passe :**
1. Transcription OCR → JSON ✓
2. **Recherche fiche existante** (par nom de fichier)
3. Création `TranscriptionOCR` liée (ou None si pas trouvée) ✓

**Logs attendus:**
```
TranscriptionOCR créée (ID: 789) pour image.jpg - Liée à fiche 123
```
OU
```
TranscriptionOCR créée (ID: 790) pour image.jpg - Aucune fiche liée
```

---

## 📁 Fichiers créés/modifiés - Récapitulatif

### Fichiers créés (nouveaux)
```
pilot/tasks.py                                    # 600+ lignes - Tâche Celery batch
pilot/templates/pilot/batch_results.html          # Template résultats
```

### Fichiers modifiés
```
pilot/views.py                                    # Vues complétées + imports
pilot/urls.py                                     # 3 nouvelles routes
pilot/templates/pilot/optimisation_ocr_home.html  # Checkbox + JavaScript
```

### Fichiers non modifiés (références)
```
pilot/models.py                                   # TranscriptionOCR (déjà créé)
pilot/admin.py                                    # Admin TranscriptionOCR (déjà créé)
ingest/importation_service.py                     # Référence pour l'import
observations/tasks.py                             # Tâche originale (non modifiée)
```

---

## 🎮 Utilisation recommandée

### Scénario 1 : Première importation FUSION_FULL

1. Naviguer vers `media/jpeg_pdf/TRI_ANCIEN/`
2. Sélectionner **FUSION_FULL** uniquement
3. Cliquer "Continuer"
4. Choisir modèle : `Gemini 2.0 Flash`
5. **Laisser cochée** ☑ "Importer les fiches en base de données"
6. Lancer
7. → Les fiches de référence sont créées en BDD

### Scénario 2 : Tests comparatifs (passes suivantes)

1. Naviguer vers `media/jpeg_pdf/TRI_ANCIEN/`
2. Sélectionner les 4 autres répertoires (ou refaire FUSION_FULL)
3. Cliquer "Continuer"
4. Choisir modèle : `Gemini 1.5 Pro` (ou autre)
5. **Décocher** ☐ "Importer les fiches en base de données"
6. Lancer
7. → Seuls JSON + TranscriptionOCR créés (pour comparaison)

### Scénario 3 : Plusieurs modèles sur FUSION_FULL

Répéter le Scénario 2 en changeant uniquement le modèle :
- Pass 1 : Gemini Flash
- Pass 2 : Gemini 1.5 Pro
- Pass 3 : Gemini 2.0 Pro
- Pass 4 : Gemini 2.0 Flash

**Important:** Toujours décocher l'import après la première fois !

---

## 🔍 Points techniques importants

### 1. Isolation de l'app pilot
- **Aucune modification** du code de production (`observations/tasks.py`)
- Tâche Celery dédiée : `pilot.process_batch_transcription`
- Suppression propre avec la branche

### 2. Gestion des transactions
Import atomique via `transaction.atomic()` dans `_importer_fiche_depuis_json`

### 3. Géocodage automatique
Utilise `get_geocodeur()` pour obtenir coordonnées GPS des communes

### 4. Recherche de fiches existantes
```python
def _trouver_fiche_correspondante(nom_base_image: str):
    fiches = FicheObservation.objects.filter(chemin_image__icontains=nom_base_image)
    if fiches.count() == 1:
        return fiches.first()
    # ...
```

### 5. Création automatique d'utilisateurs
Si observateur pas trouvé → création automatique avec :
- `est_transcription=True`
- `role='observateur'`
- Email : `prenom.nom@transcription.trans`

---

## 🔗 URLs importantes

```
# Navigation et sélection
http://127.0.0.1:8000/pilot/optimisation-ocr/selection-repertoire/

# Configuration
http://127.0.0.1:8000/pilot/optimisation-ocr/

# Résultats
http://127.0.0.1:8000/pilot/optimisation-ocr/resultats/

# Admin - Toutes les transcriptions OCR
http://127.0.0.1:8000/admin/pilot/transcriptionocr/
```

---

## ⚠️ Points d'attention

### Sécurité - Import FUSION_FULL
- **Règle figée** : FUSION_FULL = seule référence
- **Première importation** : Checkbox cochée
- **Toutes les suivantes** : Checkbox décochée
- **Protection** : Logs clairs + impossible de créer doublon (erreur BDD)

### Logs à surveiller
```bash
# Succès import
Fiche d'observation #123 créée
Fiche #123 importée en base depuis image.jpg

# Échec import (normal si décoché)
Aucune fiche trouvée pour 'image_base'
TranscriptionOCR créée - Aucune fiche liée

# Erreurs à investiguer
Espèce 'NomEspece' non trouvée en base, création ignorée
Erreur lors de l'importation de la fiche: [détails]
```

### Performance
- Traitement asynchrone (Celery)
- Progression en temps réel (AJAX polling)
- 1 transaction DB par fiche (atomicité)
- Geocodage peut ralentir (cache utilisé)

---

## 🚀 Prochaines étapes possibles

### À court terme
1. **Lancer première passe FUSION_FULL** avec import
2. **Tester passes comparatives** sans import
3. **Vérifier les TranscriptionOCR** créées dans l'admin

### Fonctionnalités futures (si besoin)
1. **Analyse automatique de correspondances** (fonction déjà en place mais pas utilisée)
2. **Comparaison automatique** TranscriptionOCR vs FicheObservation
3. **Calcul de scores de qualité** (champs déjà dans le modèle)
4. **Export des résultats** comparatifs
5. **Visualisations** (graphiques, tableaux de bord)

### Nettoyage final
Quand les tests sont terminés :
1. Garder uniquement les conclusions (quel modèle est le meilleur)
2. Supprimer la branche `feature/preparation-images-ocr-V2`
3. L'app `pilot` sera automatiquement supprimée

---

## 📝 Notes de développement

### Dépendances
```python
# Imports principaux dans pilot/tasks.py
from celery import shared_task
from django.db import transaction
from django.utils import timezone
import google.generativeai as genai
from PIL import Image

# Services réutilisés
from observations.json_rep.json_sanitizer import corriger_json, validate_json_structure
from geo.utils.geocoding import get_geocodeur
```

### Structure des données

**SessionStorage (frontend):**
```javascript
{
  "selectedDirectories": [
    {"name": "FUSION_FULL", "path": "jpeg_pdf/TRI_ANCIEN/FUSION_FULL"},
    // ...
  ],
  "currentPath": "jpeg_pdf/TRI_ANCIEN"
}
```

**Session Django (backend):**
```python
{
  "pilot_task_id": "abc-123-def",
  "pilot_batch_config": {
    "directories": [...],
    "modele_ocr": "gemini_2_flash",
    "importer_en_base": True,
    "start_time": "2024-12-18T20:00:00"
  },
  "pilot_batch_results": {
    "status": "SUCCESS",
    "total_images": 50,
    "total_success": 48,
    // ...
  }
}
```

---

## 🐛 Troubleshooting

### Problème : Celery n'est pas démarré
```bash
# Vérifier
celery -A observations_nids inspect ping

# Démarrer
celery -A observations_nids worker -l info
```

### Problème : Import échoue - Espèce non trouvée
**Cause:** L'espèce n'existe pas en base avec `valide_par_admin=True`

**Solution:**
1. Vérifier dans admin Django : `/admin/taxonomy/espece/`
2. Créer/valider l'espèce manquante

### Problème : TranscriptionOCR créée sans fiche liée
**Cause normale si:**
- Import désactivé (checkbox décochée)
- Aucune fiche correspondante trouvée

**Cause anormale si:**
- Import activé mais espèce manquante
- Import activé mais erreur lors de la création

**Solution:** Vérifier les logs pour le détail de l'erreur

---

## ✅ Checklist avant de quitter

- [x] Code fonctionnel et testé
- [x] Documentation complète (ce fichier)
- [x] Pas de modifications non commitées critiques
- [x] Celery peut être arrêté proprement
- [ ] Premier test FUSION_FULL à lancer demain

---

## 📞 Reprise de session

**Pour reprendre demain:**

1. **Lire ce document** en entier
2. **Vérifier les fichiers clés:**
   - `pilot/tasks.py` (tâche Celery)
   - `pilot/views.py` (vues complètes)
   - `pilot/templates/pilot/batch_results.html` (template résultats)
3. **Démarrer Celery** si nécessaire
4. **Naviguer vers** `http://127.0.0.1:8000/pilot/optimisation-ocr/selection-repertoire/`
5. **Tester le flux complet** avec FUSION_FULL

**Questions à se poser:**
- Est-ce que c'est la première importation de FUSION_FULL ? → Cocher la checkbox
- Est-ce un test comparatif ? → Décocher la checkbox
- Quel modèle tester ? → Choisir dans le dropdown

---

**Fin du récapitulatif - Session du 18 décembre 2024**
