# Guide utilisateur - Saisir une nouvelle observation

## Vue d'ensemble

Ce guide vous accompagne **pas à pas** dans la saisie d'une nouvelle fiche d'observation de nid.

---

## Table des matières

1. [Créer une nouvelle fiche](#1-créer-une-nouvelle-fiche)
2. [Étape 1 : Localisation](#2-étape-1--localisation)
3. [Étape 2 : Enregistrer la fiche (OBLIGATOIRE)](#3-étape-2--enregistrer-la-fiche-obligatoire)
4. [Étape 3 : Informations du nid](#4-étape-3--informations-du-nid)
5. [Étape 4 : Ajouter des observations](#5-étape-4--ajouter-des-observations)
6. [Étape 5 : Ajouter des remarques](#6-étape-5--ajouter-des-remarques)
7. [Étape 6 : Résumé et validation](#7-étape-6--résumé-et-validation)
8. [Le bouton "Enregistrer" - À quoi sert-il ?](#8-le-bouton-enregistrer--à-quoi-sert-il-)
9. [Modifier une fiche existante](#9-modifier-une-fiche-existante)
10. [Questions fréquentes](#10-questions-fréquentes)

---

## 1. Créer une nouvelle fiche

### Accéder au formulaire de saisie

1. **Depuis l'accueil** : Cliquez sur "📝 Nouvelle observation"
2. **Depuis le menu** : "Observations" > "Nouvelle saisie"

Vous arrivez sur la page de saisie avec plusieurs sections.

---

## 2. Étape 1 : Localisation

La localisation est la **première étape obligatoire**. Vous avez deux méthodes pour définir la localisation du nid.

### Méthode A : Recherche par commune

**Quand l'utiliser** : Vous connaissez le nom de la commune

1. **Champ "Commune"**
   - Tapez les premières lettres du nom de la commune
   - Un menu déroulant s'affiche avec les suggestions
   - Sélectionnez la commune dans la liste

2. **Précision automatique**
   - Les coordonnées GPS de la commune sont automatiquement ajoutées
   - Le code postal et le département sont renseignés

3. **Affiner la localisation (optionnel)**
   - Vous pouvez ajuster manuellement les coordonnées
   - Utilisez les champs "Latitude" et "Longitude"

**Exemple** :
```
Commune : Strasbourg
Code postal : 67000 (automatique)
Latitude : 48.5734 (automatique)
Longitude : 7.7521 (automatique)
```

---

### Méthode B : Géolocalisation GPS

**Quand l'utiliser** : Vous êtes sur le terrain avec un smartphone/tablette

1. **Bouton "📍 Me géolocaliser"**
   - Cliquez sur le bouton de géolocalisation
   - Autorisez l'accès à votre position GPS (si demandé)
   - Les coordonnées sont automatiquement renseignées

2. **Reverse geocoding (recherche de commune)**
   - L'application cherche automatiquement la commune correspondante
   - **⚠️ IMPORTANT** : Vérifiez et **précisez manuellement la commune**
   - Le reverse geocoding n'est pas toujours précis !

3. **Corriger la commune si nécessaire**
   - Vérifiez le champ "Commune"
   - Si la commune détectée est incorrecte, sélectionnez la bonne dans la liste
   - Gardez les coordonnées GPS précises

**Exemple** :
```
[Clic sur 📍 Me géolocaliser]
→ Coordonnées détectées : 48.8566, 2.3522
→ Commune suggérée : Paris
→ Vous vérifiez : C'est correct ✓
→ Ou vous corrigez : Paris 5e arrondissement
```

---

### ⚠️ Précision importante : Commune obligatoire

**Pourquoi la commune est obligatoire ?**
- Les coordonnées GPS seules ne suffisent pas pour les analyses
- La commune permet le tri et les statistiques par zone
- C'est une donnée administrative stable

**Workflow recommandé** :
```
1. Cliquer sur "Me géolocaliser" (coordonnées précises)
   ↓
2. Vérifier la commune suggérée
   ↓
3. Corriger/préciser la commune si nécessaire
   ↓
4. Enregistrer
```

---

### Champs de localisation

| Champ | Obligatoire | Description | Exemple |
|-------|-------------|-------------|---------|
| **Commune** | ✅ Oui | Nom de la commune | Strasbourg |
| **Code postal** | Non | Auto-rempli avec la commune | 67000 |
| **Département** | Non | Auto-rempli avec la commune | Bas-Rhin (67) |
| **Coordonnées** | ✅ Oui | Format Latitude, Longitude | 48.5734, 7.7521 |
| **Lieu-dit** | Non | Précision supplémentaire | La Robertsau |

---

## 3. Étape 2 : Enregistrer la fiche (OBLIGATOIRE)

### ⚠️ IMPORTANT : Enregistrer AVANT d'ajouter des observations

**Pourquoi cette étape est obligatoire ?**

Une fois la localisation renseignée, vous **DEVEZ enregistrer la fiche** avant de pouvoir ajouter :
- ✅ Des observations (dates, œufs, poussins)
- ✅ Des remarques

**Raison technique** :
- La fiche doit avoir un ID en base de données
- Les observations et remarques sont liées à cet ID
- Sans ID, impossible d'enregistrer des observations

---

### Comment enregistrer

1. **Remplissez les informations de base**
   - Localisation (commune + coordonnées)
   - Informations du nid (voir section suivante)
   - Causes d'échec éventuelles

2. **Cliquez sur le bouton "💾 Enregistrer"**
   - Le bouton se trouve en bas du formulaire
   - Un message de confirmation s'affiche
   - La page se recharge avec votre fiche sauvegardée

3. **Vous êtes maintenant en mode "Modification"**
   - La fiche a un numéro d'identification
   - Les sections "Observations" et "Remarques" sont maintenant actives
   - Vous pouvez ajouter autant d'observations que nécessaire

---

## 4. Étape 3 : Informations du nid

### Informations générales

| Champ | Obligatoire | Description | Valeurs possibles |
|-------|-------------|-------------|-------------------|
| **Espèce** | ✅ Oui | Espèce observée | Liste déroulante d'espèces |
| **Année** | ✅ Oui | Année d'observation | 2024, 2025, etc. |
| **Observateur** | Auto | Rempli automatiquement | Votre nom d'utilisateur |
| **Photo du nid** | Non | Image du nid | Fichier JPG/PNG |

---

### Détails du nid

| Champ | Description | Exemple |
|-------|-------------|---------|
| **Hauteur du nid** | Hauteur en mètres | 5.5 |
| **Support du nid** | Type de support | Arbre, bâtiment, pylône |
| **Exposition** | Orientation cardinale | Nord, Sud, Est, Ouest |
| **Type d'habitat** | Environnement | Urbain, Rural, Forestier |

---

### Résumé de l'observation

| Champ | Description |
|-------|-------------|
| **Date de première observation** | Première fois que le nid a été repéré |
| **Date de dernière observation** | Dernière visite du nid |
| **Succès de reproduction** | Oui / Non / Inconnu |
| **Nombre d'envols réussis** | Nombre de jeunes ayant quitté le nid |

---

### Causes d'échec (si applicable)

Si la reproduction a échoué, précisez les causes :
- Prédation
- Conditions météorologiques
- Dérangement humain
- Destruction du nid
- Autre (à préciser)

---

## 5. Étape 4 : Ajouter des observations

### ⚠️ Prérequis

**Vous devez avoir enregistré la fiche au moins une fois** (voir Étape 2)

---

### Ajouter une observation

Les observations permettent de suivre l'évolution du nid au fil du temps.

1. **Cliquez sur "+ Ajouter une observation"**
   - Le bouton apparaît après l'enregistrement initial
   - Un nouveau formulaire d'observation s'affiche

2. **Remplissez les champs**

| Champ | Obligatoire | Description | Exemple |
|-------|-------------|-------------|---------|
| **Date d'observation** | ✅ Oui | Date de la visite | 15/04/2025 |
| **Nombre d'œufs** | Non | Œufs comptés | 3 |
| **Nombre de poussins** | Non | Poussins visibles | 2 |
| **Observations** | Non | Notes textuelles | "2 poussins bien nourris, parents actifs" |

3. **Cliquez sur "Enregistrer l'observation"**
   - L'observation est ajoutée à la fiche
   - Vous pouvez en ajouter d'autres

---

### Exemple de suivi chronologique

Voici un exemple de suivi d'un nid avec plusieurs observations :

| Date | Œufs | Poussins | Notes |
|------|------|----------|-------|
| 01/04/2025 | 3 | 0 | Ponte terminée |
| 15/04/2025 | 0 | 3 | Éclosion réussie |
| 01/05/2025 | 0 | 3 | Poussins bien développés |
| 20/05/2025 | 0 | 2 | Un poussin mort (cause inconnue) |
| 05/06/2025 | 0 | 0 | Envol réussi des 2 jeunes |

---

### Modifier ou supprimer une observation

- **Modifier** : Cliquez sur l'icône ✏️ à côté de l'observation
- **Supprimer** : Cliquez sur l'icône 🗑️ (confirmation demandée)

---

## 6. Étape 5 : Ajouter des remarques

### ⚠️ Prérequis

**Vous devez avoir enregistré la fiche au moins une fois** (voir Étape 2)

---

### À quoi servent les remarques ?

Les remarques permettent d'ajouter :
- Des notes contextuelles
- Des informations complémentaires
- Des observations non structurées
- Des commentaires pour les correcteurs

---

### Ajouter une remarque

1. **Cliquez sur "+ Ajouter une remarque"**
   - Le bouton apparaît après l'enregistrement initial
   - Une zone de texte s'affiche

2. **Saisissez votre remarque**
   ```
   Exemple : "Nid situé dans un jardin privé, accès difficile.
   Les propriétaires ont accepté les observations depuis la rue."
   ```

3. **Cliquez sur "Enregistrer la remarque"**
   - La remarque est sauvegardée avec la date et l'auteur
   - Vous pouvez en ajouter d'autres

---

### Exemples de remarques utiles

- Contexte d'accès : "Nid visible depuis la route départementale"
- Conditions météo : "Fortes pluies pendant la période d'observation"
- Interactions : "Dérangement fréquent par des corbeaux"
- Incertitudes : "Nombre d'œufs estimé, visibilité limitée"

---

## 7. Étape 6 : Résumé et validation

### Vérifier votre fiche

Avant de soumettre votre fiche pour correction, vérifiez :

- ✅ Localisation complète et précise
- ✅ Espèce correctement sélectionnée
- ✅ Au moins une observation enregistrée
- ✅ Dates cohérentes
- ✅ Informations du nid renseignées
- ✅ Résumé de la reproduction complété

---

### Soumettre pour correction

Une fois votre fiche complète :

1. **Cliquez sur "🚀 Soumettre pour correction"**
   - Le bouton se trouve en bas du formulaire
   - Une confirmation vous est demandée

2. **Changement de statut**
   - La fiche passe de **EN_EDITION** à **EN_COURS**
   - Vous ne pouvez plus la modifier seul
   - Un correcteur pourra la réviser

3. **Pourcentage de complétion**
   - Un pourcentage de complétion est calculé
   - Il indique si toutes les informations importantes sont renseignées
   - Visez au moins 80% pour une fiche de qualité

---

### Que se passe-t-il après la soumission ?

1. **Révision par un correcteur**
   - Un correcteur ou administrateur révise votre fiche
   - Des remarques peuvent être ajoutées
   - Des corrections peuvent être apportées

2. **Validation finale**
   - Une fois validée, la fiche passe au statut **VALIDEE**
   - Elle est intégrée dans les statistiques
   - Elle ne peut plus être modifiée (sauf par un administrateur)

---

## 8. Le bouton "Enregistrer" - À quoi sert-il ?

### 🔄 Enregistrements multiples

Le bouton "Enregistrer" peut être utilisé **plusieurs fois** pendant la saisie :

| Moment | Action | Effet |
|--------|--------|-------|
| **1er enregistrement** | Sauvegarder la fiche avec localisation + infos nid | Création de la fiche en base, génération d'un ID |
| **2e enregistrement** | Après ajout d'une observation | Sauvegarde de l'observation |
| **3e enregistrement** | Après ajout d'une remarque | Sauvegarde de la remarque |
| **Nième enregistrement** | Modification de n'importe quel champ | Mise à jour de la fiche |

---

### Bonnes pratiques

✅ **Enregistrez régulièrement** pour ne pas perdre vos données
✅ **Enregistrez AVANT d'ajouter des observations**
✅ **Enregistrez après chaque modification importante**

❌ **Ne fermez pas votre navigateur sans enregistrer**
❌ **N'utilisez pas le bouton "Retour" du navigateur** (utilisez les liens de navigation)

---

## 9. Modifier une fiche existante

### Accéder à une fiche existante

1. **Depuis la liste des observations**
   - Menu "Observations" > "Mes observations"
   - Cliquez sur la fiche à modifier

2. **Cliquez sur "✏️ Modifier"**
   - Le bouton apparaît si vous avez les droits
   - Vous accédez au formulaire de modification

---

### Différences entre création et modification

| Action | Création | Modification |
|--------|----------|--------------|
| Changer la localisation | ✅ Oui | ✅ Oui |
| Ajouter des observations | ✅ Oui (après 1er enregistrement) | ✅ Oui |
| Supprimer des observations | ❌ Non (pas encore créées) | ✅ Oui |
| Modifier le statut | ❌ Non (toujours NOUVEAU) | ✅ Oui (si droits suffisants) |

---

### Historique des modifications

Toutes les modifications sont tracées :

- **Qui** a modifié
- **Quand** la modification a eu lieu
- **Quel champ** a été modifié
- **Ancienne valeur** → **Nouvelle valeur**

Pour consulter l'historique :
- Cliquez sur "📜 Historique" dans la fiche

---

## 10. Questions fréquentes

### "Je n'arrive pas à ajouter d'observations"

**Réponse** : Avez-vous enregistré la fiche au moins une fois ?
- Les observations ne peuvent être ajoutées qu'après le premier enregistrement
- Cliquez sur "Enregistrer" en bas du formulaire
- Puis cliquez sur "+ Ajouter une observation"

---

### "La géolocalisation ne fonctionne pas"

**Solutions possibles** :
1. Vérifiez que vous avez autorisé l'accès GPS sur votre navigateur
2. Assurez-vous d'avoir une connexion internet
3. Sur mobile, vérifiez les paramètres de localisation
4. En cas d'échec, saisissez les coordonnées manuellement

---

### "Je ne peux plus modifier ma fiche"

**Raison** : Vous avez probablement soumis la fiche pour correction
- Les fiches au statut EN_COURS ou VALIDEE ne peuvent plus être modifiées par l'auteur
- Contactez un correcteur ou administrateur pour des modifications

---

### "Comment annuler une observation ?"

**Procédure** :
1. Allez dans votre fiche en mode modification
2. Trouvez l'observation à supprimer
3. Cliquez sur l'icône 🗑️
4. Confirmez la suppression
5. Enregistrez la fiche

---

### "Puis-je sauvegarder une fiche incomplète ?"

**Réponse** : Oui !
- Vous pouvez enregistrer une fiche même si elle n'est pas complète
- Elle restera au statut EN_EDITION
- Vous pourrez la compléter plus tard
- Ne la soumettez pas tant qu'elle n'est pas prête

---

### "Combien d'observations puis-je ajouter ?"

**Réponse** : Illimité
- Vous pouvez ajouter autant d'observations que nécessaire
- Une observation = une visite du nid
- Suivez l'évolution du nid tout au long de la saison

---

## Récapitulatif du workflow

```
1. Créer une nouvelle fiche
   ↓
2. Renseigner la localisation (commune + coordonnées)
   ↓
3. Remplir les informations du nid
   ↓
4. 💾 ENREGISTRER LA FICHE (obligatoire)
   ↓
5. Ajouter des observations (dates, œufs, poussins)
   ↓
6. Ajouter des remarques (optionnel)
   ↓
7. 💾 Enregistrer après chaque ajout
   ↓
8. Vérifier que tout est complet
   ↓
9. 🚀 Soumettre pour correction
```

---

## Aide supplémentaire

- **[Guide de navigation](./01_navigation_generale.md)**
- **[Guide de correction (Transcription)](./03_correction_transcription.md)**
- **Support** : Contactez un administrateur

---

*Version 1.0 - Octobre 2025*
