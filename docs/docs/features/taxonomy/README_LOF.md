# Import LOF - Liste des Oiseaux de France



## Vue d'ensemble

Cette commande Django permet de charger automatiquement toutes les espèces d'oiseaux de France depuis la **Liste des Oiseaux de France (LOF)** publiée par la Commission de l'avifaune française (CAF) et disponible sur Faune-France.

### Qu'est-ce que la LOF ?

La **Liste des Oiseaux de France** est la liste officielle des espèces d'oiseaux observées en France (métropole et outre-mer), maintenue par la **Commission de l'avifaune française (CAF)**.

**Avantages :**
- Source officielle française (Commission de l'avifaune française)
- Classification taxonomique complète (Ordre → Famille → Espèce)
- Noms vernaculaires français ET noms scientifiques
- Catégories de statut (A, B, C, D, E)
- Fichier léger (64KB) et rapide à télécharger
- Mises à jour régulières (2-3 fois par an)
- **~577 espèces** spécifiques à la France

### Catégories LOF

- **A** : Espèce observée à l'état sauvage en France (566 espèces)
- **A\*** : Espèce naturalisée récemment (4 espèces)
- **AC** : Espèce présente en catégorie A + C (10 espèces)
- **B** : Espèce observée uniquement en captivité (11 espèces)
- **C** : Espèce introduite (11 espèces)
- **D** : Espèce présente avant 1800, aujourd'hui disparue
- **E** : Données douteuses

**Par défaut, la commande importe uniquement les catégories A et AC** (espèces sauvages).

## Installation et prérequis

### Dépendances Python

La commande nécessite les bibliothèques suivantes (déjà dans requirements.txt) :
```bash
requests   # Pour télécharger la LOF
openpyxl   # Pour lire les fichiers Excel
```

### Compatibilité

✅ Windows
✅ Linux (Ubuntu, Debian, etc.)
✅ **Raspberry Pi** (léger et rapide)
✅ macOS

## Utilisation

### 1. Import automatique (RECOMMANDÉ)

La méthode la plus simple - téléchargement et import automatiques :

```bash
python manage.py charger_lof
```

Cette commande va :
1. Télécharger automatiquement la LOF depuis Faune-France
2. Décompresser le fichier
3. Importer les espèces de catégories A et AC
4. Créer les ordres, familles et espèces en base de données

**Durée estimée :** 10-30 secondes

### 2. Import depuis fichier local

Si vous avez déjà téléchargé le fichier LOF :

```bash
python manage.py charger_lof --file /chemin/vers/LOF2024_decompressed.xlsx
```

### 3. Choisir les catégories à importer

Par défaut, seules les espèces sauvages (A et AC) sont importées. Pour changer :

```bash
# Importer toutes les catégories
python manage.py charger_lof --categories A,AC,B,C

# Importer uniquement catégorie A
python manage.py charger_lof --categories A

# Importer A + espèces introduites (C)
python manage.py charger_lof --categories A,C
```

### 4. Mode test (limite le nombre d'espèces)

Pour tester rapidement sans tout importer :

```bash
python manage.py charger_lof --limit 50
```

Utile pour :
- Tests de développement
- Validation rapide
- Environnements de staging

### 5. Forcer la mise à jour

⚠️ **ATTENTION** : Cette option supprime toutes les données taxonomiques existantes. Elle ne fonctionnera que si aucune fiche d'observation n'utilise ces espèces.

```bash
python manage.py charger_lof --force
```

## Exemples d'utilisation

### Sur serveur Raspberry Pi

```bash
# Se connecter au Raspberry Pi
ssh pi@raspberrypi.local

# Activer l'environnement virtuel
cd /var/www/html/Observations_Nids
source .venv/bin/activate

# Importer la LOF (première fois)
python manage.py charger_lof

# Mise à jour ultérieure
python manage.py charger_lof  # Ajoute les nouvelles espèces
```

### Sur poste de développement Windows

```powershell
# Dans le répertoire du projet
cd C:\Projets\observations_nids

# Activer l'environnement virtuel
.venv\Scripts\activate

# Import avec test limité
python manage.py charger_lof --limit 100

# Import complet quand tout fonctionne
python manage.py charger_lof
```

### Sur poste Linux/macOS

```bash
# Dans le répertoire du projet
cd /home/user/observations_nids

# Activer l'environnement virtuel
source .venv/bin/activate

# Import complet
python manage.py charger_lof
```

## Données importées

### Structure des données

La commande crée et peuple 3 tables :

#### 1. **Ordre** (taxonomy_ordre)
- Niveau taxonomique supérieur (ex: Passeriformes, Accipitriformes)
- **25 ordres** d'oiseaux

#### 2. **Famille** (taxonomy_famille)
- Niveau intermédiaire (ex: Turdidae, Accipitridae)
- **83 familles**
- Liée à un Ordre

#### 3. **Espèce** (taxonomy_espece)
- Espèce complète avec noms français et scientifique
- **~577 espèces** d'oiseaux de France
- Liée à une Famille
- Champs peuplés :
  - `nom` : Nom vernaculaire français (ex: "Merle noir")
  - `nom_scientifique` : Nom latin (ex: "Turdus merula")
  - `nom_anglais` : Vide (la LOF ne contient pas les noms anglais)
  - `famille` : Lien vers la famille
  - `statut` : Catégorie LOF (A, AC, B, C, etc.)
  - `valide_par_admin` : `True` (source officielle)
  - `commentaire` : "Import LOF 2024 - Catégorie X"

### Filtrage appliqué

Par défaut, la commande importe UNIQUEMENT :
- ✅ **Catégories A et AC** (espèces sauvages)
- ✅ **Nom français** : doit exister
- ❌ **Sous-espèces** : ignorées (seules les espèces sont importées)

Les autres catégories (B, C, D, E) peuvent être ajoutées avec `--categories`.

## Exemple de sortie

```
=== Chargement LOF - Oiseaux de France ===

Téléchargement de la Liste des Oiseaux de France...
URL: https://cdnfiles1.biolovision.net/www.faune-france.org/userfiles/FauneFrance/FFEnSavoirPlus/LOF2024IOC15.1032025.xlsx
[OK] Téléchargement terminé
Décompression du fichier...
[OK] Décompression terminée

Import des données depuis: tmp/lof/LOF2024_decompressed.xlsx
Catégories filtrées: A, AC

Fichier ouvert: 1242 lignes à traiter
  Ordre créé: ANSERIFORMES
    Famille créée: Anatidae
  Ordre créé: GALLIFORMES
    Famille créée: Phasianidae
...
Espèces importées: 50
Espèces importées: 100
...
Espèces importées: 552

=== Rapport d'import ===

Lignes traitées: 1,241

Créations:
   - Ordres: 24
   - Familles: 82
   - Espèces: 552
   - Espèces ignorées (autres catégories): 29

=== Base de données ===

Ordres: 25
Familles: 83
Espèces: 577

Exemples d'espèces importées:
  - Bernache cravant (Anatidae) - ANSERIFORMES
    Branta bernicla
  - Bernache à cou roux (Anatidae) - ANSERIFORMES
    Branta ruficollis
  - Oie cendrée (Anatidae) - ANSERIFORMES
    Anser anser
  - Canard colvert (Anatidae) - ANSERIFORMES
    Anas platyrhynchos
  - Sarcelle d'hiver (Anatidae) - ANSERIFORMES
    Anas crecca

[OK] Import terminé avec succès!
```

## Optimisations

### Performance

- Sur **Raspberry Pi 4** (4GB RAM) : **~15-20 secondes**
- Sur **Raspberry Pi 3B+** : **~30-40 secondes**
- Sur **PC standard** : **~5-10 secondes**

### Espace disque requis

- Fichier LOF téléchargé (gzippé) : **64 KB**
- Après décompression : **~120 KB**
- En base de données (SQLite) : **~500 KB**
- En base de données (PostgreSQL/MariaDB) : **~700 KB**

Le fichier gzippé est automatiquement supprimé après décompression.

### Gestion de la mémoire

- **Lecture directe du fichier Excel** (pas de chargement en mémoire)
- **Cache des ordres et familles** pour éviter les requêtes répétées
- **Gestion des doublons** avec `get_or_create()`
- Optimisé pour environnements à faible mémoire (Raspberry Pi)

## Maintenance et mises à jour

### Mettre à jour la LOF

La LOF est mise à jour 2-3 fois par an. Pour mettre à jour :

```bash
# Simplement relancer la commande - elle ajoute les nouvelles espèces
python manage.py charger_lof
```

**Note** : Les espèces déjà existantes ne sont pas modifiées (basé sur `nom_scientifique` unique).

### Vérifier les données

```bash
# Shell Django
python manage.py shell

# Compter les espèces
>>> from taxonomy.models import Espece
>>> Espece.objects.count()
577

# Espèces par catégorie
>>> Espece.objects.values('statut').annotate(count=Count('id'))
<QuerySet [{'statut': 'A', 'count': 550}, {'statut': 'AC', 'count': 10}, ...]>

# Rechercher une espèce
>>> Espece.objects.filter(nom__icontains="merle")
<QuerySet [<Espece: Merle noir>, <Espece: Merle à plastron>, ...]>

# Espèces d'une famille
>>> from taxonomy.models import Famille
>>> Famille.objects.get(nom="Turdidae").espece_set.all()
```

## Dépannage

### Erreur : "Fichier introuvable"

Si vous utilisez `--file` et obtenez cette erreur :
- Vérifier le chemin absolu du fichier
- Vérifier les permissions de lecture
- Sur Windows, utiliser des slashs (`/`) ou doubles backslashs (`\\`)

### Erreur : "Cannot delete... ProtectedError"

Si vous utilisez `--force` et obtenez cette erreur :
```
django.db.models.deletion.ProtectedError: Cannot delete some instances of model 'Espece'
because they are referenced through protected foreign keys: 'FicheObservation.espece'.
```

**Cause** : Des fiches d'observation utilisent déjà ces espèces.

**Solution** : Ne pas utiliser `--force`. La commande sans `--force` ajoutera simplement les nouvelles espèces sans toucher aux existantes.

### Erreur : "Duplicate entry 'Nom espèce' for key 'nom'"

Si vous obtenez des erreurs de doublons :

**Cause** : Des espèces avec le même nom français existent déjà en base.

**Solution** : C'est normal et attendu. La commande ignore les doublons et continue l'import. Ces erreurs sont affichées pour information mais n'empêchent pas l'import.

### Avertissement : "X espèces déjà en base"

Si vous relancez la commande :
```
577 espèces déjà en base. Utilisez --force pour recharger.
```

**Cause** : Protection contre les imports accidentels répétés.

**Solution** :
- Si vous voulez vraiment recharger : `--force` (attention aux contraintes)
- Si vous voulez juste ajouter de nouvelles espèces : supprimer le seuil de 100 espèces dans le code

### Téléchargement lent

Si le téléchargement est lent :
- Vérifier votre connexion Internet
- Utiliser `--file` avec un fichier téléchargé manuellement
- Le fichier ne fait que 64KB, donc le téléchargement devrait être quasi-instantané

## Comparaison LOF vs TaxRef

| Critère | LOF | TaxRef |
|---------|-----|--------|
| **Noms français** | ✅ Oui | ✅ Oui |
| **Noms scientifiques** | ✅ Oui | ✅ Oui |
| **Noms anglais** | ❌ Non | ❌ Non |
| **Téléchargement** | ✅ Automatique (64KB) | ⚠️ Manuel (150MB) |
| **Nombre d'espèces oiseaux** | 605 (filtrable) | ~574 |
| **Taille fichier** | 64 KB | 150 MB |
| **Vitesse d'import** | 5-30s | 1-3 min |
| **Source** | CAF (Commission avifaune) | MNHN (officiel) |
| **Catégories de statut** | ✅ A,B,C,D,E | ✅ P,E,C |
| **Facilité d'utilisation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Recommandation** : Utilisez **LOF** pour un import rapide et simple des oiseaux de France. TaxRef est plus complet mais beaucoup plus lourd.

## Licence et attribution

### Liste des Oiseaux de France
- **Source :** Commission de l'avifaune française (CAF) via Faune-France
- **URL :** https://www.faune-france.org/index.php?m_id=20061
- **Licence :** À vérifier avec la CAF
- **Citation recommandée :**
  > Liste des Oiseaux de France. Commission de l'avifaune française. Accessible en ligne : https://www.faune-france.org/

### Script d'import
- **Auteur :** Projet Observations Nids
- **Licence :** Compatible avec la licence du projet

## Voir aussi

- Documentation TaxRef (alternative) : `taxonomy/README_TAXREF.md`
- Liste LOF officielle : https://www.faune-france.org/index.php?m_id=20061
- Commission de l'avifaune française : https://www.faune-france.org/
- Modèles taxonomy : `taxonomy/models.py`
- Guide de développement : `CLAUDE.md`

## Support

En cas de problème :
1. Consulter cette documentation
2. Vérifier les logs Django
3. Tester avec `--limit 10` pour isoler le problème
4. Comparer avec TaxRef si les données semblent incorrectes
5. Ouvrir une issue sur le dépôt Git du projet

---

*Documentation générée pour le projet Observations Nids*
*Dernière mise à jour : 2025-10-09*
