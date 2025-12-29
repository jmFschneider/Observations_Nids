# Taxonomy - Vue d'ensemble

> Gestion des espèces d'oiseaux, familles et codes de référence (GONM)

## Responsabilité

L'application **taxonomy** gère le référentiel taxonomique :
- Espèces d'oiseaux (nom scientifique, nom vernaculaire)
- Familles d'oiseaux
- Codes GONM (Groupe Ornithologique Normand)
- Import depuis sources externes

## Modèles principaux

| Modèle | Description | Fichier |
|--------|-------------|---------|
| **Espece** | Espèce d'oiseau | `taxonomy/models.py` |
| **Famille** | Famille ornithologique | `taxonomy/models.py` |

## Commandes management

- `python manage.py import_codes_gonm` - Import des codes GONM depuis CSV
- `python manage.py analyser_correspondances_gonm` - Analyse des correspondances

## Documentation existante

- **[docs/developpeurs/guides/gestion_especes_taxonomie.md](../../guides/gestion_especes_taxonomie.md)**
- **[docs/INTEGRATION_CODES_GONM.md](../../../INTEGRATION_CODES_GONM.md)**

## Dépendances

- **core** - Modèles de base

## Voir aussi

- **[gotchas.md](gotchas.md)**

---

*Dernière mise à jour : 2025-12-27*
