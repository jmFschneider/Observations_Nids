# Import TaxRef - Référentiel taxonomique des oiseaux

## Vue d'ensemble

Cette commande Django permet de charger automatiquement toutes les espèces d'oiseaux de France depuis le référentiel **TaxRef** du Muséum national d'Histoire naturelle (MNHN).

### Qu'est-ce que TaxRef ?

TaxRef est le **référentiel taxonomique national officiel** pour la faune, la flore et la fonge de France. Il est élaboré et diffusé par le MNHN et constitue la base de données de référence pour toutes les institutions scientifiques françaises.

**Avantages :**
- Source officielle gouvernementale
- Classification taxonomique complète (Ordre → Famille → Espèce)
- Noms vernaculaires français, scientifiques et anglais
- Statuts de conservation et présence géographique
- Mises à jour régulières (2 fois par an)

## Installation et prérequis

### Dépendances Python

La commande nécessite les bibliothèques suivantes (déjà dans requirements.txt) :
```bash
requests  # Pour télécharger TaxRef
```

### Compatibilité

✅ Windows
✅ Linux (Ubuntu, Debian, etc.)
✅ **Raspberry Pi** (optimisé pour faible mémoire)
✅ macOS

## Utilisation

### 1. Import depuis fichier local (RECOMMANDÉ)

**⚠️ Note importante :** Le téléchargement automatique depuis l'INPN n'est actuellement pas disponible car les URLs nécessitent une authentification. Il faut télécharger manuellement le fichier TaxRef.

**Procédure :**

1. **Télécharger TaxRef manuellement** :
   - Aller sur : https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
   - Cliquer sur "TAXREFv17 complet" (ou v18)
   - Télécharger le fichier ZIP (~50 MB)
   - Extraire le fichier `TAXREFv17.txt` ou `TAXREFv18.txt`

2. **Lancer l'import** :
```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt
```

Cette commande va :
1. Lire le fichier TaxRef
2. Filtrer les oiseaux (classe Aves) présents en France
3. Créer les ordres, familles et espèces en base de données

**Durée estimée :** 1-3 minutes selon la machine

### 2. Forcer la mise à jour

Pour **remplacer** les espèces existantes (⚠️ ATTENTION : ne fonctionne que si aucune fiche d'observation n'utilise ces espèces) :

```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt --force
```

### 3. Choisir une version spécifique de TaxRef

Pour utiliser TaxRef v18.0 (dernière version) :

```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv18.txt
```

Versions disponibles :
- v17.0 - Janvier 2023
- v18.0 - Janvier 2024
- v19.0 - Disponible début 2025

### 4. Mode test (limite le nombre d'espèces)

Pour tester rapidement sans tout importer :

```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt --limit 50
```

Utile pour :
- Tests de développement
- Validation sur Raspberry Pi
- Environnements de staging

## Exemples d'utilisation

### Sur serveur Raspberry Pi

```bash
# Se connecter au Raspberry Pi
ssh pi@raspberrypi.local

# Activer l'environnement virtuel
cd /var/www/html/Observations_Nids
source .venv/bin/activate

# Importer TaxRef (première fois)
python manage.py charger_taxref

# Mise à jour ultérieure (nouvelle version)
python manage.py charger_taxref --taxref-version 18.0 --force
```

### Sur poste de développement Windows

```powershell
# Dans le répertoire du projet
cd C:\Projets\observations_nids

# Activer l'environnement virtuel
.venv\Scripts\activate

# Import avec test limité
python manage.py charger_taxref --limit 100

# Import complet quand tout fonctionne
python manage.py charger_taxref
```

### Utiliser un fichier TaxRef téléchargé manuellement

1. Télécharger TaxRef depuis : https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/17.0/menu
2. Extraire le fichier `TAXREFv17.txt`
3. Lancer l'import :

```bash
python manage.py charger_taxref --file ~/Téléchargements/TAXREFv17.txt
```

## Données importées

### Structure des données

La commande crée et peuple 3 tables :

#### 1. **Ordre** (taxonomy_ordre)
- Niveau taxonomique supérieur (ex: Passeriformes, Accipitriformes)
- Environ 20-25 ordres d'oiseaux

#### 2. **Famille** (taxonomy_famille)
- Niveau intermédiaire (ex: Turdidae, Accipitridae)
- Environ 80-100 familles
- Liée à un Ordre

#### 3. **Espèce** (taxonomy_espece)
- Espèce complète avec noms français, scientifique, anglais
- Environ 550-600 espèces d'oiseaux présents en France
- Liée à une Famille
- Champs peuplés :
  - `nom` : Nom vernaculaire français (ex: "Merle noir")
  - `nom_scientifique` : Nom latin (ex: "Turdus merula")
  - `nom_anglais` : Nom anglais (ex: "Common Blackbird")
  - `famille` : Lien vers la famille
  - `statut` : Statut de présence en France (P=Présent, E=Endémique, C=Commun)
  - `valide_par_admin` : `True` (source officielle)
  - `commentaire` : Informations d'habitat

### Filtrage appliqué

La commande importe UNIQUEMENT :
- ✅ Classe : **Aves** (oiseaux)
- ✅ Territoire : **France** (métropolitaine + DOM-TOM)
- ✅ Statut : Présent, Endémique ou Commun
- ✅ Nom français : doit exister

Les autres espèces (invertébrés, plantes, etc.) sont **ignorées**.

## Exemple de sortie

```
=== Chargement TaxRef - Oiseaux de France ===

Téléchargement de TaxRef v17.0...
URL: https://geonature.fr/documents/taxref/TAXREF_v17_2023.zip
Progrès: [==================================================] 45.2MB
Téléchargement terminé
Extraction du fichier...
Extraction terminée

Import des données depuis: tmp/taxref/TAXREFv170.txt
Filtrage: Classe Aves (oiseaux) présents en France

Espèces importées: 574

=== Rapport d'import ===

Lignes traitées: 578,371
Oiseaux France trouvés: 574

Créations:
   - Ordres: 24
   - Familles: 93
   - Espèces: 574

=== Base de données ===

Ordres: 24
Familles: 93
Espèces: 574

Exemples d'espèces importées:
  - Cygne tuberculé (Anatidae) - Cygnus olor
  - Oie cendrée (Anatidae) - Anser anser
  - Canard colvert (Anatidae) - Anas platyrhynchos
  - Sarcelle d'hiver (Anatidae) - Anas crecca
  - Canard souchet (Anatidae) - Spatula clypeata

✓ Import terminé avec succès!
```

## Optimisations pour Raspberry Pi

La commande a été spécialement optimisée pour fonctionner sur Raspberry Pi :

### Gestion de la mémoire
- **Traitement par lots** : insertion de 500 espèces à la fois
- **Cache en mémoire** : évite les requêtes répétées
- **Lecture streaming** : fichier TaxRef lu ligne par ligne (pas chargé en entier)

### Performance
- Sur Raspberry Pi 4 (4GB RAM) : **~3-4 minutes**
- Sur Raspberry Pi 3B+ : **~5-7 minutes**
- Sur PC standard : **~1-2 minutes**

### Espace disque requis
- Fichier TaxRef téléchargé : ~50 MB
- Après extraction : ~150 MB
- En base de données (SQLite) : ~2 MB
- En base de données (PostgreSQL) : ~3 MB

Le fichier ZIP est automatiquement supprimé après extraction.

## Maintenance et mises à jour

### Mettre à jour TaxRef

TaxRef est mis à jour 2 fois par an (janvier et juillet). Pour mettre à jour :

```bash
# Mettre à jour vers la dernière version
python manage.py charger_taxref --taxref-version 18.0 --force
```

### Vérifier les données

```bash
# Shell Django
python manage.py shell

# Compter les espèces
>>> from taxonomy.models import Espece
>>> Espece.objects.count()
574

# Exemples de familles
>>> from taxonomy.models import Famille
>>> Famille.objects.all()[:5]

# Rechercher une espèce
>>> Espece.objects.filter(nom__icontains="merle")
<QuerySet [<Espece: Merle noir>, <Espece: Merle à plastron>, ...]>
```

## Dépannage

### Erreur : "Fichier introuvable"

Si vous utilisez `--file` et obtenez cette erreur :
- Vérifier le chemin absolu du fichier
- Vérifier les permissions de lecture
- Sur Windows, utiliser des slashs (`/`) ou doubles backslashs (`\\`)

### Erreur : "Timeout lors du téléchargement"

Si le téléchargement échoue :
1. Télécharger manuellement depuis : https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/17.0/menu
2. Utiliser `--file` pour pointer vers le fichier téléchargé

### Avertissement : "X espèces déjà en base"

Si vous relancez la commande sans `--force` :
```bash
574 espèces déjà en base. Utilisez --force pour recharger.
```

**Solution :** Ajouter `--force` pour remplacer les données existantes.

### Performances lentes sur Raspberry Pi

Si l'import prend plus de 10 minutes :
- Vérifier la vitesse de la carte SD (classe 10 recommandée)
- Vérifier l'utilisation CPU/RAM : `htop`
- Tester avec `--limit 50` d'abord

### Erreurs de base de données

**SQLite :** En cas d'erreur "database is locked"
```bash
# Fermer toutes les connexions Django
pkill -f "manage.py runserver"

# Relancer l'import
python manage.py charger_taxref --force
```

**PostgreSQL :** En cas d'erreur de connexion
```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql

# Vérifier les credentials dans .env
cat .env | grep DATABASE
```

## Licence et attribution

### TaxRef
- **Source :** Muséum national d'Histoire naturelle (MNHN)
- **Licence :** Libre d'utilisation avec citation obligatoire
- **Citation :**
  > TAXREF v17.0, Référentiel taxonomique pour la France. Muséum national d'Histoire naturelle. Paris. Accessible en ligne : https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref

### Script d'import
- **Auteur :** Projet Observations Nids
- **Licence :** Compatible avec la licence du projet

## Voir aussi

- Documentation TaxRef : https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref
- API TaxRef : https://taxref.mnhn.fr/taxref-web/api/doc
- Modèles taxonomy : `taxonomy/models.py`
- Guide de développement : `CLAUDE.md`

## Support

En cas de problème :
1. Consulter cette documentation
2. Vérifier les logs Django
3. Tester avec `--limit 10` pour isoler le problème
4. Ouvrir une issue sur le dépôt Git du projet
