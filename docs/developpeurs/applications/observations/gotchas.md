# Observations - Pièges et points d'attention

Ce fichier documente les erreurs récurrentes et pièges rencontrés dans l'application observations.

---

## 🔥 Problème : Modification de la méthode `save()` de FicheObservation

### Contexte
La méthode `save()` de `FicheObservation` crée automatiquement 5 objets liés lors de la première sauvegarde.

### Symptôme
- Objets liés non créés (erreurs `DoesNotExist`)
- Doublons d'objets liés (IntegrityError sur OneToOneField)
- Perte de transactions atomiques

### Cause
Modification incorrecte de la logique de création automatique.

### Code CORRECT

```python
@transaction.atomic
def save(self, *args, **kwargs):
    is_new = self.pk is None  # ✅ Détecte nouvelle fiche

    super().save(*args, **kwargs)  # ✅ Sauvegarder d'abord (génère le PK)

    # ✅ TOUJOURS utiliser get_or_create (pas create)
    if is_new:
        Localisation.objects.get_or_create(fiche=self, defaults={...})
        Nid.objects.get_or_create(fiche=self, defaults={...})
        ResumeObservation.objects.get_or_create(fiche=self, defaults={...})
        CausesEchec.objects.get_or_create(fiche=self, defaults={...})
        EtatCorrection.objects.get_or_create(fiche=self, defaults={...})
```

### Code INCORRECT

```python
# ❌ INCORRECT 1 : Utilise create au lieu de get_or_create
if is_new:
    Localisation.objects.create(fiche=self, ...)  # Peut créer des doublons

# ❌ INCORRECT 2 : Pas de @transaction.atomic
def save(self, *args, **kwargs):  # Si erreur → objets partiellement créés
    is_new = self.pk is None
    super().save(*args, **kwargs)
    if is_new:
        Localisation.objects.get_or_create(fiche=self, ...)

# ❌ INCORRECT 3 : Créer AVANT super().save()
if is_new:
    Localisation.objects.get_or_create(fiche=self, ...)  # self.pk est encore None!
super().save(*args, **kwargs)
```

### Solution
- **Toujours** utiliser `get_or_create()` (pas `create()`)
- **Toujours** utiliser `@transaction.atomic`
- **Toujours** appeler `super().save()` AVANT de créer les objets liés

### Prévention
- Ne **jamais** modifier `save()` sans lire ce document
- Tester avec plusieurs appels à `save()` pour vérifier qu'il n'y a pas de doublons
- Vérifier que tous les objets liés sont créés

### Fichiers concernés
- `observations/models.py:42-97` (méthode save de FicheObservation)

---

## ⚠️ Problème : Contraintes de cohérence sur ResumeObservation

### Contexte
Le modèle `ResumeObservation` a des contraintes complexes (paires jour/mois, compteurs cohérents).

### Symptôme
```
IntegrityError: CHECK constraint failed: resume_eclos_le_pondus
```

### Cause
Violation des contraintes de cohérence :
- `nombre_oeufs_eclos > nombre_oeufs_pondus`
- `nombre_poussins > nombre_oeufs_eclos`
- Jour renseigné mais pas le mois (ou vice versa)

### Solution

**1. Paires jour/mois** : Soit les deux NULL, soit les deux renseignés

```python
# ✅ CORRECT
resume.premier_oeuf_pondu_jour = 15
resume.premier_oeuf_pondu_mois = 4

# ✅ CORRECT
resume.premier_oeuf_pondu_jour = None
resume.premier_oeuf_pondu_mois = None

# ❌ INCORRECT
resume.premier_oeuf_pondu_jour = 15
resume.premier_oeuf_pondu_mois = None  # ERREUR : paire incomplète
```

**2. Compteurs cohérents**

```python
# ✅ CORRECT : éclos ≤ pondus, poussins ≤ éclos
resume.nombre_oeufs_pondus = 4
resume.nombre_oeufs_eclos = 3
resume.nombre_oeufs_non_eclos = 1
resume.nombre_poussins = 2

# ❌ INCORRECT : éclos > pondus
resume.nombre_oeufs_pondus = 4
resume.nombre_oeufs_eclos = 5  # ERREUR : impossible

# ❌ INCORRECT : poussins > éclos
resume.nombre_oeufs_eclos = 3
resume.nombre_poussins = 4  # ERREUR : impossible
```

### Prévention
- Valider les données dans les formulaires AVANT la sauvegarde
- Utiliser des validateurs Django
- Afficher des messages d'erreur clairs à l'utilisateur

### Fichiers concernés
- `observations/models.py:204-270` (contraintes CheckConstraint)
- `observations/forms.py` (validation des formulaires)

---

## ⚠️ Problème : NULL vs 0 pour les compteurs

### Contexte
Les champs comme `hauteur_nid`, `nombre_oeufs_pondus` acceptent NULL.

### Symptôme
Confusion entre "non observé" et "valeur observée de 0".

### Cause
Mélange entre NULL et 0.

### Solution

**Convention** :
- `NULL` = **Non observé / Non renseigné**
- `0` = **Valeur observée de 0**

```python
# ✅ CORRECT : Nid au sol
nid.hauteur_nid = 0  # Valeur observée : nid au sol

# ✅ CORRECT : Hauteur non observée
nid.hauteur_nid = None  # Non renseigné

# ✅ CORRECT : Aucun œuf pondu (nidification avortée)
resume.nombre_oeufs_pondus = 0  # Valeur observée : 0

# ✅ CORRECT : Nombre d'œufs non observé
resume.nombre_oeufs_pondus = None  # Non renseigné
```

### Prévention
- Documenter clairement dans les formulaires
- Utiliser des champs séparés : "Non observé" (checkbox) + "Valeur" (nombre)

### Fichiers concernés
- Tous les modèles avec des IntegerField nullable

---

## ⚠️ Problème : Calcul automatique du pourcentage de complétion

### Contexte
Le modèle `EtatCorrection` calcule automatiquement `pourcentage_completion` lors du `save()`.

### Symptôme
Le pourcentage ne se met pas à jour après modification des données de la fiche.

### Cause
Le calcul est fait uniquement lors du `save()` de `EtatCorrection`, pas de `FicheObservation`.

### Solution

**Recalculer manuellement** après modification :

```python
# Modifier la fiche
fiche.localisation.commune = "Grenoble"
fiche.localisation.save()

# ✅ Recalculer le pourcentage
fiche.mettre_a_jour_etat_correction()

# Ou directement :
fiche.etat_correction.calculer_pourcentage_completion()
fiche.etat_correction.save()
```

### Prévention
- Appeler `mettre_a_jour_etat_correction()` dans les vues après modification
- Utiliser des signaux Django pour automatiser (si besoin)

### Fichiers concernés
- `observations/models.py:99-110` (méthode mettre_a_jour_etat_correction)
- `observations/models.py:337-396` (méthode calculer_pourcentage_completion)

---

## ⚠️ Problème : Cascade delete sur observateur

### Contexte
`FicheObservation.observateur` a `on_delete=models.CASCADE`.

### Symptôme
Suppression d'un utilisateur → toutes ses fiches sont supprimées.

### Cause
Comportement voulu mais **irréversible**.

### Solution

**Avant de supprimer un utilisateur** :
```python
# 1. Vérifier le nombre de fiches
nb_fiches = utilisateur.fiches.count()
print(f"Attention : {nb_fiches} fiches seront supprimées")

# 2. Proposer de transférer les fiches à un autre utilisateur
if nb_fiches > 0:
    autre_utilisateur = Utilisateur.objects.get(username='admin')
    utilisateur.fiches.update(observateur=autre_utilisateur)

# 3. Supprimer l'utilisateur
utilisateur.delete()
```

### Prévention
- Toujours afficher un avertissement avant suppression d'utilisateur
- Proposer le transfert de fiches
- Utiliser soft delete (SoftDeleteModel) si besoin

### Fichiers concernés
- `observations/models.py:17-19` (ForeignKey observateur)

---

## ⚠️ Problème : Protection de l'espèce

### Contexte
`FicheObservation.espece` a `on_delete=models.PROTECT`.

### Symptôme
```
ProtectedError: Cannot delete some instances of model 'Espece' because they are referenced through a protected foreign key
```

### Cause
Tentative de suppression d'une espèce qui a des observations.

### Solution

**Pour supprimer une espèce** :
```python
# 1. Vérifier si elle a des observations
espece = Espece.objects.get(nom="Mésange bleue")
nb_observations = espece.observations.count()

if nb_observations > 0:
    print(f"Impossible : {nb_observations} observations")
    # Option 1 : Ne pas supprimer
    # Option 2 : Transférer les observations vers une autre espèce
    autre_espece = Espece.objects.get(nom="Mésange charbonnière")
    espece.observations.update(espece=autre_espece)

# 2. Supprimer l'espèce
espece.delete()
```

### Prévention
- Toujours vérifier `espece.observations.count()` avant suppression
- Afficher un message d'erreur clair à l'utilisateur

### Fichiers concernés
- `observations/models.py:20` (ForeignKey espece)

---

## ⚠️ Problème : Accès aux objets liés non créés

### Contexte
Si `FicheObservation` créée manuellement (sans passer par `save()`), les objets liés n'existent pas.

### Symptôme
```python
fiche = FicheObservation(observateur=user, espece=espece, annee=2025)
# ❌ ERREUR : les objets liés ne sont pas créés
print(fiche.localisation)  # RelatedObjectDoesNotExist
```

### Cause
Les objets liés sont créés dans `save()`, pas dans `__init__()`.

### Solution

```python
# ✅ CORRECT : Utiliser create() ou save()
fiche = FicheObservation.objects.create(
    observateur=user,
    espece=espece,
    annee=2025
)
# Les objets liés sont créés automatiquement
print(fiche.localisation)  # OK

# Ou :
fiche = FicheObservation(observateur=user, espece=espece, annee=2025)
fiche.save()  # Crée les objets liés
print(fiche.localisation)  # OK
```

### Prévention
- **Toujours** sauvegarder la fiche avant d'accéder aux objets liés
- Vérifier avec `hasattr()` si nécessaire

### Fichiers concernés
- `observations/models.py:42-97` (méthode save)

---

## ⚠️ Problème : Format de date pour Observation

### Contexte
`Observation.date_observation` est un `DateTimeField`, mais l'heure peut être inconnue.

### Symptôme
Confusion sur l'affichage de la date (avec ou sans heure).

### Cause
Le champ `heure_connue` indique si l'heure est fiable.

### Solution

```python
# ✅ CORRECT : Heure connue
obs = Observation.objects.create(
    fiche=fiche,
    date_observation=datetime(2025, 4, 15, 10, 30),  # Date + heure
    heure_connue=True,
    ...
)

# ✅ CORRECT : Heure inconnue
obs = Observation.objects.create(
    fiche=fiche,
    date_observation=datetime(2025, 4, 15, 0, 0),  # Heure à 00:00
    heure_connue=False,  # Indiquer que l'heure n'est pas fiable
    ...
)

# Affichage
if obs.heure_connue:
    print(obs.date_observation.strftime('%d/%m/%Y %H:%M'))
else:
    print(obs.date_observation.strftime('%d/%m/%Y'))
```

### Prévention
- Toujours utiliser `heure_connue` pour l'affichage
- Documenter dans les formulaires

### Fichiers concernés
- `observations/models.py:136-163` (modèle Observation)

---

## ✅ Bonnes pratiques

### 1. Utiliser select_related / prefetch_related

```python
# ✅ CORRECT : 1 requête SQL au lieu de N+6
fiche = FicheObservation.objects.select_related(
    'observateur', 'espece', 'localisation', 'nid', 'resume',
    'causes_echec', 'etat_correction'
).get(num_fiche=123)

# ❌ INCORRECT : N+6 requêtes SQL
fiche = FicheObservation.objects.get(num_fiche=123)
print(fiche.observateur.username)  # Requête SQL
print(fiche.espece.nom)  # Requête SQL
print(fiche.localisation.commune)  # Requête SQL
# ...
```

### 2. Toujours valider les données dans les formulaires

```python
# forms.py
def clean(self):
    cleaned_data = super().clean()
    eclos = cleaned_data.get('nombre_oeufs_eclos')
    pondus = cleaned_data.get('nombre_oeufs_pondus')

    if eclos and pondus and eclos > pondus:
        raise ValidationError("Le nombre d'œufs éclos ne peut pas dépasser le nombre d'œufs pondus")

    return cleaned_data
```

### 3. Utiliser transactions pour les opérations multiples

```python
from django.db import transaction

@transaction.atomic
def creer_fiche_complete(observateur, espece, annee, data):
    # Créer la fiche
    fiche = FicheObservation.objects.create(
        observateur=observateur,
        espece=espece,
        annee=annee
    )

    # Remplir les données (tout ou rien)
    fiche.localisation.commune = data['commune']
    fiche.localisation.save()

    fiche.nid.hauteur_nid = data['hauteur_nid']
    fiche.nid.save()

    return fiche
```

---

## 🔥 Checklist avant modification d'observations

- [ ] Lire ce fichier gotchas.md
- [ ] Vérifier les contraintes de cohérence (ResumeObservation)
- [ ] Ne pas modifier `save()` de FicheObservation sans tests
- [ ] Utiliser `get_or_create()` (pas `create()`) pour les objets liés
- [ ] Toujours utiliser `@transaction.atomic` pour les opérations multiples
- [ ] Tester avec plusieurs appels à `save()` (vérifier doublons)
- [ ] Vérifier les cascades (CASCADE, PROTECT)

---

*Dernière mise à jour : 2025-12-27*
