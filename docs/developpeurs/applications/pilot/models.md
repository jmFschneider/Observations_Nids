# Pilot - Modèles de données

Ce fichier documente les modèles de l'application pilot.

---

## Modèle : TranscriptionOCR

**Fichier** : `pilot/models.py:14-210`

### Responsabilité

Stocke les **métadonnées et résultats d'évaluation** d'une transcription OCR réalisée dans le cadre de l'expérimentation sur les modèles.

Ce modèle permet de :
- Comparer différents modèles OCR (Gemini Flash vs Pro, etc.)
- Évaluer l'impact du prétraitement d'images (brute vs optimisée)
- Calculer des scores de qualité par rapport aux fiches de référence

---

## Structure du modèle

### 1. Lien vers la fiche de référence

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `fiche` | ForeignKey | Fiche d'observation corrigée manuellement (vérité terrain) | → `FicheObservation`, CASCADE, **nullable** |

**Relation** :
```python
fiche = models.ForeignKey(
    FicheObservation,
    on_delete=models.CASCADE,
    related_name="transcriptions_ocr_pilot",
    null=True,
    blank=True,
)
```

**Usage** :
```python
# Récupérer toutes les transcriptions OCR d'une fiche
fiche = FicheObservation.objects.get(num_fiche=123)
transcriptions = fiche.transcriptions_ocr_pilot.all()
```

---

### 2. Métadonnées de la transcription

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `chemin_json` | CharField(255) | Chemin vers le fichier JSON brut de la transcription OCR | **Obligatoire** |
| `chemin_image` | CharField(255) | Chemin de l'image source utilisée pour cette transcription | Optionnel |
| `type_image` | CharField(20) | Type d'image : `brute` ou `optimisee` | Choix restreint |
| `modele_ocr` | CharField(50) | Modèle d'IA utilisé (ex: `gemini_2.5_pro`) | Choix restreint |
| `date_transcription` | DateTimeField | Date/heure de la transcription | Auto (auto_now_add) |

#### Choix : `type_image`

**Code** : `models.py:52-60`

| Valeur | Label |
|--------|-------|
| `brute` | Image brute |
| `optimisee` | Image optimisée pour OCR |

**Exemples d'optimisation** :
- Augmentation du contraste
- Suppression du bruit
- Redressement de perspective
- Conversion en niveaux de gris

#### Choix : `modele_ocr`

**Code** : `models.py:62-72`

| Valeur | Modèle Gemini |
|--------|---------------|
| `gemini_3_flash` | Gemini 3 Flash |
| `gemini_3_pro` | Gemini 3 Pro |
| `gemini_2.5_pro` | Gemini 2.5 Pro |
| `gemini_2.5_flash_lite` | Gemini 2.5 Flash-Lite |

**Mise à jour** : Ajouter ici les nouveaux modèles au fur et à mesure de leur disponibilité.

---

### 3. Évaluation de la qualité

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `statut_evaluation` | CharField(20) | Statut de l'évaluation | Choix restreint, défaut: `non_evaluee` |
| `date_evaluation` | DateTimeField | Date de l'évaluation | Nullable |
| `score_global` | FloatField | Score de similarité global (0-100%) | 0.0 ≤ score ≤ 100.0 |
| `nombre_champs_corrects` | IntegerField | Nombre de champs corrects | ≥ 0, nullable |
| `nombre_champs_total` | IntegerField | Nombre de champs total | ≥ 0, nullable |

#### Choix : `statut_evaluation`

**Code** : `models.py:81-91`

| Valeur | Signification |
|--------|---------------|
| `non_evaluee` | Transcription créée, pas encore évaluée |
| `en_cours` | Évaluation en cours |
| `evaluee` | Évaluation terminée, scores calculés |
| `erreur` | Erreur lors de l'évaluation |

---

### 4. Compteurs d'erreurs par type

| Champ | Type | Description | Défaut |
|-------|------|-------------|--------|
| `nombre_erreurs_dates` | IntegerField | Erreurs sur les champs de dates | 0 |
| `nombre_erreurs_nombres` | IntegerField | Erreurs sur les champs numériques | 0 |
| `nombre_erreurs_texte` | IntegerField | Erreurs sur les champs texte | 0 |
| `nombre_erreurs_especes` | IntegerField | Erreurs sur le nom d'espèce | 0 |
| `nombre_erreurs_lieux` | IntegerField | Erreurs sur les lieux (commune, département) | 0 |

**Usage** : Identifier les types de champs posant le plus de problèmes pour chaque modèle OCR.

---

### 5. Détails de comparaison (JSON)

| Champ | Type | Description |
|-------|------|-------------|
| `details_comparaison` | JSONField | Détails des différences champ par champ |

**Structure JSON** :
```json
{
  "champs_compares": [
    {
      "nom_champ": "espece",
      "valeur_reference": "Mésange bleue",
      "valeur_ocr": "Mésange bleue",
      "correspondance": true,
      "score_similarite": 100.0
    },
    {
      "nom_champ": "commune",
      "valeur_reference": "Grenoble",
      "valeur_ocr": "Grenobje",
      "correspondance": false,
      "score_similarite": 88.9,
      "type_erreur": "texte"
    },
    {
      "nom_champ": "date_ponte_jour",
      "valeur_reference": "15",
      "valeur_ocr": "16",
      "correspondance": false,
      "score_similarite": 0.0,
      "type_erreur": "date"
    }
  ],
  "resume": {
    "total_champs": 25,
    "champs_corrects": 22,
    "champs_incorrects": 3
  }
}
```

---

### 6. Performance du traitement

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `temps_traitement_secondes` | FloatField | Durée du traitement OCR en secondes | ≥ 0.0, nullable |

**Usage** : Comparer les performances entre modèles (temps vs qualité).

---

### 7. Notes manuelles

| Champ | Type | Description |
|-------|------|-------------|
| `notes_evaluation` | TextField | Notes et observations manuelles |

**Exemple** :
```
L'OCR a confondu "1" et "l" dans le champ commune.
Le modèle Flash semble moins performant sur les écritures manuscrites.
```

---

## Métadonnées du modèle

### Table de base de données

```python
class Meta:
    db_table = 'pilot_transcription_ocr'
    verbose_name = '[PILOTE] Transcription OCR'
    verbose_name_plural = '[PILOTE] Transcriptions OCR'
    ordering = ['-date_transcription']
```

**Nom de table** : `pilot_transcription_ocr`

**Tri par défaut** : Date de transcription décroissante (plus récentes en premier)

---

### Index

**Code** : `models.py:179-183`

```python
indexes = [
    models.Index(fields=['fiche', 'modele_ocr']),
    models.Index(fields=['statut_evaluation']),
    models.Index(fields=['score_global']),
]
```

**Optimisations** :
- Requêtes filtrées par fiche + modèle (comparaison de modèles pour une fiche)
- Requêtes filtrées par statut (liste des transcriptions à évaluer)
- Tri par score global (classement des meilleurs résultats)

---

## Méthodes du modèle

### `__str__()`

**Code** : `models.py:185-187`

```python
def __str__(self):
    fiche_num = self.fiche.num_fiche if self.fiche else 'N/A'
    return f"[PILOTE] OCR {self.modele_ocr} - {self.type_image} (Fiche #{fiche_num})"
```

**Exemple** :
```
[PILOTE] OCR gemini_2.5_pro - brute (Fiche #123)
```

---

### `taux_precision` (property)

**Code** : `models.py:189-198`

```python
@property
def taux_precision(self):
    """Calcule le taux de précision (champs corrects / total)"""
    if (self.nombre_champs_total and self.nombre_champs_total > 0
            and self.nombre_champs_corrects is not None):
        return (self.nombre_champs_corrects / self.nombre_champs_total) * 100
    return None
```

**Usage** :
```python
transcription = TranscriptionOCR.objects.get(id=42)
print(f"Taux de précision : {transcription.taux_precision:.1f}%")
# Taux de précision : 88.5%
```

**Retour** :
- `float` : Pourcentage de précision (0.0 à 100.0)
- `None` : Si les champs ne sont pas renseignés

---

### `nombre_erreurs_total` (property)

**Code** : `models.py:200-209`

```python
@property
def nombre_erreurs_total(self):
    """Calcule le nombre total d'erreurs"""
    return (
        self.nombre_erreurs_dates +
        self.nombre_erreurs_nombres +
        self.nombre_erreurs_texte +
        self.nombre_erreurs_especes +
        self.nombre_erreurs_lieux
    )
```

**Usage** :
```python
print(f"Erreurs totales : {transcription.nombre_erreurs_total}")
# Erreurs totales : 7
```

---

## Requêtes ORM courantes

### Récupérer les transcriptions d'une fiche

```python
fiche = FicheObservation.objects.get(num_fiche=123)
transcriptions = fiche.transcriptions_ocr_pilot.all()

for t in transcriptions:
    print(f"{t.modele_ocr} ({t.type_image}): {t.score_global:.1f}%")
```

### Comparer les modèles sur une fiche

```python
from django.db.models import Avg

stats = TranscriptionOCR.objects.filter(
    fiche__num_fiche=123
).values('modele_ocr').annotate(
    score_moyen=Avg('score_global'),
    temps_moyen=Avg('temps_traitement_secondes')
)

for stat in stats:
    print(f"{stat['modele_ocr']}: {stat['score_moyen']:.1f}% en {stat['temps_moyen']:.1f}s")
```

### Meilleures transcriptions par score

```python
top_transcriptions = TranscriptionOCR.objects.filter(
    statut_evaluation='evaluee'
).order_by('-score_global')[:10]
```

### Transcriptions en attente d'évaluation

```python
a_evaluer = TranscriptionOCR.objects.filter(
    statut_evaluation='non_evaluee'
).select_related('fiche')
```

### Statistiques par modèle OCR

```python
from django.db.models import Avg, Count

stats_modeles = TranscriptionOCR.objects.filter(
    statut_evaluation='evaluee'
).values('modele_ocr').annotate(
    nb_transcriptions=Count('id'),
    score_moyen=Avg('score_global'),
    temps_moyen=Avg('temps_traitement_secondes'),
    erreurs_dates_moy=Avg('nombre_erreurs_dates'),
    erreurs_especes_moy=Avg('nombre_erreurs_especes')
)
```

---

## Points d'attention

### ⚠️ Nullable vs Blank

- `fiche` : `null=True, blank=True` → Peut ne pas avoir de fiche de référence
- `score_global`, `nombre_champs_corrects`, etc. : `null=True` → Calculés après évaluation

### ⚠️ Cascade delete

Si une `FicheObservation` est supprimée, toutes ses transcriptions OCR pilote sont supprimées (`CASCADE`).

**Prévention** : Éviter de supprimer des fiches ayant servi de référence.

### ⚠️ Taille du JSONField

Le champ `details_comparaison` peut devenir volumineux si beaucoup de champs sont comparés.

**Optimisation** : Limiter le niveau de détail ou archiver les anciennes transcriptions.

---

## Voir aussi

- **[Vue d'ensemble de pilot](index.md)** - Architecture globale
- **[Workflow OCR](ocr_workflow.md)** - Pipeline complet
- **[Pièges à éviter](gotchas.md)** - Erreurs courantes

---

*Dernière mise à jour : 2025-12-27*
