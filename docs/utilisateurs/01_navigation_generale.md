# Guide utilisateur - Navigation générale

## Bienvenue sur Observations Nids !

Ce guide vous accompagne dans la découverte de l'application, de l'inscription jusqu'à la correction des fiches d'observation.

---

## Table des matières

[TOC]

---

## 1. Inscription et connexion

### Première visite - Créer un compte

1. **Accéder à la page d'inscription**
   - Cliquez sur "S'inscrire" ou "Créer un compte" sur la page d'accueil

2. **Remplir le formulaire d'inscription**
   - **Nom d'utilisateur** : Choisissez un identifiant unique
   - **Email** : Votre adresse email
   - **Mot de passe** : Minimum 8 caractères, lettres et chiffres recommandés
   - **Confirmation du mot de passe** : Saisissez à nouveau votre mot de passe

3. **Validation du compte**
   - Après inscription, vous serez redirigé vers la page de connexion
   - Votre compte est actif immédiatement

### Se connecter

1. **Page de connexion**
   - Saisissez votre nom d'utilisateur
   - Saisissez votre mot de passe
   - Cliquez sur "Se connecter"

2. **Mot de passe oublié**
   - Cliquez sur "Mot de passe oublié ?"
   - Suivez les instructions envoyées par email

### Se déconnecter

- Cliquez sur votre nom d'utilisateur en haut à droite
- Sélectionnez "Déconnexion"

---

## 2. Page d'accueil et navigation

### Menu principal

Une fois connecté, vous accédez au tableau de bord avec plusieurs sections :

```
┌─────────────────────────────────────────────────┐
│  Observations Nids            [Votre nom] ▼     │
├─────────────────────────────────────────────────┤
│  🏠 Accueil                                      │
│                                                 │
│  FICHES OBSERVATIONS                            │
│  📝 Nouvelle fiche                              │
│  📋 Liste des fiches                            │
│                                                 │
│  ✏️  Transcription                              │
│  📊 Statistiques                                │
│  🎫 Support                                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Barre de navigation latérale

- **Accueil** : Retour au tableau de bord
- **Fiches Observations** : Créer ou consulter des fiches
  - Nouvelle fiche
  - Liste des fiches
- **Transcription** : Accès à l'outil de transcription automatique
- **Mon compte** : Paramètres de votre profil
- **Aide** : Documentation et tutoriels

💡 **Nouveau** : Le menu actif est surligné en bleu clair pour faciliter la navigation !

---

## 3. Les différentes sections

### 📝 Nouvelle fiche

**Quand l'utiliser** : Vous souhaitez enregistrer une nouvelle observation de terrain.

**Accès** :
- Menu "Fiches Observations" → "Nouvelle fiche"
- Bouton rapide sur l'accueil

💡 **Astuce** : Sur mobile/tablette, une barre d'actions flottante reste accessible en bas d'écran pour un accès rapide aux boutons "Enregistrer" et "Valider" !

Voir le guide détaillé : [Saisir une nouvelle fiche](./02_saisie_nouvelle_observation.md)

---

### 📋 Liste des fiches

**Quand l'utiliser** : Visualiser, rechercher ou filtrer les observations existantes.

**Fonctionnalités** :
- **Liste des fiches** : Affichage avec Fiche ID, N° perso de fiche, Espèce, Commune
- **Filtres** : Par date, espèce, lieu, observateur
- **Recherche de communes** : 🆕 Recherche optimisée par pertinence
  - Les communes courtes (Ur, Ger, Eu) apparaissent en premier
  - Tri intelligent : match exact → commence par → contient
- **Export** : Télécharger les données (CSV, JSON)

**Actions possibles** :
- Voir les détails d'une fiche (cliquer sur le Fiche ID)
- Modifier vos propres fiches (bouton "Corriger")
- Consulter l'historique des modifications

---

### ✏️ Corriger des fiches (Transcription)

**Quand l'utiliser** : Vous avez scanné des carnets d'observations papier et souhaitez les transcrire/corriger.

**Workflow** :
1. Upload des images de carnets scannés
2. Traitement automatique par IA (Gemini)
3. Révision et correction des fiches générées

Voir le guide détaillé : [Corriger des fiches (Transcription)](./03_correction_transcription.md)

---

### 📊 Statistiques

**Quand l'utiliser** : Analyser les données d'observations.

**Informations disponibles** :
- Nombre d'observations par espèce
- Répartition géographique
- Évolution temporelle
- Taux de réussite des nids

---

## 4. Cycle de vie d'une fiche d'observation

Une fiche d'observation passe par différents états au cours de son cycle de vie :

```
┌─────────────┐
│   NOUVEAU   │  ← Fiche créée, en cours de saisie
└──────┬──────┘
       ↓
┌─────────────┐
│ EN_EDITION  │  ← Fiche sauvegardée, modifications possibles
└──────┬──────┘
       ↓
┌─────────────┐
│  EN_COURS   │  ← Fiche soumise pour correction/révision
└──────┬──────┘
       ↓
┌─────────────┐
│   VALIDEE   │  ← Fiche complète et validée
└─────────────┘
```

### États détaillés

| État | Description | Qui peut modifier | Actions disponibles |
|------|-------------|-------------------|---------------------|
| **NOUVEAU** | Fiche juste créée | Auteur uniquement | Saisie des informations |
| **EN_EDITION** | Fiche sauvegardée | Auteur uniquement | Modification, ajout d'observations |
| **EN_COURS** | Fiche soumise | Auteur + Correcteurs | Correction, validation |
| **VALIDEE** | Fiche complète | Administrateurs | Consultation uniquement |

---

## 5. Rôles et permissions

### Observateur (Rôle par défaut)

**Permissions** :
- ✅ Créer de nouvelles fiches d'observation
- ✅ Modifier ses propres fiches (états NOUVEAU et EN_EDITION)
- ✅ Consulter toutes les observations
- ✅ Soumettre ses fiches pour correction
- ❌ Modifier les fiches d'autres utilisateurs
- ❌ Valider des fiches

**Restrictions** :
- Une fois qu'une fiche est soumise (EN_COURS), vous ne pouvez plus la modifier seul
- Seuls les correcteurs ou administrateurs peuvent intervenir

---

### Correcteur

**Permissions supplémentaires** :
- ✅ Corriger les fiches en statut EN_COURS
- ✅ Utiliser l'outil de transcription
- ✅ Modifier les fiches de tous les utilisateurs
- ✅ Ajouter des remarques de correction

---

### Administrateur

**Toutes les permissions** :
- ✅ Accès complet à toutes les fiches
- ✅ Modifier les fiches à n'importe quel statut
- ✅ Gérer les utilisateurs
- ✅ Accès aux statistiques avancées
- ✅ Configuration du système

---

## Conseils pratiques

### 🎯 Bonnes pratiques

1. **Sauvegardez régulièrement** : Utilisez le bouton "Enregistrer" fréquemment pour ne pas perdre vos données

2. **Vérifiez avant de soumettre** : Une fois soumise, une fiche ne peut plus être modifiée par vous seul

3. **Utilisez les remarques** : Ajoutez des notes pour vous-même ou les correcteurs

4. **Complétez la localisation** : Une géolocalisation précise facilite l'analyse

5. **Consultez l'historique** : En cas de doute, l'historique des modifications montre tous les changements

### ⚡ Raccourcis utiles

- **Ctrl + S** : Sauvegarder (sur certains formulaires)
- **Échap** : Fermer les popups
- **Tab** : Naviguer entre les champs

### ❓ Problèmes courants

**"Je ne peux pas modifier ma fiche"**
- Vérifiez le statut de la fiche
- Si elle est EN_COURS ou VALIDEE, contactez un correcteur/administrateur

**"Mes données ont disparu"**
- Vérifiez que vous avez cliqué sur "Enregistrer"
- Consultez l'historique pour voir les modifications récentes

**"Je ne trouve pas ma fiche"**
- Utilisez les filtres de recherche
- Vérifiez la date de création
- Contactez un administrateur si nécessaire

---

## Prochaines étapes

Maintenant que vous connaissez la navigation générale, consultez les guides spécifiques :

- **[Saisir une nouvelle observation](./02_saisie_nouvelle_observation.md)**
  Guide détaillé pour créer et compléter une fiche d'observation

- **[Corriger des fiches (Transcription)](./03_correction_transcription.md)**
  Guide pour utiliser l'outil de transcription et correction

---

## Besoin d'aide ?


- **Support** : Contactez un administrateur
- **Signaler un bug** : Utilisez le formulaire de contact

---

*Version 1.1 - Décembre 2025*

---

## 🆕 Nouveautés (Décembre 2025)

### Améliorations de navigation et ergonomie

1. **Menu restructuré**
   - Section "Fiches Observations" plus claire
   - "Nouvelle fiche" au lieu de "Nouvelle observation"
   - Menu actif surligné en bleu clair

2. **Barre d'actions flottante**
   - Sur mobile/tablette, boutons toujours accessibles en bas d'écran
   - Facilite l'enregistrement et la validation
   - Se masque automatiquement en bas de page

3. **Recherche de communes optimisée**
   - Tri intelligent par pertinence
   - Communes courtes (Ur, Ger, Eu, Ay) trouvées facilement
   - Plus besoin de scroller dans de longues listes

4. **Terminologie clarifiée**
   - **Fiche ID** : Numéro unique attribué automatiquement (non modifiable, affiché en gris)
   - **N° perso de fiche** : Votre numéro de référence personnel (modifiable)

**→ Consultez le [Guide rapide](./00_guide_rapide.md) pour découvrir ces nouveautés en action !**
