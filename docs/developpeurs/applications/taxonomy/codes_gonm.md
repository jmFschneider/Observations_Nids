# Codes GONM - Guide complet

> Guide détaillé sur l'intégration et l'utilisation des codes du Groupe Ornithologique Normand

## Vue d'ensemble

Les codes GONM sont des identifiants standardisés utilisés par le Groupe Ornithologique Normand pour référencer les espèces d'oiseaux. Ces codes facilitent les échanges de données et la compatibilité avec les systèmes du GONM.

**Format** : Une ou plusieurs lettres suivies d'un numéro (ex: `A01`, `C08`, `V16`)

**Couverture** : 425 espèces sur 576 (74%)

## Structure du modèle

### Champ dans le modèle Espece

```python
# taxonomy/models.py
class Espece(models.Model):
    # ... autres champs ...

    code_gonm = models.CharField(
        max_length=10,
        blank=True,
        help_text="Code GONM de l'espèce"
    )
```

**Propriétés** :
- **Type** : CharField
- **Longueur max** : 10 caractères
- **Nullable** : Non (mais peut être vide avec `blank=True`)
- **Index** : Non (pas nécessaire pour ce volume)
- **Unique** : Non (plusieurs espèces peuvent théoriquement partager un code)

## Catégories de codes

Les codes GONM sont organisés par grandes catégories d'oiseaux :

| Préfixe | Catégorie | Exemples | Nombre |
|---------|-----------|----------|--------|
| **A** | Plongeons, Pétrels, Grèbes | A01 (Plongeon arctique) | 21 |
| **B** | Hérons, Cigognes, Flamants | B01 (Fou de Bassan) | 20 |
| **C** | Anatidés (canards, oies) | C08 (Canard colvert) | 24 |
| **D** | Anatidés (suite) | D02 (Fuligule milouin) | 19 |
| **E** | Rapaces diurnes | E18 (Balbuzard pêcheur) | 33 |
| **F** | Galliformes, Râles, Grues | F11 (Râle d'eau) | 16 |
| **G** | Limicoles (vanneaux, pluviers) | G02 (Vanneau huppé) | 20 |
| **H** | Limicoles (bécasseaux, chevaliers) | H07 (Chevalier guignette) | 36 |
| **J** | Labbes, Goélands, Mouettes | J06 (Goéland brun) | 23 |
| **K** | Sternes, Guillemots, Pingouins | K01 (Guifette noire) | 21 |
| **L** | Pigeons, Coucous, Rapaces nocturnes | L09 (Grand-duc d'Europe) | 19 |
| **M** | Martinets, Pics | M09 (Pic vert) | 16 |
| **N** | Alouettes, Hirondelles | N08 (Hirondelle de rivage) | 10 |
| **P** | Pipits, Bergeronnettes, Pies-grièches | P07 (Bergeronnette grise) | 23 |
| **Q** | Traquets, Rougequeues, Grives | Q10 (Rougegorge familier) | 23 |
| **R** | Locustelles, Rousserolles, Phragmites | R01 (Bouscarle de Cetti) | 14 |
| **S** | Fauvettes, Pouillots, Roitelets | S03 (Fauvette à tête noire) | 21 |
| **T** | Gobemouches, Mésanges | T12 (Mésange charbonnière) | 17 |
| **U** | Bruants, Fringilles | U08 (Pinson des arbres) | 31 |
| **V** | Moineaux, Loriots, Corvidés | V16 (Grand Corbeau) | 18 |

## Import des codes GONM

### Processus d'import

#### 1. Préparation du fichier

Le fichier TSV doit contenir les colonnes suivantes :

```
code_gonm    espece_trouvee_id    espece_trouvee_nom    score_pourcent
A01          235                  Plongeon arctique     100%
C08          26                   Canard colvert        100%
```

**Format requis** :
- Délimiteur : Tabulation (`\t`)
- Encodage : UTF-8 (avec ou sans BOM)
- En-tête : Première ligne avec noms de colonnes

#### 2. Lancement de l'import

```bash
# Mode dry-run (recommandé en premier)
python manage.py import_codes_gonm --dry-run

# Import réel
python manage.py import_codes_gonm

# Import avec fichier personnalisé
python manage.py import_codes_gonm --file /chemin/vers/fichier.tsv
```

#### 3. Vérification

La commande affiche un rapport détaillé :

```
=== Import des codes GONM ===
Fichier à importer: analyse-correspondances-gonm.tsv
Encodage détecté: utf-8-sig
Colonnes détectées: code_gonm, espece_trouvee_id, ...
Espèces mises à jour: 50...100...150...200...250...300...350...400

=== Rapport d'import ===
Lignes traitées: 427
Résultats:
   - Espèces mises à jour: 427
   - Espèces non trouvées: 0
   - Lignes sans code: 0

=== Exemples d'espèces avec code GONM ===
  - [A01] Plongeon arctique (Gavia arctica)
  - [C08] Canard colvert (Anas platyrhynchos)
  ...

[OK] Import terminé avec succès!
```

### Mise à jour des codes

Pour mettre à jour les codes existants :

1. Préparer un nouveau fichier TSV avec les modifications
2. Lancer la commande d'import (elle écrase les codes existants)
3. Vérifier les modifications dans l'interface

**Note** : L'import est idempotent - vous pouvez le relancer sans risque.

## Affichage dans l'interface

### 1. Liste des espèces

**URL** : `/taxonomy/especes/`
**Template** : `taxonomy/templates/taxonomy/liste_especes.html`

Colonne "Code GONM" avec badge :

```html
<th>Code GONM</th>
...
<td>
    {% if espece.code_gonm %}
    <span class="badge bg-secondary">{{ espece.code_gonm }}</span>
    {% else %}
    <span class="text-muted">-</span>
    {% endif %}
</td>
```

**Style** :
- Badge gris (`bg-secondary`) pour les codes existants
- Tiret grisé pour les espèces sans code

### 2. Fiche d'observation

**URL** : `/observations/<id>/`
**Template** : `observations/templates/fiche_observation.html`

Tableau des informations générales :

```html
<table class="fiche-table">
    <tr>
        <th>Fiche ID</th>
        <th>Observateur</th>
        <th>N° perso de fiche</th>
        <th>Espèce</th>
        <th>Code GONM</th>
        <th>Année</th>
    </tr>
    <tr>
        <td>{{ fiche.num_fiche }}</td>
        <td>{{ fiche.observateur.first_name }} {{ fiche.observateur.last_name }}</td>
        <td>{% if fiche.numero_personnel %}{{ fiche.numero_personnel }}{% else %}-{% endif %}</td>
        <td>{{ fiche.espece.nom }}</td>
        <td>{% if fiche.espece.code_gonm %}{{ fiche.espece.code_gonm }}{% else %}-{% endif %}</td>
        <td>{{ fiche.annee }}</td>
    </tr>
</table>
```

### 3. Modification d'observation

**URL** : `/observations/modifier/<id>/`
**Template** : `observations/templates/saisie/saisie_observation.html`

Le code GONM apparaît dans :
- Le tableau principal (comme dans la fiche)
- La modale de recherche de fiches

**API de recherche** : La fonction `rechercher_fiches()` retourne le code GONM :

```python
# observations/views/saisie_observation_view.py
def rechercher_fiches(request):
    # ... filtres ...

    for fiche in fiches:
        resultats.append({
            'num_fiche': fiche.num_fiche,
            'observateur': f"{fiche.observateur.first_name} {fiche.observateur.last_name}",
            'espece': fiche.espece.nom,
            'code_gonm': fiche.espece.code_gonm or '-',  # ← Important
            'annee': fiche.annee,
            'numero_personnel': fiche.numero_personnel or '',
            'commune': commune,
        })

    return JsonResponse({'fiches': resultats})
```

**JavaScript** : Affichage dans le tableau de résultats :

```javascript
data.fiches.forEach(function(fiche) {
    var tr = document.createElement('tr');
    tr.innerHTML =
        '<td><strong>' + fiche.num_fiche + '</strong></td>' +
        '<td>' + fiche.observateur + '</td>' +
        '<td>' + (fiche.numero_personnel || '-') + '</td>' +
        '<td>' + fiche.espece + '</td>' +
        '<td>' + (fiche.code_gonm || '-') + '</td>' +  // ← Ajouté
        '<td>' + fiche.annee + '</td>' +
        '<td>' + fiche.commune + '</td>' +
        '<td><button>...</button></td>';
    tbody.appendChild(tr);
});
```

## Utilisation dans le code

### Accès au code GONM

```python
# Dans une vue
from taxonomy.models import Espece

espece = Espece.objects.get(id=26)
print(espece.code_gonm)  # "C08"

# Dans un template
{{ fiche.espece.code_gonm }}

# Avec valeur par défaut
{{ fiche.espece.code_gonm|default:"-" }}
```

### Filtrage par code GONM

```python
# Toutes les espèces avec un code GONM
especes_avec_code = Espece.objects.exclude(code_gonm='')

# Espèces sans code GONM
especes_sans_code = Espece.objects.filter(code_gonm='')

# Recherche par code spécifique
canard_colvert = Espece.objects.get(code_gonm='C08')

# Recherche par préfixe (tous les anatidés C et D)
anatides = Espece.objects.filter(
    code_gonm__regex=r'^[CD]'
).exclude(code_gonm='')
```

### Export vers format GONM

Pour exporter les observations au format GONM :

```python
from observations.models import FicheObservation

fiches = FicheObservation.objects.select_related('espece').all()

for fiche in fiches:
    print(f"{fiche.espece.code_gonm},{fiche.annee},{fiche.localisation.commune}")
```

## Maintenance

### Ajout de nouveaux codes

Lorsque le GONM publie de nouveaux codes :

1. Mettre à jour le fichier TSV source
2. Lancer l'analyse pour vérifier les correspondances :
   ```bash
   python manage.py analyser_correspondances_gonm
   ```
3. Valider les correspondances (≥80% de confiance recommandé)
4. Faire un backup de la base de données
5. Lancer l'import :
   ```bash
   python manage.py import_codes_gonm
   ```

### Correction d'un code erroné

```python
from taxonomy.models import Espece

# Corriger un code
espece = Espece.objects.get(nom="Plongeon arctique")
espece.code_gonm = "A01"  # Au lieu de l'ancien code
espece.save()

# Supprimer un code
espece = Espece.objects.get(nom="Espèce incorrecte")
espece.code_gonm = ""
espece.save()
```

### Statistiques

Pour obtenir des statistiques sur les codes GONM :

```python
from taxonomy.models import Espece

# Nombre total d'espèces
total = Espece.objects.count()

# Nombre d'espèces avec code GONM
avec_code = Espece.objects.exclude(code_gonm='').count()

# Pourcentage de couverture
couverture = (avec_code / total) * 100
print(f"Couverture : {couverture:.1f}%")

# Répartition par catégorie
from django.db.models import Count, Substr

stats = (
    Espece.objects
    .exclude(code_gonm='')
    .annotate(categorie=Substr('code_gonm', 1, 1))
    .values('categorie')
    .annotate(count=Count('id'))
    .order_by('categorie')
)

for stat in stats:
    print(f"Catégorie {stat['categorie']}: {stat['count']} espèces")
```

## Intégration avec d'autres systèmes

### Export CSV pour le GONM

```python
import csv
from taxonomy.models import Espece

with open('export_gonm.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['Code GONM', 'Nom scientifique', 'Nom français'])

    especes = Espece.objects.exclude(code_gonm='').order_by('code_gonm')
    for espece in especes:
        writer.writerow([
            espece.code_gonm,
            espece.nom_scientifique,
            espece.nom
        ])
```

### Import d'observations avec codes GONM

```python
import csv
from taxonomy.models import Espece
from observations.models import FicheObservation

with open('observations_gonm.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')

    for row in reader:
        code_gonm = row['code_gonm']

        # Trouver l'espèce par son code GONM
        try:
            espece = Espece.objects.get(code_gonm=code_gonm)
            # Créer l'observation...
            # fiche = FicheObservation.objects.create(espece=espece, ...)
        except Espece.DoesNotExist:
            print(f"Espèce non trouvée pour le code {code_gonm}")
```

## Troubleshooting

### Problème : Les codes ne s'affichent pas

**Vérifications** :
1. Les codes sont-ils en base ?
   ```python
   Espece.objects.exclude(code_gonm='').count()
   ```
2. Le template accède-t-il correctement au champ ?
   ```django
   {{ espece.code_gonm|default:"VIDE" }}
   ```
3. Le `select_related` est-il utilisé pour optimiser ?
   ```python
   fiches = FicheObservation.objects.select_related('espece')
   ```

### Problème : Import échoue

**Erreurs courantes** :
- **Encodage** : Vérifier que le fichier est en UTF-8
- **Délimiteur** : Doit être une tabulation, pas une virgule
- **Colonnes manquantes** : Vérifier les noms des colonnes
- **IDs invalides** : Les `espece_trouvee_id` doivent exister en base

**Debug** :
```bash
# Voir les détails avec verbosité
python manage.py import_codes_gonm --dry-run --verbosity 2
```

### Problème : Codes dupliqués

Si plusieurs espèces ont le même code GONM :

```python
from django.db.models import Count

duplicates = (
    Espece.objects
    .exclude(code_gonm='')
    .values('code_gonm')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

for dup in duplicates:
    print(f"Code {dup['code_gonm']} : {dup['count']} espèces")
    especes = Espece.objects.filter(code_gonm=dup['code_gonm'])
    for espece in especes:
        print(f"  - {espece.nom} ({espece.nom_scientifique})")
```

## Ressources

### Fichiers importants

- **Modèle** : `taxonomy/models.py`
- **Migration** : `taxonomy/migrations/0002_espece_code_gonm.py`
- **Commande d'import** : `taxonomy/management/commands/import_codes_gonm.py`
- **Commande d'analyse** : `taxonomy/management/commands/analyser_correspondances_gonm.py`
- **Documentation détaillée** : `docs/INTEGRATION_CODES_GONM.md`

### Liens externes

- [Site du GONM](http://www.gonm.org/) (si accessible)
- Liste officielle des codes GONM (fichier CSV source)

---

*Dernière mise à jour : 2026-01-10*
