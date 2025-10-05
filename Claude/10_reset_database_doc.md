# Guide de Réinitialisation de la Base de Données

Ce document explique comment utiliser les commandes de réinitialisation de la base de données pour gérer les cycles de développement et de test du projet Observations Nids.

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Commande `reset_importations`](#commande-reset_importations)
3. [Commande `reset_transcriptions`](#commande-reset_transcriptions)
4. [Scénarios d'utilisation](#scénarios-dutilisation)
5. [Précautions et bonnes pratiques](#précautions-et-bonnes-pratiques)

---

## Vue d'ensemble

Le projet dispose de **deux commandes Django** pour gérer la réinitialisation des données :

| Commande | Usage | Données préservées |
|----------|-------|-------------------|
| `reset_importations` | Réinitialisation complète | `geo_commune_france`, `taxonomy_espece` |
| `reset_transcriptions` | Réinitialisation partielle | Idem + fiches créées (optionnel) |

### Pourquoi ces commandes ?

- **Tests d'importation** : Relancer le processus OCR et d'importation sans recréer les communes
- **Développement** : Nettoyer la base sans perdre les données de référence
- **Débogage** : Repartir d'un état propre tout en gardant les communes françaises chargées

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
|--------|-------------|
| `--confirm` | Confirmer la réinitialisation sans demander (pour scripts automatisés) |
| `--keep-users` | Conserver tous les utilisateurs (pas seulement ceux de transcription) |
| `-h, --help` | Afficher l'aide |

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
- Utilisateurs créés manuellement (si `--keep-users`)

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
  • 150 fiches d'observation
  • 450 observations
  • 75 remarques
  • 1250 entrées d'historique
  • 150 importations en cours
  • 150 transcriptions brutes
  • 45 espèces candidates
  • 12 utilisateurs de transcription

🗑️  Suppression en cours...
  ✓ Validations et historique supprimés
  ✓ Remarques supprimées
  ✓ Observations supprimées
  ✓ Historique des modifications supprimé
  ✓ Objets liés aux fiches supprimés
  ✓ Fiches d'observation supprimées
  ✓ Importations en cours supprimées
  ✓ Transcriptions brutes supprimées
  ✓ Espèces candidates supprimées
  ✓ Utilisateurs de transcription supprimés
  ✓ Séquences SQLite réinitialisées

✅ Réinitialisation terminée avec succès !

📊 Résumé :
  • 150 fiches supprimées
  • 450 observations supprimées
  • 75 remarques supprimées
  • 1250 entrées d'historique supprimées
  • 150 importations supprimées
  • 150 transcriptions supprimées
  • 45 espèces candidates supprimées
  • 12 utilisateurs supprimés

✅ geo_commune_france intact : 34970 communes préservées
```

#### Utilisation automatique (sans confirmation)

```bash
python manage.py reset_importations --confirm
```

Idéal pour les **scripts de déploiement** ou les **tests automatisés**.

#### Conserver les utilisateurs

```bash
python manage.py reset_importations --keep-users
```

Utile pour **conserver les comptes administrateurs** créés manuellement.

#### Combinaison des options

```bash
python manage.py reset_importations --confirm --keep-users
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
|--------|-------------|
| `--confirm` | Confirmer la réinitialisation sans demander |
| `--delete-fiches` | Supprimer également les fiches créées par transcription |
| `-h, --help` | Afficher l'aide |

### Données concernées

✅ **Toujours supprimées :**
- Importations en cours
- Espèces candidates

🔄 **Réinitialisées (pas supprimées) :**
- Transcriptions brutes (marquées comme `traite=False`)

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
⚠️  Cette opération va supprimer :

  • Importations en cours
  • Transcriptions brutes
  • Espèces candidates
  ✅ Les fiches créées par transcription seront PRÉSERVÉES

Êtes-vous sûr de vouloir continuer ? (oui/non) : oui

📊 Décompte avant suppression :
  • 150 importations en cours
  • 150 transcriptions brutes
  • 45 espèces candidates

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

#### Réinitialisation complète (supprime aussi les fiches)

```bash
python manage.py reset_transcriptions --delete-fiches
```

Supprime également les fiches créées par le processus OCR.

#### Utilisation automatique

```bash
python manage.py reset_transcriptions --confirm --delete-fiches
```

---

## Scénarios d'utilisation

### 🔄 Scénario 1 : Relancer l'importation OCR

**Problème :** Vous avez corrigé un bug dans le processus OCR et voulez réimporter les fiches.

**Solution :**
```bash
# Supprimer les fiches transcrites et réinitialiser
python manage.py reset_transcriptions --delete-fiches

# Relancer l'importation
# 1. Importer les JSON
# 2. Extraire les candidats
# 3. Valider les espèces
# 4. Finaliser l'importation
```

### 🧪 Scénario 2 : Tests de développement

**Problème :** Vous développez une nouvelle fonctionnalité et voulez tester sur une base propre.

**Solution :**
```bash
# Tout effacer sauf les communes
python manage.py reset_importations --confirm

# Les communes sont toujours là, pas besoin de les recharger
# Vous pouvez maintenant tester votre nouvelle fonctionnalité
```

### 🔍 Scénario 3 : Débogage du géocodage

**Problème :** Vous avez amélioré le géocodeur et voulez retester toutes les importations.

**Solution :**
```bash
# Garder les fiches mais réinitialiser le processus
python manage.py reset_transcriptions

# Les transcriptions sont marquées comme non traitées
# Relancer l'extraction et l'importation
```

### 📊 Scénario 4 : Préparation démo/production

**Problème :** Vous voulez partir d'une base propre pour une démo ou la mise en production.

**Solution :**
```bash
# Tout nettoyer en gardant les utilisateurs admins
python manage.py reset_importations --keep-users

# La base est propre, les communes et espèces sont là
# Les comptes admins sont préservés
```

### 🚀 Scénario 5 : Script de déploiement automatisé

**Problème :** Vous voulez automatiser la réinitialisation dans un script CI/CD.

**Solution :**
```bash
#!/bin/bash
# Script de reset automatique

# Réinitialisation complète sans confirmation
python manage.py reset_importations --confirm --keep-users

# Vérifier que les communes sont présentes
python manage.py shell -c "from geo.models import CommuneFrance; print(f'Communes: {CommuneFrance.objects.count()}')"

# Charger les données de test
python manage.py loaddata initial_data.json
```

---

## Précautions et bonnes pratiques

### ⚠️ Avant d'exécuter une réinitialisation

1. **Sauvegarde de sécurité**
   ```bash
   # Créer une sauvegarde SQLite
   cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

   # Ou pour PostgreSQL
   pg_dump observations_nids > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Vérifier l'environnement**
   ```bash
   # S'assurer qu'on est en développement
   python manage.py shell -c "from django.conf import settings; print(f'DEBUG={settings.DEBUG}')"
   ```

3. **Compter les données**
   ```bash
   # Vérifier ce qui va être supprimé
   python manage.py shell -c "
   from observations.models import FicheObservation
   from geo.models import CommuneFrance
   print(f'Fiches: {FicheObservation.objects.count()}')
   print(f'Communes: {CommuneFrance.objects.count()}')
   "
   ```

### ✅ Bonnes pratiques

#### 1. **Ne jamais exécuter en production sans sauvegarde**
```bash
# ❌ DANGER - Ne pas faire en prod sans backup
python manage.py reset_importations --confirm

# ✅ CORRECT - Toujours sauvegarder d'abord
pg_dump observations_nids > backup_avant_reset.sql
python manage.py reset_importations --confirm
```

#### 2. **Utiliser `--confirm` uniquement dans des scripts**
```bash
# ❌ Mauvaise pratique - Pas de confirmation interactive
python manage.py reset_importations --confirm  # Tapé à la main

# ✅ Bonne pratique - Confirmation manuelle
python manage.py reset_importations  # Demande confirmation
```

#### 3. **Vérifier après réinitialisation**
```bash
# Après reset, vérifier que les communes sont toujours là
python manage.py shell -c "
from geo.models import CommuneFrance
from observations.models import FicheObservation
assert CommuneFrance.objects.count() > 30000, 'Communes manquantes!'
assert FicheObservation.objects.count() == 0, 'Fiches non supprimées!'
print('✅ Réinitialisation OK')
"
```

#### 4. **Documenter les réinitialisations**
```bash
# Créer un fichier de log
echo "$(date): Reset importations - $(whoami)" >> reset_history.log
python manage.py reset_importations --confirm
```

### 🔒 Sécurité

#### Variables d'environnement
```bash
# Protéger la production avec une variable
if [ "$ENVIRONMENT" = "production" ]; then
    echo "❌ Reset interdit en production!"
    exit 1
fi

python manage.py reset_importations --confirm
```

#### Permissions
```bash
# Restreindre l'accès aux admins seulement
# Ajouter dans settings.py
RESET_ALLOWED_USERS = ['admin', 'dev_team']
```

### 📝 Checklist de réinitialisation

Avant d'exécuter `reset_importations` :

- [ ] Sauvegarde de la base de données créée
- [ ] Environnement de développement confirmé (DEBUG=True)
- [ ] Données importantes exportées si nécessaire
- [ ] Équipe prévenue (si environnement partagé)
- [ ] Documentation à jour

Après l'exécution :

- [ ] Vérifier que `geo_commune_france` contient ~35 000 communes
- [ ] Vérifier que `taxonomy_espece` contient les espèces
- [ ] Vérifier que les fiches sont bien à 0
- [ ] Tester une importation pour valider

---

## Workflow complet d'importation

Voici le cycle complet pour réimporter des données après réinitialisation :

```bash
# 1. Réinitialiser la base
python manage.py reset_importations --confirm

# 2. Vérifier les communes (doivent être présentes)
python manage.py shell -c "from geo.models import CommuneFrance; print(f'Communes: {CommuneFrance.objects.count()}')"

# 3. Importer les fichiers JSON de transcription
# Via l'interface web : /importation/importer-json/

# 4. Extraire les espèces et observateurs candidats
# Via l'interface web : /importation/extraire-candidats/

# 5. Valider les correspondances d'espèces
# Via l'interface web : /importation/valider-especes/

# 6. Préparer les importations
# Via l'interface web : /importation/preparer-importations/

# 7. Finaliser l'importation
# Via l'interface web : /importation/finaliser/

# 8. Vérifier les résultats
python manage.py shell -c "
from observations.models import FicheObservation
from geo.models import Localisation
fiches = FicheObservation.objects.count()
localisations_geocodees = Localisation.objects.exclude(source_coordonnees='geocodage_auto').count()
print(f'✅ {fiches} fiches importées')
print(f'✅ {localisations_geocodees} localisations géocodées')
"
```

---

## Résolution de problèmes

### Problème : "Communes manquantes après reset"

**Diagnostic :**
```bash
python manage.py shell -c "from geo.models import CommuneFrance; print(CommuneFrance.objects.count())"
```

**Solution :**
```bash
# Recharger les communes
python manage.py charger_communes_france
```

### Problème : "Erreur de séquence d'auto-incrémentation"

**Symptôme :** Les nouvelles fiches ont des ID qui entrent en conflit.

**Solution :**
```bash
# Réinitialiser manuellement les séquences (SQLite)
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("DELETE FROM sqlite_sequence WHERE name='observations_ficheobservation'")
>>> cursor.execute("DELETE FROM sqlite_sequence WHERE name='observations_observation'")
```

### Problème : "Permission denied"

**Cause :** Fichiers de base de données verrouillés.

**Solution :**
```bash
# Arrêter tous les processus Django
pkill -f "manage.py runserver"

# Réessayer
python manage.py reset_importations
```

---

## Fichiers créés

Les commandes de réinitialisation sont définies dans :

- `geo/management/commands/reset_importations.py` - Réinitialisation complète
- `geo/management/commands/reset_transcriptions.py` - Réinitialisation partielle

### Modification des commandes

Pour personnaliser le comportement :

```python
# geo/management/commands/reset_importations.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Ajouter une vérification custom
        if not options.get('i_am_sure'):
            self.stdout.write('Ajoutez --i-am-sure pour confirmer')
            return

        # Votre logique de réinitialisation
        ...
```

---

## Commandes connexes

### Charger les communes françaises

```bash
python manage.py charger_communes_france
```

Charge les ~35 000 communes françaises depuis l'API Géoplateforme.

### Charger les altitudes

```bash
python manage.py charger_altitudes
```

Complète les données d'altitude des communes.

### Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Créer un compte admin après réinitialisation.

---

## Conclusion

Les commandes `reset_importations` et `reset_transcriptions` sont des outils puissants pour gérer le cycle de développement du projet. Utilisez-les avec précaution et suivez toujours les bonnes pratiques décrites dans ce document.

**Règle d'or :** Toujours faire une sauvegarde avant une réinitialisation en production ou pré-production !

---

<!-- SOMMAIRE FLOTTANT (Typora) -->
<div style="position:fixed; top:80px; right:16px; width:280px; max-height:70vh; 
            overflow:auto; padding:10px 12px; border-radius:10px;
            background:rgba(245,245,245,.95); box-shadow:0 4px 12px rgba(0,0,0,.15);
            font-size:0.9rem; z-index:9998;">
[TOC]
</div>


*Documentation mise à jour : 2025-01-04*
*Version : 1.0*
*Auteur : Claude Code - Généré avec l'assistance de Claude*
