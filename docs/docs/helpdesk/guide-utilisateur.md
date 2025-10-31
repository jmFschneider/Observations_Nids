# Guide utilisateur : Système de support (Helpdesk)

## 🎯 Objectif

Le système de support permet de signaler des problèmes, demander de l'aide ou proposer des améliorations pour l'application Observations Nids.

---

## 📋 Accès au système de support

### Depuis la page d'accueil

1. Connectez-vous à l'application
2. Sur la page d'accueil, cliquez sur **"Support"** dans la barre de navigation en haut

### URL directe

Vous pouvez également accéder directement via : `https://votre-site.fr/helpdesk/`

---

## 🎫 Créer un nouveau ticket

### Étape 1 : Accéder au formulaire

1. Cliquez sur **"Soumettre un ticket"** dans le menu de gauche
2. Ou cliquez sur **"Créer un ticket"** depuis le tableau de bord

### Étape 2 : Remplir le formulaire

Le formulaire contient les champs suivants :

#### **Catégorie** (obligatoire)
Choisissez la catégorie qui correspond le mieux à votre demande :

- **🐛 Bug** : Signaler un problème technique ou un dysfonctionnement
- **✨ Nouvelle fonctionnalité** : Proposer une amélioration ou une nouvelle fonction
- **❓ Support/Question** : Poser une question ou demander de l'aide
- **📚 Documentation** : Signaler un problème dans la documentation ou demander des clarifications

#### **Résumé du problème** (obligatoire)
Un titre court et clair décrivant votre demande.

**Exemples :**
- ✅ "Impossible de sauvegarder une observation"
- ✅ "Erreur lors de l'upload d'images"
- ❌ "Ça marche pas" (trop vague)

#### **Description** (obligatoire)
Décrivez en détail votre problème ou votre demande.

**Pour un bug, incluez :**
- Ce que vous essayiez de faire
- Ce qui s'est passé
- Ce que vous attendiez
- Les étapes pour reproduire le problème
- Des captures d'écran si possible

**Exemple de bonne description :**
```
Étapes pour reproduire :
1. Je vais sur "Nouvelle observation"
2. Je remplis tous les champs
3. Je clique sur "Enregistrer"
4. J'obtiens une erreur "500 Server Error"

Ce qui devrait se passer :
L'observation devrait être enregistrée et je devrais être redirigé vers la liste.

Navigateur : Chrome 118
Date : 30/10/2024 14:30
```

#### **Priorité** (optionnel)
Indiquez l'urgence de votre demande :

- **🔴 Critique** : Bloquant, empêche l'utilisation de l'application
- **🟠 Haute** : Important mais des solutions de contournement existent
- **🟡 Normale** : Problème gênant mais non bloquant
- **🟢 Basse** : Amélioration souhaitée, pas urgent

#### **Résolution souhaitée le** (optionnel)
Si vous avez une date limite, indiquez-la ici.

#### **Fichiers joints** (optionnel)
Vous pouvez joindre des captures d'écran, documents ou fichiers pour illustrer votre demande.

### Étape 3 : Envoyer le ticket

Cliquez sur **"Soumettre le ticket"** en bas du formulaire.

Vous recevrez un **email de confirmation** avec le numéro de votre ticket.

---

## 📊 Suivre vos tickets

### Tableau de bord

Le tableau de bord affiche :

- **Vos tickets ouverts** : Tickets en cours de traitement
- **Statistiques** : Nombre de tickets par statut
- **Tickets récents** : Derniers tickets créés

### Voir un ticket

1. Cliquez sur un ticket dans la liste
2. Vous verrez :
   - Le statut actuel (Ouvert, En cours, Résolu, Fermé)
   - L'historique des échanges
   - Les pièces jointes
   - L'assignation (qui traite le ticket)

### Répondre à un ticket

1. Ouvrez votre ticket
2. Faites défiler jusqu'à la section **"Ajouter un suivi"**
3. Rédigez votre message
4. Cliquez sur **"Ajouter un suivi"**

Votre réponse sera ajoutée à l'historique et une notification sera envoyée à l'équipe support.

---

## 🔔 Notifications par email

Vous recevrez automatiquement un email lorsque :

- ✅ Votre ticket est créé (avec numéro de référence)
- ✅ Quelqu'un répond à votre ticket
- ✅ Le statut de votre ticket change
- ✅ Votre ticket est résolu

**Format de l'email :**
```
Sujet : [Ticket #123] Nouveau ticket : Impossible de sauvegarder
De : observationnids@gmail.com

Bonjour,

Votre ticket a été créé avec succès.

Numéro : #123
Catégorie : Bug
Statut : Ouvert

Pour voir ou répondre à ce ticket :
https://votre-site.fr/helpdesk/tickets/bug-123/

Merci,
L'équipe Observations Nids
```

### Répondre directement par email

Vous pouvez répondre directement à l'email de notification. Votre réponse sera automatiquement ajoutée au ticket.

---

## 📖 Statuts des tickets

| Statut | Signification |
|--------|---------------|
| **🆕 Ouvert** | Ticket créé, en attente de prise en charge |
| **👀 En cours** | Un membre de l'équipe traite votre demande |
| **⏸️ En attente** | En attente d'informations supplémentaires de votre part |
| **✅ Résolu** | Le problème est résolu, en attente de votre confirmation |
| **🔒 Fermé** | Ticket terminé et archivé |
| **❌ Rejeté** | La demande a été refusée (avec explication) |

---

## 💡 Bonnes pratiques

### ✅ À faire

- **Soyez précis** : Plus votre description est détaillée, plus vite nous pourrons vous aider
- **Un ticket = un problème** : Si vous avez plusieurs problèmes, créez plusieurs tickets
- **Joignez des captures d'écran** : Une image vaut mille mots
- **Répondez rapidement** : Si on vous demande des informations, répondez dès que possible
- **Confirmez la résolution** : Quand le problème est résolu, confirmez-le

### ❌ À éviter

- Créer plusieurs tickets pour le même problème (utilisez le suivi à la place)
- Mettre "Critique" pour tout (réservez ce statut aux vrais blocages)
- Écrire en majuscules (ÇA DONNE L'IMPRESSION DE CRIER)
- Oublier de répondre quand on vous demande des informations

---

## 🔍 Rechercher dans les tickets

### Barre de recherche

1. Utilisez la barre de recherche en haut du tableau de bord
2. Tapez des mots-clés (ex: "observation", "erreur", "upload")
3. Les résultats s'afficheront automatiquement

### Filtres

Vous pouvez filtrer les tickets par :

- **Statut** : Ouvert, En cours, Résolu, etc.
- **Catégorie** : Bug, Fonctionnalité, Support, Documentation
- **Assigné à** : Membre de l'équipe traitant le ticket
- **Date** : Date de création

---

## ❓ Questions fréquentes

### Combien de temps avant qu'on réponde à mon ticket ?

Nous nous efforçons de répondre :
- **Tickets critiques** : Dans les 4 heures ouvrées
- **Tickets normaux** : Dans les 24 heures ouvrées
- **Tickets basse priorité** : Dans les 48-72 heures

### Puis-je modifier un ticket après l'avoir créé ?

Non, vous ne pouvez pas modifier le ticket directement. Si vous avez des informations à ajouter, utilisez la fonction **"Ajouter un suivi"** pour compléter votre demande initiale.

### Comment fermer un ticket ?

Seul un administrateur peut fermer un ticket. Lorsque votre problème est résolu, le ticket passera en statut "Résolu". Si vous confirmez que tout fonctionne, il sera ensuite fermé.

### Puis-je rouvrir un ticket fermé ?

Si le problème réapparaît, créez un **nouveau ticket** en faisant référence à l'ancien (ex: "Réapparition du bug #123"). Cela permet un meilleur suivi.

### Je n'ai pas reçu l'email de confirmation

Vérifiez :
1. Votre dossier **spam/courrier indésirable**
2. Que votre **adresse email** dans votre profil est correcte
3. Les **filtres** de votre messagerie

Si vous ne le trouvez toujours pas, contactez un administrateur.

---

## 📞 Contact direct

En cas d'urgence critique (site totalement inaccessible), vous pouvez contacter directement :

- **Email** : admin@observations-nids.fr
- **Téléphone** : [Numéro d'urgence]

**Note** : Privilégiez le système de tickets pour un meilleur suivi et une meilleure traçabilité.

---

## 📚 Ressources supplémentaires

- [Documentation générale](../aide_utilisateurs/README.md)
- [Guide de navigation](../aide_utilisateurs/01_navigation_generale.md)
- [Saisie d'observations](../aide_utilisateurs/02_saisie_nouvelle_observation.md)
- [Guide développeur Helpdesk](guide-developpeur.md)
