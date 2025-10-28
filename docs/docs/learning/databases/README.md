# Guide Technique : MariaDB vs. PostgreSQL avec PostGIS

Ce document explore les différences entre la gestion de données géographiques dans une base de données standard comme MariaDB (utilisée actuellement par le projet) et une base de données avec des extensions spatiales comme PostgreSQL avec PostGIS.

L'objectif est de comprendre les limitations de l'approche actuelle et de déterminer à quel moment une migration vers PostGIS deviendrait pertinente pour des fonctionnalités géographiques avancées.

**Configuration actuelle du projet :**
- **Développement :** SQLite
- **Production & CI :** MariaDB (ou compatible MySQL)
- **Stockage GPS :** Les coordonnées sont stockées dans des champs de type `CharField` ou `DecimalField`.

---

## PostGIS : c'est quoi ?

PostGIS est une extension de PostgreSQL qui ajoute des types de données géographiques et des fonctions spatiales pour manipuler des coordonnées GPS, des formes géométriques, etc.

### Votre situation actuelle (sans PostGIS)

**Comment vous stockez les coordonnées GPS maintenant :**
```python
class Localisation(models.Model):
    coordonnees_gps = CharField(max_length=50)  # "48.8566,2.3522"
    commune = CharField(max_length=100)
    altitude = IntegerField()
```

**Limitations :**
- Les coordonnées sont du texte simple.
- Pas d'opérations géographiques natives.
- Calculs manuels nécessaires pour les distances, zones, etc.

**Exemple de requête simple (ce que vous faites actuellement) :**

*Question : "Trouve toutes les observations de l'année 2024 dans la commune de Lyon"*

```python
observations = FicheObservation.objects.filter(
    annee=2024,
    localisation__commune='Lyon'
)
```
✅ **Ça marche parfaitement sans PostGIS !**

---

## Quand PostGIS devient-il utile ?

PostGIS devient intéressant pour des requêtes géographiques complexes.

### Exemple 1 : Recherche par distance

*Question : "Trouve tous les nids dans un rayon de 5 km autour d'un point GPS"*

**Sans PostGIS (MariaDB) :**
```python
# Vous devez :
# 1. Récupérer TOUTES les localisations en mémoire.
# 2. Calculer la distance en Python pour chacune.
# 3. Filtrer manuellement les résultats.

from math import radians, cos, sin, sqrt, atan2

def distance_gps(lat1, lon1, lat2, lon2):
    # ... (implémentation de la formule Haversine)
    pass

# Récupérer TOUTES les fiches
toutes_les_fiches = FicheObservation.objects.all()

# Filtrer en Python (lent si beaucoup de données)
fiches_proches = []
for fiche in toutes_les_fiches:
    # ... (calcul de distance pour chaque fiche)
    if distance <= 5:
        fiches_proches.append(fiche)
```
❌ **Problèmes :**
- Inefficace : récupère toutes les données en mémoire.
- Lent : les calculs sont faits en Python, pas par la base de données.
- Pas d'indexation spatiale possible.

**Avec PostGIS (PostgreSQL) :**
```python
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # Distance

# Le modèle utiliserait un champ géographique natif
class Localisation(models.Model):
    position = PointField(geography=True)
    
# Requête directe et optimisée en base de données
point_reference = Point(2.3522, 48.8566, srid=4326)  # lon, lat

fiches_proches = FicheObservation.objects.filter(
    localisation__position__distance_lte=(point_reference, D(km=5))
)
```
✅ **Avantages :**
- Le calcul est fait par la base de données (très rapide).
- Utilise des index spatiaux pour des performances optimales.
- Une seule requête SQL, efficace même avec des millions de points.

### Exemple 2 : Trouver les observations dans une zone

*Question : "Trouve tous les nids dans le Parc National des Écrins (défini par un polygone)"*

**Sans PostGIS :**
- Il faudrait implémenter un algorithme complexe de "point dans polygone" en Python et le tester sur chaque observation. Très lent.

**Avec PostGIS :**
```python
from django.contrib.gis.geos import Polygon

# Définir le polygone du parc
parc_ecrins = Polygon(((6.1, 44.8), (6.5, 44.8), ...))

# Requête SQL directe
fiches_dans_parc = FicheObservation.objects.filter(
    localisation__position__within=parc_ecrins
)
```
✅ **Calcul instantané par la base de données !**

---

## Comparaison Concrète

| Fonctionnalité | Votre système actuel (MariaDB) | Avec PostGIS |
|---|---|---|
| Stocker des coordonnées | ✅ `CharField` | ✅ `PointField` (type natif) |
| Chercher par commune | ✅ Facile | ✅ Facile |
| Distance entre 2 points | ⚠️ Calcul Python manuel | ✅ Fonction SQL native |
| Trouver dans un rayon | ❌ Boucle Python (lent) | ✅ Index spatial (rapide) |
| Point dans un polygone | ❌ Code complexe en Python | ✅ Fonction SQL native |

## Ma recommandation pour votre projet

**Phase actuelle : Gardez MariaDB.**

**Pourquoi ?**
- ✅ Vos besoins sont simples (stockage et affichage).
- ✅ La recherche par commune/année suffit.
- ✅ Pas de requêtes géographiques complexes requises pour l'instant.
- ✅ Le volume de données est raisonnable.

**Envisagez PostGIS si, plus tard, vous voulez :**
- Ajouter une carte interactive avec recherche de "nids dans un rayon de X km".
- Créer des zones de protection automatiques.
- Analyser la densité géographique des nidifications.

## Conclusion

PostGIS est un outil surpuissant pour la géographie, mais il ajoute de la complexité. Pour les besoins actuels et prévisibles du projet, **MariaDB est un choix simple, performant et parfaitement adéquat.**
