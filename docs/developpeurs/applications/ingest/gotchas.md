# Ingest - Pièges et points d'attention

Ce fichier documente les erreurs récurrentes et pièges rencontrés dans l'application ingest.

---

## 🔥 Problème : Doublons de TranscriptionBrute

### Contexte
Le champ `fichier_source` de `TranscriptionBrute` a une contrainte **UNIQUE**.

### Symptôme
```
IntegrityError: UNIQUE constraint failed: ingest_transcriptionbrute.fichier_source
```

### Cause
Tentative d'importer deux fois le même fichier JSON.

### Solution

**Toujours utiliser `get_or_create()`** :

```python
# ✅ CORRECT
transcription, created = TranscriptionBrute.objects.get_or_create(
    fichier_source='fiche_042_result.json',
    defaults={'json_brut': data}
)

if not created:
    logger.info(f"Transcription déjà importée : {fichier_source}")
else:
    logger.info(f"Nouvelle transcription importée : {fichier_source}")

# ❌ INCORRECT
TranscriptionBrute.objects.create(
    fichier_source='fiche_042_result.json',
    json_brut=data
)  # Erreur si fichier déjà importé
```

### Prévention
Le `ImportationService.importer_fichiers_json()` utilise déjà `filter().exists()` pour éviter les doublons.

### Fichiers concernés
- `ingest/importation_service.py:56-59` (vérification des doublons)
- `ingest/models.py:63` (contrainte UNIQUE)

---

## ⚠️ Problème : Matching fuzzy trop permissif ou trop strict

### Contexte
Le seuil de similarité pour le matching d'espèces est configuré à **80%**.

### Symptôme
- **Trop permissif** (< 80%) : Faux positifs (mauvaises espèces matchées)
- **Trop strict** (> 80%) : Trop d'espèces nécessitent validation manuelle

### Cause
Seuil fixe qui ne convient pas à tous les cas.

### Solution

**Ajuster le seuil selon les besoins** :

```python
# ingest/importation_service.py
class ImportationService:
    def __init__(self, seuil_similarite=0.8):
        self.seuil_similarite = seuil_similarite  # Configurable
```

**Recommandations par cas** :
- **Noms courts** (ex: "M. bleue") : Seuil ≥ 90% (risque de faux positifs)
- **Noms longs** (ex: "Mésange charbonnière à longue queue") : Seuil ≥ 70% (plus tolérant)
- **Production** : Conserver 80% + validation manuelle des cas limites

### Prévention
- Analyser les scores de similarité en base :
  ```python
  EspeceCandidate.objects.values('score_similarite').annotate(count=Count('id'))
  ```
- Valider manuellement les candidats avec score entre 70-90%

### Fichiers concernés
- `ingest/importation_service.py:34-36` (seuil de similarité)

---

## ⚠️ Problème : Création automatique d'utilisateurs avec conflits d'email

### Contexte
`ImportationService.extraire_donnees_candidats()` crée automatiquement des utilisateurs depuis les noms transcrits.

### Symptôme
- Création d'utilisateurs en doublon (même email)
- Utilisateurs avec nom mal transcrit (ex: "Jear Dupont" au lieu de "Jean Dupont")

### Cause
- L'OCR peut faire des erreurs sur les noms
- La génération automatique d'email peut créer des conflits

### Solution

**1. Matching des utilisateurs existants** :
```python
# Rechercher l'utilisateur existant avec matching fuzzy
utilisateurs = Utilisateur.objects.all()
meilleur_match = None
meilleur_score = 0

for user in utilisateurs:
    score = SequenceMatcher(None, nom_transcrit.lower(), user.username.lower()).ratio()
    if score > meilleur_score and score >= 0.8:
        meilleur_match = user
        meilleur_score = score

if meilleur_match:
    # Utiliser l'utilisateur existant
    importation.observateur = meilleur_match
else:
    # Créer un nouvel utilisateur avec validation manuelle
    pass
```

**2. Validation manuelle des nouveaux utilisateurs** :
- Afficher la liste des utilisateurs créés automatiquement
- Permettre de fusionner avec un utilisateur existant
- Permettre de corriger le nom

### Prévention
- Ne pas activer la création automatique en production sans validation
- Utiliser une table intermédiaire `UtilisateurCandidat` (comme `EspeceCandidate`)

### Fichiers concernés
- `ingest/importation_service.py:88-93` (extraction utilisateurs)

---

## ⚠️ Problème : Géocodage échoue pour certaines communes

### Contexte
`ImportationService` utilise le géocodeur pour valider les communes transcrites.

### Symptôme
- Commune non trouvée (NULL ou coordonnées 0,0)
- Mauvaise commune (ex: "Grenoble" → "Grenoble-sur-Garonne" au lieu de "Grenoble")

### Cause
- Nom de commune mal transcrit
- Ancienne commune fusionnée
- Plusieurs communes avec le même nom

### Solution

**1. Vérifier les résultats du géocodage** :
```python
from geo.utils.geocoding import get_geocodeur

geocodeur = get_geocodeur()
resultat = geocodeur.geocoder_commune("Grenoble", departement="38")

if not resultat or resultat['latitude'] == 0:
    logger.warning(f"Commune non trouvée : Grenoble (38)")
    # Marquer l'importation comme en erreur
    importation.statut = 'erreur'
```

**2. Validation manuelle** :
- Afficher les communes non géocodées
- Permettre de corriger le nom de commune
- Utiliser `CommuneAncienne` pour les communes fusionnées

### Prévention
- Vérifier le taux de succès du géocodage dans les logs
- Créer un rapport des communes problématiques

### Fichiers concernés
- `ingest/importation_service.py` (appel au géocodeur)
- `geo/utils/geocoding.py` (logique de géocodage)

---

## ⚠️ Problème : JSON mal formaté (markdown code fences)

### Contexte
Les JSON générés par Gemini peuvent contenir des marqueurs Markdown (` ```json ... ``` `).

### Symptôme
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### Cause
Le JSON est entouré de backticks Markdown :
```
```json
{
  "espece": "Mésange bleue"
}
```
```

### Solution

**Le service nettoie déjà automatiquement** :

```python
# ingest/importation_service.py:66-67
if contenu.startswith('```json') and contenu.endswith('```'):
    contenu = contenu[7:-3].strip()
```

**Si le problème persiste** :
```python
# Utiliser le sanitizer d'observations
from observations.json_rep.json_sanitizer import corriger_json

json_clean = corriger_json(contenu_brut)
data = json.loads(json_clean)
```

### Prévention
- Toujours nettoyer le JSON avant `json.loads()`
- Utiliser `corriger_json()` pour les cas complexes

### Fichiers concernés
- `ingest/importation_service.py:62-70` (nettoyage JSON)
- `observations/json_rep/json_sanitizer.py` (sanitizer)

---

## ⚠️ Problème : Statut `traite` non mis à jour

### Contexte
Le champ `TranscriptionBrute.traite` indique si la transcription a été traitée.

### Symptôme
Les transcriptions sont traitées plusieurs fois (doublons d'`ImportationEnCours`).

### Cause
Oubli de mettre à jour `traite=True` après traitement.

### Solution

**Toujours marquer comme traité** après import :

```python
# ✅ CORRECT : Workflow complet
transcription = TranscriptionBrute.objects.get(fichier_source='fiche_042_result.json')

# 1. Créer l'ImportationEnCours
importation = ImportationEnCours.objects.create(
    transcription=transcription,
    ...
)

# 2. Créer la fiche
fiche = service.creer_fiche_depuis_importation(importation)

# 3. Marquer comme complète
importation.statut = 'complete'
importation.fiche_observation = fiche
importation.save()

# 4. ✅ Marquer la transcription comme traitée
transcription.traite = True
transcription.save()
```

### Prévention
- Utiliser une transaction atomique
- Vérifier `traite=False` dans `extraire_donnees_candidats()`

### Fichiers concernés
- `ingest/importation_service.py:90` (filtre `traite=False`)
- `ingest/models.py:66` (champ `traite`)

---

## ⚠️ Problème : Navigation dans les répertoires JSON (sécurité)

### Contexte
La vue `importer_json` permet de naviguer dans `transcription_results/`.

### Symptôme
Risque de directory traversal si chemins non sécurisés.

### Cause
Similaire au problème de pilot (navigation dans les répertoires).

### Solution

**Le code est déjà sécurisé** :

```python
# ingest/views/importation.py:39-48
safe_path = current_path.replace('\\', '/').replace('..', '').strip('/')
full_current_path = os.path.join(base_dir, safe_path.replace('/', os.sep))

# Vérifier que le chemin est dans le répertoire de base
if not full_current_path.startswith(base_dir):
    safe_path = ''
    full_current_path = base_dir
```

**Ne jamais retirer ces vérifications** !

### Prévention
- Lire [pilot/gotchas.md](../pilot/gotchas.md#probleme-perte-acces-sous-repertoires)
- Tester avec chemins malveillants (`../../etc/passwd`)

### Fichiers concernés
- `ingest/views/importation.py:39-48` (sécurisation chemins)

---

## ⚠️ Problème : Cascade delete sur ImportationEnCours

### Contexte
`ImportationEnCours.transcription` a `on_delete=models.CASCADE`.

### Symptôme
Suppression de `TranscriptionBrute` → suppression de `ImportationEnCours` associé.

### Cause
Comportement voulu mais **irréversible**.

### Solution

**Avant de supprimer une transcription** :
```python
transcription = TranscriptionBrute.objects.get(fichier_source='fiche_042_result.json')

# Vérifier si une importation existe
if hasattr(transcription, 'importationencours'):
    importation = transcription.importationencours
    print(f"Attention : Importation #{importation.id} (statut: {importation.statut}) sera supprimée")

    # Décision : conserver l'historique ou supprimer
    if importation.statut == 'complete':
        # Option 1 : Ne pas supprimer
        print("Importation complète, conservation recommandée")
    else:
        # Option 2 : Supprimer
        transcription.delete()
```

### Prévention
- Ne supprimer que les transcriptions non traitées ou en erreur
- Archiver les transcriptions complètes au lieu de les supprimer

### Fichiers concernés
- `ingest/models.py:85` (CASCADE delete)

---

## ✅ Bonnes pratiques

### 1. Toujours valider les données avant création de fiche

```python
def creer_fiche_depuis_importation(importation):
    # Vérifier espèce validée
    if not importation.espece_candidate or not importation.espece_candidate.espece_validee:
        raise ValueError("Espèce non validée")

    # Vérifier observateur assigné
    if not importation.observateur:
        raise ValueError("Observateur non assigné")

    # Créer la fiche
    fiche = FicheObservation.objects.create(...)
```

### 2. Utiliser transactions atomiques

```python
from django.db import transaction

@transaction.atomic
def importer_et_creer_fiche(json_data):
    # Tout ou rien
    transcription = TranscriptionBrute.objects.create(...)
    importation = ImportationEnCours.objects.create(...)
    fiche = FicheObservation.objects.create(...)
```

### 3. Logger les erreurs détaillées

```python
try:
    fiche = service.creer_fiche_depuis_importation(importation)
except Exception as e:
    logger.error(f"Erreur import {importation.id}: {str(e)}", exc_info=True)
    importation.statut = 'erreur'
    importation.save()
```

### 4. Gérer les conflits d'unicité

```python
# Espèces candidates
espece_candidate, created = EspeceCandidate.objects.get_or_create(
    nom_transcrit=nom_transcrit,
    defaults={'score_similarite': score, ...}
)

if not created:
    # Mettre à jour le score si meilleur
    if score > espece_candidate.score_similarite:
        espece_candidate.score_similarite = score
        espece_candidate.save()
```

---

## 🔥 Checklist avant modification d'ingest

- [ ] Lire ce fichier gotchas.md
- [ ] Vérifier la sécurité des chemins de fichiers (directory traversal)
- [ ] Utiliser `get_or_create()` pour éviter les doublons (TranscriptionBrute, EspeceCandidate)
- [ ] Toujours marquer `transcription.traite=True` après traitement
- [ ] Valider les données avant création de FicheObservation
- [ ] Utiliser des transactions atomiques
- [ ] Logger les erreurs avec `exc_info=True`
- [ ] Tester le matching fuzzy avec différents seuils

---

*Dernière mise à jour : 2025-12-27*
