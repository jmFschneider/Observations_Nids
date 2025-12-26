# Guide de Migration des Utilisateurs

Ce guide explique comment migrer les utilisateurs de l'ancienne base de données vers la nouvelle base Docker Ubuntu.

## Table des matières
1. [Installation des scripts dans l'ancien environnement](#installation-des-scripts-dans-lancien-environnement)
2. [Approche Django (Recommandée)](#approche-django-recommandée)
3. [Approche SQL/phpMyAdmin](#approche-sqlphpmyadmin)
4. [Comparaison des approches](#comparaison-des-approches)

---

## Installation des scripts dans l'ancien environnement

Vous n'avez **pas besoin de faire `git pull`** sur l'ancien environnement ! Vous pouvez simplement copier le fichier `export_users.py`.

### Option 1: Copie manuelle (Recommandée pour l'ancien environnement)

**Étape 1: Créer la structure de dossiers** (si elle n'existe pas déjà):

```powershell
# Dans le dossier de votre ancien projet
cd accounts
mkdir management\commands
```

**Étape 2: Créer les fichiers `__init__.py`** (marqueurs Python obligatoires):

```powershell
# Créer les fichiers vides
type nul > management\__init__.py
type nul > management\commands\__init__.py
```

**Étape 3: Copier le fichier**:

Vous avez deux options pour copier `export_users.py`:

**Option A - Copie depuis ce projet** (si sur la même machine):
```powershell
# Depuis le répertoire du nouveau projet
copy accounts\management\commands\export_users.py C:\chemin\vers\ancien_projet\accounts\management\commands\export_users.py
```

**Option B - Copie manuelle**:
1. Ouvrir `accounts/management/commands/export_users.py` dans ce projet
2. Copier tout le contenu
3. Créer un nouveau fichier dans l'ancien projet: `accounts/management/commands/export_users.py`
4. Coller le contenu

**Étape 4: Vérifier la structure finale**:

Votre dossier `accounts/` devrait ressembler à ceci:

```
accounts/
├── __init__.py
├── models.py
├── views.py
├── ...
└── management/
    ├── __init__.py
    └── commands/
        ├── __init__.py
        └── export_users.py
```

**Étape 5: Vérifier l'installation**:

```powershell
# Dans l'ancien projet
python manage.py export_users --help
```

Si vous voyez l'aide de la commande, c'est bon ! ✅

**Exemple de sortie attendue**:
```
usage: manage.py export_users [-h] [--output OUTPUT]

Exporte tous les utilisateurs avec leurs groupes, permissions et mots de passe hashés

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Fichier de sortie (défaut: users_export.json)
```

### Option 2: Via Git (Pour le nouvel environnement)

Pour le **nouvel environnement Docker Ubuntu**, vous pouvez simplement faire:

```bash
git pull origin main
```

Les fichiers `export_users.py` et `import_users.py` seront automatiquement disponibles.

### Avantages de la copie manuelle

- ✅ **Pas de git pull** nécessaire
- ✅ **Pas de risque** de conflits de merge
- ✅ **Rapide** - juste un fichier à copier
- ✅ **Indépendant** - fonctionne sur n'importe quelle version du projet
- ✅ **Pas de modification** de l'ancien environnement en production

---

## Approche Django (Recommandée) ✅

### Avantages
- ✅ Préserve automatiquement les mots de passe hashés
- ✅ Gère les relations (groupes, permissions)
- ✅ Respecte les contraintes du modèle
- ✅ Sûr et maintenable
- ✅ Compatible avec les migrations futures

### Étape 0: Installer le script d'export (si nécessaire)

Si vous n'avez pas encore le script `export_users.py` dans votre ancien environnement, consultez la section [Installation des scripts dans l'ancien environnement](#installation-des-scripts-dans-lancien-environnement).

💡 **Astuce**: Vous pouvez simplement copier le fichier sans faire de `git pull` !

### Étape 1: Export depuis l'ancienne base de données

Sur votre **ancien environnement** (Windows):

```bash
# Activer l'environnement virtuel
.venv\Scripts\activate

# Exporter les utilisateurs
python manage.py export_users --output users_backup.json
```

Le fichier `users_backup.json` sera créé avec tous les utilisateurs, leurs mots de passe hashés, groupes et permissions.

⚠️ **IMPORTANT**: Ce fichier contient des données sensibles. Gardez-le sécurisé et supprimez-le après l'import.

### Étape 2: Transférer le fichier

Transférez `users_backup.json` vers votre **nouvel environnement Docker Ubuntu**:

```bash
# Depuis Windows vers Docker
docker cp users_backup.json observations_nids_web:/app/users_backup.json
```

### Étape 3: Import dans la nouvelle base

Dans votre **nouvel environnement Docker**:

```bash
# Entrer dans le conteneur
docker exec -it observations_nids_web bash

# Importer les utilisateurs
python manage.py import_users --input users_backup.json

# Ou pour mettre à jour les utilisateurs existants:
python manage.py import_users --input users_backup.json --update-existing

# Ou pour ignorer les utilisateurs existants:
python manage.py import_users --input users_backup.json --skip-existing
```

### Étape 4: Vérification

```bash
# Vérifier le nombre d'utilisateurs
python manage.py shell
>>> from accounts.models import Utilisateur
>>> print(f"Nombre d'utilisateurs: {Utilisateur.objects.count()}")
>>> print(f"Superutilisateurs: {Utilisateur.objects.filter(is_superuser=True).count()}")
>>> exit()
```

### Étape 5: Nettoyage

```bash
# Supprimer le fichier de backup (contient des données sensibles)
rm users_backup.json

# Sur Windows également
del users_backup.json
```

---

## Approche SQL/phpMyAdmin

### ⚠️ Avertissements
- Approche plus risquée
- Nécessite une attention particulière aux clés étrangères
- Peut poser problème si les structures diffèrent

### Avec phpMyAdmin

#### Étape 1: Export depuis l'ancienne base

1. Ouvrir phpMyAdmin sur l'ancien serveur (http://localhost:8081)
2. Sélectionner votre base de données
3. Aller dans l'onglet "Export"
4. Sélectionner les tables suivantes:
   - `accounts_utilisateur` (table des utilisateurs)
   - `auth_group` (groupes)
   - `auth_permission` (permissions)
   - `accounts_utilisateur_groups` (relation utilisateurs-groupes)
   - `accounts_utilisateur_user_permissions` (relation utilisateurs-permissions)

5. Options d'export:
   - Format: SQL
   - ✅ Structure et données
   - ✅ "DROP TABLE" (pour éviter les conflits)
   - ✅ "IF NOT EXISTS"

6. Cliquer sur "Exécuter" pour télécharger le fichier SQL

#### Étape 2: Import dans la nouvelle base

1. Ouvrir phpMyAdmin sur le nouveau serveur Docker (http://localhost:8081)
2. Sélectionner la nouvelle base de données
3. Aller dans l'onglet "Import"
4. Choisir le fichier SQL exporté
5. Cliquer sur "Exécuter"

⚠️ **Attention**:
- Vérifiez qu'il n'y a pas de conflits d'ID
- Les AUTO_INCREMENT doivent être bien gérés
- Les contraintes de clés étrangères peuvent poser problème

### Avec SQL pur

#### Étape 1: Export

```bash
# Sur l'ancien serveur
mysqldump -u root -p --no-create-info \
  --tables accounts_utilisateur auth_group auth_permission \
  accounts_utilisateur_groups accounts_utilisateur_user_permissions \
  observations_nids > users_export.sql
```

#### Étape 2: Import

```bash
# Sur le nouveau serveur Docker
docker exec -i observations_nids_db mysql -u root -p observations_nids < users_export.sql
```

### Vérification SQL

```sql
-- Nombre d'utilisateurs
SELECT COUNT(*) FROM accounts_utilisateur;

-- Superutilisateurs
SELECT username, email, is_superuser, is_staff
FROM accounts_utilisateur
WHERE is_superuser = 1;

-- Utilisateurs avec leurs rôles
SELECT username, email, role, est_valide
FROM accounts_utilisateur;
```

---

## Comparaison des approches

| Critère | Django Commands | SQL/phpMyAdmin |
|---------|----------------|----------------|
| **Sécurité** | ✅ Excellent | ⚠️ Risqué |
| **Facilité** | ✅ Simple | ⚠️ Complexe |
| **Mots de passe** | ✅ Auto | ⚠️ Manuel |
| **Relations** | ✅ Gérées | ⚠️ À gérer |
| **Maintenabilité** | ✅ Excellent | ❌ Faible |
| **Validation** | ✅ Automatique | ❌ Aucune |
| **Rollback** | ✅ Transaction | ⚠️ Manuel |

### Recommandation finale

**Utilisez l'approche Django Commands** sauf si:
- Vous n'avez pas accès à Django sur l'un des serveurs
- Vous avez une expertise SQL avancée
- Vous avez des besoins très spécifiques

---

## Dépannage

### Problème: "Permission denied"

```bash
# Vérifier les permissions du fichier
ls -la users_backup.json
chmod 644 users_backup.json
```

### Problème: "User already exists"

```bash
# Option 1: Ignorer les utilisateurs existants
python manage.py import_users --skip-existing

# Option 2: Mettre à jour les utilisateurs existants
python manage.py import_users --update-existing
```

### Problème: "Permission codename not found"

Cela signifie qu'une permission n'existe pas encore. Exécutez d'abord:

```bash
python manage.py migrate
```

### Problème: Encodage de caractères

Si vous avez des erreurs d'encodage avec des caractères accentués:

```bash
# Le script utilise UTF-8 par défaut
# Si nécessaire, vérifiez l'encodage du fichier JSON
file -i users_backup.json
```

---

## Sécurité

### ⚠️ Points importants

1. **Fichiers de backup**: Contiennent des mots de passe hashés
   - Ne les committez JAMAIS dans Git
   - Supprimez-les après utilisation
   - Stockez-les dans un endroit sécurisé temporairement

2. **Transmission**:
   - Utilisez SFTP/SCP pour transférer entre serveurs
   - Évitez les emails ou stockage cloud non chiffré

3. **Permissions**:
   ```bash
   chmod 600 users_backup.json  # Lecture/écriture propriétaire uniquement
   ```

4. **Après import**:
   ```bash
   # Supprimer le fichier
   shred -u users_backup.json  # Linux (écrasement sécurisé)
   del users_backup.json       # Windows
   ```

---

## Scripts créés

Les scripts suivants ont été créés dans `accounts/management/commands/`:

1. **export_users.py**: Exporte les utilisateurs vers JSON
2. **import_users.py**: Importe les utilisateurs depuis JSON

Pour voir les options disponibles:

```bash
python manage.py export_users --help
python manage.py import_users --help
```
