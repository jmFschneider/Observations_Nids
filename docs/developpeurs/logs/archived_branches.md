# Branches archivées

Ce fichier documente les branches qui ont été archivées (mergées puis supprimées) pour garder le dépôt propre.

Les branches archivées sont conservées sous forme de **tags Git** et peuvent être restaurées à tout moment.

---

## 📦 Branches archivées

### 1. `feature/documentation`
- **Tag d'archive** : `archive/feature-documentation`
- **Dernier commit** : `29cacc3` - Correction de la documentation : recherche de liens morts, des absences de liens
- **Date de merge** : Octobre 2025
- **Description** : Refonte de la documentation avec deux branches distinctes (utilisateurs/développeurs)
- **Mergée dans** : `main`

### 2. `feature/droit_transcription`
- **Tag d'archive** : `archive/feature-droit-transcription`
- **Dernier commit** : `05e33c9` - feat: Ajouter favicon sur toutes les pages du site
- **Date de merge** : Octobre 2025
- **Description** : Ajout des droits de transcription et favicon sur toutes les pages
- **Mergée dans** : `main`

### 3. `optim/nettoyage`
- **Tag d'archive** : `archive/optim-nettoyage`
- **Dernier commit** : `4909b5b` - suppression des fichiers orphelins
- **Date de merge** : Octobre 2025
- **Description** : Nettoyage du dépôt - suppression des fichiers orphelins
- **Mergée dans** : `main`

---

## 🔍 Comment retrouver une branche archivée

### Lister toutes les branches archivées

```bash
git tag -l "archive/*"
```

### Voir les détails d'une branche archivée

```bash
git show archive/feature-documentation
```

### Restaurer une branche archivée

Si vous avez besoin de restaurer une branche archivée :

```bash
# Créer une nouvelle branche depuis le tag
git checkout -b feature/documentation archive/feature-documentation

# Ou juste consulter le code
git checkout archive/feature-documentation
```

### Consulter l'historique

```bash
# Voir les commits de la branche archivée
git log archive/feature-documentation

# Voir les différences avec main
git diff main..archive/feature-documentation
```

---

## 📌 Pousser les tags sur le dépôt distant

Pour sauvegarder les tags d'archive sur GitHub/GitLab :

```bash
# Pousser tous les tags d'archive
git push origin --tags

# Ou pousser un tag spécifique
git push origin archive/feature-documentation
```

---

## 🗑️ Supprimer définitivement un tag d'archive

**⚠️ Attention** : Cette action est irréversible si le tag n'a pas été poussé sur le dépôt distant.

```bash
# Supprimer le tag local
git tag -d archive/feature-documentation

# Supprimer le tag distant (si poussé)
git push origin --delete archive/feature-documentation
```

---

## 📋 Conventions de nommage

Les tags d'archive suivent le format :

```
archive/<nom-branche-normalisé>
```

Exemples :
- `feature/mon-feature` → `archive/feature-mon-feature`
- `fix/bug-123` → `archive/fix-bug-123`
- `optim/performance` → `archive/optim-performance`

---

**Dernière mise à jour** : Novembre 2025
**Mainteneur** : Équipe de développement
