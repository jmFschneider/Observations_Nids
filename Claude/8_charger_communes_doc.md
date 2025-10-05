# Guide : Chargement de la base des communes françaises

## Vue d'ensemble

La base de données locale des communes françaises est essentielle pour le **géocodage automatique** des observations. Elle permet de convertir rapidement les noms de communes en coordonnées GPS sans solliciter d'API externe.

---

## Pourquoi charger cette base ?

### Avantages de la base locale

1. **Performance** : Recherche instantanée en base de données (vs requêtes HTTP)
2. **Fiabilité** : Pas de dépendance à une API externe
3. **Gratuit** : Pas de limite de requêtes ni de coût
4. **Précision** : Données officielles de data.gouv.fr

### Utilisation dans le workflow

La base locale est utilisée par le **GeocodeurCommunes** lors de :
- L'extraction des candidats depuis les fichiers JSON transcrits
- La finalisation des importations
- Le géocodage manuel via l'interface

---

## Commande de chargement

### Commande de base

```bash
python manage.py charger_communes_france
```

### Options disponibles

#### `--force` : Forcer le rechargement

Supprime les données existantes et recharge depuis l'API :

```bash
python manage.py charger_communes_france --force
```

⚠️ **Attention** : Cette option supprime toutes les communes existantes avant de recharger.

---

## Procédure de chargement initial

### Étape 1 : Vérifier la connexion

Assurez-vous que MariaDB est démarré et accessible :

```bash
python manage.py check
```

### Étape 2 : Lancer le chargement

```bash
python manage.py charger_communes_france
```

### Étape 3 : Vérifier le résultat

La commande affiche :
- Le nombre de communes récupérées depuis l'API
- Le nombre de communes chargées en base
- Le nombre d'erreurs (territoires d'outre-mer sans code postal)
- Les statistiques finales

**Exemple de sortie :**

```
Téléchargement des communes depuis l'API Géoplateforme...
34969 communes récupérées
Chargement en base de données...

Chargement terminé:
   - 34964 communes chargées
   - 5 erreurs

Base de données:
   - 34964 communes
   - 108 départements
```

---

## Données chargées

### Source

- **API** : https://geo.api.gouv.fr/communes
- **Source officielle** : data.gouv.fr (Institut National de Géographie)

### Champs importés

Pour chaque commune :

| Champ | Description | Exemple |
|-------|-------------|---------|
| `nom` | Nom de la commune | "Chamonix-Mont-Blanc" |
| `code_insee` | Code INSEE unique | "74056" |
| `code_postal` | Code postal | "74400" |
| `departement` | Nom du département | "Haute-Savoie" |
| `code_departement` | Code du département | "74" |
| `region` | Nom de la région | "Auvergne-Rhône-Alpes" |
| `latitude` | Latitude (centre commune) | 45.923697 |
| `longitude` | Longitude (centre commune) | 6.869433 |
| `population` | Population | 8897 |
| `superficie` | Superficie en km² | 245.46 |

---

## Erreurs connues

### Territoires sans code postal

5 territoires d'outre-mer n'ont pas de code postal et génèrent des erreurs (comportement normal) :
- Îles Saint-Paul et Nouvelle-Amsterdam
- Archipel des Kerguelen
- Archipel des Crozet
- La Terre-Adélie
- Îles Éparses de l'océan Indien

Ces erreurs sont **normales** et n'affectent pas le fonctionnement du système.

---

## Maintenance

### Quand recharger la base ?

Rechargez la base dans les cas suivants :

1. **Mise à jour annuelle** : Nouvelles communes, fusions communales
2. **Données corrompues** : Erreurs en base de données
3. **Migration de serveur** : Nouvelle installation

### Commande de rechargement

```bash
python manage.py charger_communes_france --force
```

### Durée du chargement

- **Téléchargement API** : ~5-10 secondes
- **Insertion en base** : ~10-20 secondes
- **Total** : ~30 secondes

---

## Vérification du chargement

### Via Django shell

```bash
python manage.py shell
```

```python
from geo.models import CommuneFrance

# Nombre total de communes
print(CommuneFrance.objects.count())
# 34964

# Exemple de recherche
commune = CommuneFrance.objects.filter(nom__iexact="PARIS").first()
print(f"{commune.nom} - {commune.code_insee} - {commune.coordonnees_gps}")
# PARIS - 75056 - 48.856614,2.352222

# Communes par département
from django.db.models import Count
stats = CommuneFrance.objects.values('departement').annotate(total=Count('id')).order_by('-total')[:5]
for s in stats:
    print(f"{s['departement']}: {s['total']} communes")
```

### Via l'interface admin Django

1. Accéder à `/admin/geo/communefrance/`
2. Vérifier le nombre d'entrées
3. Tester la recherche par nom

---

## Intégration dans le workflow d'importation

### Étape 1 : Charger les communes (une seule fois)

```bash
python manage.py charger_communes_france
```

### Étape 2 : Importer les fichiers JSON transcrits

Via l'interface web : `/ingest/importer-json/`

### Étape 3 : Extraire les candidats (avec géocodage)

Via l'interface web : `/ingest/extraire-candidats/`

**Le système va automatiquement :**
1. Extraire le nom de la commune depuis les données JSON
2. Rechercher la commune en base locale MariaDB
3. Récupérer les coordonnées GPS
4. Logger les résultats dans les logs

### Étape 4 : Consulter les logs

Les logs indiquent les communes trouvées :

```
INFO: Commune trouvée pour 'Chamonix': Chamonix-Mont-Blanc, Haute-Savoie, France
      (source: base_locale, coordonnées: 45.923697,6.869433)
```

---

## Architecture technique

### Modèle de données

```python
class CommuneFrance(models.Model):
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True)
    code_postal = models.CharField(max_length=5, db_index=True)
    departement = models.CharField(max_length=100)
    code_departement = models.CharField(max_length=3, db_index=True)
    region = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    population = models.IntegerField(null=True, blank=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2)
```

### Stratégie de recherche du GeocodeurCommunes

1. **Recherche exacte** : nom + département
2. **Recherche par code postal**
3. **Recherche par nom unique** (si une seule commune en France)
4. **Recherche floue** : contient + département (erreurs OCR)
5. **Fallback Nominatim** : si toujours non trouvé

### Index de performance

```sql
INDEX idx_nom (nom)
INDEX idx_code_departement (code_departement)
INDEX idx_code_postal (code_postal)
INDEX idx_nom_dept (nom, code_departement)
```

---

## Dépannage

### Erreur "requests module not found"

```bash
pip install requests
```

### Erreur de timeout

Augmenter le timeout dans la commande :

```python
response = requests.get(url, params=params, timeout=60)  # 60 secondes
```

### Erreur "API non accessible"

Vérifier la connexion internet :

```bash
curl https://geo.api.gouv.fr/communes?limit=1
```

### Base déjà chargée

Si vous voyez ce message :

```
34964 communes déjà en base. Utilisez --force pour recharger.
```

C'est normal, la base est déjà chargée. Utilisez `--force` seulement si nécessaire.

---

## Commandes utiles

### Vider la table des communes

```bash
python manage.py shell
```

```python
from geo.models import CommuneFrance
CommuneFrance.objects.all().delete()
```

### Statistiques détaillées

```bash
python manage.py shell
```

```python
from geo.models import CommuneFrance
from django.db.models import Count, Avg

# Total
print(f"Total communes: {CommuneFrance.objects.count()}")

# Par département (top 10)
top_depts = CommuneFrance.objects.values('departement').annotate(
    total=Count('id')
).order_by('-total')[:10]

for dept in top_depts:
    print(f"{dept['departement']}: {dept['total']} communes")

# Population moyenne
avg_pop = CommuneFrance.objects.aggregate(Avg('population'))
print(f"Population moyenne: {avg_pop['population__avg']:.0f} habitants")
```

---

## Références

- **API Géoplateforme** : https://geo.api.gouv.fr/decoupage-administratif
- **Documentation officielle** : https://geo.api.gouv.fr/
- **Source des données** : data.gouv.fr / IGN
- **Code de la commande** : `geo/management/commands/charger_communes_france.py`

---

*Dernière mise à jour : 2025-10-03*
