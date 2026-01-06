# Intégration des codes GONM dans la base de données

**Date**: 27 décembre 2024
**Statut**: Analyse terminée - En attente de validation pour importation
**Fichier d'analyse**: `C:\Projets\GONM\analyse-correspondances-gonm.csv`

---

## 📋 Contexte

Le Groupe Ornithologique Normand (GONM) utilise un système de codes pour identifier les espèces d'oiseaux (ex: A01, B02, C13, etc.). Nous souhaitons intégrer ces codes dans notre base de données pour faciliter les échanges et la compatibilité avec les données du GONM.

**Fichier source**: `C:\Projets\GONM\codes-especes-normandie.csv`
- Format: CSV délimité par `;`, encodage UTF-8
- Colonnes: Code, Nom scientifique, Nom français vernaculaire, Nom anglais
- Contenu: 484 espèces répertoriées

---

## ✅ Travaux réalisés

### 1. Modification du modèle de données

**Fichier**: `taxonomy/models.py`

Ajout d'un nouveau champ au modèle `Espece` :
```python
code_GONM = models.CharField(max_length=10, blank=True, help_text="Code GONM de l'espèce")
```

**Migration créée**: `taxonomy/migrations/0002_espece_code_gonm.py`
**Migration appliquée**: ✅ Oui

### 2. Système de correspondance automatique avec scoring

**Problématique identifiée** :
- Les noms scientifiques en base contiennent parfois l'auteur et la date (ex: `"Anas platyrhynchos Linnaeus, 1758"`)
- Le CSV GONM contient uniquement le nom binomial (ex: `"Anas platyrhynchos"`)
- Une correspondance simple par nom exact ne fonctionne que pour 274 espèces sur 484

**Solution développée** : Système de scoring multi-critères

### 3. Commande d'analyse créée

**Fichier**: `taxonomy/management/commands/analyser_correspondances_gonm.py`

**Fonctionnalités** :
1. **Comparaison multi-critères** pour chaque espèce du CSV :
   - Nom scientifique (nettoyé des auteurs/dates)
   - Nom français
   - Nom anglais

2. **Calcul de similarité** (0-100%) pour chaque critère avec la bibliothèque `difflib`

3. **Score global** = moyenne des scores des champs disponibles

4. **Système de bonus** pour garantir la qualité :
   - Si nom scientifique = 100% → score minimum garanti à 95%
   - Si nom français OU anglais = 100% → score minimum garanti à 85%

5. **Export CSV** avec :
   - Toutes les informations du CSV source
   - Meilleure correspondance trouvée en base
   - Scores détaillés (scientifique, français, anglais)
   - Score global de confiance
   - **Tri par score décroissant** (meilleurs scores en premier)

**Usage** :
```bash
python manage.py analyser_correspondances_gonm
```

**Sortie** : `C:\Projets\GONM\analyse-correspondances-gonm.csv`

---

## 📊 Résultats de l'analyse

### Distribution des scores (sur 484 espèces analysées)

| Tranche de score | Nombre | Pourcentage | Qualité |
|-----------------|--------|-------------|---------|
| **100%** | 347 | 71.7% | ✅ Correspondances parfaites |
| **90-99%** | 50 | 10.3% | ✅ Excellentes (bonus appliqué) |
| **80-89%** | 30 | 6.2% | ✅ Très bonnes |
| **70-79%** | 8 | 1.7% | ⚠️ Bonnes (à vérifier) |
| **60-69%** | 17 | 3.5% | ⚠️ Douteuses |
| **< 60%** | 32 | 6.6% | ❌ Fausses correspondances |

**Score moyen global** : 93.77%

### Recommandation de seuil

| Seuil | Espèces importées | Taux | Recommandation |
|-------|------------------|------|----------------|
| ≥ 100% | 347 | 71.7% | Trop restrictif |
| ≥ 90% | 397 | 82.0% | Bon compromis |
| **≥ 80%** | **427** | **88.2%** | **✅ RECOMMANDÉ** |
| ≥ 70% | 435 | 89.9% | Inclut des cas douteux |

**Seuil recommandé** : **80%** = 427 espèces avec haute confiance

### Exemples de correspondances parfaites (100%)
- A01: Gavia arctica → Plongeon arctique ✅
- A07: Podiceps nigricollis → Grèbe à cou noir ✅
- C08: Anas platyrhynchos → Canard colvert ✅

### Exemples de bonnes correspondances avec bonus (90-95%)
- A09: Hydrobates pelagicus (95%)
  - CSV: "Pétrel tempête"
  - Base: "Océanite tempête"
  - Bonus appliqué car nom scientifique = 100%

### Exemples de fausses correspondances (< 60%)
- A08a: Diomedea exulans "Albatros hurleur" → "Balbuzard pêcheur" (48.48%) ❌
- X04: Euodice malabarica "Capucin bec-de-plomb" → "Grive de Sibérie" (44.44%) ❌

Ces espèces sont probablement absentes de notre base de données.

---

## 📁 Fichier d'analyse produit

**Fichier** : `C:\Projets\GONM\analyse-correspondances-gonm.csv`

**Format** : CSV délimité par `;`, encodage UTF-8
**Tri** : Par score décroissant (meilleurs scores en premier)

**Colonnes** :
- `code_gonm` : Code GONM (A01, B02, etc.)
- `nom_scientifique_csv` : Nom scientifique dans le CSV source
- `nom_francais_csv` : Nom français dans le CSV source
- `nom_anglais_csv` : Nom anglais dans le CSV source
- `espece_trouvee_id` : ID de l'espèce trouvée en base
- `espece_trouvee_nom` : Nom français de l'espèce en base
- `espece_trouvee_nom_sci` : Nom scientifique de l'espèce en base
- `espece_trouvee_nom_en` : Nom anglais de l'espèce en base
- `score_nom_scientifique` : Score de similarité sur le nom scientifique (0.0-1.0)
- `score_nom_francais` : Score de similarité sur le nom français (0.0-1.0)
- `score_nom_anglais` : Score de similarité sur le nom anglais (0.0-1.0)
- `score_moyen` : Score global de confiance (0.0-1.0)
- `score_pourcent` : Score en pourcentage (0%-100%)

---

## 👥 Validation collaborative

### Objectif
Permettre à l'équipe de vérifier et corriger les correspondances avant l'importation définitive.

### Zones à vérifier en priorité

1. **Scores entre 70-89%** (38 espèces)
   - Vérifier que la correspondance proposée est correcte
   - Corriger si nécessaire

2. **Scores < 70%** (49 espèces)
   - Vérifier si l'espèce existe en base sous un autre nom
   - Noter si l'espèce est réellement absente de notre base

### Comment contribuer

1. **Ouvrir le fichier** `analyse-correspondances-gonm.csv` dans Excel/LibreOffice/Google Sheets

2. **Filtrer les scores** < 90% pour voir les cas à vérifier

3. **Pour chaque ligne douteuse** :
   - ✅ Si la correspondance est **correcte** : ne rien faire
   - ❌ Si la correspondance est **incorrecte** :
     - Chercher manuellement l'espèce en base
     - Noter le bon ID d'espèce dans une colonne de commentaires
   - ⚠️ Si l'espèce est **absente** de la base : le noter

4. **Partager vos remarques** via le fichier Google Drive ou un document de suivi

---

## 🚀 Prochaines étapes

### Étape 1 : Validation collaborative (EN COURS)
- [ ] Mettre le fichier CSV sur Google Drive
- [ ] Partager avec l'équipe pour validation
- [ ] Recueillir les corrections/remarques
- [ ] Deadline : **[À définir]**

### Étape 2 : Ajustement du seuil (si nécessaire)
- [ ] Analyser les retours de l'équipe
- [ ] Ajuster le seuil recommandé (80%) si nécessaire
- [ ] Décider du traitement des cas < 80%

### Étape 3 : Création de la commande d'importation
**À faire** : Créer `taxonomy/management/commands/importer_codes_gonm.py`

Cette commande devra :
- Lire le fichier d'analyse validé
- Importer uniquement les correspondances au-dessus du seuil choisi
- Mettre à jour le champ `code_GONM` des espèces concernées
- Générer un rapport d'importation

**Usage prévu** :
```bash
# Simulation (dry-run)
python manage.py importer_codes_gonm --seuil 80 --dry-run

# Importation réelle
python manage.py importer_codes_gonm --seuil 80
```

### Étape 4 : Importation finale
- [ ] Backup de la base de données
- [ ] Lancement de la commande d'importation
- [ ] Vérification des résultats
- [ ] Documentation des espèces importées

---

## 🔧 Comment reprendre le travail

### Si vous voulez refaire l'analyse

```bash
# Régénérer le fichier d'analyse
python manage.py analyser_correspondances_gonm

# Le fichier sera recréé à :
# C:\Projets\GONM\analyse-correspondances-gonm.csv
```

### Si vous voulez modifier le système de bonus

**Fichier** : `taxonomy/management/commands/analyser_correspondances_gonm.py`
**Lignes** : 129-135

```python
# Bonus : si au moins un champ matche parfaitement, augmenter le score minimal
if scores['nom_scientifique'] == 1.0:
    # Nom scientifique parfait = très forte indication
    score_moyen = max(score_moyen, 0.95)  # ← Modifier ici (0.95 = 95%)
elif scores['nom_francais'] == 1.0 or scores['nom_anglais'] == 1.0:
    # Nom français ou anglais parfait = forte indication
    score_moyen = max(score_moyen, 0.85)  # ← Modifier ici (0.85 = 85%)
```

### Si vous voulez créer la commande d'importation finale

1. Copier/adapter `analyser_correspondances_gonm.py`
2. Au lieu de générer un CSV, mettre à jour la base de données
3. Ajouter un paramètre `--seuil` pour choisir le seuil minimal
4. Ajouter un mode `--dry-run` pour tester sans modifier la base

---

## 📝 Notes techniques

### Fichiers modifiés
- `taxonomy/models.py` : Ajout du champ `code_GONM`
- `taxonomy/migrations/0002_espece_code_gonm.py` : Migration du nouveau champ

### Fichiers créés
- `taxonomy/management/commands/analyser_correspondances_gonm.py` : Commande d'analyse
- `C:\Projets\GONM\analyse-correspondances-gonm.csv` : Fichier de résultats

### Dépendances Python utilisées
- `difflib.SequenceMatcher` : Calcul de similarité entre chaînes (bibliothèque standard)
- `csv` : Lecture/écriture CSV (bibliothèque standard)
- `django.core.management.base.BaseCommand` : Framework de commandes Django

### Base de données actuelle
- **577 espèces** en base de données
- **5 espèces** sans nom scientifique (à corriger ?)
- **152 espèces** avec auteur/date dans le nom scientifique

---

## 💡 Améliorations futures possibles

1. **Interface web de validation**
   - Permettre la validation/correction directement dans l'application
   - Afficher les correspondances douteuses pour validation manuelle

2. **Détection des espèces manquantes**
   - Identifier les espèces du CSV absentes de la base
   - Proposer un import automatique depuis une source de référence (TaxRef, IOC, etc.)

3. **Historique des importations**
   - Logger chaque importation avec date, utilisateur, nombre d'espèces
   - Permettre un rollback en cas de problème

4. **Synchronisation bidirectionnelle**
   - Exporter notre base vers le format GONM
   - Détecter les divergences entre notre base et le référentiel GONM

---

## 📞 Contact / Questions

Pour toute question sur ce travail :
- Consulter ce document
- Vérifier les fichiers de commandes dans `taxonomy/management/commands/`
- Relancer l'analyse si nécessaire

**Bon courage pour la validation ! 🚀**
