# Guide de Gestion des Espèces et Taxonomie

Guide complet pour la gestion de la taxonomie ornithologique et des espèces d'oiseaux dans le projet "Observations Nids".

> **🎯 Public cible :** Administrateurs et développeurs
> **📅 Dernière mise à jour :** 26 décembre 2025
> **✨ Nouveauté :** Interface web d'administration centralisée avec tâches asynchrones

---

## 📋 Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Interface d'administration](#2-interface-dadministration)
3. [Gestion des espèces](#3-gestion-des-especes)
4. [Architecture taxonomique](#4-architecture-taxonomique)
5. [Référence rapide](#5-reference-rapide)
6. [Dépannage](#6-depannage)

---

## 1. Vue d'ensemble

### Objectif

Le système de taxonomie permet de :
- ✅ Gérer une base de données de ~577 espèces d'oiseaux de France
- ✅ Organiser selon la hiérarchie : **Ordre → Famille → Espèce**
- ✅ Enrichir avec des liens vers oiseaux.net
- ✅ Administrer les données depuis une interface web unique

### Hiérarchie taxonomique

```
Ordre (ex: Passériformes)
  └─ Famille (ex: Paridés)
       └─ Espèce (ex: Mésange bleue)
            ├─ Nom commun français
            ├─ Nom anglais (optionnel)
            ├─ Nom scientifique (latin)
            └─ Lien oiseaux.net
```

### Sources de données disponibles

| Source | Type | Nombre d'espèces | Avantages |
|--------|------|------------------|-----------|
| **LOF** | Liste Officielle de France | ~577 | ⭐ **Recommandé** - Téléchargement auto, rapide (10-30s) |
| **TaxRef** | Référentiel national MNHN | ~574 | Complet mais lourd (1-3 min), téléchargement manuel |
| **oiseaux.net** | Enrichissement liens | ~98% réussite | Fiches détaillées par espèce |

---

## 2. Interface d'administration

### 🎯 Accès

**URL :** `/taxonomy/administration-donnees/`

**Permissions :** Réservé aux administrateurs (`is_staff=True`)

**Navigation :**
1. Se connecter comme administrateur
2. Menu principal → Section "Référentiels" ou "Administration"
3. Cliquer sur "Administration des données taxonomiques"

### Page d'administration

L'interface centralise toutes les opérations de gestion des espèces :

#### 📊 Statistiques affichées

- **Total espèces** : Nombre d'espèces en base
- **Ordres** : Nombre d'ordres taxonomiques (~25)
- **Familles** : Nombre de familles (~83)
- **LOF** : Espèces issues de la Liste Officielle de France
- **TaxRef** : Espèces issues du référentiel TaxRef
- **Avec liens** : Espèces enrichies avec lien oiseaux.net

#### 🔧 Scripts d'administration (3 boutons)

##### 1. Liste Officielle de France (LOF) ⭐ RECOMMANDÉ

**Fonction :** Charge toutes les espèces depuis la Liste Officielle des Oiseaux de France

**Source :** [Faune-France](https://www.faune-france.org/index.php?m_id=20061)
**Nombre :** ~577 espèces
**Durée :** 10-30 secondes
**Taille :** 64 KB (téléchargement automatique)

**Options :**
- ☐ **Force** : Remplacer les données existantes
- 🔢 **Limite** : Nombre d'espèces à importer (pour test)

**Catégories LOF :**
- **A** : Espèce sauvage observée en France (566 espèces)
- **A*** : Espèce naturalisée récemment (4 espèces)
- **AC** : Catégorie A + C (10 espèces)
- **B** : Observée uniquement en captivité (11 espèces)
- **C** : Espèce introduite (11 espèces)
- **D** : Disparue depuis avant 1800
- **E** : Données douteuses

**Utilisation :**
```
1. (Optionnel) Saisir une limite pour tester (ex: 50)
2. Cocher "Force" si vous voulez écraser les données existantes
3. Cliquer sur "Lancer le chargement LOF"
4. Attendre la fin du traitement (~10-30 secondes)
5. Un message de succès s'affiche avec le résumé
```

**Données importées :**
- Ordres : ~25
- Familles : ~83
- Espèces : ~577 (catégories A et AC par défaut)

**Équivalent commande (ancienne méthode) :**
```bash
python manage.py charger_lof [--force] [--limit 50] [--categories A,AC]
```

##### 2. TaxRef (MNHN/INPN) - Alternative

**Fonction :** Charge depuis le référentiel taxonomique national du Muséum d'Histoire Naturelle

**Source :** [INPN TaxRef](https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo)
**Nombre :** ~574 espèces
**Durée :** 1-3 minutes
**Taille :** 150 MB (⚠️ téléchargement manuel requis)

**Options :**
- ☐ **Force** : Remplacer les données existantes
- 📝 **Version TaxRef** : Version à utiliser (ex: 18.0)

**Prérequis :**
Télécharger manuellement le fichier TaxRef :
```bash
# 1. Télécharger depuis https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
# 2. Extraire TAXREFv17.txt ou TAXREFv18.txt
# 3. Placer le fichier dans le dossier du projet
```

**Utilisation :**
```
1. Télécharger et placer TAXREFv17.txt dans le projet
2. (Optionnel) Saisir la version (ex: 18.0)
3. Cocher "Force" si nécessaire
4. Cliquer sur "Lancer le chargement TaxRef"
5. Attendre la fin (~1-3 minutes)
```

**Filtrage appliqué :**
- ✅ Classe : **Aves** (oiseaux uniquement)
- ✅ Territoire : **France** (métropole + DOM-TOM)
- ✅ Statut : Présent, Endémique ou Commun
- ✅ Nom français : doit exister

**Équivalent commande :**
```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt [--force]
```

##### 3. Liens oiseaux.net 🚀 ASYNCHRONE

**Fonction :** Récupère automatiquement les URLs vers les fiches oiseaux.net

**Source :** [oiseaux.net](https://www.oiseaux.net)
**Taux de réussite :** ~98%
**Durée :** 5-15 minutes (asynchrone via Celery)

**Options :**
- ☐ **Force** : Remplacer les liens existants
- ☐ **Dry-run** : Simulation sans enregistrement
- 🔢 **Limite** : Nombre d'espèces à traiter (pour test)
- ⏱️ **Délai** : Délai entre requêtes en secondes (défaut: 1.0)

**Stratégie de recherche :**
1. **Méthode 1** : URL depuis nom français (~95% réussite)
   - Ex: "Bernache cravant" → `oiseaux.net/oiseaux/bernache.cravant.html`
2. **Méthode 2** : URL depuis nom scientifique (~20% réussite)
   - Ex: "Branta bernicla" → `oiseaux.net/oiseaux/branta.bernicla.html`
3. **Méthode 3** : Recherche Google (~80% réussite)
   - Recherche: `"Nom scientifique" "Nom français" site:oiseaux.net`

**Utilisation :**
```
1. (Optionnel) Saisir une limite pour tester (ex: 10)
2. (Optionnel) Ajuster le délai (1.5-2.0 sec recommandé)
3. Cocher "Dry-run" pour simuler sans modifier la base
4. Cliquer sur "Lancer en arrière-plan"
5. Suivre la progression dans Flower (s'ouvre automatiquement)
```

**Suivi de progression :**
- La tâche s'exécute en arrière-plan via Celery
- Flower s'ouvre automatiquement dans un nouvel onglet
- URL Flower : `/flower/task/<task_id>`

**Équivalent commande :**
```bash
python manage.py recuperer_liens_oiseaux_net [--force] [--limit 10] [--delay 1.5] [--dry-run]
```

#### 🔄 Ordre recommandé pour une nouvelle installation

1. **Charger les espèces depuis la LOF** (avec force) - ⭐ Recommandé
2. **OU** charger depuis TaxRef si vous préférez
3. **Récupérer les liens oiseaux.net** pour enrichir

**Note :** LOF est recommandée car plus rapide, spécifique à la France, et téléchargement automatique.

---

## 3. Gestion des espèces

### Liste des espèces

**URL :** `/taxonomy/especes/`

**Fonctionnalités :**

#### Recherche
- Par nom français (ex: "Mésange")
- Par nom scientifique (ex: "Cyanistes")
- Par nom anglais (ex: "Blue tit")

#### Filtres
- Ordre (liste déroulante)
- Famille
- Source (LOF, TaxRef, Manuel)
- Validé par admin (Oui/Non)

#### Affichage
- Pagination (50 espèces par page)
- Tri par nom français
- Badges visuels :
  - Source (LOF / TaxRef / Manuel)
  - Statut validation
  - Présence lien oiseaux.net

### Détail d'une espèce

**URL :** `/taxonomy/especes/<id>/`

**Informations affichées :**

| Section | Contenu |
|---------|---------|
| **Identification** | Nom français, nom scientifique, nom anglais |
| **Classification** | Ordre, famille |
| **Statut** | Statut de conservation (UICN) |
| **Liens externes** | Lien vers oiseaux.net |
| **Utilisation** | Nombre d'observations |
| **Métadonnées** | Source, validé par admin, dates |

**Actions disponibles :**
- 🔧 Modifier l'espèce
- 🗑️ Supprimer (si non utilisée)
- 🔗 Voir sur oiseaux.net

### Création manuelle

**URL :** `/taxonomy/especes/creer/`

**Champs obligatoires :**
- Nom français

**Champs optionnels :**
- Nom anglais
- Nom scientifique (format: "Genre species")
- Famille (sélection dans liste)
- Statut de conservation
- Lien oiseaux.net
- Commentaire

**Utilisation :**
Pour ajouter une espèce rare, exotique ou récemment observée non présente dans LOF/TaxRef.

### Modification

**URL :** `/taxonomy/especes/<id>/modifier/`

**Cas d'usage :**
- Corriger une erreur d'orthographe
- Ajouter le lien oiseaux.net manuellement
- Mettre à jour le statut de conservation
- Valider une espèce ajoutée par un utilisateur

### Suppression

**URL :** `/taxonomy/especes/<id>/supprimer/`

**Règles de sécurité :**
- ❌ **Impossible** si l'espèce est utilisée dans des observations (protection PROTECT)
- ✅ **Possible** si aucune observation ne l'utilise

**Alternative :** Marquer comme inactive au lieu de supprimer

---

## 4. Architecture taxonomique

### Modèles de données

#### Ordre

```python
class Ordre(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
```

**Exemples :**
- Passériformes (~60% des espèces)
- Accipitriformes (rapaces diurnes)
- Strigiformes (rapaces nocturnes)
- Anseriformes (canards, oies)

**Nombre en base :** ~25 ordres

#### Famille

```python
class Famille(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    ordre = models.ForeignKey(Ordre, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
```

**Relations :**
- Un Ordre contient plusieurs Familles (1:N)
- Si un Ordre est supprimé → toutes ses Familles sont supprimées (CASCADE)

**Exemples :**
- Paridés (mésanges) → Passériformes
- Corvidés (corbeaux, pies) → Passériformes
- Anatidae (canards) → Anseriformes

**Nombre en base :** ~83 familles

#### Espèce

```python
class Espece(models.Model):
    # Noms
    nom = models.CharField(max_length=100, unique=True)  # Nom français
    nom_anglais = models.CharField(max_length=100, blank=True)
    nom_scientifique = models.CharField(max_length=100, blank=True)

    # Classification
    famille = models.ForeignKey(
        Famille,
        on_delete=models.SET_NULL,  # Préserve l'espèce si famille supprimée
        null=True,
        blank=True
    )

    # Métadonnées
    statut = models.CharField(max_length=50, blank=True)
    lien_oiseau_net = models.URLField(blank=True)
    valide_par_admin = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)

    # Traçabilité (ajoutée par scripts d'import)
    source_import = models.CharField(max_length=50)  # 'LOF', 'TaxRef', 'Manuel'
```

**Relations :**
- Une Famille contient plusieurs Espèces (1:N)
- Une Espèce est référencée par plusieurs FicheObservation (1:N)
- Si une Famille est supprimée → `espece.famille = NULL` (SET_NULL)
- Si une Espèce est supprimée → **ERREUR** si observations existent (PROTECT)

**Protection CASCADE/SET_NULL/PROTECT :**

```python
# Ordre → Famille : CASCADE
ordre.delete()  # → Supprime toutes ses familles

# Famille → Espèce : SET_NULL
famille.delete()  # → Les espèces conservent espece.famille=NULL

# Espèce → FicheObservation : PROTECT
espece.delete()  # → ERREUR si observations existent
```

### Champ `valide_par_admin`

**Workflow de validation :**
1. Utilisateur crée une nouvelle espèce → `valide_par_admin=False`
2. Admin vérifie et valide → `valide_par_admin=True`
3. Seules les espèces validées apparaissent dans les formulaires publics

**Filtrage dans les formulaires :**
```python
especes_validees = Espece.objects.filter(valide_par_admin=True)
```

### Statuts de conservation (UICN)

| Code | Signification | Exemple |
|------|---------------|---------|
| **LC** | Least Concern (Préoccupation mineure) | Moineau domestique |
| **NT** | Near Threatened (Quasi menacée) | Tourterelle des bois |
| **VU** | Vulnerable (Vulnérable) | Tarier des prés |
| **EN** | Endangered (En danger) | Gypaète barbu |
| **CR** | Critically Endangered (En danger critique) | Vautour moine |

**Utilisation :**
```python
especes_menacees = Espece.objects.filter(statut__in=['VU', 'EN', 'CR'])
```

---

## 5. Référence rapide

### Commandes manage.py (si besoin)

Bien que l'interface web soit recommandée, les commandes sont toujours disponibles :

```bash
# Charger depuis LOF (recommandé)
python manage.py charger_lof [--force] [--limit 50] [--categories A,AC]

# Charger depuis TaxRef (alternatif)
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt [--force]

# Récupérer liens oiseaux.net
python manage.py recuperer_liens_oiseaux_net [--force] [--delay 1.5] [--limit 10] [--dry-run]
```

### URLs principales

| URL | Description |
|-----|-------------|
| `/taxonomy/administration-donnees/` | Page d'administration (scripts) |
| `/taxonomy/especes/` | Liste des espèces |
| `/taxonomy/especes/<id>/` | Détail d'une espèce |
| `/taxonomy/especes/creer/` | Création manuelle |
| `/taxonomy/especes/<id>/modifier/` | Modification |
| `/taxonomy/especes/<id>/supprimer/` | Suppression |

### Tâches Celery (asynchrones)

| Tâche | Description | Suivi |
|-------|-------------|-------|
| `recuperer_liens_oiseaux_net_task` | Enrichissement oiseaux.net | Flower `/flower/` |

### Méthodes utiles du modèle

```python
# Nombre d'observations pour cette espèce
espece.observations.count()

# Toutes les espèces d'une famille
famille.especes.all()

# Toutes les espèces d'un ordre
Espece.objects.filter(famille__ordre=ordre)

# Espèces sans lien oiseaux.net
Espece.objects.filter(lien_oiseau_net='')

# Espèces par source
Espece.objects.filter(source_import='LOF')
```

---

## 6. Dépannage

### Problème : Téléchargement LOF échoue

**Erreur :** `Erreur de téléchargement de la LOF`

**Causes possibles :**
- Pas de connexion Internet
- Site Faune-France indisponible
- Timeout réseau

**Solutions :**
```bash
# 1. Vérifier la connexion
ping www.faune-france.org

# 2. Télécharger manuellement le fichier LOF (.xlsx)
# 3. Utiliser l'option --file
python manage.py charger_lof --file /chemin/vers/LOF2025.xlsx
```

### Problème : Fichier TaxRef introuvable

**Erreur :** `FileNotFoundError: TAXREFv17.txt`

**Solution :**
1. Télécharger depuis https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
2. Extraire le fichier ZIP
3. Placer `TAXREFv17.txt` dans le dossier du projet
4. Vérifier le chemin absolu

### Problème : Suppression impossible

**Erreur :** `ProtectedError: Cannot delete... FicheObservation.espece`

**Cause :** Des observations utilisent cette espèce

**Solution :**
```python
# Vérifier le nombre d'observations
espece.observations.count()  # → 42

# Option 1 : Ne pas supprimer
# Les données historiques doivent être préservées

# Option 2 : Marquer comme inactive (si champ ajouté)
espece.active = False
espece.save()
```

### Problème : Tâche Celery ne démarre pas

**Symptôme :** Clic sur "Lancer en arrière-plan" mais rien ne se passe

**Diagnostic :**
```bash
# Vérifier que Celery est démarré
celery -A observations_nids status

# Vérifier les logs
tail -f logs/celery.log
```

**Solutions :**
```bash
# Démarrer Celery worker
celery -A observations_nids worker -l info

# Ou avec Docker
docker compose up -d celery
```

### Problème : Google bloque les requêtes (oiseaux.net)

**Symptôme :** Beaucoup d'échecs avec la méthode 3 (Google)

**Cause :** Trop de requêtes Google en peu de temps

**Solutions :**
```bash
# 1. Augmenter le délai
--delay 2.0  # ou 3.0

# 2. Traiter par petits lots
--limit 50

# 3. Attendre quelques heures avant de relancer
```

### Problème : Noms scientifiques manquants

**Symptôme :** Plusieurs espèces sans nom scientifique

**Diagnostic :**
```python
from taxonomy.models import Espece

# Lister les espèces concernées
sans_nom_scientifique = Espece.objects.filter(
    nom_scientifique__in=['', None]
)
print(f"{sans_nom_scientifique.count()} espèces sans nom scientifique")
```

**Solution :** Compléter manuellement ou importer depuis une autre source

### Problème : Doublon après import

**Erreur :** `IntegrityError: UNIQUE constraint failed: taxonomy_espece.nom`

**Cause :** Espèce déjà en base

**Comportement normal :** La commande ignore les doublons et continue

**Vérification :**
```python
# Rechercher les doublons potentiels
from django.db.models import Count

doublons = Espece.objects.values('nom').annotate(
    count=Count('id')
).filter(count__gt=1)
```

### Maintenance annuelle recommandée

**Quand :** Une fois par an (janvier/février après publication LOF)

**Procédure :**
1. Aller sur `/taxonomy/administration-donnees/`
2. Cliquer sur "Lancer le chargement LOF" (cocher Force)
3. Attendre la fin (~30 secondes)
4. Cliquer sur "Lancer en arrière-plan" (récupération liens)
5. Suivre la progression dans Flower
6. Vérifier les statistiques affichées

---

## Annexes

### Technologies utilisées

- **Django 6.0** - Framework web Python
- **Celery** - Tâches asynchrones
- **Redis** - Broker Celery
- **Flower** - Monitoring Celery
- **openpyxl** - Lecture fichiers Excel (LOF)
- **requests** - Téléchargement et HTTP
- **beautifulsoup4** - Parsing HTML (oiseaux.net)

### Fichiers du projet

| Fichier | Description |
|---------|-------------|
| `taxonomy/models.py` | Modèles Ordre, Famille, Espece |
| `taxonomy/views_admin.py` | Vues d'administration (scripts et CRUD) |
| `taxonomy/tasks.py` | Tâches Celery asynchrones |
| `taxonomy/templates/taxonomy/administration_donnees.html` | Interface d'administration |
| `taxonomy/management/commands/charger_lof.py` | Script de chargement LOF |
| `taxonomy/management/commands/charger_taxref.py` | Script de chargement TaxRef |
| `taxonomy/management/commands/recuperer_liens_oiseaux_net.py` | Script d'enrichissement |

### Performance et optimisations

**LOF (recommandé) :**
- Raspberry Pi 4 : ~15-20 secondes
- Raspberry Pi 3B+ : ~30-40 secondes
- PC standard : ~5-10 secondes
- Fichier : 64 KB
- Base SQLite : ~500 KB
- Base MariaDB : ~700 KB

**TaxRef (alternatif) :**
- Raspberry Pi 4 : ~3-4 minutes
- Raspberry Pi 3B+ : ~5-7 minutes
- PC standard : ~1-2 minutes
- Fichier : ~150 MB
- Base SQLite : ~2 MB
- Base MariaDB : ~3 MB

**Liens oiseaux.net :**
- Durée : 5-15 minutes (577 espèces avec delay 1.0s)
- Taux de réussite : ~98%
- Mode asynchrone : pas de blocage de l'interface

### Comparaison LOF vs TaxRef

| Critère | LOF | TaxRef |
|---------|-----|--------|
| **Téléchargement** | ✅ Automatique (64KB) | ⚠️ Manuel (150MB) |
| **Nombre d'espèces** | 577 | 574 |
| **Vitesse d'import** | 5-30s | 1-3 min |
| **Source** | CAF (Commission avifaune) | MNHN (Muséum national) |
| **Catégories** | A, AC, B, C, D, E | P, E, C |
| **Noms français** | ✅ Oui | ✅ Oui |
| **Noms scientifiques** | ✅ Oui | ✅ Oui |
| **Noms anglais** | ❌ Non | ❌ Non |
| **Facilité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Recommandation :** Utilisez **LOF** sauf si vous avez besoin de la source gouvernementale officielle.

### Évolutions futures possibles

**Court terme :**
- [ ] Import des noms anglais depuis une source tierce
- [ ] Export CSV de la liste des espèces
- [ ] Historique des modifications

**Moyen terme :**
- [ ] API REST complète (DRF)
- [ ] Synchronisation automatique annuelle
- [ ] Interface de validation en masse

**Long terme :**
- [ ] Intégration d'autres référentiels européens
- [ ] Photos d'espèces (intégration Wikimedia Commons)
- [ ] Chants d'oiseaux (intégration Xeno-canto)

### Ressources

**Documentation officielle :**
- [LOF - Faune France](https://www.faune-france.org/index.php?m_id=20061)
- [TaxRef - INPN](https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref)
- [Oiseaux.net](https://www.oiseaux.net)
- [UICN - Liste rouge](https://www.iucnredlist.org/)

**Licence et attribution :**

**LOF :**
- Source : Commission de l'avifaune française (CAF)
- Licence : À vérifier avec la CAF

**TaxRef :**
- Source : Muséum national d'Histoire naturelle (MNHN)
- Licence : Libre avec citation obligatoire

**Oiseaux.net :**
- Site : LPO (Ligue pour la Protection des Oiseaux)
- Respectez les conditions générales et délais entre requêtes

---

**Document créé le :** 26 décembre 2025
**Auteur :** Documentation consolidée
**Version :** 2.0
**Remplace :**
- `01_taxonomie.md`
- `07_taxonomie.md` (architecture/domaines)
