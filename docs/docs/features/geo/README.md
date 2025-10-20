# Documentation de la fonctionnalité : Géo

Ce document décrit le fonctionnement du module `geo`, dont le rôle est de gérer les données géographiques, notamment la base de données des communes françaises et les services de géocodage.

## 1. Base de Données des Communes Françaises

La performance et la fiabilité du géocodage reposent sur une base de données locale contenant les ~35 000 communes françaises.

### Avantages
- **Performance** : La recherche d'une commune est quasi-instantanée.
- **Fiabilité** : Aucune dépendance à une API externe qui pourrait être lente ou indisponible.
- **Gratuité** : Pas de limite de requêtes.

### Commande de chargement

Pour peupler cette base de données, une commande de gestion est fournie.

```bash
# À exécuter une seule fois lors de l'installation initiale
python manage.py charger_communes_france
```

Cette commande télécharge les données depuis l'API officielle [geo.api.gouv.fr](https://geo.api.gouv.fr/decoupage-administratif) et les charge dans la table `geo_commune_france`.

Pour forcer le rechargement complet des données (par exemple, pour une mise à jour annuelle), utilisez l'option `--force` :
```bash
python manage.py charger_communes_france --force
```

### Modèle de données `CommuneFrance`

Le modèle (`geo/models.py`) stocke pour chaque commune :
- Le nom, code INSEE, code postal, département et région.
- La latitude et la longitude du centre de la commune.
- L'altitude moyenne.
- Des métadonnées comme la population et la superficie.

---

## 2. Stratégie de Géocodage

Le système utilise un utilitaire intelligent (`geo.utils.geocoding.GeocodeurCommunes`) qui opère en plusieurs niveaux pour trouver les coordonnées d'une commune.

### Architecture

1.  **Recherche en base locale (Priorité 1)** : Le système tente de trouver une correspondance exacte dans la table `geo_commune_france`. C'est la méthode la plus rapide.

2.  **Fallback sur API externe (Priorité 2)** : Si aucune correspondance n'est trouvée (par exemple, à cause d'une faute de frappe, d'un nom de lieu-dit ou d'une ancienne commune), le système interroge l'API **Nominatim** (basée sur OpenStreetMap) via la bibliothèque `geopy`.

3.  **Singleton Pattern** : Pour optimiser les ressources, le géocodeur est implémenté comme un singleton. Une seule instance est créée et réutilisée pour toutes les opérations de géocodage, évitant ainsi de multiples initialisations et connexions réseau.

### Gestion de l'altitude

Lors du géocodage, le système gère intelligemment le champ "altitude" :
- Si le champ est vide, il est automatiquement rempli avec l'altitude de la commune trouvée.
- Si le champ contient déjà une valeur (saisie manuellement), le système demande une confirmation à l'utilisateur avant de l'écraser.

---

## 3. Points d'accès API

Le module `geo` expose deux APIs JSON pour les besoins de l'interface utilisateur. Pour plus de détails, consultez le **[Guide des URLs et des APIs](../api/API_DOCUMENTATION.md)**.

- **`POST /geo/geocoder/`**
  - **Rôle** : Géocode manuellement une commune pour une fiche d'observation donnée et met à jour ses coordonnées en base.

- **`GET /geo/rechercher-communes/`**
  - **Rôle** : API de recherche pour l'auto-complétion du champ "Commune" dans les formulaires. Elle retourne une liste de communes correspondant à la recherche de l'utilisateur.
