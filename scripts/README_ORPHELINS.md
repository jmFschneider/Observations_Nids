# Système de Gestion des Fichiers Orphelins

Ce système permet de détecter, vérifier, documenter et archiver les fichiers orphelins du projet.

## 📋 Fichiers du système

- `find_orphan_files.py` : Détecte les fichiers orphelins
- `verifier_orphelins.py` : Vérifie et permet de gérer les orphelins
- `archiver_orphelins.py` : Archive et supprime les fichiers
- `exceptions_orphelins.json` : Liste des exceptions connues
- `rapport_fichiers_orphelins.md` : Rapport de détection
- `verification_orphelins.md` : Rapport de vérification détaillé

## 🚀 Utilisation

### Étape 1 : Détecter les orphelins

```bash
python scripts/find_orphan_files.py
```

**Résultat** : Génère `scripts/rapport_fichiers_orphelins.md`

### Étape 2 : Vérifier et gérer

```bash
python scripts/verifier_orphelins.py
```

**Prompt** :
```
9 fichiers vraiment orphelins détectés.
Voulez-vous mettre à jour les exceptions ? (o/n):
```

**Options** :
- `o` : Mode interactif (recommandé)
- `n` : Juste générer le rapport

### Étape 3 : Mode interactif

Pour chaque fichier orphelin :

#### Si le fichier a déjà une exception :

```
[1/9] maintenance.html
  Exception actuelle : "Utilisé par Apache..." (Infrastructure)
  [m]odifier / [s]upprimer exception / [d]etruire fichier / [c]onserver :
```

**Options** :
- `m` : Modifier la raison/catégorie de l'exception
- `s` : Supprimer l'exception (le fichier redeviendra orphelin)
- `d` : Marquer le fichier pour suppression/archivage
- `c` : Conserver l'exception telle quelle

#### Si le fichier n'a pas d'exception :

```
[2/9] observation_card.html
  Exception actuelle : Aucune
  Marquer comme exception ou supprimer ? (o/n/d):
```

**Options** :
- `o` : Créer une exception (raison + catégorie)
- `n` : Ignorer (ne rien faire)
- `d` : Marquer pour suppression/archivage

### Étape 4 : Confirmation de suppression

Si vous avez marqué des fichiers avec `d` :

```
3 fichier(s) marqué(s) pour suppression.
Les fichiers seront archivés dans .archived_orphans/
Confirmer l'archivage et la suppression ? (o/n):
```

**Options** :
- `o` : Archiver et supprimer
- `n` : Annuler

## 📂 Structure d'archive

Les fichiers supprimés sont archivés dans :

```
.archived_orphans/
└── 2025-11-09_12h37/
    ├── README.md                    # Détails de l'archivage
    ├── restore.sh                   # Script de restauration
    └── [fichiers archivés avec leur structure]
```

## 🔄 Restauration

Si vous avez archivé par erreur :

```bash
# Depuis la racine du projet
bash .archived_orphans/2025-11-09_12h37/restore.sh
```

## 📝 Catégories d'exceptions

1. **Infrastructure** : Fichiers utilisés par le serveur web, déploiement
2. **Bibliothèque externe** : Templates de packages Django/Flask
3. **Inclusion dynamique** : Fichiers inclus via variables
4. **Déploiement** : Scripts/fichiers pour le déploiement
5. **Autre** : Autres raisons

## 📊 Exemple de workflow complet

```bash
# 1. Détection
python scripts/find_orphan_files.py

# 2. Vérification interactive
python scripts/verifier_orphelins.py

# Répondre 'o' au prompt
# Pour chaque fichier :
#   - Si à conserver : 'o' + documenter la raison
#   - Si à supprimer : 'd'
#   - Si incertain : 'n' (reporter la décision)

# 3. Confirmer la suppression
# Répondre 'o' pour archiver et supprimer

# 4. Vérifier l'archive
ls -la .archived_orphans/

# 5. Si besoin, restaurer
bash .archived_orphans/YYYY-MM-DD_HHhMM/restore.sh
```

## ⚠️ Précautions

1. **Vérifier manuellement** : Le script peut avoir des faux positifs
2. **Ne jamais forcer** : Si incertain, marquer comme exception
3. **Garder les archives** : Ne supprimer les archives qu'après vérification
4. **Tester en dev** : D'abord tester sur environnement de développement

## 🗑️ Nettoyage des archives

Après avoir vérifié que les fichiers archivés ne sont vraiment plus nécessaires :

```bash
# Supprimer une archive spécifique
rm -rf .archived_orphans/2025-11-09_12h37

# Supprimer toutes les archives (ATTENTION !)
rm -rf .archived_orphans/
```

## 🔧 Maintenance

### Mettre à jour les exceptions manuellement

Éditer `scripts/exceptions_orphelins.json` :

```json
{
  "exceptions": [
    {
      "file": "maintenance.html",
      "reason": "Utilisé par Apache lors de la mise en maintenance du site",
      "category": "Infrastructure"
    }
  ]
}
```

### Réexécuter une vérification

Les scripts sont réutilisables. Vous pouvez les lancer régulièrement :

```bash
# Mensuel
python scripts/find_orphan_files.py
python scripts/verifier_orphelins.py
```

## 📈 Évolution du système

### Le système peut nécessiter des ajustements si :

- Changement de framework (Django → Flask)
- Nouvelle structure de dossiers
- Nouveaux types de fichiers
- Changement de conventions de nommage

### Pour adapter :

1. Modifier `find_orphan_files.py` : Ajuster les patterns de détection
2. Modifier `verifier_orphelins.py` : Ajuster les recherches
3. Tester sur un échantillon avant déploiement complet
