# Core - Vue d'ensemble

> Modèles abstraits, utilitaires et constantes de base du projet

## Responsabilité

L'application **core** fournit :
- Modèles abstraits (SoftDeleteModel, TimestampedModel)
- Mixins réutilisables
- Constantes globales (choix de statuts, etc.)
- Utilitaires communs

## Modèles de base

| Modèle abstrait | Description | Fichier |
|-----------------|-------------|---------|
| **SoftDeleteModel** | Soft delete (suppression logique) | `core/models.py` |
| **TimestampedModel** | created_at / updated_at automatiques | `core/models.py` |

## Constantes

**Fichier** : `core/constants.py`

```python
STATUT_CORRECTION_CHOICES = [
    ('nouveau', 'Nouveau'),
    ('en_edition', 'En édition'),
    ('en_cours', 'En cours de validation'),
    ('valide', 'Validé'),
]

STATUT_IMPORTATION_CHOICES = [
    ('en_attente', 'En attente de validation'),
    ('erreur', 'Erreur détectée'),
    ('complete', 'Importation complétée'),
]
```

## Dépendances

Aucune (app de base)

## Voir aussi

- **[gotchas.md](gotchas.md)**

---

*Dernière mise à jour : 2025-12-27*
