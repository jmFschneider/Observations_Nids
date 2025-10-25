# Domaine : Données de nidification

## Vue d'ensemble

Le modèle **`ResumeObservation`** agrège les données clés de nidification d'une fiche : dates partielles (jour/mois) et compteurs d'œufs/poussins. Il implémente **6 contraintes CHECK complexes** pour garantir la cohérence des données.

**Fichier** : `observations/models.py:138-240`

---

## Modèle ResumeObservation

### Rôle métier

Synthétise les étapes clés du cycle de reproduction observé :
- Dates partielles (jour/mois) : premier œuf pondu, premier poussin éclos, premier poussin volant
- Compteurs : nombre d'œufs pondus/éclos/non éclos, nombre de poussins observés

**Relation** : OneToOne avec `FicheObservation` (créé automatiquement à la création de la fiche)

### Champs : Dates partielles

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `premier_oeuf_pondu_jour` | PositiveSmallIntegerField | Jour du premier œuf pondu | NULL ou 1-31 |
| `premier_oeuf_pondu_mois` | PositiveSmallIntegerField | Mois du premier œuf pondu | NULL ou 1-12 |
| `premier_poussin_eclos_jour` | PositiveSmallIntegerField | Jour du premier poussin éclos | NULL ou 1-31 |
| `premier_poussin_eclos_mois` | PositiveSmallIntegerField | Mois du premier poussin éclos | NULL ou 1-12 |
| `premier_poussin_volant_jour` | PositiveSmallIntegerField | Jour du premier poussin volant | NULL ou 1-31 |
| `premier_poussin_volant_mois` | PositiveSmallIntegerField | Mois du premier poussin volant | NULL ou 1-12 |

**Pourquoi des dates partielles ?**
- Les fiches papier historiques ne contiennent souvent que jour/mois (sans année)
- L'année est déjà stockée dans `FicheObservation.annee`
- Permet de saisir des dates incomplètes (ex: "mi-avril" → jour=NULL, mois=4)

### Champs : Compteurs

| Champ | Type | Description | Valeur NULL |
|-------|------|-------------|-------------|
| `nombre_oeufs_pondus` | PositiveSmallIntegerField | Nombre total d'œufs pondus | NULL = non observé |
| `nombre_oeufs_eclos` | PositiveSmallIntegerField | Nombre d'œufs ayant éclos | NULL = non observé |
| `nombre_oeufs_non_eclos` | PositiveSmallIntegerField | Nombre d'œufs n'ayant pas éclos | NULL = non observé |
| `nombre_poussins` | PositiveSmallIntegerField | Nombre de poussins observés | NULL = non observé |

**Distinction importante** : `NULL` vs `0`
- `NULL` : Donnée non observée/inconnue
- `0` : Donnée observée, valeur effectivement zéro (ex: aucun œuf non éclos)

---

## Contraintes CHECK (6)

### Contraintes 1-3 : Cohérence jour/mois

Chaque paire (jour, mois) doit respecter : **soit les deux NULL, soit les deux renseignés**.

#### 1. Premier œuf pondu

```python
models.CheckConstraint(
    name="resume_premier_oeuf_pondu_jour_mois_both_or_none",
    check=(
        (Q(premier_oeuf_pondu_jour__isnull=True) & Q(premier_oeuf_pondu_mois__isnull=True))
        | (Q(premier_oeuf_pondu_jour__isnull=False) & Q(premier_oeuf_pondu_mois__isnull=False))
    ),
)
```

**Empêche** :
```python
# ❌ INVALIDE : jour renseigné mais pas le mois
ResumeObservation(premier_oeuf_pondu_jour=15, premier_oeuf_pondu_mois=None)

# ❌ INVALIDE : mois renseigné mais pas le jour
ResumeObservation(premier_oeuf_pondu_jour=None, premier_oeuf_pondu_mois=4)
```

**Autorise** :
```python
# ✅ VALIDE : les deux renseignés
ResumeObservation(premier_oeuf_pondu_jour=15, premier_oeuf_pondu_mois=4)

# ✅ VALIDE : les deux NULL (non observé)
ResumeObservation(premier_oeuf_pondu_jour=None, premier_oeuf_pondu_mois=None)
```

#### 2. Premier poussin éclos

```python
models.CheckConstraint(
    name="resume_premier_poussin_eclos_jour_mois_both_or_none",
    check=(
        (Q(premier_poussin_eclos_jour__isnull=True) & Q(premier_poussin_eclos_mois__isnull=True))
        | (Q(premier_poussin_eclos_jour__isnull=False) & Q(premier_poussin_eclos_mois__isnull=False))
    ),
)
```

#### 3. Premier poussin volant

```python
models.CheckConstraint(
    name="resume_premier_poussin_volant_jour_mois_both_or_none",
    check=(
        (Q(premier_poussin_volant_jour__isnull=True) & Q(premier_poussin_volant_mois__isnull=True))
        | (Q(premier_poussin_volant_jour__isnull=False) & Q(premier_poussin_volant_mois__isnull=False))
    ),
)
```

---

### Contraintes 4-6 : Cohérence des compteurs

Ces contraintes garantissent la logique métier : **éclos ≤ pondus**, **non éclos ≤ pondus**, **poussins ≤ éclos**.

#### 4. Œufs éclos ≤ Œufs pondus

```python
models.CheckConstraint(
    name="resume_eclos_le_pondus",
    check=(
        Q(nombre_oeufs_eclos__isnull=True)
        | Q(nombre_oeufs_pondus__isnull=True)
        | Q(nombre_oeufs_eclos__lte=models.F("nombre_oeufs_pondus"))
    ),
)
```

**Interprétation** : La contrainte est respectée si :
- `nombre_oeufs_eclos` est NULL (non observé)
- OU `nombre_oeufs_pondus` est NULL (non observé)
- OU `nombre_oeufs_eclos ≤ nombre_oeufs_pondus`

**Exemples** :
```python
# ✅ VALIDE : 3 œufs éclos sur 5 pondus
ResumeObservation(nombre_oeufs_pondus=5, nombre_oeufs_eclos=3)

# ✅ VALIDE : données manquantes
ResumeObservation(nombre_oeufs_pondus=None, nombre_oeufs_eclos=None)

# ✅ VALIDE : ponte connue, éclosion non observée
ResumeObservation(nombre_oeufs_pondus=5, nombre_oeufs_eclos=None)

# ❌ INVALIDE : 6 œufs éclos mais seulement 5 pondus (incohérent)
ResumeObservation(nombre_oeufs_pondus=5, nombre_oeufs_eclos=6)
```

#### 5. Œufs non éclos ≤ Œufs pondus

```python
models.CheckConstraint(
    name="resume_non_eclos_le_pondus",
    check=(
        Q(nombre_oeufs_non_eclos__isnull=True)
        | Q(nombre_oeufs_pondus__isnull=True)
        | Q(nombre_oeufs_non_eclos__lte=models.F("nombre_oeufs_pondus"))
    ),
)
```

**Exemples** :
```python
# ✅ VALIDE : 5 pondus, 3 éclos, 2 non éclos (3+2=5 ✓)
ResumeObservation(
    nombre_oeufs_pondus=5,
    nombre_oeufs_eclos=3,
    nombre_oeufs_non_eclos=2
)

# ❌ INVALIDE : 5 pondus mais 6 non éclos
ResumeObservation(nombre_oeufs_pondus=5, nombre_oeufs_non_eclos=6)
```

#### 6. Poussins ≤ Œufs éclos

```python
models.CheckConstraint(
    name="resume_poussins_le_eclos",
    check=(
        Q(nombre_poussins__isnull=True)
        | Q(nombre_oeufs_eclos__isnull=True)
        | Q(nombre_poussins__lte=models.F("nombre_oeufs_eclos"))
    ),
)
```

**Exemples** :
```python
# ✅ VALIDE : 3 éclos, 2 poussins observés (1 poussin mort)
ResumeObservation(nombre_oeufs_eclos=3, nombre_poussins=2)

# ❌ INVALIDE : 3 éclos mais 4 poussins (impossible)
ResumeObservation(nombre_oeufs_eclos=3, nombre_poussins=4)
```

---

## Cas d'usage

### Création automatique

Le `ResumeObservation` est créé automatiquement lors de la création de la fiche :

```python
fiche = FicheObservation.objects.create(
    observateur=user,
    espece=espece_mesange,
    annee=2025
)

# ResumeObservation créé automatiquement avec valeurs NULL
resume = fiche.resume
print(resume.nombre_oeufs_pondus)  # None (non observé)
```

### Remplissage progressif

```python
resume = fiche.resume

# 1. Observation de la ponte (15 avril)
resume.premier_oeuf_pondu_jour = 15
resume.premier_oeuf_pondu_mois = 4
resume.nombre_oeufs_pondus = 5
resume.save()

# 2. Observation de l'éclosion (5 mai)
resume.premier_poussin_eclos_jour = 5
resume.premier_poussin_eclos_mois = 5
resume.nombre_oeufs_eclos = 4
resume.nombre_oeufs_non_eclos = 1
resume.save()

# 3. Observation des poussins volants (25 mai)
resume.premier_poussin_volant_jour = 25
resume.premier_poussin_volant_mois = 5
resume.nombre_poussins = 3  # 1 poussin mort après éclosion
resume.save()
```

### Validation avant sauvegarde

```python
from django.core.exceptions import ValidationError

try:
    resume = fiche.resume
    resume.nombre_oeufs_pondus = 5
    resume.nombre_oeufs_eclos = 6  # ❌ Erreur : 6 > 5
    resume.save()
except Exception as e:
    print(f"Erreur : {e}")
    # IntegrityError: CHECK constraint failed: resume_eclos_le_pondus
```

---

## Requêtes ORM courantes

### Fiches avec ponte complète

```python
from django.db.models import Q

fiches_ponte = FicheObservation.objects.filter(
    Q(resume__nombre_oeufs_pondus__isnull=False) &
    Q(resume__nombre_oeufs_pondus__gt=0)
).select_related('resume', 'espece')

for fiche in fiches_ponte:
    print(f"{fiche.espece.nom} : {fiche.resume.nombre_oeufs_pondus} œufs")
```

### Fiches avec dates de ponte renseignées

```python
fiches_dates = FicheObservation.objects.filter(
    resume__premier_oeuf_pondu_jour__isnull=False
).select_related('resume')

for fiche in fiches_dates:
    jour = fiche.resume.premier_oeuf_pondu_jour
    mois = fiche.resume.premier_oeuf_pondu_mois
    print(f"Ponte : {jour}/{mois}/{fiche.annee}")
```

### Statistiques par espèce

```python
from django.db.models import Avg, Count, Max, Min

stats = FicheObservation.objects.values('espece__nom').annotate(
    nb_fiches=Count('num_fiche'),
    ponte_moyenne=Avg('resume__nombre_oeufs_pondus'),
    ponte_min=Min('resume__nombre_oeufs_pondus'),
    ponte_max=Max('resume__nombre_oeufs_pondus'),
    eclosion_moyenne=Avg('resume__nombre_oeufs_eclos')
).order_by('-nb_fiches')

# Exemple de résultat :
# {
#     'espece__nom': 'Mésange bleue',
#     'nb_fiches': 150,
#     'ponte_moyenne': 8.5,
#     'ponte_min': 5,
#     'ponte_max': 12,
#     'eclosion_moyenne': 7.2
# }
```

### Taux de succès de reproduction

```python
from django.db.models import F, FloatField, ExpressionWrapper

fiches_avec_taux = FicheObservation.objects.filter(
    resume__nombre_oeufs_pondus__gt=0
).annotate(
    taux_eclosion=ExpressionWrapper(
        F('resume__nombre_oeufs_eclos') * 100.0 / F('resume__nombre_oeufs_pondus'),
        output_field=FloatField()
    )
).select_related('espece', 'resume')

for fiche in fiches_avec_taux:
    print(f"Fiche {fiche.num_fiche} : {fiche.taux_eclosion:.1f}% d'éclosion")
```

---

## Algorithme de complétude

Le `ResumeObservation` contribue au calcul du pourcentage de complétion de la fiche (voir [workflow-correction.md](workflow-correction.md)).

**Critère 5** : Résumé avec données d'œufs (+1 point)

```python
# Extrait de EtatCorrection.calculer_pourcentage_completion()
if hasattr(self.fiche, 'resume'):
    resume = self.fiche.resume
    if resume.nombre_oeufs_pondus is not None and resume.nombre_oeufs_pondus > 0:
        score += 1  # +12.5% au total
```

---

## Points d'attention

### Contraintes CHECK au niveau base de données

Les 6 contraintes CHECK sont appliquées **au niveau de la base de données** (PostgreSQL/SQLite).

**Conséquence** :
- ✅ Protection maximale des données (même en cas de requête SQL directe)
- ⚠️ Erreur `IntegrityError` si violation (pas `ValidationError`)
- ⚠️ Gestion d'erreur à prévoir dans les vues/formulaires

**Exemple de gestion** :
```python
from django.db import IntegrityError

try:
    resume.save()
except IntegrityError as e:
    if 'resume_eclos_le_pondus' in str(e):
        messages.error(request, "Le nombre d'œufs éclos ne peut pas dépasser le nombre d'œufs pondus")
    elif 'resume_poussins_le_eclos' in str(e):
        messages.error(request, "Le nombre de poussins ne peut pas dépasser le nombre d'œufs éclos")
    else:
        messages.error(request, "Erreur de cohérence des données")
```

### Distinction NULL vs 0

**NULL** : "Je ne sais pas" / "Non observé"
**0** : "J'ai observé et la valeur est zéro"

**Exemple métier** :
```python
# Cas 1 : Nid trouvé vide (échec avant ponte)
resume.nombre_oeufs_pondus = 0  # Observation : 0 œuf

# Cas 2 : Nid trouvé avec œufs, éclosion non suivie
resume.nombre_oeufs_pondus = 5
resume.nombre_oeufs_eclos = None  # Non observé
```

### Validation jour/mois (31 jours max)

Les validators `MaxValueValidator(31)` ne vérifient PAS la validité calendaire :
- ✅ Accepte : `jour=31, mois=2` (31 février, invalide)
- ⚠️ À valider au niveau formulaire

**Validation recommandée** :
```python
from datetime import datetime

def valider_date_partielle(jour, mois, annee):
    try:
        datetime(annee, mois, jour)
        return True
    except ValueError:
        return False

# Dans le formulaire
if jour and mois:
    if not valider_date_partielle(jour, mois, fiche.annee):
        raise ValidationError(f"{jour}/{mois}/{fiche.annee} n'est pas une date valide")
```

---

## Voir aussi

- **[Fiches d'observation](observations.md)** - Modèle `FicheObservation` parent
- **[Workflow de correction](workflow-correction.md)** - Algorithme de complétude utilisant `ResumeObservation`
- **[Diagramme ERD](../diagrammes/erd.md)** - Vue d'ensemble des relations
- **[Stratégie de tests](../../testing/STRATEGIE_TESTS.md)** - Tests unitaires des contraintes CHECK

---

*Dernière mise à jour : 2025-10-20*
