# Documentation utilisateur - Observations Nids

Bienvenue dans la documentation utilisateur de l'application **Observations Nids**.

Cette documentation vous guide dans l'utilisation de l'application, de l'inscription jusqu'à la validation des fiches d'observation.

---

## 📚 Guides disponibles

### 1. [Navigation générale](./01_navigation_generale.md)

**Quand le consulter** : Première visite de l'application

**Ce que vous apprendrez** :
- S'inscrire et se connecter
- Naviguer dans l'application
- Comprendre les différentes sections
- Le cycle de vie d'une fiche d'observation
- Les rôles et permissions

**Durée de lecture** : 10 minutes

---

### 2. [Saisir une nouvelle observation](./02_saisie_nouvelle_observation.md)

**Quand le consulter** : Vous souhaitez enregistrer une observation de terrain

**Ce que vous apprendrez** :
- Créer une nouvelle fiche d'observation
- Définir la localisation (commune ou GPS)
- **Important** : Enregistrer la fiche AVANT d'ajouter des observations
- Ajouter des observations et des remarques
- Le rôle du bouton "Enregistrer"
- Valider et soumettre une fiche

**Durée de lecture** : 20 minutes

---

### 3. [Corriger des fiches (Transcription)](./03_correction_transcription.md)

**Quand le consulter** : Vous avez des carnets papier scannés à transcrire

**Ce que vous apprendrez** :
- Préparer et uploader vos images de carnets
- Lancer la transcription automatique (IA Gemini)
- Suivre la progression du traitement
- Visualiser les fichiers source (JPEG et JSON)
- Corriger les fiches générées
- **Important** : La logique de correction est identique à la saisie manuelle

**Durée de lecture** : 20 minutes

---

### 4. [Support : Signaler un problème](./04_support_tickets.md)

**Quand le consulter** : Vous rencontrez un problème ou avez une question

**Ce que vous apprendrez** :
- Créer un ticket de support (Bug, Question, Fonctionnalité, Documentation)
- Suivre vos tickets
- Répondre et communiquer avec l'équipe support
- Comprendre les statuts des tickets
- Bonnes pratiques pour signaler un problème

**Durée de lecture** : 10 minutes

---

## 🎯 Par où commencer ?

### Nouvel utilisateur

```
1. Lisez la navigation générale (01_navigation_generale.md)
   ↓
2. Créez votre compte
   ↓
3. Lisez le guide de saisie (02_saisie_nouvelle_observation.md)
   ↓
4. Créez votre première observation
```

### Utilisateur avec carnets papier

```
1. Lisez la navigation générale (01_navigation_generale.md)
   ↓
2. Scannez vos carnets
   ↓
3. Lisez le guide de transcription (03_correction_transcription.md)
   ↓
4. Uploadez et lancez la transcription
   ↓
5. Corrigez les fiches générées
```

---

## 🔑 Points clés à retenir

### Saisie manuelle

1. **Localisation** : Commune OU GPS + commune
2. **Enregistrer AVANT** d'ajouter des observations
3. **Enregistrer régulièrement** pour ne pas perdre vos données
4. **Vérifier avant de soumettre** (impossible de modifier seul après)

### Transcription

1. **Images de qualité** pour un meilleur OCR
2. **Traitement asynchrone** (peut prendre plusieurs minutes)
3. **L'IA n'est pas parfaite** : correction humaine indispensable
4. **Logique identique à la saisie** pour les corrections

---

## 📖 Glossaire

| Terme | Définition |
|-------|------------|
| **Fiche d'observation** | Document structuré contenant les informations d'un nid suivi |
| **Observation** | Visite d'un nid à une date précise (œufs, poussins, notes) |
| **Remarque** | Note libre associée à une fiche |
| **Transcription** | Conversion automatique d'un carnet papier en fiche numérique |
| **OCR** | Optical Character Recognition - Reconnaissance de caractères |
| **Gemini** | IA de Google utilisée pour la transcription |
| **JSON** | Format de données structurées généré par la transcription |
| **Statut** | État d'une fiche (NOUVEAU, EN_EDITION, EN_COURS, VALIDEE) |
| **Géolocalisation** | Coordonnées GPS d'un lieu |
| **Reverse geocoding** | Recherche d'une adresse à partir de coordonnées GPS |

---

## ❓ Besoin d'aide ?

### Documentation technique

- **[CHANGELOG.md](../CHANGELOG.md)** : Historique des versions
- **[OPTIMISATIONS_FUTURES.md](../OPTIMISATIONS_FUTURES.md)** : Améliorations prévues
- **[TODO_NETTOYAGE.md](../TODO_NETTOYAGE.md)** : Tâches de maintenance

### Support

- **[Système de tickets](./04_support_tickets.md)** : Signaler un problème ou poser une question
- **Email direct** : admin@observations-nids.fr (urgences uniquement)
- **[Documentation Helpdesk complète](../helpdesk/README.md)** : Guides détaillés utilisateur et développeur

---

## 🚀 Raccourcis utiles

### Navigation rapide

| Raccourci | Action |
|-----------|--------|
| **Accueil** | Retour au tableau de bord |
| **Ctrl + S** | Enregistrer (si disponible) |
| **Échap** | Fermer les popups |
| **Tab** | Naviguer entre les champs |

### Liens directs

- [Nouvelle observation](#) → `/observations/nouvelle/`
- [Mes observations](#) → `/observations/`
- [Transcription](#) → `/transcription/`
- [Mon compte](#) → `/compte/`

---

## 📊 Statistiques de la documentation

- **Nombre de guides** : 4
- **Pages totales** : ~150 lignes par guide
- **Temps de lecture total** : ~60 minutes
- **Dernière mise à jour** : Octobre 2024

---

## 🤝 Contribution

Cette documentation est vivante et s'améliore avec vos retours !

**Vous avez remarqué une erreur ?**
- Signalez-la à un administrateur
- Proposez une correction

**Vous avez une suggestion ?**
- Partagez vos idées
- Aidez à améliorer les guides

---

## 📜 Licence

Cette documentation fait partie du projet **Observations Nids**.

---

*Version 1.1 - Octobre 2024*

**Auteurs** : Équipe Observations Nids
**Contributeurs** : Tous les utilisateurs qui ont partagé leurs retours
