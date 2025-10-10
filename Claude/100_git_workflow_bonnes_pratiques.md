# Git Workflow - Bonnes Pratiques

## Vue d'ensemble

Ce document décrit le workflow Git recommandé pour le projet Observations Nids, basé sur une version simplifiée de Git Flow.

## Structure des branches

### Branches principales

- **`production`** : Code actuellement déployé en production (stable)
- **`develop`** : Branche de développement principal, intègre toutes les fonctionnalités terminées
- **`feature/*`** : Branches temporaires pour le développement de nouvelles fonctionnalités
- **`hotfix/*`** : Branches temporaires pour les corrections urgentes en production

### Schéma du workflow

```
production (stable, déployé)
    ↓
develop (développement, tests)
    ↓
feature/nom-fonctionnalite (travail en cours)
```

## Workflow quotidien

### 1. Configuration initiale (une seule fois)

```bash
# Commiter l'état actuel sur production
git add .
git commit -m "État stable avant création branche develop"

# Créer la branche develop depuis production
git checkout -b develop
git push -u origin develop

# Retourner sur production
git checkout production
```

### 2. Développer une nouvelle fonctionnalité

```bash
# Se positionner sur develop
git checkout develop

# Créer une branche feature
git checkout -b feature/nom-de-la-fonctionnalite

# Travailler et commiter régulièrement
git add .
git commit -m "Description claire des changements"

# Pousser la branche (optionnel, pour backup ou collaboration)
git push -u origin feature/nom-de-la-fonctionnalite
```

### 3. Intégrer la fonctionnalité dans develop

```bash
# Se positionner sur develop
git checkout develop

# S'assurer d'avoir la dernière version
git pull origin develop

# Merger la feature
git merge feature/nom-de-la-fonctionnalite

# Pousser sur le serveur
git push origin develop

# Supprimer la branche feature (optionnel)
git branch -d feature/nom-de-la-fonctionnalite
git push origin --delete feature/nom-de-la-fonctionnalite
```

### 4. Tester sur develop

- Déployer `develop` sur un environnement de test (si disponible)
- Tester toutes les fonctionnalités
- Corriger les bugs directement sur `develop` ou créer des branches `bugfix/*`

### 5. Mettre en production

```bash
# Se positionner sur production
git checkout production

# Merger develop dans production
git merge develop

# Pousser sur le serveur
git push origin production

# Déployer sur le serveur de production (Raspberry Pi)
# Suivre les instructions de docs/DEPLOIEMENT_PI.md
```

## Cas particuliers

### Correction urgente en production (hotfix)

Si un bug critique doit être corrigé immédiatement en production :

```bash
# Créer une branche hotfix depuis production
git checkout production
git checkout -b hotfix/correction-bug-critique

# Corriger le bug
git add .
git commit -m "Fix: correction bug critique"

# Merger dans production
git checkout production
git merge hotfix/correction-bug-critique
git push origin production

# Merger aussi dans develop pour ne pas perdre la correction
git checkout develop
git merge hotfix/correction-bug-critique
git push origin develop

# Supprimer la branche hotfix
git branch -d hotfix/correction-bug-critique
```

### Travailler sur plusieurs fonctionnalités en parallèle

```bash
# Fonctionnalité 1
git checkout develop
git checkout -b feature/export-donnees
# ... travailler ...

# Passer à une autre fonctionnalité sans merger la première
git checkout develop
git checkout -b feature/amelioration-interface
# ... travailler ...

# Merger dans l'ordre souhaité
git checkout develop
git merge feature/export-donnees
git merge feature/amelioration-interface
```

### Annuler un merge non poussé

Si vous venez de merger et que vous vous rendez compte d'une erreur :

```bash
# Annuler le dernier commit (le merge)
git reset --hard HEAD~1
```

**⚠️ Attention : Ne jamais utiliser `reset --hard` après un `push` !**

## Commandes utiles

### Voir l'état actuel

```bash
# Voir la branche actuelle et les fichiers modifiés
git status

# Voir l'historique des commits
git log --oneline --graph --all

# Voir les différences non commitées
git diff

# Voir les branches locales
git branch

# Voir toutes les branches (locales et distantes)
git branch -a
```

### Gérer les branches

```bash
# Créer une branche
git checkout -b nom-branche

# Changer de branche
git checkout nom-branche

# Supprimer une branche locale
git branch -d nom-branche

# Supprimer une branche distante
git push origin --delete nom-branche
```

### Synchroniser avec le serveur

```bash
# Récupérer les changements sans les appliquer
git fetch origin

# Récupérer et appliquer les changements
git pull origin nom-branche

# Envoyer les commits locaux
git push origin nom-branche
```

## Bonnes pratiques

### Messages de commit

Utilisez des messages clairs et descriptifs :

```bash
# ✅ Bon
git commit -m "Ajout formulaire d'export des observations"
git commit -m "Fix: correction calcul date de ponte"
git commit -m "Refactor: simplification du code de validation"

# ❌ Mauvais
git commit -m "update"
git commit -m "fix bug"
git commit -m "wip"
```

**Format recommandé :**
- `feat:` pour une nouvelle fonctionnalité
- `fix:` pour une correction de bug
- `refactor:` pour une refactorisation
- `docs:` pour la documentation
- `test:` pour les tests
- `style:` pour le formatage

### Commits fréquents

- Commiter régulièrement (plusieurs fois par jour)
- Faire des petits commits logiques
- Un commit = une modification cohérente

### Ne jamais commiter

- Fichiers de configuration locale (`.env`, `settings_local.py`)
- Fichiers temporaires (`.pyc`, `__pycache__`, etc.)
- Dépendances (venv, node_modules)
- Secrets et mots de passe

→ Ces fichiers doivent être dans `.gitignore`

### Tester avant de merger

- Toujours tester sur `develop` avant de merger vers `production`
- Vérifier que l'application démarre correctement
- Tester les fonctionnalités ajoutées/modifiées

## Résolution de conflits

Si Git signale un conflit lors d'un merge :

```bash
# 1. Git marque les fichiers en conflit
git status  # Voir les fichiers en conflit

# 2. Éditer manuellement chaque fichier en conflit
# Chercher les marqueurs : <<<<<<<, =======, >>>>>>>
# Choisir la version à garder ou combiner les deux

# 3. Marquer les conflits comme résolus
git add fichier-resolu.py

# 4. Finaliser le merge
git commit -m "Merge: résolution des conflits"
```

## Pour aller plus loin

### Alias Git utiles

Ajouter dans `~/.gitconfig` :

```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --all --decorate
    last = log -1 HEAD
```

### Outils visuels

- **GitKraken** : Interface graphique complète
- **GitHub Desktop** : Simple et intuitif
- **VSCode** : Extension Git intégrée

## Références

- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Documentation Git officielle](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
