# Domaine : Audit et traçabilité

## Vue d'ensemble

Le modèle **`HistoriqueModification`** enregistre **chaque modification** apportée aux fiches d'observation et leurs objets liés, garantissant une **traçabilité complète** des données.

**Fichier** : `audit/models.py`

---

## Modèle HistoriqueModification

### Rôle métier

Journalise toutes les modifications de données avec :
- Le champ modifié
- L'ancienne et la nouvelle valeur
- L'utilisateur ayant effectué la modification
- La date de modification
- La catégorie de modification (fiche, nid, localisation, etc.)

**Permet** :
- ✅ Audit complet des modifications
- ✅ Récupération de valeurs passées
- ✅ Détection d'erreurs de saisie
- ✅ Analyse des patterns de modifications

### Champs

| Champ | Type | Description | Index |
|-------|------|-------------|-------|
| `fiche` | ForeignKey | Fiche concernée | → `FicheObservation`, CASCADE |
| `champ_modifie` | CharField(100) | Nom du champ modifié | - |
| `ancienne_valeur` | TextField | Valeur avant modification | - |
| `nouvelle_valeur` | TextField | Valeur après modification | - |
| `date_modification` | DateTimeField | Date de la modification | Auto (auto_now_add) |
| `modifie_par` | ForeignKey | Utilisateur ayant modifié | → `Utilisateur`, SET_NULL |
| `categorie` | CharField(20) | Catégorie de modification | Choix, **Indexé** |

### Catégories de modifications

```python
# core/constants.py
CATEGORIE_MODIFICATION_CHOICES = [
    ('fiche', 'Fiche Observation'),
    ('observation', 'Observation'),
    ('validation', 'Validation'),
    ('localisation', 'Localisation'),
    ('nid', 'Nid'),
    ('resume_observation', 'Résumé Observation'),
    ('causes_echec', "Causes d'échec"),
]
```

**Usage** : Permet de filtrer rapidement par type de modification.

### Index

```python
indexes = [
    models.Index(fields=['categorie']),  # Recherche par catégorie
]
```

**Optimise** :
```python
# Modifications de localisation
HistoriqueModification.objects.filter(categorie='localisation')
```

### Ordonnancement

```python
class Meta:
    ordering = ['-date_modification']  # Plus récentes en premier
```

### Localisation dans le code

**Fichier** : `audit/models.py:7-27`

---

## Stratégies d'enregistrement

### Option 1 : Signals Django (recommandé)

Enregistrer automatiquement les modifications via signals `pre_save` :

```python
# observations/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from audit.models import HistoriqueModification

@receiver(pre_save, sender=FicheObservation)
def log_fiche_modification(sender, instance, **kwargs):
    if instance.pk:  # Modification (pas création)
        try:
            old_instance = FicheObservation.objects.get(pk=instance.pk)

            # Comparer chaque champ
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(old_instance, field_name)
                new_value = getattr(instance, field_name)

                if old_value != new_value:
                    HistoriqueModification.objects.create(
                        fiche=instance,
                        champ_modifie=field_name,
                        ancienne_valeur=str(old_value),
                        nouvelle_valeur=str(new_value),
                        categorie='fiche',
                        modifie_par=getattr(instance, '_modifier_user', None)
                    )
        except FicheObservation.DoesNotExist:
            pass

# Dans AppConfig
from django.apps import AppConfig

class ObservationsConfig(AppConfig):
    name = 'observations'

    def ready(self):
        import observations.signals
```

**Avantages** :
- ✅ Automatique et transparent
- ✅ Capture toutes les modifications
- ✅ Pas de code supplémentaire dans les vues

**Inconvénients** :
- ⚠️ Difficulté à récupérer l'utilisateur (`request.user`)
- ⚠️ Performance (1 requête SELECT + N requêtes INSERT par modification)

### Option 2 : Méthode save() surchargée

```python
class FicheObservation(models.Model):
    # ... champs ...

    def save(self, *args, **kwargs):
        modifier_user = kwargs.pop('modifier_user', None)

        if self.pk:
            old_instance = FicheObservation.objects.get(pk=self.pk)

            # Espèce modifiée
            if old_instance.espece != self.espece:
                HistoriqueModification.objects.create(
                    fiche=self,
                    champ_modifie='espece',
                    ancienne_valeur=old_instance.espece.nom,
                    nouvelle_valeur=self.espece.nom,
                    categorie='fiche',
                    modifie_par=modifier_user
                )

        super().save(*args, **kwargs)

# Usage dans les vues
fiche.save(modifier_user=request.user)
```

### Option 3 : Middleware (pour `request.user`)

Stocker `request.user` dans un contexte global :

```python
# core/middleware.py
from threading import local

_thread_locals = local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        return response

# Dans signals
from core.middleware import get_current_user

@receiver(pre_save, sender=FicheObservation)
def log_modification(sender, instance, **kwargs):
    current_user = get_current_user()
    # ... créer HistoriqueModification avec modifie_par=current_user
```

**Ajouter dans `settings.py`** :
```python
MIDDLEWARE = [
    # ...
    'core.middleware.CurrentUserMiddleware',
]
```

---

## Cas d'usage

### Créer une entrée d'historique

```python
from audit.models import HistoriqueModification

# Modification manuelle
HistoriqueModification.objects.create(
    fiche=fiche,
    champ_modifie='commune',
    ancienne_valeur='Paris',
    nouvelle_valeur='Grenoble',
    categorie='localisation',
    modifie_par=request.user
)
```

### Historique d'une fiche

```python
fiche = FicheObservation.objects.get(num_fiche=123)

historique = fiche.modifications.all().select_related('modifie_par')

for modif in historique:
    print(f"{modif.date_modification} : {modif.champ_modifie}")
    print(f"  {modif.ancienne_valeur} → {modif.nouvelle_valeur}")
    print(f"  par {modif.modifie_par.username if modif.modifie_par else 'Système'}")

# Exemple de sortie :
# 2025-10-20 14:30 : commune
#   Paris → Grenoble
#   par user_john
# 2025-10-20 14:32 : altitude
#   0 → 212
#   par user_john
```

### Modifications par utilisateur

```python
user = Utilisateur.objects.get(username='john')

modifications = HistoriqueModification.objects.filter(
    modifie_par=user
).select_related('fiche')

print(f"{user.username} a effectué {modifications.count()} modifications")
```

### Modifications récentes (24h)

```python
from datetime import timedelta
from django.utils import timezone

hier = timezone.now() - timedelta(days=1)

modifications_recentes = HistoriqueModification.objects.filter(
    date_modification__gte=hier
).select_related('fiche', 'modifie_par')

for modif in modifications_recentes:
    print(f"Fiche {modif.fiche.num_fiche} : {modif.champ_modifie} modifié")
```

### Modifications par catégorie

```python
modifs_localisation = HistoriqueModification.objects.filter(
    categorie='localisation'
).values('champ_modifie').annotate(
    nb_modifications=Count('id')
).order_by('-nb_modifications')

for modif in modifs_localisation:
    print(f"{modif['champ_modifie']} : {modif['nb_modifications']} modifications")

# Exemple :
# commune : 245 modifications
# coordonnees : 187 modifications
# altitude : 92 modifications
```

---

## Requêtes ORM courantes

### Fiches les plus modifiées

```python
from django.db.models import Count

fiches_modifiees = FicheObservation.objects.annotate(
    nb_modifications=Count('modifications')
).order_by('-nb_modifications')[:10]

for fiche in fiches_modifiees:
    print(f"Fiche {fiche.num_fiche} : {fiche.nb_modifications} modifications")
```

### Utilisateurs les plus actifs

```python
utilisateurs_actifs = Utilisateur.objects.annotate(
    nb_modifications=Count('modificateur_de')
).order_by('-nb_modifications')[:10]

for user in utilisateurs_actifs:
    print(f"{user.username} : {user.nb_modifications} modifications")
```

### Rollback : Récupérer une ancienne valeur

```python
# Récupérer la dernière modification du champ 'commune'
derniere_modif = HistoriqueModification.objects.filter(
    fiche=fiche,
    champ_modifie='commune'
).order_by('-date_modification').first()

if derniere_modif:
    # Restaurer l'ancienne valeur
    fiche.localisation.commune = derniere_modif.ancienne_valeur
    fiche.localisation.save()

    # Créer une nouvelle entrée d'historique pour le rollback
    HistoriqueModification.objects.create(
        fiche=fiche,
        champ_modifie='commune',
        ancienne_valeur=derniere_modif.nouvelle_valeur,
        nouvelle_valeur=derniere_modif.ancienne_valeur,
        categorie='localisation',
        modifie_par=request.user
    )
```

### Timeline complète d'une fiche

```python
def afficher_timeline(fiche):
    """Affiche la timeline complète d'une fiche"""

    # Toutes les modifications
    modifications = fiche.modifications.all().select_related('modifie_par')

    # Toutes les validations
    validations = fiche.validations.all().select_related('reviewer')

    # Fusionner et trier par date
    events = []

    for modif in modifications:
        events.append({
            'date': modif.date_modification,
            'type': 'modification',
            'description': f"{modif.champ_modifie} : {modif.ancienne_valeur} → {modif.nouvelle_valeur}",
            'user': modif.modifie_par
        })

    for val in validations:
        events.append({
            'date': val.date_modification,
            'type': 'validation',
            'description': f"Statut : {val.statut}",
            'user': val.reviewer
        })

    # Trier par date
    events.sort(key=lambda x: x['date'], reverse=True)

    # Afficher
    for event in events:
        print(f"{event['date']} - {event['type'].upper()}")
        print(f"  {event['description']}")
        print(f"  par {event['user'].username if event['user'] else 'Système'}")
        print()

# Usage
afficher_timeline(fiche)
```

---

## Analyse des patterns

### Champs les plus modifiés

```python
from django.db.models import Count

champs_populaires = HistoriqueModification.objects.values(
    'champ_modifie', 'categorie'
).annotate(
    nb_modifications=Count('id')
).order_by('-nb_modifications')[:20]

for champ in champs_populaires:
    print(f"{champ['categorie']}.{champ['champ_modifie']} : {champ['nb_modifications']}")

# Exemple :
# localisation.commune : 450 modifications
# nid.hauteur_nid : 320 modifications
# resume_observation.nombre_oeufs_pondus : 280 modifications
```

### Détection d'erreurs de saisie

```python
# Trouver les fiches avec commune modifiée plusieurs fois
from django.db.models import Count

fiches_commune_instable = HistoriqueModification.objects.filter(
    champ_modifie='commune',
    categorie='localisation'
).values('fiche').annotate(
    nb_changements=Count('id')
).filter(nb_changements__gte=3)

for fiche_id in fiches_commune_instable:
    fiche = FicheObservation.objects.get(num_fiche=fiche_id['fiche'])
    print(f"Fiche {fiche.num_fiche} : commune modifiée {fiche_id['nb_changements']} fois")
    # → Possibilité d'erreur de saisie ou d'incertitude
```

### Activité par jour de la semaine

```python
from django.db.models.functions import ExtractWeekDay

activite = HistoriqueModification.objects.annotate(
    jour_semaine=ExtractWeekDay('date_modification')
).values('jour_semaine').annotate(
    nb_modifications=Count('id')
).order_by('jour_semaine')

jours = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']

for jour in activite:
    print(f"{jours[jour['jour_semaine']-1]} : {jour['nb_modifications']} modifications")
```

---

## Points d'attention

### Performance : Volume de données

L'historique peut devenir **très volumineux** (plusieurs milliers/millions d'entrées).

**Optimisations** :
1. **Index sur `fiche`** : Déjà présent (ForeignKey auto-indexé)
2. **Index sur `date_modification`** : Pour filtres temporels
   ```python
   indexes = [
       models.Index(fields=['categorie']),
       models.Index(fields=['date_modification']),  # Ajouter
   ]
   ```
3. **Partitionnement** : Archiver les modifications > 1 an
   ```python
   # Script de nettoyage
   from datetime import timedelta
   from django.utils import timezone

   un_an = timezone.now() - timedelta(days=365)
   HistoriqueModification.objects.filter(
       date_modification__lt=un_an
   ).delete()
   ```

### Suppression CASCADE

```python
# Si FicheObservation supprimée → tous ses HistoriqueModification supprimés
fiche.delete()  # Supprime aussi son historique

# Si Utilisateur supprimé → modifie_par = NULL (SET_NULL)
user.delete()  # Historique conservé mais sans auteur
```

**Recommandation** : Soft delete pour FicheObservation et Utilisateur.

### Valeurs sensibles

Éviter de logger les **mots de passe, tokens, données personnelles sensibles**.

**Filtrage** :
```python
CHAMPS_EXCLUS = ['password', 'token', 'api_key']

if field_name not in CHAMPS_EXCLUS:
    HistoriqueModification.objects.create(...)
```

### Format des valeurs (TextField)

Les valeurs sont stockées en **texte brut** (`str(value)`).

**Problème** : Perte de type (int, bool, date, etc.)

**Solutions** :
1. **Parser à la lecture** :
   ```python
   ancienne_valeur_int = int(modif.ancienne_valeur)
   ```
2. **Stocker en JSON** (optionnel) :
   ```python
   import json

   nouvelle_valeur = json.dumps({
       'type': 'int',
       'value': 42
   })

   # À la lecture
   data = json.loads(modif.nouvelle_valeur)
   value = data['value']
   ```

---

## Comparaison avec `HistoriqueValidation`

### Deux systèmes distincts

| Aspect | HistoriqueModification | HistoriqueValidation |
|--------|------------------------|----------------------|
| **Scope** | Modifications de données | Changements de statut de validation |
| **Granularité** | Par champ | Par validation |
| **Automatique** | Signals ou manuel | Automatique (save) |
| **Volume** | Élevé (tous les champs) | Faible (statuts uniquement) |
| **Fichier** | `audit/models.py` | `review/models.py` |

### Complémentarité

- **HistoriqueModification** : "Qui a changé quoi et quand ?"
- **HistoriqueValidation** : "Quel a été le parcours de validation ?"

**Exemple** :
```python
# Modifications de données
fiche.modifications.filter(categorie='localisation')
# → commune modifiée, altitude modifiée, etc.

# Parcours de validation
fiche.validations.first().historique.all()
# → en_cours → rejete → en_cours → validee
```

---

## Voir aussi

- **[Validation](08_validation.md)** - Modèle `HistoriqueValidation` complémentaire
- **[Workflow de correction](09_workflow-correction.md)** - Suivi de l'état des fiches
- **[Utilisateurs & Transferts](../../guides/gestion_utilisateurs_transferts.md)** - Identification des auteurs
- **[Diagramme ERD](../diagrammes/erd.md)** - Vue d'ensemble des relations
- **[Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)** - Documentation Django

---

*Dernière mise à jour : 2025-10-20*
