# Git Workflow, Bonnes Pratiques et Checklists

Ce document est le guide de référence pour l'utilisation de Git dans le projet Observations Nids.

## 1. Workflow Git

Le projet utilise une version simplifiée de Git Flow pour organiser le développement.

### Structure des Branches

- **`production`** : Code actuellement déployé et stable.
- **`develop`** : Branche d'intégration où toutes les fonctionnalités terminées sont fusionnées et testées.
- **`feature/*`** : Branches temporaires pour le développement de nouvelles fonctionnalités (ex: `feature/nouvelle-carte`).
- **`hotfix/*`** : Branches temporaires pour les corrections urgentes en production.

### Schéma du Workflow

```
production (stable, déployé)
    ↑
develop (développement, tests)
    ↑
feature/nom-fonctionnalite (travail en cours)
```

### Processus Quotidien

1.  **Démarrer une nouvelle fonctionnalité :**
    ```bash
    # Se positionner sur develop et s'assurer qu'il est à jour
    git checkout develop
    git pull origin develop

    # Créer une branche pour la nouvelle fonctionnalité
    git checkout -b feature/nom-de-la-fonctionnalite
    ```

2.  **Travailler sur la fonctionnalité :**
    - Faites des commits atomiques et réguliers.
    - Utilisez des messages de commit clairs (ex: `feat: Ajout du formulaire de contact`).

3.  **Intégrer la fonctionnalité dans `develop` :**
    - Une fois la fonctionnalité terminée et testée localement, créez une **Pull Request (PR)** sur GitHub de votre branche `feature/...` vers la branche `develop`.
    - Attendez la validation de l'intégration continue (CI) et la revue de code.
    - Une fois la PR approuvée, fusionnez-la.

4.  **Mettre en Production :**
    - Périodiquement, une PR est créée de `develop` vers `production` pour déployer les nouvelles fonctionnalités stables.

---

## 2. Comment la CI Prévient les Régressions

L'intégration continue (CI), configurée dans `../ci-cd/README.md`, est votre filet de sécurité. À chaque Pull Request, elle exécute automatiquement `Ruff`, `Mypy`, et `Pytest`.

Si une de vos modifications casse une fonctionnalité existante qui est couverte par un test, la CI échouera et la Pull Request sera bloquée. Cela vous informe **immédiatement** d'une régression, avant même que le code ne soit fusionné.

Par exemple, si vous modifiez une API Python et que le format de la réponse JSON change, un test `pytest` qui vérifie ce format échouera, vous alertant que vous avez cassé le contrat avec le code JavaScript qui consomme cette API.

---

## 3. Checklist Avant de Merger une Pull Request

Utilisez cette checklist pour vérifier que votre code est prêt à être fusionné sans introduire de problèmes.

### ✅ 3.1. Vérifications de Base (Local)
- [ ] Le code compile sans erreur : `python manage.py check`
- [ ] Les migrations sont à jour : `python manage.py makemigrations --check`
- [ ] Les tests unitaires passent : `pytest`
- [ ] Le linter ne signale pas d'erreurs critiques : `ruff check .`
- [ ] L'analyseur de type ne signale pas d'erreurs : `mypy .`

### ✅ 3.2. Tests Fonctionnels Critiques
- [ ] **Authentification :** Connexion, déconnexion et permissions par rôle fonctionnent.
- [ ] **Saisie d'observation :** Le formulaire de création/modification fonctionne, y compris les validations.
- [ ] **Autocomplétion (Communes) :** La recherche de communes fonctionne et remplit correctement les champs (GPS, altitude) sans écraser les valeurs existantes.
- [ ] **Transcription OCR :** Le processus se lance et affiche les résultats (si applicable).

### ✅ 3.3. Interface Utilisateur
- [ ] **Responsive :** L'affichage est correct sur mobile, tablette et desktop.
- **Console Navigateur :** Aucune erreur JavaScript n'apparaît lors de l'utilisation de la fonctionnalité.

### ✅ 3.4. Documentation et Qualité
- [ ] **Messages de commit** descriptifs.
- [ ] **Code commenté** si la logique est complexe.
- [ ] **Documentation mise à jour** si des changements majeurs ont été apportés.

---

## 4. Commandes et Bonnes Pratiques Utiles

### Commandes

- **Synchroniser avec le distant :** `git pull origin <nom-branche>`
- **Voir les modifications :** `git status`, `git diff`
- **Voir l'historique :** `git log --oneline --graph --all`

### Bonnes Pratiques

- **Commits Atomiques :** Un commit doit représenter une seule modification logique.
- **Messages de Commit Conventionnels :** Préfixez vos messages avec `feat:`, `fix:`, `docs:`, `refactor:`, etc.
- **Ne Jamais Commiter de Secrets :** Le fichier `.env` est dans `.gitignore` pour cette raison.
- **Tester Avant de Pousser :** Lancez `pytest` localement avant de créer une Pull Request.

---

## 5. Exemple Pratique : de la Feature à la Production

Ce guide illustre le processus complet depuis la poussée (push) d'une branche de fonctionnalité (`feature branch`) jusqu'à sa mise en production, en passant par une branche de développement (`develop`).

### Étape 1 : Pousser la branche et créer la Pull Request (PR)

1.  **Pousser la branche sur GitHub :**
    ```bash
    # Après vos commits sur la branche 'feature/nom-de-la-feature'
    git push -u origin feature/nom-de-la-feature
    ```
    GitHub fournira un lien direct pour créer une Pull Request.

2.  **Créer la Pull Request vers `develop` :**
    *   Cliquez sur le lien fourni par `git push`.
    *   **Vérification importante :** Assurez-vous que la fusion se fait bien de votre branche `feature/...` vers la branche `develop`.
    *   Remplissez le titre et la description de la PR.
    *   Cliquez sur "Create pull request" et attendez le passage de la CI.

### Étape 2 : Tester sur le serveur de développement (ex: Raspberry Pi)

Une fois la PR fusionnée dans `develop`, il faut tester sur le serveur de pré-production.

1.  **Se connecter au serveur et mettre à jour :**
    ```bash
    ssh user@votre-raspberry-pi
    cd /chemin/vers/le/projet
    git checkout develop
    git pull origin develop
    ```

2.  **Mettre à jour l'environnement :**
    ```bash
    # Activer l'environnement virtuel
    source .venv/bin/activate
    # Installer les nouvelles dépendances
    pip install -r requirements-prod.txt
    # Appliquer les migrations
    python manage.py migrate
    # Redémarrer le serveur
    sudo systemctl restart apache2
    ```

### Étape 3 : Mettre en production

Si tout fonctionne correctement, une autre PR sera créée de `develop` vers `production` pour le déploiement final.

---

## 6. Gestion des Modifications Urgentes en Production (Hotfix)

Dans des cas exceptionnels, il peut être nécessaire d'intervenir directement sur le serveur de production (Raspberry Pi) pour corriger un bug critique. Voici la procédure pour sécuriser ces modifications et les réintégrer proprement dans le cycle de développement.

### Étape 1 : Sécuriser les modifications sur le serveur

Connectez-vous au serveur et naviguez vers le dossier du projet :
```bash
ssh user@serveur-prod
cd /chemin/vers/observations_nids
```

Avant toute chose, vérifiez l'état du dépôt :
```bash
git status
git diff
```

### Étape 2 : Créer une branche de sauvegarde

Ne committez jamais directement sur `production` ou `main` depuis le serveur. Créez une branche dédiée à ce correctif :

```bash
# Créer et basculer sur une branche de hotfix
git checkout -b hotfix/prod-urgent-fix-description

# Ajouter toutes les modifications
git add -A

# Committer avec un message explicite
git commit -m "fix: Modifications urgentes sur serveur production

- Détails des corrections...
- Sauvegarde avant intégration"
```

### Étape 3 : Pousser vers le dépôt central

```bash
# Pousser la branche vers GitHub/GitLab
git push -u origin hotfix/prod-urgent-fix-description
```

**En cas de problème d'identité ou d'authentification :**
```bash
# Configurer l'identité si demandé
git config user.name "Nom Prénom"
git config user.email "email@exemple.com"

# Vérifier l'URL du remote si le push est rejeté
git remote -v
```

### Étape 4 : Réintégration en local

Une fois la branche poussée, retournez sur votre machine de développement pour l'intégrer proprement :

1.  `git fetch origin`
2.  `git checkout develop`
3.  `git merge origin/hotfix/prod-urgent-fix-description`
4.  Gérer les conflits éventuels et lancer les tests.
