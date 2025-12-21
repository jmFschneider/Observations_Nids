# Renommage de Modèles Django - Guide de Décision Technique

> **Document de référence** pour évaluer la faisabilité et les risques du renommage de modèles Django dans le projet Observations Nids.
>
> **Dernière mise à jour** : 1er novembre 2025

---

## Table des matières

[TOC]

---

## Contexte

Cette documentation évalue la faisabilité technique du renommage du modèle `Observation` (ou tout autre modèle central) dans le projet Observations Nids.

### Cas d'usage typique

**Demande** : "Pourrait-on renommer le modèle `Observation` en `SuiviTerrain` ?"

**Motivation potentielle** :
- Clarifier la terminologie métier
- Éviter les confusions sémantiques
- Harmoniser le vocabulaire avec les utilisateurs

### Pourquoi ce document ?

Un renommage de modèle Django en production est une opération **à haut risque** qui nécessite :
- Une analyse d'impact complète
- Une évaluation du rapport coût/bénéfice
- Un plan de migration détaillé si validation

---

## Analyse d'impact

### Portée du changement (modèle `Observation`)

**Analyse effectuée le 1er novembre 2025** :

| Catégorie | Fichiers impactés | Occurrences |
|-----------|-------------------|-------------|
| **Code Python** | 36 fichiers | 168 occurrences |
| **Templates HTML** | 27 fichiers | 202 occurrences |
| **Documentation** | 9 fichiers Markdown | 42+ occurrences |
| **Références directes** | Tous types | 140 imports/usages |
| **Migrations existantes** | 5 migrations | Dépendances critiques |

### Fichiers critiques à modifier

#### 1. Modèles et logique métier

| Fichier | Occurrences | Criticité |
|---------|-------------|-----------|
| `observations/models.py` | 12 | 🔴 Critique |
| `observations/admin.py` | 6 | 🟡 Haute |
| `observations/forms.py` | 11 | 🟡 Haute |
| `ingest/importation_service.py` | 9 | 🔴 Critique |
| `audit/models.py` | 1 (relation) | 🟡 Haute |
| `geo/models.py` | 1 (relation) | 🟡 Haute |

#### 2. Vues et contrôleurs

| Fichier | Occurrences | Criticité |
|---------|-------------|-----------|
| `observations/views/saisie_observation_view.py` | 28 | 🔴 Critique |
| `observations/views/views_observation.py` | 3 | 🟡 Haute |
| `observations/views/views_home.py` | 3 | 🟡 Haute |
| `geo/views.py` | 3 | 🟡 Haute |
| `ingest/views/home.py` | 2 | 🟢 Moyenne |

#### 3. Tests

| Fichier | Occurrences | Criticité |
|---------|-------------|-----------|
| `observations/tests/test_models.py` | 11 | 🟡 Haute |
| `observations/tests/test_views.py` | 8 | 🟡 Haute |
| `observations/tests/test_views_observation.py` | 7 | 🟡 Haute |
| `audit/tests/test_historique.py` | 3 | 🟢 Moyenne |
| `geo/tests/test_api_communes.py` | 2 | 🟢 Moyenne |

#### 4. Templates Django

**27 fichiers HTML** contenant "observation" dans :
- Formulaires de saisie
- Listes d'observations
- Détails de fiches
- Emails automatiques
- Composants réutilisables

#### 5. Scripts et utilitaires

- `scripts/reset_et_jeu_test.py` (8 occurrences)
- `scripts/efface_bdd_test.py` (6 occurrences)
- `geo/management/commands/reset_*` (13 occurrences)

---

## Risques identifiés

### 🔴 Risques critiques

#### 1. Modification de la base de données en production

```python
# Django génère automatiquement cette migration :
class Migration(migrations.Migration):
    operations = [
        migrations.RenameModel(
            old_name='Observation',
            new_name='NouveauNom',
        ),
    ]
```

**Conséquences** :
- ⚠️ Renommage de la table `observations_observation` → `observations_nouveaunom`
- ⚠️ Exécution SQL `ALTER TABLE RENAME` sur la production
- ⚠️ Si échec : risque de corruption de données ou d'incohérence
- ⚠️ **Downtime potentiel** pendant l'exécution de la migration
- ⚠️ Impossible de rollback facilement si données modifiées entre-temps

**Impact sur les données existantes** :
- Table contenant potentiellement des milliers d'observations
- Opération atomique mais risquée
- Backup obligatoire avant migration

#### 2. Relations avec d'autres modèles

```python
# FicheObservation a une ForeignKey vers Observation
fiche.observations.all()  # ← related_name pourrait casser

# HistoriqueModification référence indirectement
# ImportationEnCours utilise Observation dans le service
```

**Risque** : Casser des relations existantes si mal géré

#### 3. Conflits de migrations

- 5 migrations existantes font référence à `Observation`
- Si quelqu'un a des migrations non appliquées : conflits garantis
- Ordre d'application critique

### 🟡 Risques élevés

#### 4. Oublis dans le code

Avec **168 occurrences** à modifier manuellement :
- Risque élevé d'oubli dans un fichier
- Erreurs silencieuses potentielles (imports non utilisés)
- Tests qui passent mais code mort

#### 5. Tests incomplets

- 78 tests existants à vérifier
- Risque de tests qui passent en local mais échouent en prod
- Cas d'usage oubliés

### 🟢 Risques moyens

#### 6. Documentation obsolète

- 9 fichiers Markdown à mettre à jour
- Risque de documentation incohérente
- Confusion pour les futurs développeurs

---

## Estimation de l'effort

### Temps de développement

| Tâche | Temps estimé | Niveau de difficulté |
|-------|--------------|----------------------|
| Analyse et planification | 1-2 h | 🟢 Facile |
| Backup et préparation environnement | 0.5 h | 🟢 Facile |
| Renommer la classe + générer migration | 0.5 h | 🟡 Moyen |
| Mettre à jour imports Python (36 fichiers) | 2-3 h | 🟡 Moyen |
| Mettre à jour templates HTML (27 fichiers) | 1-2 h | 🟢 Facile |
| Mettre à jour tous les tests | 2-3 h | 🟡 Moyen |
| Mettre à jour documentation (9 fichiers) | 1 h | 🟢 Facile |
| Créer et tester migration sur copie prod | 1-2 h | 🔴 Difficile |
| Tests manuels exhaustifs | 2-3 h | 🟡 Moyen |
| Déploiement et monitoring | 1 h | 🔴 Difficile |

**Total estimé** : **11-17 heures de travail**

### Coût en termes de risque

- **Probabilité d'erreur** : Élevée (nombreux fichiers à modifier)
- **Impact d'une erreur** : Critique (base de données en production)
- **Réversibilité** : Difficile (migration de schéma)
- **Période de stabilisation** : 1-2 semaines (monitoring post-déploiement)

---

## Alternative sans risque

### Solution recommandée : `verbose_name`

Au lieu de renommer le modèle, **modifier uniquement la terminologie affichée** :

```python
class Observation(models.Model):
    fiche = models.ForeignKey(
        'FicheObservation', on_delete=models.CASCADE, related_name="observations"
    )
    date_observation = models.DateTimeField(blank=False, null=False, db_index=True)
    # ... autres champs ...

    class Meta:
        ordering = ['date_observation']
        verbose_name = "Suivi terrain"              # ← Nouveau nom affiché
        verbose_name_plural = "Suivis terrain"      # ← Pluriel
```

### Avantages de cette approche

| Critère | Renommage complet | verbose_name |
|---------|-------------------|--------------|
| **Temps de développement** | 11-17 h | **5 min** ⚡ |
| **Risque technique** | 🔴 Élevé | 🟢 Aucun |
| **Impact base de données** | Oui (ALTER TABLE) | **Non** ✅ |
| **Fichiers à modifier** | 62+ fichiers | **1 fichier** ✅ |
| **Tests à mettre à jour** | Tous | **Aucun** ✅ |
| **Réversibilité** | Difficile | **Immédiate** ✅ |
| **Impact utilisateurs** | Identique | Identique |

### Où le nouveau nom apparaît

Avec `verbose_name`, le nouveau nom est visible dans :
- ✅ Interface admin Django (`/admin/observations/observation/`)
- ✅ Formulaires générés automatiquement
- ✅ Messages d'erreur (`"Ce suivi terrain est invalide"`)
- ✅ Documentation auto-générée

**Le code reste inchangé** :
```python
from observations.models import Observation  # ← Toujours "Observation" dans le code
```

---

## Checklist complète (si renommage nécessaire)

Si, malgré les risques, le renommage est validé, suivre **impérativement** cette checklist :

### Phase 1 : Préparation (OBLIGATOIRE)

- [ ] **Backup complet** de la base de données de production
- [ ] **Tester la restauration** du backup (ne pas faire confiance à un backup non testé)
- [ ] Créer un **environnement de test** identique à la production
- [ ] Copier les données de production vers l'environnement de test
- [ ] Documenter le plan de rollback
- [ ] Informer tous les utilisateurs du downtime prévu

### Phase 2 : Développement

- [ ] Créer une branche dédiée : `refactor/rename-observation-to-nouveaunom`
- [ ] Renommer la classe dans `observations/models.py`
- [ ] Générer la migration : `python manage.py makemigrations`
- [ ] **Inspecter la migration générée** ligne par ligne
- [ ] Mettre à jour tous les imports Python (36 fichiers minimum)
  - [ ] `observations/admin.py`
  - [ ] `observations/forms.py`
  - [ ] `observations/views/*.py`
  - [ ] `observations/tests/*.py`
  - [ ] `ingest/importation_service.py`
  - [ ] `geo/views.py`
  - [ ] `audit/models.py`
  - [ ] Scripts dans `scripts/`
  - [ ] Commands Django dans `*/management/commands/`
- [ ] Mettre à jour tous les templates HTML (27 fichiers minimum)
- [ ] Mettre à jour la documentation (9 fichiers Markdown minimum)
- [ ] Rechercher tous les `related_name` affectés

### Phase 3 : Tests

- [ ] Lancer la suite de tests complète : `pytest`
- [ ] Vérifier que **100% des tests passent**
- [ ] Tester la migration sur l'environnement de test :
  - [ ] `python manage.py migrate`
  - [ ] Vérifier l'intégrité des données
  - [ ] Vérifier les relations entre modèles
- [ ] Tests manuels exhaustifs :
  - [ ] Créer une observation
  - [ ] Modifier une observation
  - [ ] Supprimer une observation
  - [ ] Lister les observations
  - [ ] Importer des observations (transcription)
  - [ ] Consulter l'historique
  - [ ] Géolocalisation
  - [ ] Toutes les vues liées
- [ ] Tester le rollback de la migration

### Phase 4 : Code Review

- [ ] Revue de code complète par un autre développeur
- [ ] Vérifier qu'aucun fichier n'a été oublié : `git grep -i "Observation"`
- [ ] Vérifier la migration générée
- [ ] Valider le plan de déploiement

### Phase 5 : Déploiement (Production)

- [ ] **Backup final** de la production avant déploiement
- [ ] Activer le mode maintenance
- [ ] Déployer le code sur le serveur
- [ ] Exécuter la migration : `python manage.py migrate`
- [ ] Vérifier les logs pour toute erreur
- [ ] Tests de fumée (smoke tests) en production :
  - [ ] Afficher une fiche
  - [ ] Créer une observation test
  - [ ] Supprimer l'observation test
- [ ] Désactiver le mode maintenance
- [ ] **Monitoring intensif** pendant 24-48h

### Phase 6 : Validation post-déploiement

- [ ] Vérifier les logs d'erreur pendant 1 semaine
- [ ] Recueillir les retours utilisateurs
- [ ] Documenter les incidents éventuels
- [ ] Mettre à jour le CHANGELOG

---

## Recommandation

### 🚫 Ne PAS renommer si :

- ✅ Le nom actuel fonctionne (pas de confusion majeure)
- ✅ C'est uniquement esthétique ou préférence personnelle
- ✅ Le projet est en production avec des utilisateurs actifs
- ✅ Les bénéfices sont faibles par rapport aux risques
- ✅ **Alternative `verbose_name` résout le problème**

### ✅ Envisager le renommage UNIQUEMENT si :

- ✅ Confusion sémantique **critique** impactant le développement
- ✅ Nom actuel est **objectivement trompeur** (ex: classe `User` qui gère des produits)
- ✅ Vous avez **8-17h disponibles** pour le faire correctement
- ✅ Vous avez un **backup testé** et un plan de rollback
- ✅ Vous pouvez tester sur une **copie exacte** de la production
- ✅ Alternative `verbose_name` ne suffit **absolument pas**

### Décision recommandée par défaut

**🎯 Utiliser `verbose_name` + `verbose_name_plural` dans `Meta`**

- Temps : 5 minutes
- Risque : Aucun
- Bénéfice : Identique à un renommage complet pour les utilisateurs
- Maintenance : Aucune

---

## Message type pour refuser la demande

Voici un message professionnel pour décliner une demande de renommage :

```
Bonjour,

J'ai analysé la demande de renommer le modèle `Observation` en `[NouveauNom]`.

Après analyse technique, cette opération nécessiterait :
- 11-17 heures de développement
- Modification de 168 occurrences dans 36 fichiers Python
- Modification de 202 occurrences dans 27 templates HTML
- Migration de la base de données en production (risque élevé)
- Tests exhaustifs et période de stabilisation de 1-2 semaines

**Alternative proposée** : Utiliser `verbose_name` dans le modèle pour changer
uniquement la terminologie affichée, sans toucher au code ni à la base de données.
Temps : 5 minutes, risque : aucun, résultat identique pour les utilisateurs.

Exemple :
class Observation(models.Model):
    class Meta:
        verbose_name = "Suivi terrain"
        verbose_name_plural = "Suivis terrain"

Cette solution change l'affichage dans l'interface admin, les formulaires et
les messages, sans aucun risque technique.

Quel nom souhaitez-vous afficher ? Je peux implémenter cette solution rapidement.

Cordialement,
```

---

## Références

- [Django Migrations Documentation](https://docs.djangoproject.com/en/5.1/topics/migrations/)
- [RenameModel Operation](https://docs.djangoproject.com/en/5.1/ref/migration-operations/#renamemodel)
- [Model Meta Options](https://docs.djangoproject.com/en/5.1/ref/models/options/)

---

**Document maintenu par** : Équipe développement Observations Nids
**Dernière révision** : 1er novembre 2025
**Version** : 1.0
