# Review - Pièges et points d'attention

Ce fichier documente les erreurs récurrentes et pièges rencontrés dans l'application review.

---

## 🔥 Problème : Modification de save() sans comprendre la logique automatique

### Contexte
`Validation.save()` crée **automatiquement** un `HistoriqueValidation` lors d'un changement de statut.

### Symptôme
- Doublons d'historique
- Historique manquant
- Erreurs sur champs requis

### Cause
Modification de `save()` sans tenir compte de la logique existante.

### Solution

**TOUJOURS lire le code existant avant de modifier** :

```python
# review/models.py:23-34
def save(self, *args, **kwargs):
    if self.pk:  # Si modification (pas création)
        ancienne_instance = Validation.objects.filter(pk=self.pk).first()

        # Si le statut a changé → créer un historique
        if ancienne_instance and ancienne_instance.statut != self.statut:
            HistoriqueValidation.objects.create(
                validation=self,
                ancien_statut=ancienne_instance.statut,
                nouveau_statut=self.statut,
                modifie_par=self.reviewer,
            )

    super().save(*args, **kwargs)
```

**✅ CORRECT** : Laisser save() créer l'historique automatiquement

```python
validation = Validation.objects.get(id=42)
validation.statut = 'validee'
validation.save()  # ✅ Historique créé automatiquement
```

**❌ INCORRECT** : Créer manuellement l'historique

```python
validation.statut = 'validee'
validation.save()

# ❌ Doublon : save() a déjà créé l'historique !
HistoriqueValidation.objects.create(
    validation=validation,
    ancien_statut='en_cours',
    nouveau_statut='validee',
    modifie_par=reviewer
)
```

### Prévention
- **Toujours lire** `review/models.py` avant toute modification
- **Ne jamais** créer `HistoriqueValidation` manuellement (sauf cas exceptionnel)
- **Tester** qu'un seul historique est créé par changement de statut

### Fichiers concernés
- `review/models.py:23-34` (logique save())

---

## ⚠️ Problème : CASCADE delete sur reviewer

### Contexte
`Validation.reviewer` a `on_delete=models.CASCADE`.

### Symptôme
Suppression d'un utilisateur reviewer → suppression de toutes ses validations.

### Cause
Comportement CASCADE voulu mais **perte de traçabilité**.

### Solution

**Avant de supprimer un reviewer** :

```python
reviewer = Utilisateur.objects.get(username='marie.dupont')

# Vérifier le nombre de validations
nb_validations = reviewer.validation_set.count()
print(f"Attention : {nb_validations} validations seront supprimées")

# Vérifier les fiches impactées
fiches_impactees = FicheObservation.objects.filter(
    validations__reviewer=reviewer
).distinct()

for fiche in fiches_impactees:
    print(f"Fiche {fiche.num_fiche} : {fiche.validations.filter(reviewer=reviewer).count()} validations")
```

**Alternative** : Changer pour `SET_NULL` si on veut conserver l'historique

```python
# À modifier dans review/models.py si besoin
reviewer = models.ForeignKey(
    Utilisateur,
    on_delete=models.SET_NULL,  # Conserver l'historique
    null=True,
    blank=True,
    limit_choices_to={'role': 'reviewer'}
)
```

### Prévention
- Ne supprimer un reviewer que si aucune validation n'existe
- Archiver les reviewers au lieu de les supprimer (soft delete)

### Fichiers concernés
- `review/models.py:16-18` (CASCADE on reviewer)

---

## ⚠️ Problème : Validation par un non-reviewer

### Contexte
`Validation.reviewer` a une contrainte `limit_choices_to={'role': 'reviewer'}`.

### Symptôme
Dans l'admin Django, seuls les reviewers apparaissent dans le champ. Mais **en code Python, la contrainte n'est pas appliquée** !

### Cause
`limit_choices_to` ne s'applique qu'aux formulaires Django, pas aux opérations ORM.

### Solution

**Toujours valider le rôle en code** :

```python
# ✅ CORRECT : Vérifier le rôle avant création
utilisateur = Utilisateur.objects.get(username='jean.dupont')

if utilisateur.role != 'reviewer':
    raise ValueError(f"L'utilisateur {utilisateur.username} n'est pas un reviewer")

validation = Validation.objects.create(
    fiche=fiche,
    reviewer=utilisateur,
    statut='en_cours'
)
```

**❌ INCORRECT** : Faire confiance à la contrainte

```python
# ❌ Pas de vérification : peut créer une validation avec un non-reviewer
validation = Validation.objects.create(
    fiche=fiche,
    reviewer=observateur,  # observateur n'est pas reviewer !
    statut='en_cours'
)
```

**Meilleure solution** : Ajouter une méthode de validation au modèle

```python
# review/models.py
class Validation(models.Model):
    # ...

    def clean(self):
        super().clean()
        if self.reviewer and self.reviewer.role != 'reviewer':
            raise ValidationError(
                f"L'utilisateur {self.reviewer.username} n'a pas le rôle 'reviewer'"
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Appliquer clean() avant save
        # ... reste du code
```

### Prévention
- Toujours valider le rôle avant assignation
- Implémenter `clean()` sur le modèle
- Ajouter des tests unitaires

### Fichiers concernés
- `review/models.py:16-18` (contrainte limit_choices_to)

---

## ⚠️ Problème : Coordonner Validation et EtatCorrection

### Contexte
`Validation` (review) et `EtatCorrection` (observations) doivent être cohérents.

### Symptôme
- Fiche marquée `EtatCorrection.statut='valide'` mais pas toutes les validations à 'validee'
- Fiche avec toutes validations 'validee' mais `EtatCorrection.statut='en_cours'`

### Cause
Pas de synchronisation automatique entre les deux modèles.

### Solution

**Vérifier toutes les validations avant de marquer comme valide** :

```python
# ✅ CORRECT : Workflow complet
fiche = FicheObservation.objects.get(num_fiche=123)

# Vérifier que toutes les validations sont 'validee'
validations = fiche.validations.all()

if not validations.exists():
    raise ValueError("Aucune validation pour cette fiche")

toutes_validees = all(v.statut == 'validee' for v in validations)
une_rejetee = any(v.statut == 'rejete' for v in validations)

if toutes_validees:
    # Marquer la fiche comme validée
    fiche.etat_correction.statut = 'valide'
    fiche.etat_correction.date_validation = timezone.now()
    fiche.etat_correction.validee_par = validations.first().reviewer  # Ou le dernier
    fiche.etat_correction.save()

elif une_rejetee:
    # Retour à l'observateur pour corrections
    fiche.etat_correction.statut = 'en_edition'
    fiche.etat_correction.save()
```

**Requête optimisée** :

```python
from django.db.models import Q, Count

# Fiches avec toutes les validations à 'validee'
fiches_validees = FicheObservation.objects.annotate(
    nb_validations=Count('validations'),
    nb_validees=Count('validations', filter=Q(validations__statut='validee'))
).filter(nb_validations=models.F('nb_validees'), nb_validations__gt=0)

# Mettre à jour leur EtatCorrection
for fiche in fiches_validees:
    if fiche.etat_correction.statut != 'valide':
        fiche.etat_correction.statut = 'valide'
        fiche.etat_correction.date_validation = timezone.now()
        fiche.etat_correction.save()
```

### Prévention
- Créer une méthode `fiche.verifier_validations_completes()` dans `FicheObservation`
- Utiliser un signal `post_save` sur `Validation` pour mettre à jour `EtatCorrection`
- Ajouter des tests pour vérifier la cohérence

### Fichiers concernés
- `review/models.py` (Validation)
- `observations/models.py` (EtatCorrection)

---

## ⚠️ Problème : Validations simultanées (race condition)

### Contexte
Plusieurs reviewers peuvent valider la même fiche en même temps.

### Symptôme
- Deux reviewers marquent la fiche comme 'valide' presque simultanément
- Incohérence entre validations et EtatCorrection

### Cause
Pas de verrouillage transactionnel lors de la mise à jour.

### Solution

**Utiliser select_for_update() pour verrouiller** :

```python
from django.db import transaction

@transaction.atomic
def valider_fiche(validation_id, nouveau_statut):
    # Verrouiller la validation pour éviter les conflits
    validation = Validation.objects.select_for_update().get(id=validation_id)

    # Vérifier le statut actuel
    if validation.statut == nouveau_statut:
        return  # Déjà dans cet état

    # Changer le statut
    validation.statut = nouveau_statut
    validation.save()

    # Verrouiller la fiche pour vérifier toutes les validations
    fiche = FicheObservation.objects.select_for_update().get(pk=validation.fiche_id)
    validations = fiche.validations.all()

    toutes_validees = all(v.statut == 'validee' for v in validations)

    if toutes_validees:
        fiche.etat_correction.statut = 'valide'
        fiche.etat_correction.date_validation = timezone.now()
        fiche.etat_correction.save()
```

### Prévention
- Toujours utiliser des transactions atomiques
- Utiliser `select_for_update()` pour verrouiller les objets
- Tester avec plusieurs utilisateurs simultanés

### Fichiers concernés
- `review/views.py` (quand implémenté)

---

## ⚠️ Problème : Suppression de HistoriqueValidation

### Contexte
`HistoriqueValidation` stocke la traçabilité complète des changements.

### Symptôme
Perte de traçabilité, historique incomplet.

### Cause
Suppression manuelle ou CASCADE delete.

### Solution

**JAMAIS supprimer HistoriqueValidation** :

```python
# ❌ INCORRECT : Perte de traçabilité
HistoriqueValidation.objects.filter(validation=validation).delete()

# ✅ CORRECT : Conserver l'historique
# Ne jamais supprimer l'historique !
```

**Si besoin de "nettoyer"** : Archiver plutôt que supprimer

```python
# Option : Soft delete (ajouter un champ archive)
class HistoriqueValidation(models.Model):
    # ...
    archive = models.BooleanField(default=False)

# Archiver au lieu de supprimer
HistoriqueValidation.objects.filter(
    date_modification__lt=timezone.now() - timedelta(days=365*5)
).update(archive=True)
```

### Prévention
- Ne jamais supprimer `HistoriqueValidation` en production
- Utiliser soft delete si archivage nécessaire
- Sauvegarder régulièrement la base de données

### Fichiers concernés
- `review/models.py:37-48` (HistoriqueValidation)

---

## ⚠️ Problème : Valider une fiche qui n'est pas en_cours

### Contexte
Une fiche doit être dans l'état `EtatCorrection.statut='en_cours'` avant validation.

### Symptôme
Création de validations sur des fiches en_edition, nouveau, ou déjà validées.

### Cause
Pas de vérification de l'état de la fiche avant création de validation.

### Solution

**Toujours vérifier l'état avant création** :

```python
# ✅ CORRECT : Vérifier l'état
fiche = FicheObservation.objects.get(num_fiche=123)

if not hasattr(fiche, 'etat_correction'):
    raise ValueError("La fiche n'a pas d'état de correction")

if fiche.etat_correction.statut != 'en_cours':
    raise ValueError(
        f"La fiche doit être en cours de révision (statut actuel : {fiche.etat_correction.get_statut_display()})"
    )

# Créer la validation
validation = Validation.objects.create(
    fiche=fiche,
    reviewer=reviewer,
    statut='en_cours'
)
```

**❌ INCORRECT** : Créer sans vérifier

```python
# ❌ Pas de vérification
validation = Validation.objects.create(
    fiche=fiche,  # Peut être en_edition, nouveau, ou déjà valide !
    reviewer=reviewer,
    statut='en_cours'
)
```

### Prévention
- Implémenter `clean()` sur Validation pour vérifier l'état
- Ajouter des contraintes en base de données si possible
- Vérifier dans les vues avant création

### Fichiers concernés
- `review/models.py` (Validation)
- `observations/models.py` (EtatCorrection)

---

## ⚠️ Problème : Plusieurs validations par le même reviewer

### Contexte
Un reviewer peut-il créer plusieurs validations pour la même fiche ?

### Symptôme
Doublons de validations par le même reviewer.

### Cause
Pas de contrainte UNIQUE sur (fiche, reviewer).

### Solution

**Option 1** : Ajouter une contrainte unique au modèle

```python
# review/models.py
class Validation(models.Model):
    # ...

    class Meta:
        ordering = ['-date_modification']
        constraints = [
            models.UniqueConstraint(
                fields=['fiche', 'reviewer'],
                name='unique_validation_par_reviewer'
            )
        ]
```

**Option 2** : Utiliser get_or_create en code

```python
# ✅ CORRECT : Éviter les doublons
validation, created = Validation.objects.get_or_create(
    fiche=fiche,
    reviewer=reviewer,
    defaults={'statut': 'en_cours'}
)

if not created:
    # Déjà une validation par ce reviewer
    validation.statut = 'en_cours'  # Réinitialiser si besoin
    validation.save()
```

### Prévention
- Décider si plusieurs validations par reviewer sont permises
- Ajouter contrainte UNIQUE si non permis
- Utiliser `get_or_create()` en code

### Fichiers concernés
- `review/models.py` (Validation)

---

## ✅ Bonnes pratiques

### 1. Toujours utiliser des transactions atomiques

```python
from django.db import transaction

@transaction.atomic
def workflow_validation_complete(fiche, reviewer, nouveau_statut):
    # Tout ou rien
    validation = Validation.objects.get(fiche=fiche, reviewer=reviewer)
    validation.statut = nouveau_statut
    validation.save()

    # Mettre à jour EtatCorrection si nécessaire
    if nouveau_statut == 'validee':
        toutes_validees = all(v.statut == 'validee' for v in fiche.validations.all())
        if toutes_validees:
            fiche.etat_correction.statut = 'valide'
            fiche.etat_correction.save()
```

### 2. Vérifier les statuts avant actions

```python
def peut_etre_validee(fiche):
    """Vérifie si une fiche peut recevoir des validations"""
    if not hasattr(fiche, 'etat_correction'):
        return False
    return fiche.etat_correction.statut == 'en_cours'
```

### 3. Logger les changements de statut

```python
import logging
logger = logging.getLogger(__name__)

validation.statut = 'validee'
validation.save()

logger.info(
    f"Validation {validation.id} : fiche {validation.fiche.num_fiche} validée par {validation.reviewer.username}"
)
```

### 4. Requêtes optimisées

```python
# Toujours utiliser select_related pour les ForeignKey
validations = Validation.objects.select_related(
    'fiche',
    'reviewer',
    'fiche__etat_correction'
).all()

# Précharger l'historique
validations = Validation.objects.prefetch_related(
    'historique'
).all()
```

---

## 🔥 Checklist avant modification de review

- [ ] Lire ce fichier gotchas.md
- [ ] Comprendre la logique automatique de save() (création d'historique)
- [ ] Vérifier les états de EtatCorrection avant création de Validation
- [ ] Utiliser des transactions atomiques
- [ ] Vérifier que reviewer.role == 'reviewer'
- [ ] Ne jamais supprimer HistoriqueValidation
- [ ] Coordonner Validation et EtatCorrection
- [ ] Tester avec plusieurs reviewers simultanés

---

*Dernière mise à jour : 2025-12-27*
