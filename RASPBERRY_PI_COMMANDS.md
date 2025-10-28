# Commandes à exécuter sur le Raspberry Pi (Serveur Prod)

## Date: 2025-10-20

## Objectif
Créer une branche avec les modifications faites en urgence sur le serveur de production, puis pousser cette branche vers GitHub pour l'intégrer dans le développement local.

---

## Étape 1: Se connecter au Raspberry Pi et naviguer vers le projet

```bash
ssh pi@<adresse_ip_raspberry>
cd /chemin/vers/observations_nids
```

---

## Étape 2: Vérifier l'état actuel du dépôt

```bash
# Voir la branche actuelle
git branch

# Voir l'état des modifications
git status

# Voir les modifications non committées
git diff
```

---

## Étape 3: Créer une nouvelle branche pour sauvegarder les modifications

```bash
# Créer et basculer sur une nouvelle branche
git checkout -b prod/raspberry-pi-urgent-changes-20251020

# Vérifier qu'on est bien sur la nouvelle branche
git branch
```

---

## Étape 4: Ajouter et committer toutes les modifications

```bash
# Ajouter toutes les modifications
git add -A

# Voir ce qui sera committé
git status

# Créer le commit avec un message descriptif
git commit -m "fix: Modifications urgentes faites sur le serveur de production

- Corrections appliquées directement sur le Raspberry Pi
- Sauvegarde avant intégration dans la branche de développement

🔧 Modifications de production
Date: 2025-10-20"
```

---

## Étape 5: Pousser la branche vers GitHub

```bash
# Pousser la nouvelle branche vers GitHub
git push -u origin prod/raspberry-pi-urgent-changes-20251020

# Vérifier que le push a réussi
git branch -vv
```

---

## Étape 6: Optionnel - Retourner à la branche précédente

Si vous voulez retourner à la branche sur laquelle vous étiez avant:

```bash
# Voir toutes les branches
git branch -a

# Retourner à la branche précédente (remplacer <nom_branche> par la branche voulue)
git checkout <nom_branche>
```

---

## Notes importantes

⚠️ **Avant de commencer:**
- Assurez-vous d'avoir une connexion internet stable
- Vérifiez que vous avez les droits de push sur le dépôt GitHub
- Notez bien le nom de la branche créée pour l'intégration locale

✅ **Après le push:**
- Notez le nom exact de la branche créée
- Revenez me voir pour intégrer ces modifications dans la branche locale `feature/reinitialisation_mdp`

---

## En cas de problème

### Si git demande de configurer l'identité:
```bash
git config user.name "Votre Nom"
git config user.email "votre.email@example.com"
```

### Si le push est rejeté (problème d'authentification):
```bash
# Vérifier la configuration du remote
git remote -v

# Mettre à jour l'URL si nécessaire (utiliser HTTPS avec token ou SSH)
git remote set-url origin <nouvelle_url>
```

### Si vous voulez annuler et recommencer:
```bash
# Revenir à la branche précédente
git checkout <branche_precedente>

# Supprimer la branche créée
git branch -D prod/raspberry-pi-urgent-changes-20251020
```

---

## Prochaines étapes (à faire ensuite sur Windows)

Une fois la branche poussée sur GitHub, retournez sur votre machine Windows pour:
1. Récupérer la branche depuis GitHub
2. L'intégrer dans `feature/reinitialisation_mdp`
3. Résoudre les conflits éventuels
4. Préparer la mise à jour de la branche main
