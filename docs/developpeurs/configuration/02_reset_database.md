# Guide de Réinitialisation de la Base de Données

Ce document explique comment utiliser les commandes de réinitialisation de la base de données pour gérer les cycles de développement et de test du projet Observations Nids.

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Commande `reset_importations`](#commande-reset_importations)
3. [Commande `reset_transcriptions`](#commande-reset_transcriptions)
4. [Scénarios d'utilisation](#scenarios-dutilisation)
5. [Précautions et bonnes pratiques](#precautions-et-bonnes-pratiques)

---

## Vue d'ensemble

Le projet dispose de **deux commandes Django** pour gérer la réinitialisation des données :

| Commande | Usage | Données préservées |
|---|---|---|
| `reset_importations` | Réinitialisation complète | `geo_commune_france`, `taxonomy_espece` |
| `reset_transcriptions` | Réinitialisation partielle | Idem + fiches créées (optionnel) |

### Pourquoi ces commandes ?

- **Tests d'importation** : Relancer le processus OCR et d'importation sans recréer les communes.
- **Développement** : Nettoyer la base sans perdre les données de référence.
- **Débogage** : Repartir d'un état propre tout en gardant les communes françaises chargées.

---

## Commande `reset_importations`

### Description

Réinitialise **TOUTES** les données d'importation et d'observation en préservant uniquement les données de référence géographique et taxonomique.

### Syntaxe

```bash
python manage.py reset_importations [OPTIONS]
```

### Options disponibles

| Option | Description |
|---|---|
| `--confirm` | Confirmer la réinitialisation sans demander (pour scripts automatisés). |
| `--keep-users` | Conserver tous les utilisateurs (sauf ceux créés par transcription). |
| `-h, --help` | Afficher l'aide. |

### Données supprimées

✅ **Supprimées :**
- Fiches d'observation
- Observations individuelles
- Remarques
- Historique des modifications
- États de correction
- Validations et historique de révision
- Importations en cours
- Transcriptions brutes
- Espèces candidates
- Utilisateurs créés par transcription (sauf si `--keep-users`)

❌ **Préservées :**
- Table `geo_commune_france` (toutes les communes françaises)
- Table `taxonomy_espece` (catalogue des espèces)
- Utilisateurs créés manuellement (ou tous si `--keep-users`)

**Note technique :** La commande tente également de réinitialiser les séquences d'auto-incrémentation pour les clés primaires (pour SQLite et PostgreSQL) afin d'éviter les conflits d'ID lors de la réinsertion de données.

### Exemples d'utilisation

#### Utilisation interactive (avec confirmation)

```bash
python manage.py reset_importations
```

**Sortie attendue :**
```
⚠️  ATTENTION : Cette opération va supprimer TOUTES les données suivantes :

  • Fiches d'observation
  • Observations
  • Remarques
  • Historique des modifications
  • États de correction
  • Importations en cours
  • Transcriptions brutes
  • Espèces candidates
  • Validations et historique de révision
  • Utilisateurs créés par transcription

✅ Les données suivantes seront PRÉSERVÉES :

  • geo_commune_france (toutes les communes)
  • taxonomy_espece (catalogue des espèces)

Êtes-vous sûr de vouloir continuer ? (oui/non) : oui

📊 Décompte avant suppression :
  ...

🗑️  Suppression en cours...
  ...
  ✓ Séquences SQLite réinitialisées

✅ Réinitialisation terminée avec succès !
...
```

---

## Commande `reset_transcriptions`

### Description

Réinitialise **uniquement** le processus de transcription OCR sans toucher aux fiches créées manuellement. Plus légère que `reset_importations`.

### Syntaxe

```bash
python manage.py reset_transcriptions [OPTIONS]
```

### Options disponibles

| Option | Description |
|---|---|
| `--confirm` | Confirmer la réinitialisation sans demander. |
| `--delete-fiches` | Supprimer également les fiches créées par transcription. |
| `-h, --help` | Afficher l'aide. |

### Données concernées

✅ **Supprimées :**
- Importations en cours
- Espèces candidates

🔄 **Réinitialisées (pas supprimées) :**
- Transcriptions brutes (le champ `traite` est remis à `False` pour permettre un nouvel import)

⚠️ **Supprimées si `--delete-fiches` :**
- Fiches d'observation créées par transcription

❌ **Toujours préservées :**
- Fiches créées manuellement
- Utilisateurs
- Communes françaises
- Espèces du catalogue

### Exemples d'utilisation

#### Réinitialisation simple (garde les fiches)

```bash
python manage.py reset_transcriptions
```

**Sortie attendue :**
```
⚠️  Cette opération va :

  • Supprimer : Importations en cours
  • Supprimer : Espèces candidates
  • Réinitialiser : Transcriptions brutes (marquées comme non traitées)

  ✅ Les fiches créées par transcription seront PRÉSERVÉES

Êtes-vous sûr de vouloir continuer ? (oui/non) : oui

📊 Décompte avant suppression :
  ...

🗑️  Suppression en cours...
  ✓ Importations en cours supprimées
  ✓ Transcriptions marquées comme non traitées
  ✓ Espèces candidates supprimées

✅ Réinitialisation des transcriptions terminée !

📋 Actions effectuées :
  • Importations supprimées : prêtes à être recréées
  • Transcriptions réinitialisées : prêtes à être retraitées
  • Espèces candidates supprimées : prêtes à être re-extraites

💡 Vous pouvez maintenant relancer l'importation depuis le début.
```

---

## Scénarios d'utilisation

### 🔄 Scénario 1 : Relancer l'importation OCR

**Problème :** Vous avez corrigé un bug dans le processus OCR et voulez réimporter les fiches.

**Solution :**
```bash
# Supprimer les fiches transcrites et réinitialiser
python manage.py reset_transcriptions --delete-fiches --confirm

# Relancer le workflow d'importation via l'interface web
```

### 🧪 Scénario 2 : Tests de développement

**Problème :** Vous développez une nouvelle fonctionnalité et voulez tester sur une base propre.

**Solution :**
```bash
# Tout effacer sauf les communes et espèces
python manage.py reset_importations --confirm
```

---

## Précautions et bonnes pratiques

### ⚠️ Avant d'exécuter une réinitialisation

1. **Sauvegarde de sécurité**
   ```bash
   # Pour SQLite
   cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
   # Pour PostgreSQL
   pg_dump -U <user> -h <host> <db_name> > backup.sql
   ```

2. **Vérifier l'environnement**
   ```bash
   # S'assurer qu'on est en développement
   python manage.py shell -c "from django.conf import settings; print(f'DEBUG={settings.DEBUG}')"
   ```

### ✅ Bonnes pratiques

- **Ne jamais exécuter en production** sans une sauvegarde vérifiée et un plan de retour en arrière.
- Utiliser `--confirm` uniquement dans des scripts automatisés.
- Vérifier l'état de la base après une réinitialisation pour confirmer que le résultat est celui attendu.

---

## Commandes connexes

- `python manage.py charger_communes_france`: Charge les ~35 000 communes françaises.
- `python manage.py charger_lof`: Charge la taxonomie des espèces d'oiseaux (recommandé).
- `python manage.py createsuperuser`: Crée un compte administrateur.