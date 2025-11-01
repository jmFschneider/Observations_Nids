# Domaine : Localisation et géocodage

## Vue d'ensemble

Le domaine localisation gère deux aspects complémentaires :
1. **`Localisation`** : Informations géographiques d'une fiche d'observation (commune, coordonnées GPS, paysage)
2. **`CommuneFrance`** : Cache local des communes françaises pour géocodage rapide

**Fichiers** :
- `geo/models.py` (Localisation, CommuneFrance)
- Création automatique via `FicheObservation.save()`

---

## Modèle Localisation

### Rôle métier

Stocke la localisation précise d'un nid observé avec plusieurs niveaux de précision :
- **Administrative** : commune, département
- **Géographique** : coordonnées GPS, altitude
- **Descriptive** : lieu-dit, paysage environnant

**Relation** : OneToOne avec `FicheObservation` (créé automatiquement à la création de la fiche)

### Champs principaux

| Champ | Type | Description | Défaut |
|-------|------|-------------|--------|
| `fiche` | OneToOne | Fiche parente | → `FicheObservation`, CASCADE |
| `commune` | CharField(100) | Nom de la commune | 'Non spécifiée' |
| `lieu_dit` | CharField(100) | Lieu-dit précis | 'Non spécifiée' |
| `departement` | CharField(100) | Nom ou code du département | '00' |
| `coordonnees` | CharField(30) | Coordonnées "lat,lon" | '0,0' |
| `latitude` | CharField(15) | Latitude seule | '0.0' |
| `longitude` | CharField(15) | Longitude seule | '0.0' |
| `altitude` | IntegerField | Altitude en mètres | 0 |
| `paysage` | TextField | Description du paysage | 'Non spécifié' |
| `alentours` | TextField | Description des alentours | 'Non spécifié' |

### Champs de géocodage

| Champ | Type | Description | Défaut |
|-------|------|-------------|--------|
| `precision_gps` | IntegerField | Précision estimée en mètres | 5000 |
| `source_coordonnees` | CharField(50) | Source des coordonnées | 'geocodage_auto' |
| `code_insee` | CharField(5) | Code INSEE de la commune | '' |

#### Choix `source_coordonnees`

```python
CHOICES = [
    ('gps_terrain', 'GPS de terrain'),           # Précision ~10m
    ('geocodage_auto', 'Géocodage automatique'), # Précision ~5000m (centre commune)
    ('geocodage_manuel', 'Géocodage manuel'),    # Précision variable
    ('carte', 'Pointé sur carte'),               # Précision ~100m
    ('base_locale', 'Base locale des communes'), # Précision ~5000m
    ('nominatim', 'Nominatim (OSM)'),            # Précision variable
]
```

### Localisation dans le code

**Fichier** : `geo/models.py:53-88`

---

## Modèle CommuneFrance

### Rôle métier

Cache local des **35 000+ communes françaises** pour :
- Géocodage rapide sans appel API externe
- Autocomplete dans les formulaires
- Validation des communes saisies
- Récupération automatique des coordonnées GPS

**Source** : API Géoplateforme (data.gouv.fr)

### Champs : Identification

| Champ | Type | Description | Index |
|-------|------|-------------|-------|
| `nom` | CharField(200) | Nom de la commune | **Indexé** |
| `code_insee` | CharField(5) | Code INSEE | **UNIQUE** |
| `code_postal` | CharField(5) | Code postal | **Indexé** |

### Champs : Localisation administrative

| Champ | Type | Description |
|-------|------|-------------|
| `departement` | CharField(100) | Nom du département |
| `code_departement` | CharField(3) | Code département (ex: '75', '2A') |
| `region` | CharField(100) | Nom de la région |

### Champs : Coordonnées GPS

| Champ | Type | Description |
|-------|------|-------------|
| `latitude` | DecimalField(9,6) | Latitude du centre de la commune |
| `longitude` | DecimalField(9,6) | Longitude du centre de la commune |
| `altitude` | IntegerField | Altitude moyenne (optionnel) |

### Champs : Métadonnées

| Champ | Type | Description |
|-------|------|-------------|
| `population` | IntegerField | Population (optionnel) |
| `superficie` | DecimalField(10,2) | Superficie en km² (optionnel) |
| `date_maj` | DateTimeField | Date de dernière mise à jour (auto) |

### Index composites

```python
indexes = [
    models.Index(fields=['nom', 'code_departement']),  # Recherche commune par dépt
    models.Index(fields=['code_postal']),               # Recherche par code postal
]
```

**Optimise** :
```python
# Recherche de commune par nom et département
CommuneFrance.objects.filter(nom__icontains='Paris', code_departement='75')

# Recherche par code postal
CommuneFrance.objects.filter(code_postal='75001')
```

### Propriété `coordonnees_gps`

```python
@property
def coordonnees_gps(self):
    """Retourne les coordonnées au format 'lat,lon'"""
    return f"{self.latitude},{self.longitude}"

# Usage
commune = CommuneFrance.objects.get(code_insee='75056')
print(commune.coordonnees_gps)  # "48.856614,2.352222"
```

### Localisation dans le code

**Fichier** : `geo/models.py:4-51`

---

## Workflow de géocodage

### 1. Création automatique

Lors de la création d'une fiche, une `Localisation` est créée avec valeurs par défaut :

```python
fiche = FicheObservation.objects.create(
    observateur=user,
    espece=espece,
    annee=2025
)

# Localisation créée automatiquement
loc = fiche.localisation
print(loc.commune)      # "Non spécifiée"
print(loc.departement)  # "00"
print(loc.coordonnees)  # "0,0"
print(loc.precision_gps) # 5000
```

### 2. Géocodage automatique (base locale)

Lors de la saisie de la commune, récupérer les coordonnées depuis `CommuneFrance` :

```python
# Utilisateur saisit "Grenoble"
commune = CommuneFrance.objects.filter(
    nom__iexact='Grenoble',
    code_departement='38'
).first()

if commune:
    loc = fiche.localisation
    loc.commune = commune.nom
    loc.departement = commune.departement
    loc.code_insee = commune.code_insee
    loc.latitude = str(commune.latitude)
    loc.longitude = str(commune.longitude)
    loc.coordonnees = commune.coordonnees_gps
    loc.altitude = commune.altitude or 0
    loc.precision_gps = 5000  # Centre de la commune
    loc.source_coordonnees = 'base_locale'
    loc.save()
```

### 3. Géocodage manuel (carte interactive)

L'utilisateur clique sur une carte pour affiner la position :

```python
# JavaScript envoie les coordonnées cliquées
def update_localisation(request, fiche_id):
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')

    loc = get_object_or_404(Localisation, fiche_id=fiche_id)
    loc.latitude = lat
    loc.longitude = lon
    loc.coordonnees = f"{lat},{lon}"
    loc.precision_gps = 100  # Pointé carte ~100m de précision
    loc.source_coordonnees = 'carte'
    loc.save()
```

### 4. GPS de terrain

Saisie manuelle de coordonnées GPS relevées sur le terrain :

```python
loc = fiche.localisation
loc.latitude = '45.192067'
loc.longitude = '5.730569'
loc.coordonnees = '45.192067,5.730569'
loc.precision_gps = 10  # GPS terrain ~10m
loc.source_coordonnees = 'gps_terrain'
loc.save()
```

---

## Cas d'usage

### Autocomplete commune

```python
# Vue pour autocomplete (AJAX)
def autocomplete_commune(request):
    query = request.GET.get('q', '')

    communes = CommuneFrance.objects.filter(
        nom__icontains=query
    ).values(
        'nom', 'code_postal', 'code_departement', 'code_insee'
    )[:10]

    return JsonResponse(list(communes), safe=False)

# Résultat :
# [
#     {"nom": "Grenoble", "code_postal": "38000", "code_departement": "38", "code_insee": "38185"},
#     {"nom": "Grenoble-en-Vercors", "code_postal": "38570", "code_departement": "38", ...},
# ]
```

### Calcul de distance

```python
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points GPS"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return 6371 * c  # Rayon de la Terre en km

# Usage : fiches dans un rayon de 10 km autour de Grenoble
grenoble = CommuneFrance.objects.get(code_insee='38185')

fiches_proches = []
for fiche in FicheObservation.objects.select_related('localisation'):
    if fiche.localisation.latitude != '0.0':
        lat = float(fiche.localisation.latitude)
        lon = float(fiche.localisation.longitude)
        distance = haversine(
            float(grenoble.latitude),
            float(grenoble.longitude),
            lat, lon
        )
        if distance <= 10:
            fiches_proches.append((fiche, distance))

fiches_proches.sort(key=lambda x: x[1])  # Tri par distance
```

### Statistiques par département

```python
from django.db.models import Count

stats = FicheObservation.objects.values(
    'localisation__departement'
).annotate(
    nb_fiches=Count('num_fiche')
).order_by('-nb_fiches')

# Résultat :
# [
#     {'localisation__departement': '38', 'nb_fiches': 120},
#     {'localisation__departement': '73', 'nb_fiches': 85},
#     ...
# ]
```

---

## Requêtes ORM courantes

### Fiches géolocalisées (GPS terrain)

```python
fiches_gps = FicheObservation.objects.filter(
    localisation__source_coordonnees='gps_terrain'
).select_related('localisation', 'espece')

for fiche in fiches_gps:
    print(f"{fiche.espece.nom} : {fiche.localisation.coordonnees}")
```

### Fiches à géocoder

```python
from django.db.models import Q

a_geocoder = FicheObservation.objects.filter(
    Q(localisation__coordonnees='0,0') |
    Q(localisation__commune='Non spécifiée')
).select_related('localisation')
```

### Communes avec observations

```python
communes_avec_obs = CommuneFrance.objects.filter(
    code_insee__in=Localisation.objects.exclude(
        code_insee=''
    ).values_list('code_insee', flat=True)
).distinct()

print(f"{communes_avec_obs.count()} communes avec observations")
```

### Fiches par altitude

```python
# Fiches en montagne (> 1000m)
fiches_montagne = FicheObservation.objects.filter(
    localisation__altitude__gt=1000
).select_related('localisation', 'espece')

for fiche in fiches_montagne:
    print(f"{fiche.espece.nom} à {fiche.localisation.altitude}m")
```

---

## Import des communes

### Script d'import (exemple)

```python
import requests
from geo.models import CommuneFrance

def importer_communes():
    """Importe les communes depuis l'API Géoplateforme"""

    # API data.gouv.fr
    url = "https://geo.api.gouv.fr/communes"
    params = {
        'fields': 'nom,code,codesPostaux,departement,region,centre,population,surface',
        'format': 'json',
        'geometry': 'centre'
    }

    response = requests.get(url, params=params)
    communes_data = response.json()

    communes = []
    for data in communes_data:
        commune = CommuneFrance(
            nom=data['nom'],
            code_insee=data['code'],
            code_postal=data['codesPostaux'][0] if data['codesPostaux'] else '',
            departement=data['departement']['nom'],
            code_departement=data['departement']['code'],
            region=data.get('region', {}).get('nom', ''),
            latitude=data['centre']['coordinates'][1],
            longitude=data['centre']['coordinates'][0],
            population=data.get('population'),
            superficie=data.get('surface')
        )
        communes.append(commune)

    # Bulk create pour performance
    CommuneFrance.objects.bulk_create(communes, batch_size=1000, ignore_conflicts=True)

    print(f"{len(communes)} communes importées")

# Usage
importer_communes()
```

---

## Algorithme de complétude

La `Localisation` contribue au calcul du pourcentage de complétion de la fiche (voir [09_workflow-correction.md](09_workflow-correction.md)).

**Critère 3** : Localisation complète (+1 point)

```python
# Extrait de EtatCorrection.calculer_pourcentage_completion()
if hasattr(self.fiche, 'localisation'):
    loc = self.fiche.localisation
    if (loc.commune and loc.commune != 'Non spécifiée' and
        loc.departement and loc.departement != '00'):
        score += 1  # +12.5% au total
```

---

## Points d'attention

### Choix de type `CharField` pour lat/lon

**Pourquoi pas `DecimalField` ?**
- Historique : compatibilité avec anciennes données
- Flexibilité : permet stockage de formats variés ('0,0', '0.0', 'N/A')

**Inconvénient** : Nécessite conversion pour calculs
```python
# Conversion obligatoire
lat = float(fiche.localisation.latitude)
lon = float(fiche.localisation.longitude)
```

**Amélioration future** : Migrer vers `DecimalField` comme dans `CommuneFrance`

### Précision GPS par source

| Source | Précision typique | Usage |
|--------|-------------------|-------|
| GPS terrain | 10m | Nid localisé précisément |
| Carte interactive | 100m | Pointé manuel sur carte |
| Géocodage commune | 5000m | Centre de la commune |
| Non renseigné | - | coordonnees='0,0' |

**Exploitation** :
```python
# Filtrer les fiches avec précision < 100m
fiches_precises = FicheObservation.objects.filter(
    localisation__precision_gps__lt=100
)
```

### Coordonnées '0,0'

**Signification** : Golfe de Guinée (océan Atlantique) = **valeur par défaut, non renseignée**

**Validation** :
```python
def localisation_est_renseignee(fiche):
    return fiche.localisation.coordonnees not in ['0,0', '0.0,0.0']

# Statistiques
nb_total = FicheObservation.objects.count()
nb_geolocalisees = FicheObservation.objects.exclude(
    localisation__coordonnees='0,0'
).count()

print(f"{nb_geolocalisees}/{nb_total} fiches géolocalisées")
```

---

## Voir aussi

- **[Fiches d'observation](02_observations_core.md)** - Modèle `FicheObservation` parent
- **09_workflow-correction.md** - Algorithme de complétude
- **[Diagramme ERD](../diagrammes/erd.md)** - Vue d'ensemble des relations
- **[API Géoplateforme](https://geoservices.ign.fr/)** - Documentation API IGN

---

*Dernière mise à jour : 2025-10-20*
