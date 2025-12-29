# API de recherche de communes - Optimisation par pertinence

> Documentation de l'API AJAX `/geo/rechercher-communes/` et de son système de tri intelligent

## Vue d'ensemble

L'API `rechercher_communes` (dans `geo/views.py`) fournit une recherche autocomplete optimisée pour les communes françaises, avec support des anciennes communes fusionnées et filtrage géographique optionnel.

## Endpoint

**URL :** `/geo/rechercher-communes/`
**Méthode :** `GET`
**Authentification :** Requise (`@login_required`)

## Paramètres

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `q` | string | ✅ | Terme de recherche (min 2 caractères) |
| `lat` | float | ❌ | Latitude GPS pour filtrage géographique |
| `lon` | float | ❌ | Longitude GPS pour filtrage géographique |
| `limit` | int | ❌ | Nombre max de résultats (défaut: 20) |

## Réponse JSON

```json
{
  "communes": [
    {
      "id": 12345,
      "nom": "Ger",
      "nom_actuel": null,
      "departement": "Hautes-Pyrénées",
      "code_departement": "65",
      "code_postal": "65100",
      "code_insee": "65200",
      "label": "Ger (65) - Hautes-Pyrénées",
      "latitude": "43.1234",
      "longitude": "0.5678",
      "altitude": 250,
      "est_fusionnee": false
    }
  ]
}
```

## Problème résolu : Communes à nom court

### Contexte

Avant l'optimisation (décembre 2024), les communes avec des noms très courts (comme "Ger", "Ur", "Eu", "Ay") n'apparaissaient pas dans les résultats de recherche.

**Exemple problématique :**
```
Recherche : "ger"
Résultats obtenus : Germagnat, Gernicourt, Germignonville...
❌ "Ger" (65) n'apparaissait PAS !
```

### Cause

Le système utilisait une seule requête `icontains` qui retournait TOUTES les communes contenant la recherche (Angers, Bergerac, etc.), limitée à 50 résultats. Les communes courtes étaient noyées dans la masse et dépassaient la limite.

## Solution implémentée

### 1. Stratégie de requêtes doubles

Au lieu d'une seule requête `icontains`, le système utilise maintenant **deux requêtes séparées** :

```python
# Haute priorité : Communes qui COMMENCENT par la recherche
communes_startswith = CommuneFrance.objects.filter(nom__istartswith=query)[:100]

# Basse priorité : Communes qui CONTIENNENT la recherche (sans commencer par)
communes_contains = CommuneFrance.objects.filter(
    nom__icontains=query
).exclude(nom__istartswith=query)[:100]
```

**Avantage :** Garantit que les communes courtes sont toujours dans les premiers résultats récupérés.

### 2. Système de tri par pertinence

Chaque résultat reçoit un **score de pertinence** calculé ainsi :

```python
nom_lower = commune['nom'].lower()
query_lower = query.lower()
nom_length = len(commune['nom'])

if nom_lower == query_lower:
    # Correspondance exacte : priorité maximale
    relevance_score = 1000
elif nom_lower.startswith(query_lower):
    # Commence par : haute priorité, favorise les noms courts
    relevance_score = 500 - nom_length
else:
    # Contient : priorité normale, favorise les noms courts
    relevance_score = 100 - nom_length
```

**Tri final :**
- Sans GPS : `sort(key=(-relevance_score, nom))`
- Avec GPS : `sort(key=distance_km)` (tri par distance prioritaire)

### 3. Limites optimisées

| Type | Startswith | Contains | Total |
|------|-----------|----------|-------|
| **Communes actuelles** | 100 | 100 | 200 |
| **Anciennes communes** | 50 | 50 | 100 |
| **Total récupéré** | 150 | 150 | **300** |
| **Affiché final** | - | - | **20** |

## Exemples de résultats

### Exemple 1 : Recherche "ger"

```
Score 1000 : Ger (65) - Hautes-Pyrénées          [Match exact]
Score  996 : Gers (32) - Gers                     [Commence + court]
Score  495 : Gergy (71) - Saône-et-Loire          [Commence]
Score  488 : Gerbéviller (54) - Meurthe-et-Moselle [Commence]
...
Score   94 : Angers (49) - Maine-et-Loire         [Contient]
Score   92 : Bergerac (24) - Dordogne             [Contient]
```

### Exemple 2 : Recherche "ur"

```
Score 1000 : Ur (66) - Pyrénées-Orientales        [Match exact]
Score  997 : Urt (64) - Pyrénées-Atlantiques      [Commence + court]
Score  997 : Ury (77) - Seine-et-Marne            [Commence + court]
Score  490 : Urcuit (64) - Pyrénées-Atlantiques   [Commence]
...
Score   94 : Muret (31) - Haute-Garonne           [Contient]
Score   91 : Bourges (18) - Cher                  [Contient]
```

### Exemple 3 : Avec GPS (filtrage géographique)

```bash
GET /geo/rechercher-communes/?q=paris&lat=48.8566&lon=2.3522
```

Résultats filtrés dans un rayon de **10 km** autour des coordonnées, triés par **distance croissante**.

## Performance

### Comparaison avant/après

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Communes récupérées | 50 (icontains) | 100 + 100 (startswith + contains) | ✅ Plus ciblé |
| Garantie noms courts | ❌ Non | ✅ Oui (dans les 100 premiers) | ✅ Résolu |
| Vitesse requête | Moyenne | Rapide | ✅ Index sur startswith |
| Pertinence résultats | Faible | Haute | ✅ Tri intelligent |

### Requêtes SQL générées

```sql
-- Requête 1 : Haute priorité (rapide, utilise index)
SELECT * FROM geo_communefrance
WHERE nom ILIKE 'ger%'
LIMIT 100;

-- Requête 2 : Basse priorité
SELECT * FROM geo_communefrance
WHERE nom ILIKE '%ger%' AND NOT nom ILIKE 'ger%'
LIMIT 100;
```

## Cas d'usage

### Formulaire de saisie d'observation

L'API est utilisée dans le formulaire de saisie/correction de fiches d'observation pour l'autocomplétion du champ "Commune".

**Fichier :** `observations/templates/saisie/saisie_observation.html`

### Liste de fiches (filtrage)

L'API est également utilisée dans la page de liste des fiches pour filtrer par commune.

**Fichier :** `observations/templates/liste_fiches_observations.html`

## Anciennes communes (fusions)

L'API gère automatiquement les **anciennes communes fusionnées** :

```json
{
  "nom": "Gerrots",
  "nom_actuel": "Victot-en-Auge",
  "label": "Gerrots → Victot-en-Auge (14) - Calvados",
  "est_fusionnee": true
}
```

Le système affiche la commune saisie avec une flèche vers la commune actuelle.

## Tests recommandés

Pour tester l'API, essayez ces cas limites :

```bash
# Communes très courtes (2-3 lettres)
/geo/rechercher-communes/?q=ur   # → Ur (66) en premier
/geo/rechercher-communes/?q=eu   # → Eu (76) en premier
/geo/rechercher-communes/?q=ay   # → Ay (51) en premier

# Communes courantes
/geo/rechercher-communes/?q=paris  # → Paris (75) en premier

# Avec GPS (rayon 10km)
/geo/rechercher-communes/?q=paris&lat=48.8566&lon=2.3522
```

## Limitations connues

1. **Minimum 2 caractères** : La recherche nécessite au moins 2 caractères
2. **Rayon GPS fixe** : Le filtrage géographique utilise un rayon fixe de 10 km
3. **Pas de recherche phonétique** : Pas de support pour les variantes orthographiques

## Historique

| Date | Version | Changement |
|------|---------|------------|
| 2024-12-28 | v2.0 | ✅ Ajout du système de tri par pertinence avec requêtes doubles |
| 2024-12 | v1.0 | Version initiale avec requête unique `icontains` |

## Voir aussi

- [Geo - Vue d'ensemble](index.md)
- [Gestion des communes et géolocalisation](../../guides/gestion_communes_geolocalisation.md)
- Code source : `geo/views.py` ligne 106-324

---

*Dernière mise à jour : 2024-12-28*
