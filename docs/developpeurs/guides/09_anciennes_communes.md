# Guide : Gestion des Anciennes Communes (Fusions)

Ce guide explique comment gérer les anciennes communes qui ont fusionné avec d'autres communes françaises.

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Installation et Configuration](#3-installation-et-configuration)
4. [Utilisation](#4-utilisation)
5. [Script d'import](#5-script-dimport)
6. [Intégration au géocodeur](#6-intégration-au-geocodeur)
7. [Référence API](#7-référence-api)

---

## 1. Vue d'ensemble

### Problématique

En France, les communes fusionnent régulièrement pour créer de nouvelles communes. Par exemple :
- **"Les Praz"** (ancienne commune) a fusionné avec **"Chamonix-Mont-Blanc"** en 2017
- **"La Bohalle"** a fusionné avec **"Loire-Authion"**

Les anciennes fiches d'observation peuvent encore mentionner ces anciennes communes, mais elles n'existent plus officiellement.

### Solution

Nous avons créé un système à **deux tables séparées** :

- **`CommuneFrance`** : Contient uniquement les communes **actuelles** (actives)
- **`AncienneCommune`** : Contient les communes **fusionnées** avec un lien vers leur commune actuelle

Cette séparation permet :
- ✅ Clarté : On sait immédiatement si une commune existe encore
- ✅ Géocodage précis : Les anciennes communes gardent leurs coordonnées historiques
- ✅ Requêtes simples : `CommuneFrance.objects.all()` retourne seulement les communes actives
- ✅ Traçabilité historique : On garde l'historique des fusions

---

## 2. Architecture

### Modèle de données

```
┌─────────────────────────────────────┐
│      CommuneFrance (35 000+)        │
│  Communes actuelles uniquement      │
├─────────────────────────────────────┤
│ id                                  │
│ nom                                 │
│ code_insee (unique)                 │
│ latitude, longitude                 │
│ code_departement                    │
│ ...                                 │
└─────────────────────────────────────┘
                △
                │ commune_actuelle
                │ (ForeignKey)
                │
┌─────────────────────────────────────┐
│     AncienneCommune (1 587)         │
│   Communes fusionnées/déléguées     │
├─────────────────────────────────────┤
│ id                                  │
│ nom                                 │
│ code_insee (inactif)                │
│ latitude, longitude (historique)    │
│ code_departement                    │
│ commune_actuelle_id → CommuneFrance │
│ date_fusion                         │
│ commentaire                         │
└─────────────────────────────────────┘
```

### Fichiers du projet

| Fichier | Rôle |
|---------|------|
| `geo/models.py` | Modèle `AncienneCommune` (lignes 105-183) |
| `geo/migrations/0007_*.py` | Migration de création de la table |
| `geo/management/commands/importer_anciennes_communes.py` | Script d'import |
| `communes_nouvelles.csv` | Données officielles (data.gouv.fr) |

---

## 3. Installation et Configuration

### Étape 1 : Vérifier que la migration est appliquée

```bash
python manage.py showmigrations geo
```

Vous devriez voir :
```
[X] 0007_remove_communefrance_commune_actuelle_and_more
```

Si ce n'est pas le cas :
```bash
python manage.py migrate geo
```

### Étape 2 : Télécharger les données officielles

```bash
curl -L -o communes_nouvelles.csv "https://www.data.gouv.fr/fr/datasets/r/eaa68059-aaea-4ff9-a6f8-cf6146fe8a8b"
```

Ou téléchargez manuellement depuis :
https://www.data.gouv.fr/fr/datasets/communes-nouvelles/

### Étape 3 : Importer les données

```bash
python manage.py importer_anciennes_communes --file communes_nouvelles.csv
```

**Résultat attendu** :
```
Lecture du fichier communes_nouvelles.csv...
  + Les Praz -> Chamonix-Mont-Blanc
  + La Bohalle -> Loire-Authion
  ...
============================================================
Import terminé !
============================================================
Anciennes communes importées : 1587
Lignes ignorées (commune siège) : 1376
Communes actuelles introuvables : 6
Erreurs : 0
============================================================
```

### Étape 4 : Vérifier l'import

```bash
python manage.py shell
```

```python
from geo.models import AncienneCommune, CommuneFrance

# Nombre d'anciennes communes
print(f"Anciennes communes : {AncienneCommune.objects.count()}")  # → 1587

# Exemple
ancienne = AncienneCommune.objects.filter(nom__icontains="Praz").first()
if ancienne:
    print(f"{ancienne.nom} → {ancienne.commune_actuelle.nom}")
```

---

## 4. Utilisation

### 4.1 Rechercher une ancienne commune

```python
from geo.models import AncienneCommune

# Par nom
anciennes_74 = AncienneCommune.objects.filter(code_departement='74')

# Trouver la commune actuelle
ancienne = AncienneCommune.objects.get(nom="Les Praz", code_departement='74')
commune_actuelle = ancienne.commune_actuelle
# → CommuneFrance(nom="Chamonix-Mont-Blanc")
```

### 4.2 Voir les anciennes communes d'une commune actuelle

```python
from geo.models import CommuneFrance

# Récupérer une commune actuelle
chamonix = CommuneFrance.objects.get(nom="Chamonix-Mont-Blanc")

# Lister toutes ses anciennes communes
anciennes = chamonix.anciennes_communes.all()
for ancienne in anciennes:
    print(f"- {ancienne.nom} (fusionnée le {ancienne.date_fusion})")
```

### 4.3 Géocoder une observation avec ancienne commune

```python
def geocoder_observation(nom_commune):
    """
    Géocode une observation en cherchant dans les communes actuelles
    ET dans les anciennes communes fusionnées
    """
    # 1. Chercher dans les communes actuelles
    try:
        commune = CommuneFrance.objects.get(nom__iexact=nom_commune)
        return {
            'latitude': float(commune.latitude),
            'longitude': float(commune.longitude),
            'commune_actuelle': commune.nom,
            'type': 'actuelle'
        }
    except CommuneFrance.DoesNotExist:
        pass

    # 2. Chercher dans les anciennes communes
    try:
        ancienne = AncienneCommune.objects.get(nom__iexact=nom_commune)
        return {
            'latitude': float(ancienne.latitude or ancienne.commune_actuelle.latitude),
            'longitude': float(ancienne.longitude or ancienne.commune_actuelle.longitude),
            'commune_actuelle': ancienne.commune_actuelle.nom,
            'commune_ancienne': ancienne.nom,
            'type': 'fusionnee'
        }
    except AncienneCommune.DoesNotExist:
        pass

    # 3. Pas trouvée
    return None

# Exemple
result = geocoder_observation("Les Praz")
# → {
#     'latitude': 45.923700,
#     'longitude': 6.869400,
#     'commune_actuelle': 'Chamonix-Mont-Blanc',
#     'commune_ancienne': 'Les Praz',
#     'type': 'fusionnee'
# }
```

---

## 5. Script d'import

### Commande

```bash
python manage.py importer_anciennes_communes [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--file PATH` | Chemin vers le fichier CSV (défaut: `communes_nouvelles.csv`) |
| `--clear` | Supprimer toutes les anciennes communes avant import |

### Exemples

```bash
# Import standard
python manage.py importer_anciennes_communes

# Réimport complet (supprime puis réimporte)
python manage.py importer_anciennes_communes --clear

# Avec fichier personnalisé
python manage.py importer_anciennes_communes --file /chemin/vers/fichier.csv
```

### Format du fichier CSV

Le fichier CSV doit contenir les colonnes suivantes :

| Colonne | Description |
|---------|-------------|
| `Date` | Date de fusion (ex: "AVRIL 2016") |
| `Code INSEE Commune Nouvelle` | Code INSEE de la commune actuelle (5 caractères) |
| `Nom Commune Nouvelle Siège` | Nom de la commune actuelle |
| `Code INSEE Commune Déléguée (non actif)` | Code INSEE de l'ancienne commune |
| `Nom Commune Déléguée` | Nom de l'ancienne commune |

### Source des données

**Données officielles** :
https://www.data.gouv.fr/fr/datasets/communes-nouvelles/

**Fichier CSV direct** :
https://www.data.gouv.fr/fr/datasets/r/eaa68059-aaea-4ff9-a6f8-cf6146fe8a8b

**Fréquence de mise à jour** : Annuelle (généralement en janvier)

---

## 6. Intégration au géocodeur

### Modifier le géocodeur existant

Si vous avez une fonction de géocodage existante, intégrez la recherche d'anciennes communes :

```python
# geo/services/geocodeur.py

from geo.models import CommuneFrance, AncienneCommune

def geocoder_commune(nom_commune, code_departement=None):
    """
    Géocode une commune (actuelle ou ancienne)

    Args:
        nom_commune: Nom de la commune à géocoder
        code_departement: Code département optionnel pour affiner

    Returns:
        dict avec latitude, longitude, commune_actuelle, type
    """
    filters = {'nom__iexact': nom_commune}
    if code_departement:
        filters['code_departement'] = code_departement

    # 1. Chercher parmi les communes actuelles
    commune = CommuneFrance.objects.filter(**filters).first()
    if commune:
        return {
            'latitude': float(commune.latitude),
            'longitude': float(commune.longitude),
            'commune': commune.nom,
            'code_insee': commune.code_insee,
            'type': 'actuelle',
            'source': 'commune_actuelle'
        }

    # 2. Chercher parmi les anciennes communes
    ancienne = AncienneCommune.objects.filter(**filters).first()
    if ancienne:
        # Utiliser les coordonnées de l'ancienne commune si disponibles
        # Sinon, fallback sur la commune actuelle
        lat = ancienne.latitude or ancienne.commune_actuelle.latitude
        lon = ancienne.longitude or ancienne.commune_actuelle.longitude

        return {
            'latitude': float(lat),
            'longitude': float(lon),
            'commune': ancienne.commune_actuelle.nom,
            'commune_ancienne': ancienne.nom,
            'code_insee': ancienne.commune_actuelle.code_insee,
            'type': 'fusionnee',
            'source': 'ancienne_commune',
            'date_fusion': ancienne.date_fusion
        }

    # 3. Pas trouvée
    return None
```

### Exemple d'utilisation dans une vue

```python
# observations/views.py

from geo.services.geocodeur import geocoder_commune

def saisir_observation(request):
    if request.method == 'POST':
        nom_commune = request.POST.get('commune')

        # Géocoder
        resultat = geocoder_commune(nom_commune)

        if resultat:
            # Créer la localisation
            localisation = Localisation.objects.create(
                fiche=fiche,
                commune=resultat['commune'],
                latitude=resultat['latitude'],
                longitude=resultat['longitude'],
                code_insee=resultat['code_insee'],
                source_coordonnees='base_locale'
            )

            # Message informatif si commune fusionnée
            if resultat['type'] == 'fusionnee':
                messages.info(
                    request,
                    f"La commune '{resultat['commune_ancienne']}' a fusionné avec "
                    f"'{resultat['commune']}' le {resultat['date_fusion']}."
                )
        else:
            messages.error(request, f"Commune '{nom_commune}' introuvable.")
```

---

## 7. Référence API

### Modèle `AncienneCommune`

```python
class AncienneCommune(models.Model):
    """Communes ayant fusionné avec d'autres communes"""

    # Identification
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True)

    # Localisation
    code_postal = models.CharField(max_length=5, blank=True)
    code_departement = models.CharField(max_length=3, db_index=True)
    departement = models.CharField(max_length=100, blank=True)

    # Coordonnées GPS (historiques)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    altitude = models.IntegerField(null=True, blank=True)

    # Rattachement
    commune_actuelle = models.ForeignKey(
        'CommuneFrance',
        on_delete=models.CASCADE,
        related_name='anciennes_communes'
    )

    # Métadonnées fusion
    date_fusion = models.DateField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    date_import = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    @property
    def coordonnees_gps(self):
        """Retourne les coordonnées (avec fallback sur commune actuelle)"""
        if self.latitude and self.longitude:
            return f"{self.latitude},{self.longitude}"
        return self.commune_actuelle.coordonnees_gps
```

### Requêtes courantes

```python
# Toutes les anciennes communes d'un département
AncienneCommune.objects.filter(code_departement='74')

# Anciennes communes fusionnées après 2020
AncienneCommune.objects.filter(date_fusion__gte='2020-01-01')

# Anciennes communes d'une commune actuelle
CommuneFrance.objects.get(nom="Annecy").anciennes_communes.all()

# Recherche avec coordonnées GPS
AncienneCommune.objects.exclude(latitude__isnull=True)

# Statistiques par département
from django.db.models import Count
AncienneCommune.objects.values('code_departement').annotate(
    total=Count('id')
).order_by('-total')
```

---

## Annexes

### A. Communes actuelles introuvables

Lors de l'import, certaines communes nouvelles peuvent ne pas être trouvées dans votre base `CommuneFrance`. Cela peut arriver si :

1. La base des communes actuelles n'est pas à jour
2. La commune nouvelle a été créée récemment
3. Il y a une différence d'orthographe

**Solution** : Mettre à jour la base des communes actuelles :

```bash
python manage.py charger_communes_france
```

### B. Maintenance et mise à jour

**Fréquence recommandée** : 1 fois par an (en janvier après publication des données officielles)

```bash
# 1. Télécharger la nouvelle version
curl -L -o communes_nouvelles_2026.csv "https://www.data.gouv.fr/fr/datasets/r/eaa68059-aaea-4ff9-a6f8-cf6146fe8a8b"

# 2. Réimporter (supprime et récrée)
python manage.py importer_anciennes_communes --file communes_nouvelles_2026.csv --clear

# 3. Vérifier
python manage.py shell -c "from geo.models import AncienneCommune; print(f'Total: {AncienneCommune.objects.count()}')"
```

### C. Troubleshooting

#### Problème : "Commune actuelle introuvable"

**Cause** : La commune nouvelle n'existe pas dans `CommuneFrance`

**Solution** :
```bash
# Mettre à jour la base des communes actuelles
python manage.py charger_communes_france

# Réimporter les anciennes communes
python manage.py importer_anciennes_communes --clear
```

#### Problème : Coordonnées GPS manquantes

**Cause** : Le fichier CSV ne contient pas les coordonnées des anciennes communes

**Solution** : Les coordonnées de la commune actuelle seront utilisées automatiquement via la propriété `coordonnees_gps`.

Pour ajouter manuellement des coordonnées :

```python
from geo.models import AncienneCommune

ancienne = AncienneCommune.objects.get(nom="Les Praz")
ancienne.latitude = 45.923700
ancienne.longitude = 6.869400
ancienne.save()
```

---

**Document créé le** : 14 novembre 2025
**Auteur** : Claude Code
**Version** : 1.0
