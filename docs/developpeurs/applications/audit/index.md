# Audit - Vue d'ensemble

> Traçabilité et historique des modifications des fiches

## Responsabilité

L'application **audit** gère :
- Historique des modifications sur les FicheObservation
- Traçabilité (qui a modifié quoi et quand)
- Logs d'actions

## Modèles principaux

| Modèle | Description | Fichier |
|--------|-------------|---------|
| **HistoriqueModification** | Historique des changements sur une fiche | `audit/models.py` |

## Documentation existante

Voir **[docs/developpeurs/architecture/domaines/04_audit.md](../../architecture/domaines/04_audit.md)**

## Dépendances

- **observations** - FicheObservation
- **accounts** - Utilisateur (auteur de la modification)

## Voir aussi

- **[Architecture domaine audit](../../architecture/domaines/04_audit.md)**
- **[gotchas.md](gotchas.md)**

---

*Dernière mise à jour : 2025-12-27*
