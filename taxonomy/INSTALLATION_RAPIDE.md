# Installation rapide - Import TaxRef

**Remarque : je n'ai pas réussi à me connecter correctement sur le site. J'ai abandonné cette solution au profit de oiseaux.net**

[TOC]



## Guide rapide pour démarrer

**⚠️ Important :** Le téléchargement automatique n'est pas disponible. Vous devez d'abord télécharger TaxRef manuellement.

### Étape 1 : Télécharger TaxRef

1. Aller sur : https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
2. Cliquer sur "TAXREFv17 complet" ou "TAXREFv18 complet"
3. Télécharger le fichier ZIP
4. Extraire le fichier `TAXREFv17.txt` ou `TAXREFv18.txt`

### Étape 2 : Import sur votre poste Windows

```powershell
# Ouvrir PowerShell dans le répertoire du projet
cd C:\Projets\observations_nids

# Activer l'environnement virtuel
.venv\Scripts\activate

# Importer les espèces d'oiseaux de France (remplacer par votre chemin)
python manage.py charger_taxref --file C:\Users\VotreNom\Téléchargements\TAXREFv17.txt

# Attendre 1-3 minutes...
# Environ 574 espèces seront importées
```

### Étape 3 : Import sur votre serveur Raspberry Pi

```bash
# Transférer le fichier TaxRef sur le Raspberry Pi (depuis votre PC)
scp TAXREFv17.txt pi@votre-raspberry-pi:/home/pi/

# Se connecter au Raspberry Pi
ssh pi@votre-raspberry-pi

# Naviguer vers le projet
cd /var/www/html/Observations_Nids

# Activer l'environnement virtuel
source .venv/bin/activate

# Importer les espèces
python manage.py charger_taxref --file /home/pi/TAXREFv17.txt

# Attendre 3-5 minutes sur Raspberry Pi...
# Les mêmes 574 espèces seront importées
```

## Vérification

Après l'import, vérifiez que tout fonctionne :

```bash
# Shell Django
python manage.py shell

# Dans le shell Python
>>> from taxonomy.models import Espece, Famille, Ordre
>>> Espece.objects.count()
574
>>> Ordre.objects.count()
24
>>> Famille.objects.count()
93

# Rechercher une espèce
>>> Espece.objects.filter(nom__icontains="merle")
<QuerySet [<Espece: Merle noir>, <Espece: Merle à plastron>, ...]>

# Quitter
>>> exit()
```

## En cas de problème

### "X espèces déjà en base"
Utilisez `--force` pour recharger :
```bash
python manage.py charger_taxref --force
```

### Connexion internet lente ou instable
Téléchargez d'abord TaxRef manuellement :
1. Aller sur : https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/17.0/menu
2. Télécharger le fichier ZIP
3. Extraire `TAXREFv17.txt`
4. Lancer :
```bash
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt
```

### Raspberry Pi trop lent
Testez d'abord avec un échantillon :
```bash
python manage.py charger_taxref --limit 50
```

## Utilisation dans l'application

Une fois importées, les espèces seront disponibles dans :
- Le formulaire de saisie d'observations
- Les filtres de recherche
- L'autocomplétion des champs "Espèce"

## Documentation complète

Pour plus de détails : `taxonomy/README_TAXREF.md`

## Mises à jour futures

TaxRef est mis à jour 2 fois par an. Pour mettre à jour :
```bash
python manage.py charger_taxref --taxref-version 18.0 --force
```
