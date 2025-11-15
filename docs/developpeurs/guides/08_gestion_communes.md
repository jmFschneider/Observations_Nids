# Guide de Gestion des Communes

Ce guide décrit les fonctionnalités d'administration des communes françaises dans le projet "Observations Nids".

---

## 📋 Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Accès à l'interface](#2-acces-a-linterface)
3. [Fonctionnalités disponibles](#3-fonctionnalites-disponibles)
4. [Cas d'usage](#4-cas-dusage)
5. [Gestion des alias](#5-gestion-des-alias)
6. [Sources de données](#6-sources-de-donnees)

---

## 1. Vue d'ensemble

### Objectif

L'interface de gestion des communes permet aux administrateurs de :
- Visualiser toutes les communes de la base de données
- Ajouter manuellement des communes manquantes
- Rechercher et ajouter des communes via Nominatim (OpenStreetMap)
- Gérer les alias et anciennes appellations
- Tracer la provenance des données

### Accès

**URL :** `http://127.0.0.1:8000/geo/communes/`

**Permissions :** Réservé aux administrateurs uniquement (`is_staff=True`)

---

## 2. Accès à l'interface

### Page principale

La page de liste des communes (`/geo/communes/`) affiche :

- **Statistiques** :
  - Total de communes
  - Répartition par source (API Géoplateforme, Nominatim, Manuelle)
  - Nombre de communes avec alias
  - Nombre de communes fusionnées

- **Filtres de recherche** :
  - Recherche par nom, code INSEE, code postal
  - Filtre par département
  - Filtre par région
  - Filtre par source de données

- **Actions rapides** :
  - Bouton "Rechercher sur Nominatim" (killer feature)
  - Bouton "Ajouter manuellement"

---

## 3. Fonctionnalités disponibles

### 3.1 Liste des communes

**URL :** `/geo/communes/`

**Fonctionnalités :**
- Affichage paginé (50 communes par page)
- Recherche multi-critères
- Tri par nom, département, etc.
- Indicateurs visuels :
  - Badge "Fusionnée" pour les communes ayant fusionné
  - Badge de source (API Géo, Nominatim, Manuel)
  - Icône alias si autres noms disponibles

### 3.2 Détail d'une commune

**URL :** `/geo/communes/<id>/`

**Informations affichées :**
- Identification (nom, code INSEE, code postal)
- Localisation (département, région, coordonnées GPS)
- Autres appellations / alias
- Commune actuelle (si fusionnée)
- Anciennes communes rattachées
- Métadonnées (source, ajoutée par, dates)
- **Utilisation** : Nombre de fiches d'observation utilisant cette commune

**Actions :**
- Modifier la commune
- Supprimer la commune (si non utilisée)
- Lien vers Google Maps

### 3.3 Recherche Nominatim (Killer Feature)

**URL :** `/geo/communes/rechercher-nominatim/`

**Fonctionnement :**

1. **Saisir les informations** :
   - Nom de la commune (obligatoire)
   - Département / Pays (optionnel mais recommandé)

2. **Recherche** :
   - Appel à Nominatim (OpenStreetMap)
   - Récupération automatique des coordonnées GPS
   - Récupération de l'altitude si disponible

3. **Vérification** :
   - Affichage des informations trouvées
   - Lien vers Google Maps pour vérification visuelle

4. **Ajout** :
   - Bouton "Ajouter cette commune"
   - Création automatique avec source `nominatim`
   - Redirection vers page de modification pour compléter les infos

**Cas d'usage :**
- Anciennes communes (ex: "Les Praz" → fusionné avec Chamonix)
- Communes étrangères (ex: "Genève, Suisse")
- Lieux-dits importants
- Erreurs OCR récurrentes

### 3.4 Création manuelle

**URL :** `/geo/communes/creer/`

**Champs obligatoires :**
- Nom
- Code INSEE (5 caractères)
- Latitude
- Longitude

**Champs optionnels :**
- Code postal
- Code département
- Nom département
- Région
- Altitude
- Autres noms (alias)
- Commune actuelle (si fusionnée)
- Commentaire

**Utilisation :**
Pour les cas où Nominatim ne trouve pas la commune ou lorsque vous avez déjà les coordonnées GPS précises.

### 3.5 Modification

**URL :** `/geo/communes/<id>/modifier/`

Permet de modifier tous les champs d'une commune existante.

**Cas d'usage :**
- Compléter les informations après ajout via Nominatim
- Corriger une erreur
- Ajouter des alias
- Mettre à jour les coordonnées

### 3.6 Suppression

**URL :** `/geo/communes/<id>/supprimer/`

**Règles de sécurité :**
- ❌ **Impossible** si la commune est utilisée dans des observations
- ✅ **Possible** si aucune observation ne l'utilise

**Affichage :**
- Nombre de fiches utilisant la commune
- Alerte claire si suppression impossible
- Confirmation avant suppression

---

## 4. Cas d'usage

### Cas 1 : Ajouter une ancienne commune

**Problème :** L'OCR détecte "Les Praz" mais cette commune n'existe plus (fusionnée avec Chamonix).

**Solution :**

1. Aller sur `/geo/communes/rechercher-nominatim/`
2. Saisir :
   - Nom : `Les Praz`
   - Département : `Haute-Savoie`
3. Cliquer sur "Rechercher"
4. Vérifier les coordonnées GPS
5. Cliquer sur "Ajouter cette commune"
6. Compléter les informations :
   - Autres noms : `Les Praz, Les Praz-de-Chamonix`
   - Commune actuelle : `Chamonix-Mont-Blanc`
   - Commentaire : `Ancienne commune fusionnée en 2017`

**Résultat :** Les prochaines observations avec "Les Praz" seront automatiquement géocodées.

### Cas 2 : Ajouter une commune étrangère

**Problème :** Observation effectuée à Genève (Suisse), commune non présente dans la base.

**Solution :**

1. Aller sur `/geo/communes/rechercher-nominatim/`
2. Saisir :
   - Nom : `Genève`
   - Département : `Suisse`
3. Cliquer sur "Rechercher"
4. Cliquer sur "Ajouter cette commune"
5. Compléter :
   - Code département : `CH` (convention pour Suisse)
   - Commentaire : `Commune suisse - observations transfrontalières`

### Cas 3 : Gérer une erreur OCR récurrente

**Problème :** L'OCR confond souvent "Rouffiac" avec "Rouffipac".

**Solution :**

1. Rechercher la commune "Rouffiac" dans `/geo/communes/`
2. Cliquer sur "Modifier"
3. Ajouter dans "Autres noms" : `Rouffipac, Roufiac`
4. Commentaire : `Variantes OCR détectées`

**Résultat :** Le géocodeur trouvera "Rouffiac" même si l'OCR lit "Rouffipac".

---

## 5. Gestion des alias

### Qu'est-ce qu'un alias ?

Un alias est un nom alternatif pour une commune, stocké dans le champ `autres_noms`.

**Exemples d'utilisation :**
- Anciennes appellations (ex: "Les Praz" pour Chamonix)
- Erreurs OCR récurrentes (ex: "Rouffipac" pour "Rouffiac")
- Variantes orthographiques (ex: "St-James" pour "Saint-James")

### Format

Les alias doivent être séparés par des **virgules** :

```
Les Praz, Les Praz-de-Chamonix, Praz de Chamonix
```

### Fonctionnement

Le géocodeur recherche dans :
1. Le nom principal (`nom`)
2. Les alias (`autres_noms`)

Ainsi, toutes les variantes seront reconnues.

### Méthode `tous_les_noms`

Le modèle `CommuneFrance` expose une propriété utile :

```python
commune.tous_les_noms
# Retourne : ['Chamonix-Mont-Blanc', 'Les Praz', 'Les Praz-de-Chamonix']
```

---

## 6. Sources de données

### Types de sources

Le champ `source_ajout` peut avoir 3 valeurs :

| Valeur | Signification | Badge |
|--------|--------------|-------|
| `api_geo` | API Découpage administratif (geo.api.gouv.fr) | 🔵 Bleu |
| `nominatim` | Nominatim (OpenStreetMap) | 🟢 Vert |
| `manuel` | Ajout manuel par administrateur | 🟡 Jaune |

### Traçabilité

Chaque commune conserve :
- **Source** : Provenance des données
- **Ajoutée par** : Utilisateur ayant créé la commune (si ajout manuel/Nominatim)
- **Date de création** : Date d'ajout dans la base
- **Date de MAJ** : Dernière modification
- **Commentaire** : Notes sur l'origine

### Statistiques

La page principale affiche :
- Nombre de communes par source
- Permet de filtrer par source

---

## 7. Commune fusionnée

### Fonctionnalité

Le champ `commune_actuelle` permet de créer un lien entre :
- Une **ancienne commune** (ex: "Les Praz")
- La **commune actuelle** (ex: "Chamonix-Mont-Blanc")

### Utilisation

Lors de la modification d'une commune :
1. Sélectionner la commune actuelle dans le menu déroulant
2. Enregistrer

### Affichage

- Badge "Fusionnée" dans la liste
- Alerte jaune dans la page détail
- Lien vers la commune actuelle
- Liste des anciennes communes sur la page de la commune actuelle

---

## 8. Bonnes pratiques

### ✅ À faire

- **Toujours vérifier** que la commune n'existe pas déjà avant d'ajouter
- **Compléter les métadonnées** après ajout via Nominatim (code dept, code postal)
- **Utiliser les alias** pour gérer les variantes orthographiques
- **Documenter dans le commentaire** l'origine de la commune
- **Lier les communes fusionnées** via le champ `commune_actuelle`

### ❌ À éviter

- **Ne pas dupliquer** : Vérifier d'abord si la commune existe
- **Ne pas supprimer** une commune utilisée dans des observations
- **Ne pas modifier** les coordonnées sans vérification
- **Ne pas oublier** de renseigner la source

---

## 9. Référence technique

### Modèle CommuneFrance

```python
class CommuneFrance(models.Model):
    # Identification
    nom = models.CharField(max_length=200)
    code_insee = models.CharField(max_length=5, unique=True)
    code_postal = models.CharField(max_length=5)

    # Localisation
    departement = models.CharField(max_length=100)
    code_departement = models.CharField(max_length=3)
    region = models.CharField(max_length=100, blank=True)

    # GPS
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.IntegerField(null=True, blank=True)

    # Nouveaux champs
    source_ajout = models.CharField(...)  # api_geo, nominatim, manuel
    autres_noms = models.TextField(blank=True)  # Alias séparés par virgules
    commentaire = models.TextField(blank=True)
    ajoutee_par = models.ForeignKey(User, ...)
    date_creation = models.DateTimeField(auto_now_add=True)
    commune_actuelle = models.ForeignKey('self', ...)  # Fusion
```

### Méthodes utiles

```python
# Nombre d'observations utilisant cette commune
commune.nombre_observations()  # → int

# Vérifier si utilisée
commune.est_utilisee()  # → bool

# Vérifier si fusionnée
commune.est_ancienne_commune()  # → bool

# Tous les noms (principal + alias)
commune.tous_les_noms  # → list
```

### URLs

```python
# Liste
reverse('geo:liste_communes')

# Détail
reverse('geo:detail_commune', kwargs={'commune_id': 123})

# Création manuelle
reverse('geo:creer_commune')

# Modification
reverse('geo:modifier_commune', kwargs={'commune_id': 123})

# Suppression
reverse('geo:supprimer_commune', kwargs={'commune_id': 123})

# Recherche Nominatim
reverse('geo:rechercher_nominatim')
```

---

**Document créé le** : 13 novembre 2025
**Auteur** : Claude Code
**Version** : 1.0
