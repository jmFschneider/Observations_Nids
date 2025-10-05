# Guide d'utilisation - Saisie d'observations

## Vue d'ensemble

Le formulaire de saisie d'observations (`/observations/`) permet de créer une nouvelle fiche d'observation de nidification ou de modifier une fiche existante (`/observations/modifier/<id>/`).

Cette interface optimisée offre des fonctionnalités avancées pour faciliter la saisie sur le terrain, notamment sur mobile avec géolocalisation GPS.

---

## Accès au formulaire

**Nouvelle observation :**
- Depuis la page d'accueil → cliquer sur "Nouvelle observation"
- URL : `http://127.0.0.1:8000/observations/`

**Modifier une observation existante :**
- Depuis la liste des observations → cliquer sur "Modifier"
- URL : `http://127.0.0.1:8000/observations/modifier/<fiche_id>/`

---

## Structure du formulaire

Le formulaire est organisé en 6 sections principales :

### 1. Informations générales
**Champs affichés :**
- **N° Fiche** : Numéro automatique (attribué à la sauvegarde)
- **Observateur** : Nom de l'utilisateur connecté
- **Espèce** : Sélection de l'espèce observée (menu déroulant)
- **Année** : Année de l'observation

### 2. Localisation
**Champs manuels :**
- **Commune** : Saisie avec autocomplétion intelligente
- **Département** : Rempli automatiquement lors de la sélection de la commune
- **Lieu-dit** : Nom du lieu précis (optionnel)
- **Altitude** : Remplie automatiquement (commune ou GPS)
- **Latitude** : Coordonnée GPS (manuelle ou automatique)
- **Longitude** : Coordonnée GPS (manuelle ou automatique)

**Champs descriptifs :**
- **Paysage (200-500m)** : Description du paysage environnant
- **Alentours (20-50m)** : Description immédiate du site

### 3. Description du nid
- Utilisé par le même couple (Oui/Non)
- Hauteur du nid (cm)
- Hauteur du couvert végétal (cm)
- Support du nid (type)
- Orientation du nid
- Couverture végétale du nid (%)

### 4. Observations
Tableau dynamique permettant d'ajouter plusieurs observations :
- **Date et heure** : Moment de l'observation
- **Nombre d'œufs** : Comptage des œufs
- **Nombre de poussins** : Comptage des poussins
- **Observations** : Notes libres

**Actions disponibles :**
- ➕ Ajouter une ligne d'observation
- 🗑️ Supprimer une observation (marquage pour suppression)

### 5. Résumé
Synthèse des données de reproduction :
- Nombre d'œufs pondus
- Nombre d'œufs éclos
- Nombre de poussins envolés

### 6. Causes d'échec et remarques
- **Causes d'échec** : Description des causes d'échec de la nidification
- **Remarques** : Notes additionnelles avec système de gestion par popup (pour les fiches existantes)

---

## Fonctionnalités avancées

### 🗺️ Autocomplétion des communes

**Comment utiliser :**
1. Commencer à taper le nom de la commune (minimum 2 caractères)
2. Une liste déroulante apparaît avec jusqu'à 15 suggestions
3. Naviguer avec les **flèches ↑↓** ou la **souris**
4. Sélectionner avec **Entrée** ou **clic**

**Format des suggestions :**
```
Nom de la commune (Code Dept) - Département
Exemple : Saint-James (50) - Manche
```

**Remplissage automatique :**
- ✅ Commune
- ✅ Département
- ✅ Latitude (centre de la commune)
- ✅ Longitude (centre de la commune)
- ✅ Altitude (si disponible en base de données)

### 📍 Géolocalisation GPS

**Bouton "Ma position" :**
- Situé à côté du champ Longitude
- Récupère votre position GPS actuelle
- **Particulièrement utile sur mobile/tablette sur le terrain**

**Fonctionnement :**
1. Cliquer sur **"📍 Ma position"**
2. Le navigateur demande l'autorisation d'accès à la localisation
3. Autoriser l'accès
4. Les coordonnées GPS sont récupérées et affichées
5. Une liste des **15 communes les plus proches** s'affiche automatiquement avec leur distance

**Format de la liste GPS :**
```
Saint-James (50) - Manche - 141m
Huisnes-sur-Mer (50) - Manche - 2.3km
```
*La distance indique l'éloignement par rapport à votre position*

**Données récupérées :**
- ✅ Latitude GPS (position exacte)
- ✅ Longitude GPS (position exacte)
- ✅ Altitude GPS (si disponible sur l'appareil)
- ✅ Liste des communes proches

**Sélection de la commune après GPS :**
- Cliquer sur une commune dans la liste
- Remplit **uniquement** : Commune, Département, Altitude (si manquante)
- **Préserve** les coordonnées GPS exactes (ne les écrase pas)

### 🏔️ Gestion intelligente de l'altitude

Le système utilise une logique intelligente pour remplir l'altitude :

**Cas 1 : Géolocalisation GPS**
- Si le GPS fournit l'altitude → **utilise l'altitude GPS** (précise, ~10-20m d'erreur)
- Si le GPS ne fournit pas l'altitude → **utilise l'altitude de la commune** (base de données locale)

**Cas 2 : Saisie manuelle de commune**
- Utilise l'altitude du centre de la commune (base de données avec 35 000 communes)

**Cas 3 : Altitude déjà renseignée**
- Ne modifie jamais une altitude déjà saisie

### 📝 Système de remarques (fiches existantes uniquement)

**Pour ajouter/modifier des remarques :**
1. Cliquer sur **"➕ Ajouter/Modifier"** dans la section Remarques
2. Une popup modale s'ouvre
3. Ajouter des remarques (bouton **"+ Ajouter une remarque"**)
4. Saisir le texte
5. Cliquer sur **"Sauvegarder"**

**Actions disponibles :**
- ➕ Ajouter une nouvelle remarque
- ✏️ Modifier une remarque existante
- 🗑️ Supprimer une remarque

---

## Workflow de saisie

### Scénario 1 : Saisie sur le terrain (mobile avec GPS)

1. **Ouvrir le formulaire** `/observations/`
2. Sélectionner l'**espèce** et l'**année**
3. Cliquer sur **"📍 Ma position"**
   - Autoriser la géolocalisation
   - Les coordonnées GPS sont remplies
   - La liste des communes proches s'affiche
4. **Sélectionner la commune** dans la liste
   - Commune et département remplis
   - GPS préservé
   - Altitude de la commune ajoutée si GPS ne la fournit pas
5. Compléter **lieu-dit** si nécessaire
6. Remplir la **description du nid**
7. Ajouter les **observations** (dates, œufs, poussins)
8. Compléter le **résumé**
9. Ajouter les **causes d'échec** et **remarques** si nécessaire
10. Cliquer sur **"Enregistrer"**

### Scénario 2 : Saisie au bureau (ordinateur sans GPS)

1. **Ouvrir le formulaire** `/observations/`
2. Sélectionner l'**espèce** et l'**année**
3. Taper le nom de la **commune** (autocomplétion)
4. Sélectionner la commune dans la liste
   - Commune, département, lat/lon, altitude remplis automatiquement
5. Ajuster manuellement **lat/lon** si nécessaire (position exacte du nid)
6. Compléter **lieu-dit** si nécessaire
7. Remplir la **description du nid**
8. Ajouter les **observations**
9. Compléter le **résumé**
10. Ajouter les **causes d'échec** et **remarques** si nécessaire
11. Cliquer sur **"Enregistrer"**

### Scénario 3 : Modification d'une fiche existante

1. **Ouvrir la fiche** `/observations/modifier/<id>/`
2. Modifier les champs nécessaires
3. Utiliser le bouton **"📍 Ma position"** pour mettre à jour les coordonnées GPS si besoin
4. Gérer les **remarques** via la popup modale
5. Cliquer sur **"Enregistrer"**

---

## Boutons d'action

### Boutons principaux
- **Enregistrer** : Sauvegarde la fiche (nouvelle ou modification)
- **Annuler** / **Retour à la liste** : Retour sans sauvegarder

### Boutons supplémentaires (fiche existante)
- **Historique** : Consulter l'historique des modifications (nouvel onglet)
- **Voir détails** : Vue détaillée de la fiche (nouvel onglet)
- **Soumettre pour correction** : Soumettre la fiche pour validation (workflow de correction)

---

## Astuces et bonnes pratiques

### 🎯 Précision GPS sur mobile
- **Activer le GPS** avant de lancer l'application pour de meilleures performances
- La précision est affichée en mètres dans la console du navigateur (F12)
- Sur mobile : précision GPS ~5-50m
- Sur ordinateur (WiFi/IP) : précision ~100-5000m

### 🗺️ Sélection de la commune
- Toujours **sélectionner depuis la liste déroulante** (ne pas juste taper le nom)
- Cela garantit le remplissage automatique des coordonnées et de l'altitude
- Si la commune n'apparaît pas, vérifier l'orthographe ou essayer une variante (ex: "St-James" → "Saint-James")

### 📏 Altitude
- L'altitude GPS (sur mobile) est généralement plus précise que celle de la commune
- Si l'altitude affichée semble incorrecte, vous pouvez la modifier manuellement
- La base de données contient ~35 000 communes françaises avec leurs altitudes

### 🔄 Observations multiples
- Ajouter une ligne par visite sur le terrain
- Ne pas hésiter à supprimer les lignes erronées (bouton 🗑️)
- Les observations supprimées sont marquées en grisé avant suppression définitive

### 💾 Sauvegarde
- Penser à **enregistrer régulièrement** pour ne pas perdre les données
- Le formulaire ne sauvegarde pas automatiquement
- En cas d'erreur, les messages d'erreur s'affichent en haut de la page

---

## Navigation au clavier

### Autocomplétion des communes
- **↓ (Flèche bas)** : Descendre dans la liste
- **↑ (Flèche haut)** : Remonter dans la liste
- **Entrée** : Sélectionner la commune en surbrillance
- **Échap** : Fermer la liste sans sélectionner

### Formulaire
- **Tab** : Passer au champ suivant
- **Shift + Tab** : Revenir au champ précédent
- **Entrée** : Soumettre le formulaire (attention, sauvegarder)

---

## Permissions et restrictions

### Droits d'accès
- **Observateur** : Peut créer et modifier ses propres fiches
- **Correcteur** : Peut corriger les fiches soumises
- **Validateur** : Peut valider les fiches corrigées
- **Administrateur** : Accès complet

### Restrictions
- Une fiche **soumise pour correction** ne peut plus être modifiée par l'observateur
- Seul l'**auteur** ou un **administrateur** peut modifier une fiche en cours d'édition
- Les fiches **validées** ne peuvent être modifiées que par un administrateur

---

## Dépannage

### L'autocomplétion ne fonctionne pas
**Solutions :**
1. Rafraîchir la page (**Ctrl + F5** ou **Cmd + Shift + R**)
2. Vider le cache du navigateur
3. Vérifier que JavaScript est activé
4. Taper au moins **2 caractères** pour déclencher l'autocomplétion

### La géolocalisation ne fonctionne pas
**Solutions :**
1. Vérifier que le **GPS est activé** sur le mobile
2. Autoriser l'accès à la localisation dans le navigateur
3. Sur ordinateur : WiFi doit être activé pour la géolocalisation par IP
4. Essayer dans **Chrome** ou **Firefox** (meilleure compatibilité)
5. En production : le site doit être en **HTTPS** (pas HTTP)

### Les coordonnées GPS sont incorrectes
**Vérifications :**
1. La précision GPS est affichée dans la console (F12 → Console)
2. Si précision > 1000m, la position est approximative (WiFi/IP)
3. Attendre quelques secondes que le GPS se stabilise
4. Cliquer à nouveau sur **"Ma position"** pour rafraîchir

### L'altitude n'est pas remplie
**Solutions :**
1. Vérifier que la commune est sélectionnée **depuis la liste déroulante**
2. Certaines communes peuvent ne pas avoir d'altitude (en cours de chargement)
3. Saisir l'altitude manuellement si nécessaire
4. Rafraîchir la page et réessayer

### Les observations ne se suppriment pas
**Comportement normal :**
1. Cliquer sur 🗑️ marque la ligne en grisé (suppression en attente)
2. La suppression effective a lieu lors de l'**enregistrement** du formulaire
3. Pour annuler la suppression, rafraîchir la page sans enregistrer

---

## Support technique

### Logs et débogage
Pour obtenir des informations de débogage :
1. Ouvrir la **console développeur** (F12)
2. Onglet **Console** pour voir les logs
3. Chercher les messages :
   - `Altitude GPS: XXX mètres` (si altitude GPS disponible)
   - `Altitude GPS non disponible` (si pas d'altitude GPS)

### Contact
En cas de problème persistant, contacter l'administrateur du système avec :
- **Description du problème**
- **Navigateur utilisé** (Chrome, Firefox, Safari, etc.)
- **Appareil** (ordinateur, mobile, tablette)
- **Messages d'erreur** éventuels (copie depuis la console F12)

---

## Annexes

### Compatibilité navigateurs

| Navigateur | Version min. | Fonctionnalités supportées |
|------------|--------------|----------------------------|
| Chrome     | 90+          | ✅ Toutes                  |
| Firefox    | 88+          | ✅ Toutes                  |
| Safari     | 14+          | ✅ Toutes                  |
| Edge       | 90+          | ✅ Toutes                  |
| Chrome Mobile | 90+      | ✅ Toutes + GPS précis     |
| Safari iOS | 14+          | ✅ Toutes + GPS précis     |

### Technologies utilisées
- **Frontend** : Bootstrap 5, JavaScript vanilla
- **Backend** : Django 5.1, Python 3.12
- **Base de données** : SQLite (35 000 communes françaises)
- **API externe** : Open-Elevation (altitudes)
- **API navigateur** : Geolocation API (GPS)

### Performances
- **Autocomplétion** : < 10ms (recherche locale)
- **Géolocalisation** : 1-5 secondes (selon GPS)
- **Sauvegarde** : < 500ms (formulaire complet)

---

*Document généré le 2025-10-04 - Version 1.0*
*Pour le projet Observations Nids - Base de données ornithologique*
