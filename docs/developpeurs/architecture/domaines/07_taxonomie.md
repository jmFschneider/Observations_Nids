# Domaine : Taxonomie ornithologique

## Vue d'ensemble

Le domaine taxonomie structure la classification scientifique des oiseaux observés selon la hiérarchie : **Ordre → Famille → Espèce**.

**Fichier** : `taxonomy/models.py`

---

## Hiérarchie taxonomique

```
Ordre (ex: Passériformes)
  └─ Famille (ex: Paridés)
       └─ Espèce (ex: Mésange bleue)
            ├─ Nom commun français
            ├─ Nom anglais
            └─ Nom scientifique (latin)
```

**Relations** :
- Un **Ordre** contient plusieurs **Familles** (1:N)
- Une **Famille** contient plusieurs **Espèces** (1:N)
- Une **Espèce** est référencée par les **FicheObservation** (1:N)

---

## Modèle Ordre

### Rôle métier

Représente un ordre taxonomique (ex: Passériformes, Accipitriformes, Strigiformes).

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `nom` | CharField(100) | Nom de l'ordre | **UNIQUE** |
| `description` | TextField | Description libre | Optionnel |

### Exemples d'ordres

```python
# Passériformes : ~60% des espèces d'oiseaux
Ordre.objects.create(
    nom='Passériformes',
    description='Oiseaux percheurs (mésanges, moineaux, corvidés, etc.)'
)

# Accipitriformes : rapaces diurnes
Ordre.objects.create(
    nom='Accipitriformes',
    description='Rapaces diurnes (buses, éperviers, aigles, milans)'
)

# Strigiformes : rapaces nocturnes
Ordre.objects.create(
    nom='Strigiformes',
    description='Rapaces nocturnes (chouettes, hiboux)'
)
```

### Localisation dans le code

**Fichier** : `taxonomy/models.py:4-9`

---

## Modèle Famille

### Rôle métier

Représente une famille taxonomique au sein d'un ordre (ex: Paridés, Corvidés).

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `nom` | CharField(100) | Nom de la famille | **UNIQUE** |
| `ordre` | ForeignKey | Ordre parent | → `Ordre`, CASCADE |
| `description` | TextField | Description libre | Optionnel |

### Relations

| Collection | Description |
|------------|-------------|
| `especes` | Espèces de cette famille (Espece.famille) |

### Exemples de familles

```python
ordre_passeriformes = Ordre.objects.get(nom='Passériformes')

# Paridés : mésanges
Famille.objects.create(
    nom='Paridés',
    ordre=ordre_passeriformes,
    description='Mésanges (bleue, charbonnière, noire, huppée, etc.)'
)

# Corvidés : corneilles, corbeaux, pies
Famille.objects.create(
    nom='Corvidés',
    ordre=ordre_passeriformes,
    description='Corvidés (corneille, pie, geai, corbeau, etc.)'
)

# Fringillidés : pinsons, chardonnerets
Famille.objects.create(
    nom='Fringillidés',
    ordre=ordre_passeriformes,
    description='Fringillidés (pinson, chardonneret, verdier, etc.)'
)
```

### Localisation dans le code

**Fichier** : `taxonomy/models.py:12-18`

---

## Modèle Espece

### Rôle métier

Représente une espèce d'oiseau observée. C'est l'entité centrale de la taxonomie, référencée par les fiches d'observation.

### Champs principaux

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `nom` | CharField(100) | Nom commun français | **UNIQUE** |
| `nom_anglais` | CharField(100) | Nom anglais | Optionnel |
| `nom_scientifique` | CharField(100) | Nom latin (binomial) | Optionnel |
| `statut` | CharField(50) | Statut de conservation | Optionnel |
| `famille` | ForeignKey | Famille taxonomique | → `Famille`, SET_NULL |
| `commentaire` | TextField | Commentaires libres | Défaut: '' |
| `lien_oiseau_net` | URLField | Lien vers Oiseaux.net | Optionnel |
| `valide_par_admin` | BooleanField | Espèce validée par admin | Défaut: False |

### Relations

| Collection | Description |
|------------|-------------|
| `observations` | Fiches d'observation de cette espèce (FicheObservation.espece) |

### Protection CASCADE/SET_NULL

```python
famille = models.ForeignKey(
    Famille,
    on_delete=models.SET_NULL,  # ← Si famille supprimée, espece.famille = NULL
    blank=True,
    null=True,
    related_name='especes'
)
```

**Justification** : Éviter la suppression en cascade des espèces si une famille est supprimée.

### Champ `valide_par_admin`

**Usage** : Système de validation pour les espèces ajoutées par les utilisateurs.

**Workflow** :
1. Utilisateur crée une nouvelle espèce → `valide_par_admin=False`
2. Admin vérifie et valide → `valide_par_admin=True`
3. Seules les espèces validées apparaissent dans les formulaires publics

### Localisation dans le code

**Fichier** : `taxonomy/models.py:21-34`

---

## Cas d'usage

### Création d'une espèce complète

```python
# 1. Créer l'ordre
ordre = Ordre.objects.get_or_create(
    nom='Passériformes',
    defaults={'description': 'Oiseaux percheurs'}
)[0]

# 2. Créer la famille
famille = Famille.objects.get_or_create(
    nom='Paridés',
    defaults={
        'ordre': ordre,
        'description': 'Mésanges'
    }
)[0]

# 3. Créer l'espèce
espece = Espece.objects.create(
    nom='Mésange bleue',
    nom_anglais='Blue tit',
    nom_scientifique='Cyanistes caeruleus',
    statut='LC (Préoccupation mineure)',
    famille=famille,
    lien_oiseau_net='https://www.oiseaux.net/oiseaux/mesange.bleue.html',
    valide_par_admin=True
)
```

### Import depuis référentiel ornithologique

```python
import csv

def importer_especes(fichier_csv):
    """Importe des espèces depuis un fichier CSV"""

    with open(fichier_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Récupérer ou créer l'ordre
            ordre, _ = Ordre.objects.get_or_create(
                nom=row['ordre'],
                defaults={'description': row.get('ordre_description', '')}
            )

            # Récupérer ou créer la famille
            famille, _ = Famille.objects.get_or_create(
                nom=row['famille'],
                defaults={
                    'ordre': ordre,
                    'description': row.get('famille_description', '')
                }
            )

            # Créer l'espèce
            Espece.objects.get_or_create(
                nom=row['nom_francais'],
                defaults={
                    'nom_anglais': row.get('nom_anglais', ''),
                    'nom_scientifique': row.get('nom_scientifique', ''),
                    'statut': row.get('statut', ''),
                    'famille': famille,
                    'valide_par_admin': True
                }
            )

# Usage
importer_especes('data/especes_france.csv')
```

### Statistiques taxonomiques

```python
from django.db.models import Count

# Nombre d'espèces par famille
stats_familles = Famille.objects.annotate(
    nb_especes=Count('especes')
).order_by('-nb_especes')

for famille in stats_familles:
    print(f"{famille.nom} ({famille.ordre.nom}) : {famille.nb_especes} espèces")

# Résultat :
# Paridés (Passériformes) : 8 espèces
# Corvidés (Passériformes) : 6 espèces
# Fringillidés (Passériformes) : 12 espèces
```

### Espèces en attente de validation

```python
especes_a_valider = Espece.objects.filter(
    valide_par_admin=False
).select_related('famille', 'famille__ordre')

for espece in especes_a_valider:
    print(f"{espece.nom} ({espece.nom_scientifique})")
    print(f"  Famille : {espece.famille.nom if espece.famille else 'Non renseignée'}")
```

---

## Requêtes ORM courantes

### Toutes les espèces d'une famille

```python
especes_parides = Espece.objects.filter(
    famille__nom='Paridés'
).order_by('nom')

for espece in especes_parides:
    print(espece.nom)
# Mésange bleue
# Mésange charbonnière
# Mésange huppée
# Mésange noire
```

### Espèces les plus observées

```python
from django.db.models import Count

especes_populaires = Espece.objects.annotate(
    nb_observations=Count('observations')
).order_by('-nb_observations')[:10]

for espece in especes_populaires:
    print(f"{espece.nom} : {espece.nb_observations} observations")
```

### Espèces par ordre

```python
ordre = Ordre.objects.get(nom='Passériformes')

especes = Espece.objects.filter(
    famille__ordre=ordre
).select_related('famille').order_by('famille__nom', 'nom')

current_famille = None
for espece in especes:
    if espece.famille != current_famille:
        current_famille = espece.famille
        print(f"\n{current_famille.nom}:")
    print(f"  - {espece.nom}")
```

### Autocomplete espèce

```python
def autocomplete_espece(request):
    """Vue AJAX pour autocomplete"""
    query = request.GET.get('q', '')

    especes = Espece.objects.filter(
        nom__icontains=query,
        valide_par_admin=True
    ).values(
        'id', 'nom', 'nom_scientifique', 'famille__nom'
    )[:10]

    return JsonResponse(list(especes), safe=False)

# Résultat :
# [
#     {
#         "id": 42,
#         "nom": "Mésange bleue",
#         "nom_scientifique": "Cyanistes caeruleus",
#         "famille__nom": "Paridés"
#     },
#     ...
# ]
```

---

## Protection PROTECT sur FicheObservation

### Définition

```python
# Dans FicheObservation (observations/models.py)
espece = models.ForeignKey(
    Espece,
    on_delete=models.PROTECT,  # ← Empêche suppression si observations existent
    related_name="observations"
)
```

### Comportement

```python
# Tentative de suppression d'une espèce avec observations
espece = Espece.objects.get(nom='Mésange bleue')

try:
    espece.delete()
except ProtectedError as e:
    print(f"Impossible de supprimer : {e}")
    # ProtectedError: Cannot delete some instances of model 'Espece'
    # because they are referenced through protected foreign keys:
    # 'FicheObservation.espece'.

# Afficher les observations liées
nb_obs = espece.observations.count()
print(f"{nb_obs} observations utilisent cette espèce")
```

### Solution : Désactivation

Au lieu de supprimer, marquer comme inactive :

```python
# Ajouter un champ `active` au modèle Espece
class Espece(models.Model):
    # ... champs existants ...
    active = models.BooleanField(default=True)

# Désactiver au lieu de supprimer
espece.active = False
espece.save()

# Filtrer les espèces actives
especes_actives = Espece.objects.filter(active=True)
```

---

## Validation et cohérence

### Unicité du nom

```python
# ❌ INVALIDE : Nom en double
Espece.objects.create(nom='Mésange bleue', ...)
Espece.objects.create(nom='Mésange bleue', ...)
# IntegrityError: UNIQUE constraint failed: taxonomy_espece.nom
```

### Validation du nom scientifique

```python
import re

def valider_nom_scientifique(nom):
    """Valide le format binomial (Genre species)"""
    pattern = r'^[A-Z][a-z]+ [a-z]+$'
    return re.match(pattern, nom) is not None

# Exemples
valider_nom_scientifique('Cyanistes caeruleus')  # ✅ True
valider_nom_scientifique('mesange bleue')         # ❌ False (pas de majuscule)
valider_nom_scientifique('Cyanistes')             # ❌ False (pas binomial)
```

### Liens vers Oiseaux.net

```python
from django.core.validators import URLValidator

# Validation automatique par URLField
espece = Espece(
    nom='Test',
    lien_oiseau_net='https://www.oiseaux.net/oiseaux/mesange.bleue.html'
)
espece.full_clean()  # Valide l'URL
```

---

## Points d'attention

### Ordre vs Famille : Suppression CASCADE

```python
# Si un Ordre est supprimé → toutes ses Familles sont supprimées (CASCADE)
ordre = Ordre.objects.get(nom='Passériformes')
ordre.delete()
# → Supprime aussi Paridés, Corvidés, Fringillidés, etc.

# Si une Famille est supprimée → ses Espèces conservent famille=NULL (SET_NULL)
famille = Famille.objects.get(nom='Paridés')
famille.delete()
# → Mésange bleue existe toujours, mais famille=NULL
```

**Recommandation** : Implémenter soft delete pour Ordre et Famille.

### Noms scientifiques manquants

```python
# Filtrer les espèces sans nom scientifique
sans_nom_scientifique = Espece.objects.filter(
    Q(nom_scientifique='') | Q(nom_scientifique__isnull=True)
)

print(f"{sans_nom_scientifique.count()} espèces sans nom scientifique")
```

### Statut de conservation

**Codes UICN** (Union Internationale pour la Conservation de la Nature) :
- **LC** : Least Concern (Préoccupation mineure)
- **NT** : Near Threatened (Quasi menacée)
- **VU** : Vulnerable (Vulnérable)
- **EN** : Endangered (En danger)
- **CR** : Critically Endangered (En danger critique)

**Utilisation** :
```python
especes_menacees = Espece.objects.filter(
    statut__in=['VU', 'EN', 'CR']
)
```

---

## Voir aussi

- **[Fiches d'observation](02_observations_core.md)** - Utilisation de `Espece` dans les fiches
- **[Référentiel Oiseaux.net](https://www.oiseaux.net/)** - Base de données ornithologique
- **[UICN - Liste rouge](https://www.iucnredlist.org/)** - Statuts de conservation
- **[Diagramme ERD](../diagrammes/erd.md)** - Vue d'ensemble des relations

---

*Dernière mise à jour : 2025-10-20*
