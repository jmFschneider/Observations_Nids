# Guide Complet - Taxonomie des Oiseaux

Ce guide décrit le système de classification taxonomique du projet Observations Nids, ainsi que les commandes pour importer et enrichir les données d'espèces d'oiseaux.

---

## 📋 Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Modèles de données](#2-modeles-de-donnees)
3. [Import LOF (recommandé)](#3-import-lof-recommande)
4. [Import TaxRef (alternatif)](#4-import-taxref-alternatif)
5. [Enrichissement avec oiseaux.net](#5-enrichissement-avec-oiseauxnet)
6. [Gestion manuelle](#6-gestion-manuelle)
7. [Comparaison des sources](#7-comparaison-des-sources)
8. [Maintenance](#8-maintenance)

---

## 1. Vue d'ensemble

L'application `taxonomy` est le cœur de la classification des espèces pour le projet. Son rôle est de fournir une base de données propre, structurée et référencée pour toutes les espèces d'oiseaux.

### Sources de données disponibles

Le projet supporte 2 sources officielles pour l'import des espèces :

- **LOF (Liste des Oiseaux de France)** 📋 - **RECOMMANDÉE**
  - Source : Commission de l'avifaune française
  - ~577 espèces d'oiseaux de France
  - Fichier léger (64KB), import rapide (10-30 secondes)

- **TaxRef** 🏛️ - **ALTERNATIVE**
  - Source : Muséum national d'Histoire naturelle
  - ~574 espèces d'oiseaux de France
  - Fichier lourd (150MB), import plus lent (1-3 minutes)
  - Nécessite téléchargement manuel

---

## 2. Modèles de données

La taxonomie est hiérarchisée en 3 modèles principaux (`taxonomy/models.py`) :

### Ordre
- Le plus haut niveau de classification
- Exemples : *Passeriformes*, *Accipitriformes*, *Anseriformes*
- ~24-25 ordres d'oiseaux

### Famille
- Niveau intermédiaire, lié à un Ordre
- Exemples : *Turdidae*, *Accipitridae*, *Anatidae*
- ~80-93 familles

### Espèce
- Modèle principal contenant toutes les informations
- Champs :
  - `nom` : Nom vernaculaire français (ex: "Merle noir")
  - `nom_scientifique` : Nom latin (ex: "Turdus merula")
  - `nom_anglais` : Nom anglais (optionnel)
  - `famille` : Lien vers la famille
  - `statut` : Statut de présence
  - `lien_oiseau_net` : Lien vers fiche oiseaux.net
  - `valide_par_admin` : Validation administrative
  - `commentaire` : Informations complémentaires

---

## 3. Import LOF (recommandé)

### Pourquoi LOF ?

✅ **Avantages** :
- Téléchargement automatique (64KB)
- Import ultra-rapide (10-30 secondes)
- Source officielle française (CAF)
- Mises à jour régulières (2-3 fois/an)
- ~577 espèces d'oiseaux de France
- Catégories de statut claires (A, AC, B, C, D, E)

### Installation

Dépendances requises (déjà dans requirements.txt) :

```bash
pip install requests openpyxl
```

### Utilisation de base

#### Import automatique (méthode recommandée)

```bash
python manage.py charger_lof
```

Cette commande :
1. Télécharge automatiquement la LOF depuis Faune-France
2. Décompresse le fichier
3. Importe les espèces de catégories A et AC (sauvages)
4. Crée les ordres, familles et espèces en base

**Durée** : 10-30 secondes

#### Import depuis fichier local

```bash
python manage.py charger_lof --file /chemin/vers/LOF2024.xlsx
```

#### Choisir les catégories à importer

```bash
# Toutes les catégories
python manage.py charger_lof --categories A,AC,B,C

# Uniquement catégorie A (espèces sauvages)
python manage.py charger_lof --categories A

# A + espèces introduites
python manage.py charger_lof --categories A,C
```

**Catégories LOF** :
- **A** : Espèce observée à l'état sauvage (566 espèces)
- **A*** : Espèce naturalisée récemment (4 espèces)
- **AC** : Présente en catégorie A + C (10 espèces)
- **B** : Observée uniquement en captivité (11 espèces)
- **C** : Espèce introduite (11 espèces)
- **D** : Présente avant 1800, aujourd'hui disparue
- **E** : Données douteuses

#### Mode test

```bash
python manage.py charger_lof --limit 50
```

#### Forcer la mise à jour

⚠️ **ATTENTION** : Supprime les données existantes si aucune observation ne les utilise.

```bash
python manage.py charger_lof --force
```

### Exemples par plateforme

**Raspberry Pi** :

```bash
ssh pi@raspberrypi.local
cd /var/www/html/Observations_Nids
source .venv/bin/activate
python manage.py charger_lof
```

**Windows** :

```powershell
cd C:\Projets\observations_nids
.venv\Scripts\activate
python manage.py charger_lof
```

**Linux/macOS** :

```bash
cd /home/user/observations_nids
source .venv/bin/activate
python manage.py charger_lof
```

### Données importées

- **Ordres** : 25
- **Familles** : 83
- **Espèces** : ~577

### Exemple de sortie

```
=== Chargement LOF - Oiseaux de France ===

Téléchargement de la Liste des Oiseaux de France...
[OK] Téléchargement terminé
Décompression du fichier...
[OK] Décompression terminée

Import des données depuis: tmp/lof/LOF2024_decompressed.xlsx
Catégories filtrées: A, AC

Fichier ouvert: 1242 lignes à traiter
  Ordre créé: ANSERIFORMES
    Famille créée: Anatidae
...
Espèces importées: 552

=== Rapport d'import ===

Lignes traitées: 1,241

Créations:
   - Ordres: 24
   - Familles: 82
   - Espèces: 552
   - Espèces ignorées (autres catégories): 29

[OK] Import terminé avec succès!
```

### Performance

- **Raspberry Pi 4** : ~15-20 secondes
- **Raspberry Pi 3B+** : ~30-40 secondes
- **PC standard** : ~5-10 secondes

### Espace disque

- Fichier LOF : 64 KB
- Après décompression : ~120 KB
- En base SQLite : ~500 KB
- En base MariaDB : ~700 KB

---

## 4. Import TaxRef (alternatif)

### Pourquoi TaxRef ?

✅ **Avantages** :
- Source officielle gouvernementale (MNHN)
- Classification taxonomique très complète
- Noms vernaculaires français, scientifiques et anglais
- Statuts de conservation détaillés
- Mises à jour régulières (2 fois/an)

⚠️ **Inconvénients** :
- Fichier très lourd (~150MB)
- Nécessite téléchargement manuel
- Import plus lent (1-3 minutes)

### Installation

Dépendances (déjà dans requirements.txt) :

```bash
pip install requests
```

### Téléchargement manuel

1. Aller sur : https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
2. Cliquer sur "TAXREFv17 complet" (ou v18)
3. Télécharger le fichier ZIP (~50 MB)
4. Extraire `TAXREFv17.txt` ou `TAXREFv18.txt`

### Utilisation

#### Import depuis fichier

```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt
```

**Durée** : 1-3 minutes

#### Mode test

```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt --limit 50
```

#### Forcer la mise à jour

```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt --force
```

### Exemples par plateforme

**Raspberry Pi** :

```bash
ssh pi@raspberrypi.local
cd /var/www/html/Observations_Nids
source .venv/bin/activate
python manage.py charger_taxref --file ~/Téléchargements/TAXREFv17.txt
```

**Windows** :

```powershell
cd C:\Projets\observations_nids
.venv\Scripts\activate
python manage.py charger_taxref --file C:\Users\VotreNom\Téléchargements\TAXREFv17.txt
```

### Données importées

- **Ordres** : 24
- **Familles** : 93
- **Espèces** : ~574

### Filtrage appliqué

La commande importe UNIQUEMENT :
- ✅ Classe : **Aves** (oiseaux)
- ✅ Territoire : **France** (métropolitaine + DOM-TOM)
- ✅ Statut : Présent, Endémique ou Commun
- ✅ Nom français : doit exister

### Optimisations Raspberry Pi

- **Traitement par lots** : 500 espèces à la fois
- **Cache en mémoire** : évite requêtes répétées
- **Lecture streaming** : ligne par ligne (pas tout en mémoire)

**Performance** :
- Raspberry Pi 4 : ~3-4 minutes
- Raspberry Pi 3B+ : ~5-7 minutes
- PC standard : ~1-2 minutes

### Espace disque

- Fichier TaxRef téléchargé : ~50 MB
- Après extraction : ~150 MB
- En base SQLite : ~2 MB
- En base MariaDB : ~3 MB

---

## 5. Enrichissement avec oiseaux.net

### Vue d'ensemble

Une fois les espèces importées (LOF ou TaxRef), vous pouvez enrichir la base avec les liens vers les fiches [oiseaux.net](https://www.oiseaux.net).

**Taux de réussite** : ~98%

### Stratégie de recherche

La commande utilise 3 méthodes successives :

1. **Méthode 1** : Construction depuis nom français (~95% de réussite)
   - Exemple : "Bernache cravant" → `https://www.oiseaux.net/oiseaux/bernache.cravant.html`

2. **Méthode 2** : Construction depuis nom scientifique (~20% de réussite)
   - Exemple : "Branta bernicla" → `https://www.oiseaux.net/oiseaux/branta.bernicla.html`

3. **Méthode 3** : Recherche Google (~80% de réussite)
   - Recherche : `"Nom scientifique" "Nom français" site:oiseaux.net`

### Installation

Dépendances (déjà dans requirements.txt) :

```bash
pip install beautifulsoup4 requests
```

### Utilisation

#### Commande de base

```bash
python manage.py recuperer_liens_oiseaux_net
```

Traite uniquement les espèces sans lien existant.

#### Options disponibles

```bash
# Mettre à jour toutes les espèces
python manage.py recuperer_liens_oiseaux_net --force

# Mode test (10 premières espèces)
python manage.py recuperer_liens_oiseaux_net --limit 10

# Simulation sans modification BDD
python manage.py recuperer_liens_oiseaux_net --dry-run

# Définir le délai entre requêtes (défaut: 1s)
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

#### Exemples combinés

```bash
# Test sur 5 espèces sans modifier la base
python manage.py recuperer_liens_oiseaux_net --limit 5 --dry-run

# Traitement complet avec délai raisonnable
python manage.py recuperer_liens_oiseaux_net --delay 1.5

# Mise à jour forcée de toutes les espèces
python manage.py recuperer_liens_oiseaux_net --force --delay 2
```

### Sortie de la commande

```
[1/577] Bernache cravant (Branta bernicla)
  -> Test URL nom francais: https://www.oiseaux.net/oiseaux/bernache.cravant.html
  [OK] URL nom francais valide !

[2/577] Bernache à cou roux (Branta ruficollis)
  -> Test URL nom francais: https://www.oiseaux.net/oiseaux/bernache.a.cou.roux.html
  [OK] URL nom francais valide !

...

============================================================
[RESUME]
============================================================
Total traite      : 577
[OK] Succes direct   : 550
[OK] Succes Google   : 20
[!] Ignores         : 5
[X] Echecs          : 2

Taux de reussite : 98.8%
```

### Durée estimée

Pour 577 espèces (base complète LOF) :

| Configuration | Durée | Recommandation |
|---------------|-------|----------------|
| `--delay 1.0` (défaut) | ~10 min | Rapide, bon compromis |
| `--delay 1.5` | ~15 min | **Recommandé** |
| `--delay 2.0` | ~20 min | Très respectueux |

### Workflow recommandé

#### Premier usage

```bash
# 1. Test sur 10 espèces
python manage.py recuperer_liens_oiseaux_net --limit 10 --dry-run

# 2. Si OK, traitement complet
python manage.py recuperer_liens_oiseaux_net --delay 1.5

# 3. Vérifier les échecs et compléter manuellement
```

#### Après import de nouvelles espèces

```bash
# Traiter uniquement espèces sans lien
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

#### Rafraîchissement annuel

```bash
# Mettre à jour toutes les espèces
python manage.py recuperer_liens_oiseaux_net --force --delay 2
```

---

## 6. Gestion manuelle

### Interface web d'administration

**Accès** : `/taxonomy/especes/` (réservé aux administrateurs)

### Fonctionnalités

- **Liste des espèces** : Affichage paginé avec recherche et filtres
- **Détail d'une espèce** : Vue complète + nombre d'observations
- **Création/Modification** : Formulaires de gestion
- **Suppression** : Protection si espèce utilisée dans observations
- **Portail d'import** : `/taxonomy/importer/` avec instructions

---

## 7. Comparaison des sources

| Critère | LOF | TaxRef |
|---------|-----|--------|
| **Noms français** | ✅ Oui | ✅ Oui |
| **Noms scientifiques** | ✅ Oui | ✅ Oui |
| **Noms anglais** | ❌ Non | ❌ Non |
| **Téléchargement** | ✅ Automatique (64KB) | ⚠️ Manuel (150MB) |
| **Nombre d'espèces** | 605 (filtrable) | ~574 |
| **Taille fichier** | 64 KB | 150 MB |
| **Vitesse d'import** | 5-30s | 1-3 min |
| **Source** | CAF (Commission avifaune) | MNHN (officiel) |
| **Catégories de statut** | ✅ A,B,C,D,E | ✅ P,E,C |
| **Facilité d'utilisation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Recommandation** : Utilisez **LOF** pour un import rapide et simple. TaxRef si vous avez besoin de données plus complètes ou d'une source gouvernementale officielle.

---

## 8. Maintenance

### Vérifier les données

```bash
# Shell Django
python manage.py shell

# Compter les espèces
>>> from taxonomy.models import Espece, Ordre, Famille
>>> Espece.objects.count()
577

# Exemples d'ordres
>>> Ordre.objects.all()[:5]

# Exemples de familles
>>> Famille.objects.all()[:5]

# Rechercher une espèce
>>> Espece.objects.filter(nom__icontains="merle")
<QuerySet [<Espece: Merle noir>, <Espece: Merle à plastron>, ...]>

# Espèces d'une famille
>>> Famille.objects.get(nom="Turdidae").espece_set.all()

# Vérifier les liens oiseaux.net
>>> Espece.objects.filter(lien_oiseau_net__isnull=False).count()
550
```

### Mise à jour régulière

```bash
# LOF : mise à jour 2-3 fois/an
python manage.py charger_lof

# TaxRef : mise à jour janvier et juillet
python manage.py charger_taxref --file /chemin/vers/TAXREFv18.txt --force

# Liens oiseaux.net : une fois/an
python manage.py recuperer_liens_oiseaux_net --force --delay 2
```

### Workflow complet recommandé

```bash
# 1. Importer les espèces (LOF recommandé)
python manage.py charger_lof

# 2. Enrichir avec liens oiseaux.net
python manage.py recuperer_liens_oiseaux_net --delay 1.5

# 3. Vérifier les résultats
python manage.py shell
>>> from taxonomy.models import Espece
>>> Espece.objects.count()
>>> Espece.objects.filter(lien_oiseau_net__isnull=False).count()
```

---

## 🔧 Dépannage

### Erreur : "Fichier introuvable"

- Vérifier le chemin absolu
- Sur Windows, utiliser `/` ou `\\`
- Vérifier les permissions de lecture

### Erreur : "Cannot delete... ProtectedError"

- Cause : Des observations utilisent ces espèces
- Solution : Ne pas utiliser `--force`, ou supprimer d'abord les observations

### Erreur : "Duplicate entry"

- Cause : Espèces déjà en base
- Solution : Normal, la commande ignore les doublons et continue

### Téléchargement lent/échoué

- Vérifier connexion Internet
- Utiliser `--file` avec fichier téléchargé manuellement
- Augmenter le timeout si nécessaire

### Google bloque les requêtes (oiseaux.net)

- Augmenter le délai : `--delay 3`
- Lancer en plusieurs fois avec `--limit`
- Attendre quelques heures avant de relancer

---

## 📚 Ressources

### Documentation officielle

- **LOF** : https://www.faune-france.org/index.php?m_id=20061
- **TaxRef** : https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref
- **Oiseaux.net** : https://www.oiseaux.net

### Licence et attribution

**LOF** :
- Source : Commission de l'avifaune française
- Licence : À vérifier avec la CAF

**TaxRef** :
- Source : Muséum national d'Histoire naturelle
- Licence : Libre avec citation obligatoire

**Oiseaux.net** :
- Site : LPO (Ligue pour la Protection des Oiseaux)
- Respectez les conditions générales et délais entre requêtes

---

**Document mis à jour le** : 24/10/2025
**Version** : 2.0 (consolidé depuis 4 fichiers)
