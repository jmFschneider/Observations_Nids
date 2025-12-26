# Guide de Gestion des Communes et Géolocalisation

Guide complet pour la gestion des communes françaises et le système de géolocalisation dans le projet "Observations Nids".

> **🎯 Public cible :** Administrateurs et développeurs
> **📅 Dernière mise à jour :** 26 décembre 2024
> **✨ Nouveauté :** Interface web d'administration centralisée

---

## 📋 Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Interface d'administration](#2-interface-dadministration)
3. [Gestion des communes](#3-gestion-des-communes)
4. [Géolocalisation automatique](#4-geolocalisation-automatique)
5. [Architecture technique](#5-architecture-technique)
6. [Référence rapide](#6-reference-rapide)
7. [Dépannage](#7-depannage)

---

## 1. Vue d'ensemble

### Objectif

Le système permet de :
- ✅ Gérer une base de données locale de ~35 000 communes françaises
- ✅ Géolocaliser automatiquement les observations (nom commune → coordonnées GPS)
- ✅ Gérer les anciennes communes fusionnées (~2 900)
- ✅ Administrer les données depuis une interface web unique

### Niveaux de précision

| Type de donnée | Précision | Usage |
|----------------|-----------|-------|
| **Commune actuelle** | ~5 km (centre de commune) | Géocodage standard |
| **Ancienne commune** | Variable (si coordonnées disponibles) | Communes fusionnées |
| **Lieu-dit via Nominatim** | ~500 m | Précision accrue |
| **GPS terrain** | 5-20 m | Observations sur le terrain |

### Architecture en deux niveaux

```
┌─────────────────────────────────────┐
│  Base locale (35 000 communes)     │
│  Source : API Géoplateforme        │
│  Recherche instantanée             │
└─────────────────────────────────────┘
                ↓ Si non trouvé
┌─────────────────────────────────────┐
│  Géocodage en ligne (Nominatim)    │
│  Pour cas spéciaux, erreurs OCR    │
│  Gratuit avec limite 1 req/sec     │
└─────────────────────────────────────┘
```

---

## 2. Interface d'administration

### 🎯 Accès

**URL :** `/geo/administration-donnees/`

**Permissions :** Réservé aux administrateurs (`is_staff=True`)

**Navigation :**
1. Se connecter comme administrateur
2. Menu principal → Section "Référentiels" ou "Administration"
3. Cliquer sur "Administration des données communales"

### Page d'administration

L'interface centralise toutes les opérations de gestion des communes :

#### 📊 Statistiques affichées

- **Total communes** : Nombre de communes actuelles en base
- **API Géoplateforme** : Communes chargées depuis l'API officielle
- **Anciennes communes** : Communes fusionnées/déléguées

#### 🔧 Scripts d'administration (3 boutons)

##### 1. Charger les communes

**Fonction :** Charge toutes les communes de France depuis l'API Géoplateforme

**Source :** [geo.api.gouv.fr](https://geo.api.gouv.fr)
**Nombre :** ~35 000 communes
**Durée :** ~30 secondes

**Options :**
- ☐ **Force** : Remplacer les données existantes (pour mise à jour annuelle)

**Utilisation :**
```
1. Cocher "Force" si vous voulez écraser les données existantes
2. Cliquer sur "Lancer le chargement"
3. Attendre la fin du traitement
4. Un message de succès s'affiche avec le résumé
```

**Équivalent commande (ancienne méthode) :**
```bash
python manage.py charger_communes_france [--force]
```

##### 2. Anciennes communes (CSV)

**Fonction :** Importe les anciennes communes fusionnées depuis le fichier CSV officiel

**Source :** [data.gouv.fr/communes-nouvelles](https://www.data.gouv.fr/fr/datasets/communes-nouvelles/)
**Fichier :** `communes_nouvelles.csv` (doit être présent à la racine du projet)
**Nombre :** ~1 587 communes

**Options :**
- ☐ **Effacer** : Supprimer les données existantes avant import

**Utilisation :**
```
1. Télécharger le fichier CSV si nécessaire :
   curl -L -o communes_nouvelles.csv "https://www.data.gouv.fr/fr/datasets/r/eaa68059-aaea-4ff9-a6f8-cf6146fe8a8b"

2. Cocher "Effacer" pour un import propre (recommandé)
3. Cliquer sur "Importer"
4. Attendre la fin du traitement
```

**Équivalent commande :**
```bash
python manage.py importer_anciennes_communes [--clear]
```

##### 3. Vérifier les communes déléguées

**Fonction :** Complète la base avec les communes déléguées manquantes depuis l'API

**Source :** API Géoplateforme
**Ajout :** ~1 346 communes supplémentaires
**Durée :** Quelques minutes

**Avantages :**
- ✅ Récupère les coordonnées GPS de chaque ancienne commune
- ✅ Import automatique des codes postaux
- ✅ Idempotent (peut être relancé sans créer de doublons)
- ✅ Crée automatiquement les communes nouvelles si manquantes

**Utilisation :**
```
1. Cliquer sur "Vérifier"
2. Attendre la fin du traitement
3. Le script affiche le nombre de communes ajoutées
```

**Équivalent commande :**
```bash
python manage.py verifier_communes_deleguees
```

#### 🔄 Ordre recommandé pour une nouvelle installation

1. **Charger les communes** (avec force)
2. **Importer les anciennes communes** (avec effacer)
3. **Vérifier les communes déléguées**

---

## 3. Gestion des communes

### Liste des communes

**URL :** `/geo/communes/`

**Fonctionnalités :**

#### Recherche avancée
- Par nom de commune
- Par code INSEE
- Par code postal
- Par alias (autres noms)
- **Nouveauté :** Recherche aussi dans les anciennes communes

#### Filtres
- Département (liste déroulante)
- Région
- Source de données (API Géo, Nominatim, Manuel)

#### Affichage
- Pagination (50 communes par page)
- Tri par nom
- Badges visuels :
  - Source (API Géo / Nominatim / Manuel)
  - Anciennes communes rattachées (si applicable)

### Détail d'une commune

**URL :** `/geo/communes/<id>/`

**Informations affichées :**

| Section | Contenu |
|---------|---------|
| **Identification** | Nom, code INSEE, code postal |
| **Localisation** | Département, région, coordonnées GPS, altitude |
| **Alias** | Autres noms / variantes orthographiques |
| **Anciennes communes** | Liste des communes fusionnées rattachées |
| **Utilisation** | Nombre de fiches d'observation |
| **Métadonnées** | Source, ajouté par, dates création/modification |

**Actions disponibles :**
- 🔧 Modifier la commune
- 🗑️ Supprimer (si non utilisée)
- 🗺️ Voir sur Google Maps

### Recherche Nominatim (Ajout facile)

**URL :** `/geo/communes/rechercher-nominatim/`

**Fonction :** Ajouter facilement une commune en recherchant sur OpenStreetMap

**Cas d'usage :**
- ✅ Anciennes communes (ex: "Les Praz" → fusionné avec Chamonix)
- ✅ Communes étrangères (ex: "Genève, Suisse")
- ✅ Lieux-dits importants
- ✅ Corriger les erreurs OCR récurrentes

**Utilisation :**

```
1. Saisir le nom de la commune
2. Saisir le département (optionnel mais recommandé)
3. Cliquer sur "Rechercher"
4. Vérifier les coordonnées affichées
5. Vérifier sur Google Maps (lien fourni)
6. Cliquer sur "Ajouter cette commune"
7. Compléter les informations si nécessaire
```

**Exemple : Ajouter une ancienne commune**

**Problème :** L'OCR détecte "Les Praz" mais cette commune n'existe plus (fusionnée).

**Solution :**
1. Aller sur `/geo/communes/rechercher-nominatim/`
2. Saisir : Nom = `Les Praz`, Département = `Haute-Savoie`
3. Cliquer sur "Rechercher"
4. Vérifier les coordonnées
5. Ajouter la commune
6. Modifier pour compléter :
   - Autres noms : `Les Praz, Les Praz-de-Chamonix`
   - Commentaire : `Ancienne commune fusionnée avec Chamonix`

### Création manuelle

**URL :** `/geo/communes/creer/`

**Champs obligatoires :**
- Nom
- Code INSEE (5 caractères)
- Latitude
- Longitude

**Champs optionnels :**
- Code postal, département, région
- Altitude
- Autres noms (alias)
- Commentaire

**Utilisation :**
Pour les cas où Nominatim ne trouve pas la commune ou lorsque vous avez déjà les coordonnées GPS précises.

### Modification

**URL :** `/geo/communes/<id>/modifier/`

**Cas d'usage :**
- Compléter les informations après ajout via Nominatim
- Corriger une erreur
- Ajouter des alias pour gérer les variantes OCR
- Mettre à jour les coordonnées

### Suppression

**URL :** `/geo/communes/<id>/supprimer/`

**Règles de sécurité :**
- ❌ **Impossible** si la commune est utilisée dans des observations
- ✅ **Possible** si aucune observation ne l'utilise

---

## 4. Géolocalisation automatique

### Principe de fonctionnement

Le géocodeur recherche les coordonnées GPS d'une commune en 4 étapes :

```
1. Recherche nom exact + département
        ↓ Si non trouvé
2. Recherche nom exact + code postal
        ↓ Si non trouvé
3. Recherche nom seul (si unique en France)
        ↓ Si non trouvé
4. Recherche floue (nom contient...)
        ↓ Si non trouvé
5. Fallback sur Nominatim (API externe)
```

### Géocodage automatique (OCR)

Lors de la transcription OCR des fiches manuscrites :
1. OCR extrait : commune, département, lieu-dit
2. Système crée la fiche d'observation
3. **Géocodage automatique** déclenché
4. Localisation mise à jour avec coordonnées GPS

### Géocodage manuel (interface)

Depuis l'interface de saisie/correction :
1. Bouton **"Géocoder la commune"**
2. Système recherche dans la base locale
3. Si trouvé : mise à jour immédiate
4. Si non trouvé : tentative via Nominatim
5. Résultat affiché avec source

### Gestion de l'altitude

Le système gère intelligemment le champ altitude :

| Valeur actuelle | Action | Confirmation requise |
|----------------|--------|---------------------|
| Vide / `""` | Remplace automatiquement | Non |
| `"0"` ou `"0.0"` ou `"0m"` | Remplace automatiquement | Non |
| Valeur réelle (ex: `1900`) | Demande confirmation | **Oui** |

**Popup de confirmation :**
```
L'altitude actuelle est 1900m.
Voulez-vous la remplacer par 84m (altitude de Saint-James) ?

[OK] [Annuler]
```

### Gestion des alias (variantes orthographiques)

**Format :** Alias séparés par des virgules

```
Les Praz, Les Praz-de-Chamonix, Praz de Chamonix
```

**Utilisation :**
- Anciennes appellations
- Erreurs OCR récurrentes
- Variantes orthographiques

Le géocodeur cherche dans le nom principal ET dans tous les alias.

---

## 5. Architecture technique

### Modèles de données

#### CommuneFrance (communes actuelles)

```python
class CommuneFrance(models.Model):
    # Identification
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True)
    code_postal = models.CharField(max_length=5)

    # Localisation administrative
    departement = models.CharField(max_length=100)
    code_departement = models.CharField(max_length=3, db_index=True)
    region = models.CharField(max_length=100, blank=True)

    # Coordonnées GPS (centre de commune)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.IntegerField(null=True, blank=True)

    # Gestion des alias et variantes
    autres_noms = models.TextField(blank=True)  # Alias séparés par virgules

    # Métadonnées
    source_ajout = models.CharField(...)  # api_geo, nominatim, manuel
    ajoutee_par = models.ForeignKey(User, ...)
    commentaire = models.TextField(blank=True)
```

**Table :** `geo_commune_france`
**Nombre d'enregistrements :** ~35 000

#### AncienneCommune (communes fusionnées)

```python
class AncienneCommune(models.Model):
    # Identification
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True)

    # Localisation (historique)
    code_postal = models.CharField(max_length=5, blank=True)
    code_departement = models.CharField(max_length=3)
    departement = models.CharField(max_length=100, blank=True)

    # Coordonnées GPS historiques
    latitude = models.DecimalField(..., null=True, blank=True)
    longitude = models.DecimalField(..., null=True, blank=True)
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
```

**Table :** `geo_ancienne_commune`
**Nombre d'enregistrements :** ~2 933

### Pourquoi deux tables séparées ?

**Avantages :**
- ✅ **Clarté :** On sait immédiatement si une commune existe encore
- ✅ **Géocodage précis :** Les anciennes communes gardent leurs coordonnées historiques
- ✅ **Requêtes simples :** `CommuneFrance.objects.all()` retourne seulement les communes actives
- ✅ **Traçabilité :** Historique des fusions préservé

### Géocodeur (Pattern Singleton)

**Fichier :** `geo/utils/geocoding.py`

```python
from geo.utils.geocoding import get_geocodeur

# Obtenir l'instance singleton
geocodeur = get_geocodeur()

# Géocoder une commune
coords = geocodeur.geocoder_commune("Chamonix-Mont-Blanc", "Haute-Savoie")

# Avec lieu-dit (précision accrue)
coords = geocodeur.geocoder_avec_lieu_dit(
    commune="Chamonix-Mont-Blanc",
    departement="Haute-Savoie",
    lieu_dit="Les Praz"
)
```

**Avantages du singleton :**
- Une seule instance réutilisée (économie de ressources)
- Réutilisation des connexions réseau Nominatim
- Performance améliorée de ~25%

### Vues d'administration (Backend)

**Fichier :** `geo/views_admin.py`

Les vues d'administration appellent les commandes `manage.py` via `call_command()` :

```python
from django.core.management import call_command
from io import StringIO

def charger_communes_api(request):
    # Capturer la sortie du script
    output = StringIO()

    # Exécuter le script
    if force:
        call_command('charger_communes_france', '--force',
                    stdout=output, stderr=output)
    else:
        call_command('charger_communes_france',
                    stdout=output, stderr=output)

    # Récupérer et afficher le résultat
    result = output.getvalue()
    messages.success(request, f"✅ Chargement terminé !\n\n{result}")
```

Cette architecture permet de :
- Réutiliser les scripts existants sans duplication de code
- Capturer la sortie pour l'afficher dans l'interface
- Gérer les erreurs proprement avec les messages Django

### APIs disponibles

#### 1. Géocodage manuel

**Endpoint :** `POST /geo/geocoder/`

**Paramètres :**
- `fiche_id` : ID de la fiche à géocoder
- `commune` : Nom de la commune
- `departement` : Nom ou code du département (optionnel)
- `lieu_dit` : Lieu-dit pour précision (optionnel)

**Réponse :**
```json
{
    "success": true,
    "coords": {
        "lat": 45.9237,
        "lon": 6.8694,
        "coordonnees_gps": "45.9237,6.8694",
        "code_insee": "74056",
        "source": "base_locale"
    },
    "message": "Commune géocodée avec succès"
}
```

#### 2. Recherche de communes (autocomplétion)

**Endpoint :** `GET /geo/rechercher-communes/`

**Paramètres :**
- `q` : Texte de recherche (min. 2 caractères)
- `lat`, `lon` : Pour tri par distance (optionnel)
- `limit` : Nombre max de résultats (défaut: 10)

**Réponse :**
```json
{
    "communes": [
        {
            "nom": "Chamonix-Mont-Blanc",
            "departement": "Haute-Savoie",
            "code_departement": "74",
            "code_postal": "74400",
            "latitude": 45.9237,
            "longitude": 6.8694,
            "altitude": 1035,
            "distance_km": 0.15
        }
    ]
}
```

---

## 6. Référence rapide

### Commandes manage.py (si besoin)

Bien que l'interface web soit recommandée, les commandes sont toujours disponibles :

```bash
# Charger les communes depuis l'API
python manage.py charger_communes_france [--force]

# Importer les anciennes communes depuis CSV
python manage.py importer_anciennes_communes [--file communes_nouvelles.csv] [--clear]

# Vérifier et compléter avec communes déléguées
python manage.py verifier_communes_deleguees [--dry-run] [--verbose]
```

### URLs principales

| URL | Description |
|-----|-------------|
| `/geo/administration-donnees/` | Page d'administration (scripts) |
| `/geo/communes/` | Liste des communes |
| `/geo/communes/<id>/` | Détail d'une commune |
| `/geo/communes/creer/` | Création manuelle |
| `/geo/communes/<id>/modifier/` | Modification |
| `/geo/communes/<id>/supprimer/` | Suppression |
| `/geo/communes/rechercher-nominatim/` | Recherche Nominatim |

### Sources de données

| Source | Type | URL |
|--------|------|-----|
| API Géoplateforme | Communes actuelles | https://geo.api.gouv.fr/decoupage-administratif |
| data.gouv.fr | Anciennes communes (CSV) | https://www.data.gouv.fr/fr/datasets/communes-nouvelles/ |
| Nominatim | Géocodage fallback | https://nominatim.openstreetmap.org/ |

### Méthodes utiles du modèle

```python
# Nombre d'observations utilisant cette commune
commune.nombre_observations()  # → int

# Vérifier si utilisée
commune.est_utilisee()  # → bool

# Tous les noms (principal + alias)
commune.tous_les_noms  # → list

# Anciennes communes rattachées (si commune actuelle)
commune.anciennes_communes.all()  # → QuerySet
```

---

## 7. Dépannage

### Problème : "Commune actuelle introuvable" lors de l'import

**Cause :** La commune nouvelle n'existe pas dans `CommuneFrance`

**Solution :**
1. Charger d'abord les communes actuelles via `/geo/administration-donnees/`
2. Cliquer sur "Charger les communes" (avec Force si nécessaire)
3. Réimporter les anciennes communes

### Problème : Fichier CSV introuvable

**Erreur :** `FileNotFoundError: communes_nouvelles.csv`

**Solution :**
```bash
# Télécharger le fichier à la racine du projet
cd /chemin/vers/projet
curl -L -o communes_nouvelles.csv "https://www.data.gouv.fr/fr/datasets/r/eaa68059-aaea-4ff9-a6f8-cf6146fe8a8b"
```

### Problème : Géocodage échoue

**Symptôme :** "Commune non trouvée" même pour une commune valide

**Diagnostic :**
1. Vérifier que la base est chargée : `/geo/administration-donnees/`
2. Vérifier les statistiques affichées
3. Essayer de chercher la commune dans `/geo/communes/`
4. Si absente, l'ajouter via Nominatim

**Solutions :**
- Vérifier l'orthographe (tirets, espaces, majuscules)
- Essayer avec le département
- Utiliser la recherche Nominatim
- Vérifier les logs : `tail -f logs/django.log`

### Problème : TransactionManagementError

**Erreur :** Lors de l'exécution d'un script via l'interface

**Cause :** Transaction en cours non fermée

**Solution :** Déjà gérée dans le code avec `connection.close()`, mais si le problème persiste :
```python
# Dans settings.py
DATABASES = {
    'default': {
        ...
        'ATOMIC_REQUESTS': False,  # Désactiver si problème
    }
}
```

### Problème : Permissions insuffisantes

**Symptôme :** Page d'administration inaccessible

**Cause :** Utilisateur non administrateur

**Solution :**
```python
# Django shell
python manage.py shell

from accounts.models import User
user = User.objects.get(username='nom_utilisateur')
user.is_staff = True
user.save()
```

### Maintenance annuelle recommandée

**Quand :** Une fois par an (janvier après publication des nouvelles données)

**Procédure :**
1. Aller sur `/geo/administration-donnees/`
2. Télécharger le nouveau CSV :
   ```bash
   curl -L -o communes_nouvelles.csv "https://www.data.gouv.fr/fr/datasets/r/eaa68059-aaea-4ff9-a6f8-cf6146fe8a8b"
   ```
3. Cliquer sur "Charger les communes" (cocher Force)
4. Cliquer sur "Anciennes communes" (cocher Effacer)
5. Cliquer sur "Vérifier les communes déléguées"
6. Vérifier les statistiques affichées

---

## Annexes

### Technologies utilisées

- **Django 6.0** - Framework web Python
- **Geopy 2.4.1** - Bibliothèque de géocodage
- **Nominatim** - Service de géocodage gratuit (OpenStreetMap)
- **API Géoplateforme** - API officielle française des communes
- **Bootstrap 5** - Framework CSS

### Fichiers du projet

| Fichier | Description |
|---------|-------------|
| `geo/models.py` | Modèles CommuneFrance et AncienneCommune |
| `geo/views_admin.py` | Vues d'administration (scripts et CRUD) |
| `geo/utils/geocoding.py` | Utilitaire de géocodage (singleton) |
| `geo/templates/geo/administration_donnees.html` | Interface d'administration |
| `geo/management/commands/charger_communes_france.py` | Script de chargement API |
| `geo/management/commands/importer_anciennes_communes.py` | Script d'import CSV |
| `geo/management/commands/verifier_communes_deleguees.py` | Script de vérification |

### Évolutions futures possibles

**Court terme :**
- [ ] Export CSV de la liste des communes
- [ ] Import/export des alias en masse
- [ ] Historique des modifications

**Moyen terme :**
- [ ] Cache Redis pour les résultats de géocodage
- [ ] API REST complète (DRF)
- [ ] Tâches Celery pour gros imports

**Long terme :**
- [ ] Migration vers PostgreSQL + PostGIS
- [ ] Carte interactive pour sélection de commune
- [ ] Export GeoJSON / KML

---

**Document créé le :** 26 décembre 2024
**Auteur :** Documentation consolidée
**Version :** 2.0
**Remplace :**
- `08_gestion_communes.md`
- `09_anciennes_communes.md`
- `02_geolocalisation.md`
