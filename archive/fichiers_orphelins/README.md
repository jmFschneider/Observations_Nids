# Archive des Fichiers Orphelins

**Date d'archivage** : 2025-10-31
**Branche** : optim/nettoyage

## Contexte

Cette archive contient les fichiers identifiés comme orphelins (non utilisés) dans le projet Observations Nids.
Un fichier est considéré comme orphelin s'il n'est jamais importé, référencé ou appelé dans le code actif.

## Fichiers Archivés

### 📁 Python (4 fichiers)

#### `ace_tools.py`
- **Raison** : Fonction `display_dataframe_to_user` jamais importée ni utilisée
- **Confiance** : Élevée
- **Date origine** : Utilitaire de debug obsolète

#### `views.py` (anciennement `accounts/views.py`)
- **Raison** : Fichier vide redondant avec le module `accounts/views/`
- **Confiance** : Élevée
- **Note** : La logique est maintenant dans `accounts/views/auth.py` et `accounts/views/admin_views.py`

#### `ingest_views.py` (anciennement `ingest/views.py`)
- **Raison** : Fichier vide redondant avec le module `ingest/views/`
- **Confiance** : Élevée
- **Note** : La logique est répartie dans les sous-modules de `ingest/views/`

#### `workflow_importation_legacy.py`
- **Raison** : Version legacy du workflow d'importation, remplacée par des modules séparés
- **Confiance** : Élevée
- **Note** : Code refactoré et déplacé vers `home.py`, `importation.py`, et `especes.py`

---

### 📁 Templates (2 fichiers)

#### `saisie_observation_test.html`
- **Raison** : Template de test jamais référencé dans les URLs ou vues
- **Confiance** : Élevée
- **Origine** : `observations/templates/saisie/`

#### `test_api_communes.html`
- **Raison** : Fichier HTML de test standalone à la racine, jamais servi par Django
- **Confiance** : Élevée

---

### 📁 Static/CSS (6 fichiers)

Les fichiers CSS suivants ne sont référencés dans aucun template HTML :

- `board.css` - Interface de board abandonnée
- `base.css` - Ancien CSS de base remplacé
- `workflow.css` - Workflow visuel abandonné
- `timeline.css` - Timeline abandonnée
- `jsplumb.css` - Bibliothèque jsPlumb non utilisée
- `pygments.css` - Coloration syntaxique non utilisée

**Confiance** : Élevée
**Note** : Ces fichiers semblent liés à une ancienne fonctionnalité de workflow/board visuel qui a été abandonnée.

---

### 📁 Static/JS (4 fichiers)

Les fichiers JavaScript suivants ne sont référencés dans aucun template HTML :

- `jquery.jsPlumb-1.6.2-min.js` - Bibliothèque pour diagrammes de flux
- `BootstrapMenu.min.js` - Menu contextuel Bootstrap
- `board.js` - Logique du board abandonné
- `jquery.tristate.js` - Checkboxes tristate

**Confiance** : Élevée
**Note** : Fichiers liés aux CSS orphelins ci-dessus (fonctionnalité workflow/board abandonnée).

---

### 📁 Documentation (1 fichier)

#### `IA_REFACTORING_PLAN.md`
- **Raison** : Plan de travail de l'IA marqué comme "TERMINÉ", non référencé dans les nav de mkdocs
- **Confiance** : Moyenne
- **Note** : Document interne de planification, conservé pour référence historique

---

## Fichiers Réorganisés (déplacés vers /scripts/)

Les fichiers suivants ont été **déplacés vers `/scripts/`** car ils restent utiles pour la maintenance :

- `efface_bdd_test.py` - Script pour nettoyer la base de test
- `reset_et_jeu_test.py` - Script pour réinitialiser et créer un jeu de test
- `import_especes.py` - Script d'importation CSV des espèces

**Note** : Ces scripts doivent être documentés dans `/scripts/README.md`

---

## Statistiques du Nettoyage

- **Total fichiers archivés** : 17 fichiers
- **Total fichiers réorganisés** : 3 fichiers
- **Réduction estimée** : ~50KB de code mort supprimé

---

## Restauration

Si vous avez besoin de restaurer un fichier archivé :

```bash
# Pour un fichier Python
git mv archive/fichiers_orphelins/python/[fichier].py [destination]/

# Pour un fichier template
git mv archive/fichiers_orphelins/templates/[fichier].html [destination]/

# Pour un fichier statique
mv archive/fichiers_orphelins/static/[css|js]/[fichier] staticfiles/
```

---

## Notes

- Les fichiers `staticfiles/` n'étaient pas sous contrôle de version (normaux pour des fichiers collectés)
- Tous les fichiers Python étaient sous contrôle Git et ont été déplacés avec `git mv`
- L'historique Git de ces fichiers est préservé

---

**Analyse effectuée le** : 2025-10-31
**Outil** : Claude Code + Analyse manuelle
**Validé par** : [À compléter]
