# Geo - Vue d'ensemble

> Gestion de la géolocalisation : communes, départements, coordonnées GPS

## Responsabilité

L'application **geo** gère le référentiel géographique :
- Communes françaises (import INSEE, data.gouv.fr)
- Départements
- Validation des coordonnées GPS
- Géocodage et reverse géocodage

## Modèles principaux

| Modèle | Description | Fichier |
|--------|-------------|---------|
| **Commune** | Commune française avec coordonnées | `geo/models.py` |
| **CommuneAncienne** | Anciennes communes (fusions) | `geo/models.py` |
| **Departement** | Département français | `geo/models.py` |

## Commandes management

- `python manage.py importer_communes` - Import des communes depuis INSEE/data.gouv.fr
- `python manage.py importer_anciennes_communes` - Import des anciennes communes

## Documentation existante

- **[API de recherche de communes](api_recherche_communes.md)** - Système de recherche optimisé par pertinence
- **[Gestion des communes et géolocalisation](../../guides/gestion_communes_geolocalisation.md)** - Guide général

## Dépendances

- **core** - Modèles de base

## Voir aussi

- **[gotchas.md](gotchas.md)**

---

*Dernière mise à jour : 2025-12-27*
