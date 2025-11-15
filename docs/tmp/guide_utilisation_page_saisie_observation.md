# Guide d'utilisation - Page de Saisie/Modification d'Observations

## Table des matières

1. [Introduction](#introduction)
2. [Accès à la page](#accès-à-la-page)
3. [Création d'une nouvelle fiche](#création-dune-nouvelle-fiche)
4. [Modification d'une fiche existante](#modification-dune-fiche-existante)
5. [Description détaillée des sections](#description-détaillée-des-sections)
6. [Workflow de sauvegarde](#workflow-de-sauvegarde)
7. [Calcul du pourcentage de complétion](#calcul-du-pourcentage-de-complétion)
8. [Soumission pour validation](#soumission-pour-validation)
9. [Correction de transcriptions](#correction-de-transcriptions)
10. [Permissions et restrictions](#permissions-et-restrictions)
11. [Historique des modifications](#historique-des-modifications)

---

## Introduction

La page de saisie/modification d'observations permet de créer de nouvelles fiches d'observation ou de modifier des fiches existantes. Cette page centralise toutes les informations relatives à une observation de nid :
- Informations générales (observateur, espèce, année)
- Localisation géographique
- Description du nid
- Observations successives
- Résumé des observations
- Causes d'échec éventuelles
- Remarques

**URLs concernées :**
- Création : `http://127.0.0.1:8000/observations/`
- Modification : `http://127.0.0.1:8000/observations/modifier/{num_fiche}/`
- Exemple : `http://127.0.0.1:8000/observations/modifier/27/`

---

## Accès à la page

### Création d'une nouvelle observation
1. Accédez à `http://127.0.0.1:8000/observations/`
2. La page affiche le titre "Saisie d'une nouvelle observation"
3. Le numéro de fiche est indiqué comme "À définir" (il sera attribué automatiquement lors de la première sauvegarde)

### Modification d'une observation existante
1. Accédez à `http://127.0.0.1:8000/observations/modifier/{num_fiche}/`
2. La page affiche le titre "Edition d'une observation"
3. Le numéro de fiche est affiché dans le tableau d'informations générales
4. Des liens supplémentaires apparaissent dans l'en-tête :
   - **"Voir l'image"** : Ouvre l'image scannée de la fiche papier (si disponible)
   - **"Voir JSON"** : Affiche le fichier JSON de transcription automatique (si disponible)

---

## Création d'une nouvelle fiche

### Étapes pour créer une fiche

1. **Accéder à la page de création**
   - URL : `http://127.0.0.1:8000/observations/`

2. **Remplir les informations obligatoires**
   - **Espèce** : Sélectionner dans la liste déroulante avec recherche
   - **Au moins une observation** : Date et heure minimum

3. **Remplir les autres sections** (facultatif)
   - Localisation
   - Description du nid
   - Résumé des observations
   - Causes d'échec
   - Remarques

4. **Enregistrer la fiche**
   - Cliquer sur le bouton "Enregistrer"
   - Un numéro de fiche est automatiquement attribué
   - Vous êtes redirigé vers la page de modification (`/observations/modifier/{num_fiche}/`)

### Limitations importantes

**❌ VOUS NE POUVEZ PAS :**
- Enregistrer une fiche sans l'avoir créée d'abord
- Une fiche doit être créée en une seule fois avec au minimum :
  - Une espèce sélectionnée
  - Toutes les informations de base valides

**✅ VOUS POUVEZ :**
- Créer une fiche minimale et la compléter ensuite
- Modifier une fiche autant de fois que nécessaire avant soumission
- Ajouter/supprimer des observations après création

---

## Modification d'une fiche existante

### Accès et permissions

Une fiche peut être modifiée tant qu'elle est dans les statuts suivants :
- **"nouveau"** : Fiche nouvellement créée
- **"en_edition"** : Fiche en cours d'édition

**Restrictions :**
- Seul l'**auteur** (observateur) ou un **administrateur** peut modifier une fiche en statut "nouveau" ou "en_edition"
- Une fois soumise pour correction (statut "en_cours"), la fiche devient **lecture seule** pour l'observateur
- Les reviewers et administrateurs peuvent modifier les fiches en cours de correction

### Workflow de modification

1. **Accéder à la fiche** : `http://127.0.0.1:8000/observations/modifier/{num_fiche}/`
2. **Modifier les champs souhaités**
3. **Enregistrer** : Cliquer sur "Enregistrer"
4. **Résultat** :
   - La fiche est mise à jour
   - Un historique des modifications est créé automatiquement
   - Vous restez sur la page de modification

---

## Description détaillée des sections

### 1. Informations générales

**Emplacement :** Première section de la page (en-tête bleu)

| Champ | Type | Obligatoire | Éditable | Description |
|-------|------|-------------|----------|-------------|
| **N° Fiche** | Auto | Oui | ❌ Non | Numéro automatique attribué à la création |
| **Observateur** | Caché | Oui | ❌ Non* | Utilisateur connecté (modifiable par admin/reviewer) |
| **Espèce** | Liste déroulante | Oui | ✅ Oui | Espèce observée (recherche par nom) |
| **Année** | Nombre | Oui | ✅ Oui | Année de l'observation (auto-rempli à la création) |

*Note :* Le champ observateur n'est modifiable que pour les administrateurs et reviewers.

**Recherche d'espèce :**
- Tapez dans le champ pour rechercher
- Délai de 800ms entre les frappes (debounce)
- Navigation au clavier (↑↓, Entrée, Échap)
- Surlignage des termes recherchés

---

### 2. Localisation

**Emplacement :** Deuxième section (en-tête vert)

#### Tableau de localisation

| Champ | Type | Obligatoire | Éditable | Description |
|-------|------|-------------|----------|-------------|
| **Commune** | Texte avec autocomplétion | Non | ✅ Oui | Commune de l'observation |
| **Département** | Texte | Non | ❌ Non* | Auto-rempli via l'autocomplétion commune |
| **Lieu-dit** | Texte | Non | ✅ Oui | Nom du lieu précis |
| **Altitude** | Nombre | Non | ✅ Oui | Altitude en mètres |
| **Latitude** | Décimal | Non | ✅ Oui | Coordonnée GPS |
| **Longitude** | Décimal | Non | ✅ Oui | Coordonnée GPS |

*Note :* Le département est en lecture seule mais se remplit automatiquement.

**Fonctionnalité d'autocomplétion de commune :**
- Tapez au moins 2 caractères pour lancer la recherche
- Délai de 300ms entre les frappes
- Recherche via l'API Nominatim (OpenStreetMap)
- **Auto-remplissage** : Lorsque vous sélectionnez une commune, les champs suivants sont remplis automatiquement (uniquement s'ils sont vides) :
  - Département
  - Latitude
  - Longitude
  - Altitude
- **Respect des valeurs existantes** : Si ces champs contiennent déjà des valeurs, elles ne sont PAS écrasées
- Navigation au clavier (↑↓, Entrée, Échap)

**Bouton "Ma position" (GPS) :**
- Cliquer sur le bouton demande l'autorisation de géolocalisation
- Remplit automatiquement latitude et longitude
- Déclenche ensuite une recherche de commune basée sur ces coordonnées
- Gestion des erreurs : permission refusée, position indisponible, timeout

#### Descriptions textuelles

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| **Paysage (200 à 500m)** | Textarea | Non | Description du paysage environnant dans un rayon de 200 à 500 mètres |
| **Alentours (20 à 50m)** | Textarea | Non | Description des alentours immédiats dans un rayon de 20 à 50 mètres |

---

### 3. Description du Nid

**Emplacement :** Troisième section (en-tête cyan)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| **Utilisé par le même couple** | Case à cocher | Non | Indique si le nid était utilisé précédemment par le même couple |
| **Hauteur du nid (cm)** | Nombre | Non | Hauteur du nid en centimètres (valeur par défaut : 0) |
| **Hauteur du couvert (cm)** | Nombre | Non | Hauteur du couvert végétal en centimètres (valeur par défaut : 0) |
| **Détails du Nid** | Textarea | Non | Description détaillée du nid et de sa structure |

**Valeurs par défaut :**
- Les hauteurs sont initialisées à 0
- La case "Utilisé par le même couple" est décochée par défaut

---

### 4. Observations

**Emplacement :** Quatrième section (en-tête jaune)

Cette section permet de gérer **plusieurs observations** successives pour une même fiche. Chaque observation représente une visite sur le terrain à une date donnée.

#### Structure du tableau

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| **Date** | Date et heure | Oui | Date et heure de l'observation (format : datetime-local) |
| **Heure connue** | Case à cocher | Non | Indique si l'heure exacte est connue |
| **Nombre d'œufs** | Nombre | Non | Nombre d'œufs observés (défaut : 0) |
| **Nombre de poussins** | Nombre | Non | Nombre de poussins observés (défaut : 0) |
| **Observations** | Textarea | Non | Notes et remarques de l'observation |
| **Actions** | Boutons | - | Bouton "Supprimer" pour marquer une observation à supprimer |

#### Gestion de l'heure

**Comportement de la case "Heure connue" :**
- **Si cochée** : L'heure saisie est conservée
- **Si décochée** : L'heure est automatiquement mise à 00:00:00
- **Détection automatique** : Si vous modifiez manuellement l'heure à une valeur différente de 00:00, la case se coche automatiquement

**Format de la date :**
- Format : `JJ/MM/AAAA HH:MM`
- Widget HTML5 : `datetime-local` pour une saisie facile

#### Ajout d'observations

**Méthode 1 : Lors de la création/modification de la fiche**
- Les lignes d'observation sont affichées dans le tableau
- Si la fiche existe déjà, les observations existantes sont pré-remplies
- Vous pouvez modifier les observations existantes directement dans le tableau

**Méthode 2 : Ajouter une observation individuelle**
- **URL** : `http://127.0.0.1:8000/observations/ajouter/{num_fiche}/`
- Cette vue permet d'ajouter une seule observation à une fiche existante
- Après ajout, redirection vers la page de modification

**Note importante :** Pour une nouvelle fiche, au moins une observation doit être créée lors de la première sauvegarde.

#### Suppression d'observations

**Processus de suppression :**

1. **Marquer pour suppression**
   - Cliquer sur le bouton "Supprimer" d'une observation
   - La ligne devient grisée, barrée et en opacité réduite
   - Les champs de la ligne sont désactivés (non éditables)
   - Un champ caché `DELETE` est marqué pour le formset Django

2. **Bannière de confirmation**
   - Une bannière jaune apparaît en haut du tableau
   - Affiche le nombre d'observations marquées pour suppression
   - Exemple : "**Attention :** 2 observation(s) seront supprimée(s) lors de la validation."
   - Bouton "Annuler toutes les suppressions" pour annuler toutes les marques

3. **Restauration d'une observation**
   - Cliquer sur le bouton "Restaurer" (qui remplace "Supprimer")
   - La ligne redevient normale
   - Les champs sont réactivés

4. **Confirmation de soumission**
   - Si des observations sont marquées pour suppression, une confirmation JavaScript s'affiche avant la soumission du formulaire
   - Message : "Vous avez marqué X observation(s) pour suppression. Êtes-vous sûr de vouloir continuer ?"

5. **Suppression effective**
   - Les observations ne sont **réellement supprimées** que lors de l'enregistrement de la fiche (clic sur "Enregistrer")
   - Une entrée est créée dans l'historique des modifications
   - La suppression est définitive et ne peut pas être annulée après enregistrement

**Impact sur la sauvegarde :**
- Les suppressions d'observations marquées sont traitées lors de la sauvegarde globale du formulaire
- Si vous modifiez d'autres champs sans enregistrer, puis supprimez une observation et enregistrez, **TOUTES les modifications sont sauvegardées ensemble** (champs + suppressions)
- Si vous fermez la page sans enregistrer, **AUCUNE modification n'est conservée** (ni les changements de champs, ni les suppressions)

---

### 5. Résumé des Observations

**Emplacement :** Cinquième section (en-tête violet)

Cette section résume les événements clés du cycle de reproduction observé.

#### Dates des événements (jour/mois uniquement)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| **Premier œuf pondu (Jour)** | Nombre (1-31) | Non* | Jour du mois du premier œuf |
| **Premier œuf pondu (Mois)** | Nombre (1-12) | Non* | Mois du premier œuf |
| **Premier poussin éclos (Jour)** | Nombre (1-31) | Non* | Jour du mois du premier poussin |
| **Premier poussin éclos (Mois)** | Nombre (1-12) | Non* | Mois du premier poussin |
| **Premier poussin volant (Jour)** | Nombre (1-31) | Non* | Jour du mois du premier poussin volant |
| **Premier poussin volant (Mois)** | Nombre (1-12) | Non* | Mois du premier poussin volant |

*Note :* **Contrainte jour/mois** : Pour chaque événement, si vous renseignez le jour, vous **devez** renseigner le mois, et inversement. Les deux doivent être remplis ensemble ou laissés vides ensemble.

#### Compteurs

| Champ | Type | Obligatoire | Description | Valeur par défaut |
|-------|------|-------------|-------------|-------------------|
| **Nombre d'œufs pondus** | Nombre | Non | Total d'œufs pondus | NULL (= "Non observé") |
| **Nombre d'œufs éclos** | Nombre | Non | Total d'œufs ayant éclos | NULL (= "Non observé") |
| **Nombre d'œufs non éclos** | Nombre | Non | Total d'œufs n'ayant pas éclos | NULL (= "Non observé") |
| **Nombre de poussins** | Nombre | Non | Total de poussins observés | NULL (= "Non observé") |

**Valeurs spéciales :**
- **NULL (vide)** : Indique "Non observé"
- **0** : Indique une observation avec 0 (zéro confirmé)
- Placeholder dans le formulaire : "Non observé"

**Contraintes de cohérence (validation en base de données) :**
- `nombre_oeufs_eclos ≤ nombre_oeufs_pondus` (si les deux sont renseignés)
- `nombre_oeufs_non_eclos ≤ nombre_oeufs_pondus` (si les deux sont renseignés)
- `nombre_poussins ≤ nombre_oeufs_eclos` (si les deux sont renseignés)

---

### 6. Causes d'échec

**Emplacement :** Sixième section (en-tête rouge)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| **Description** | Textarea | Non | Description des causes d'échec de la reproduction (prédation, abandon, météo, etc.) |

**Utilisation :**
- Laisser vide si l'observation est un succès
- Remplir uniquement en cas d'échec de la reproduction
- Décrire les causes identifiées ou suspectées

---

### 7. Remarques

**Emplacement :** Section accessible via un **modal** (popup)

**Accès :**
- Bouton "Gérer les remarques" en bas du formulaire
- Ouvre une fenêtre modale

**Fonctionnalité AJAX :**
- Les remarques sont gérées **indépendamment** du reste du formulaire
- Chargement des remarques via requête AJAX : `GET /observations/modifier/{fiche_id}/?get_remarques=1`
- Sauvegarde via requête AJAX : `POST /observations/modifier/{fiche_id}/` avec `action=update_remarques`

#### Gestion des remarques dans le modal

| Action | Description |
|--------|-------------|
| **Consulter** | Liste des remarques existantes avec leur date de création |
| **Ajouter** | Cliquer sur "Ajouter une remarque", saisir le texte, enregistrer |
| **Supprimer** | Cocher la case "Supprimer" à côté d'une remarque |
| **Enregistrer** | Bouton "Enregistrer" dans le modal |
| **Annuler** | Bouton "Annuler" ou fermer le modal (pas de modification) |

**Comportement spécifique :**
- Les remarques sont sauvegardées **immédiatement** lors du clic sur "Enregistrer" dans le modal
- La page se recharge automatiquement après sauvegarde réussie
- Les remarques sont **indépendantes** des autres modifications du formulaire principal

**Impact de la sauvegarde séparée :**
- Vous pouvez modifier les remarques et enregistrer uniquement ces modifications sans toucher au reste de la fiche
- Si vous modifiez d'autres champs du formulaire principal sans enregistrer, puis enregistrez des remarques dans le modal, **seules les remarques sont sauvegardées**
- Les modifications non enregistrées du formulaire principal seront perdues lors du rechargement de la page après sauvegarde des remarques

---

## Workflow de sauvegarde

### Vue d'ensemble

Le système utilise une **transaction atomique** pour garantir la cohérence des données : soit toutes les modifications sont sauvegardées, soit aucune.

### Étapes de sauvegarde (POST)

1. **Validation des formulaires**
   - Fiche principale (espèce, année)
   - Localisation
   - Nid
   - Résumé des observations
   - Causes d'échec
   - Formset d'observations
   - Formset de remarques

2. **Si validation réussie :**

   **a. Sauvegarde de la fiche principale**
   - Si nouvelle fiche (`fiche_id=None`) :
     - Création de l'objet `FicheObservation`
     - Attribution automatique d'un `num_fiche`
     - Création automatique des objets liés :
       - `Localisation` (avec valeurs par défaut)
       - `Nid` (avec valeurs par défaut)
       - `ResumeObservation` (avec NULL pour les compteurs)
       - `CausesEchec` (vide)
       - `EtatCorrection` (statut = "nouveau", pourcentage = 0%)
   - Si modification (`fiche_id` existe) :
     - Mise à jour de l'objet `FicheObservation` existant

   **b. Sauvegarde des objets liés**
   - **Localisation** : Mise à jour ou création
   - **Nid** : Mise à jour ou création
   - **Résumé** : Mise à jour ou création
   - **Causes d'échec** : Mise à jour ou création

   **c. Sauvegarde des observations**
   - Traitement du formset d'observations
   - **Nouvelles observations** : Création avec enregistrement dans l'historique
   - **Observations modifiées** : Mise à jour avec enregistrement des champs modifiés
   - **Observations supprimées** : Suppression définitive avec enregistrement dans l'historique

   **d. Sauvegarde des remarques**
   - Traitement du formset de remarques (sauf si sauvegarde via modal)
   - **Nouvelles remarques** : Création avec enregistrement dans l'historique
   - **Remarques supprimées** : Suppression définitive avec enregistrement dans l'historique

   **e. Mise à jour de l'année des observations**
   - Si le champ `annee` de la fiche a été modifié
   - Mise à jour automatique de toutes les observations liées

   **f. Enregistrement de l'historique**
   - Pour chaque champ modifié, une entrée est créée dans `HistoriqueModification`
   - Contient : nom du champ, ancienne valeur, nouvelle valeur, catégorie, utilisateur, date

3. **Si validation échoue :**
   - Aucune modification n'est sauvegardée (transaction atomique)
   - Affichage des messages d'erreur pour chaque formulaire invalide
   - Le formulaire est ré-affiché avec les valeurs saisies et les erreurs

4. **Redirection**
   - Succès : Redirection vers `http://127.0.0.1:8000/observations/modifier/{num_fiche}/`
   - Message de succès : "Fiche d'observation sauvegardée avec succès!"
   - Échec : Reste sur la page avec les messages d'erreur

### Points importants

**Cohérence des données :**
- Toutes les modifications sont sauvegardées dans une **transaction atomique**
- Si une erreur survient, **toutes** les modifications sont annulées (rollback)

**Modifications non sauvegardées :**
- Si vous modifiez des champs mais ne cliquez pas sur "Enregistrer", les modifications sont **perdues**
- Exception : Les remarques sauvegardées via le modal sont enregistrées immédiatement

**Impact des suppressions :**
- Les observations/remarques marquées pour suppression ne sont supprimées que lors de l'enregistrement
- Si vous avez des modifications en attente ET des suppressions marquées :
  - Enregistrement : **Tout est sauvegardé** (modifications + suppressions)
  - Abandon : **Rien n'est sauvegardé** (modifications ni suppressions)

**Rechargement de la page :**
- Après sauvegarde, la page est rechargée avec les nouvelles données
- Tous les formulaires sont réinitialisés avec les valeurs sauvegardées en base

---

## Calcul du pourcentage de complétion

### Vue d'ensemble

Le système calcule automatiquement un **pourcentage de complétion** pour chaque fiche afin d'évaluer la qualité et l'exhaustivité des données saisies. Ce pourcentage est utilisé notamment lors de la soumission pour validation.

### Méthode de calcul

Le pourcentage de complétion est basé sur **8 critères** pondérés de manière égale. Chaque critère validé rapporte **1 point**.

**Formule :**
```
Pourcentage de complétion = (score / 8) × 100
```

Où `score` est le nombre de critères validés (entre 0 et 8).

### Les 8 critères de complétion

| # | Critère | Description | Condition de validation | Points |
|---|---------|-------------|-------------------------|--------|
| **1** | **Observateur renseigné** | L'observateur de la fiche est défini | `fiche.observateur` n'est pas NULL | 1 |
| **2** | **Espèce renseignée** | L'espèce observée est définie | `fiche.espece` n'est pas NULL | 1 |
| **3** | **Localisation complète** | Commune et département sont renseignés | `localisation.commune` non vide ET `localisation.departement` ≠ '00' | 1 |
| **4** | **Au moins une observation** | Au moins une observation avec date existe | `fiche.observations.exists()` = True | 1 |
| **5** | **Données d'œufs dans le résumé** | Le nombre d'œufs pondus est renseigné | `resume.nombre_oeufs_pondus` n'est pas NULL ET > 0 | 1 |
| **6** | **Détails du nid** | Description textuelle du nid fournie | `nid.details_nid` non vide ET ≠ "Aucun détail" | 1 |
| **7** | **Hauteur du nid** | Hauteur du nid renseignée | `nid.hauteur_nid` n'est pas NULL ET > 0 | 1 |
| **8** | **Image associée** | Une image de la fiche est disponible | `fiche.chemin_image` non vide | 1 |

### Détail des validations

#### Critère 1 : Observateur renseigné
```python
if self.fiche.observateur:
    score += 1
```
- **Validation** : L'observateur est automatiquement défini lors de la création (utilisateur connecté)
- **Impact** : Ce critère est presque toujours validé (sauf cas exceptionnels)

#### Critère 2 : Espèce renseignée
```python
if self.fiche.espece:
    score += 1
```
- **Validation** : Une espèce doit être sélectionnée dans la liste déroulante
- **Impact** : Champ obligatoire pour la création, donc généralement validé

#### Critère 3 : Localisation complète
```python
if hasattr(self.fiche, 'localisation'):
    loc = self.fiche.localisation
    if (
        loc.commune
        and loc.commune.strip()  # Vérifier que la commune n'est pas vide
        and loc.departement
        and loc.departement != '00'
    ):
        score += 1
```
- **Validation** :
  - Le champ `commune` doit être rempli (pas uniquement des espaces)
  - Le champ `département` doit être différent de '00' (valeur par défaut)
- **Conseils** :
  - Utiliser l'autocomplétion de commune pour remplir automatiquement le département
  - Le département se remplit automatiquement lors de la sélection d'une commune

#### Critère 4 : Au moins une observation
```python
if self.fiche.observations.exists():
    score += 1
```
- **Validation** : Au moins une ligne dans le tableau des observations doit exister
- **Impact** : Les observations sont le cœur de la fiche, ce critère est essentiel

#### Critère 5 : Données d'œufs dans le résumé
```python
if hasattr(self.fiche, 'resume'):
    resume = self.fiche.resume
    if resume.nombre_oeufs_pondus is not None and resume.nombre_oeufs_pondus > 0:
        score += 1
```
- **Validation** :
  - Le champ `nombre_oeufs_pondus` ne doit pas être NULL (non observé)
  - ET la valeur doit être strictement supérieure à 0
- **Note** : Si aucun œuf n'a été pondu (valeur = 0), ce critère n'est PAS validé
- **Conseils** : Remplir le champ "Nombre d'œufs pondus" dans la section "Résumé des Observations"

#### Critère 6 : Détails du nid
```python
if hasattr(self.fiche, 'nid'):
    nid = self.fiche.nid
    if nid.details_nid and nid.details_nid != 'Aucun détail':
        score += 1
```
- **Validation** :
  - Le champ `details_nid` ne doit pas être vide
  - ET ne doit pas contenir la chaîne "Aucun détail" (valeur par défaut à éviter)
- **Conseils** : Décrire la structure, les matériaux, l'emplacement du nid dans la section "Description du Nid"

#### Critère 7 : Hauteur du nid
```python
if hasattr(self.fiche, 'nid'):
    nid = self.fiche.nid
    if nid.hauteur_nid is not None and nid.hauteur_nid > 0:
        score += 1
```
- **Validation** :
  - Le champ `hauteur_nid` ne doit pas être NULL
  - ET la valeur doit être strictement supérieure à 0
- **Note** : La valeur par défaut est 0, qui ne valide PAS le critère
- **Conseils** : Renseigner la hauteur du nid en centimètres dans la section "Description du Nid"

#### Critère 8 : Image associée
```python
if self.fiche.chemin_image:
    score += 1
```
- **Validation** : Le champ `chemin_image` doit contenir un chemin vers une image
- **Impact** : Ce critère est automatiquement validé pour les fiches issues de transcriptions
- **Note** : Pour les saisies manuelles, ce critère n'est généralement pas validé (sauf si une image a été téléversée)

### Exemples de calculs

#### Exemple 1 : Fiche minimale (nouvelle saisie)
- ✅ Observateur renseigné
- ✅ Espèce renseignée
- ❌ Localisation incomplète (département = '00')
- ✅ 1 observation créée
- ❌ Pas de données d'œufs
- ❌ Détails du nid vides
- ❌ Hauteur du nid = 0
- ❌ Pas d'image

**Score : 3/8 = 37.5% → arrondi à 37%**

#### Exemple 2 : Fiche bien complétée
- ✅ Observateur renseigné
- ✅ Espèce renseignée
- ✅ Localisation complète (commune + département)
- ✅ 3 observations créées
- ✅ Nombre d'œufs pondus = 5
- ✅ Détails du nid = "Nid en coupe, matériaux : herbes sèches..."
- ✅ Hauteur du nid = 150 cm
- ❌ Pas d'image

**Score : 7/8 = 87.5% → arrondi à 87%**

#### Exemple 3 : Fiche issue de transcription complète
- ✅ Observateur renseigné
- ✅ Espèce renseignée
- ✅ Localisation complète
- ✅ 5 observations
- ✅ Nombre d'œufs pondus = 4
- ✅ Détails du nid renseignés
- ✅ Hauteur du nid = 200 cm
- ✅ Image de la fiche papier

**Score : 8/8 = 100%**

### Déclenchement du calcul

Le pourcentage de complétion est **calculé automatiquement** dans les cas suivants :

1. **Lors de la sauvegarde de l'état de correction**
   - Méthode `EtatCorrection.save()` (sauf si `skip_auto_calculation=True`)
   - Appelée après chaque modification de fiche

2. **Lors de la soumission pour correction**
   - Méthode `soumettre_pour_correction()` dans la vue
   - Calcul explicite via `etat_correction.calculer_pourcentage_completion()`

3. **Lors de la mise à jour de la fiche**
   - Méthode `FicheObservation.mettre_a_jour_etat_correction()`

### Changement automatique de statut

Le calcul du pourcentage déclenche également un **changement automatique de statut** :

```python
# Passer en "en_edition" si la fiche est en cours de saisie par l'observateur
if pourcentage > 0 and self.statut == 'nouveau':
    self.statut = 'en_edition'
```

**Comportement :**
- Si le pourcentage passe de 0% à une valeur > 0%
- ET que le statut actuel est **"nouveau"**
- Alors le statut passe automatiquement à **"en_edition"**

**Impact :**
- Indique que la fiche a commencé à être éditée
- La fiche reste modifiable par l'observateur
- Le statut ne change PAS si déjà en "en_cours" ou "valide"

### Affichage du pourcentage

Le pourcentage de complétion est affiché :
- Dans le message de confirmation lors de la soumission pour correction
- Exemple : "Fiche #27 soumise pour correction. Complétion : 75%"
- Dans l'interface d'administration ou de gestion des fiches (selon configuration)

### Conseils pour augmenter le pourcentage

Pour obtenir une fiche bien complétée (≥ 75%) :

| Action | Impact | Priorité |
|--------|--------|----------|
| Sélectionner une espèce | +12.5% | ⭐⭐⭐ Obligatoire |
| Renseigner la commune (avec autocomplétion) | +12.5% | ⭐⭐⭐ Très important |
| Ajouter au moins 1 observation | +12.5% | ⭐⭐⭐ Obligatoire |
| Remplir "Nombre d'œufs pondus" (> 0) | +12.5% | ⭐⭐ Important |
| Renseigner "Détails du nid" | +12.5% | ⭐⭐ Important |
| Renseigner "Hauteur du nid" (> 0) | +12.5% | ⭐ Recommandé |
| Associer une image (transcription) | +12.5% | ⭐ Automatique pour transcriptions |

**Note :** L'observateur est automatiquement renseigné (+12.5% gratuit).

---

## Soumission pour validation

### Concept

Lorsqu'une fiche est complète (ou suffisamment avancée), l'observateur peut la **soumettre pour validation**. Cela change le statut de la fiche et la rend accessible aux reviewers pour correction/validation.

### Processus

**1. Prérequis**
- La fiche doit être en statut **"nouveau"** ou **"en_edition"**
- Vous devez être l'**auteur** de la fiche (ou administrateur)

**2. Bouton de soumission**
- Affiché en bas du formulaire de modification
- Libellé : "Soumettre pour correction" ou similaire

**3. Action de soumission**
- **URL** : `http://127.0.0.1:8000/observations/soumettre/{num_fiche}/`
- **Méthode** : POST

**4. Traitement**
- Calcul du **pourcentage de complétion** de la fiche (voir section dédiée ci-dessus)
- Changement du statut de `nouveau` ou `en_edition` vers **`en_cours`**
- Sauvegarde de l'état de correction

**5. Conséquences**
- La fiche devient **lecture seule** pour l'observateur
- Les reviewers et administrateurs peuvent désormais la corriger/valider
- Message de succès : "Fiche #{num_fiche} soumise pour correction. Complétion : {pourcentage}%"
- Redirection vers la vue de détail (lecture seule) : `http://127.0.0.1:8000/observations/{num_fiche}/`

**6. Affichage du pourcentage**
- Le pourcentage de complétion est calculé et affiché dans le message de confirmation
- Exemple : "Fiche #27 soumise pour correction. Complétion : 87%"
- Permet à l'observateur de savoir si la fiche est bien complétée

### Statuts de correction

| Statut | Description | Éditable par observateur | Pourcentage calculé |
|--------|-------------|--------------------------|---------------------|
| **nouveau** | Fiche nouvellement créée | ✅ Oui | 0% |
| **en_edition** | Fiche en cours d'édition | ✅ Oui | > 0% |
| **en_cours** | Soumise pour correction | ❌ Non | Variable |
| **valide** | Validée par un reviewer | ❌ Non | Variable |

**Note :** Les administrateurs et reviewers peuvent modifier les fiches quel que soit leur statut.

### Recommandations avant soumission

Il est conseillé de soumettre une fiche lorsque son pourcentage de complétion est :
- **≥ 75%** : Fiche bien complétée, prête pour review
- **50-74%** : Fiche correcte mais peut être améliorée
- **< 50%** : Fiche incomplète, compléter avant soumission

---

## Correction de transcriptions

### Contexte

Certaines fiches proviennent de la transcription automatique de fiches papier scannées. Ces fiches contiennent :
- Un fichier image (scan de la fiche papier)
- Un fichier JSON (résultat de la transcription automatique)
- Le champ `transcription` est défini à `True`

### Distinction entre nouvelle fiche et correction de transcription

| Aspect | Nouvelle fiche | Correction de transcription |
|--------|----------------|------------------------------|
| **Origine** | Saisie manuelle par l'utilisateur | Import depuis image scannée + OCR/IA |
| **Champ `transcription`** | `False` | `True` |
| **Image disponible** | Non | Oui (lien "Voir l'image" dans l'en-tête) |
| **JSON disponible** | Non | Oui (lien "Voir JSON" dans l'en-tête) |
| **Champs pré-remplis** | Vides (sauf valeurs par défaut) | Pré-remplis avec les données de la transcription |
| **Objectif** | Créer une nouvelle observation | Corriger/valider les données transcrites automatiquement |
| **Pourcentage initial** | Généralement bas (37-50%) | Généralement élevé (75-100%) grâce à l'image |

### Workflow de correction de transcription

1. **Accès à la fiche transcrite**
   - Liste des fiches en attente de correction
   - Clic sur "Modifier" pour ouvrir la fiche

2. **Consultation de l'image**
   - Cliquer sur "Voir l'image" dans l'en-tête
   - Compare les données transcrites avec l'image originale

3. **Correction des champs**
   - Parcourir chaque section
   - Corriger les erreurs de transcription
   - Compléter les champs manquants ou mal transcrits

4. **Vérifications importantes**
   - **Espèce** : Vérifier que l'espèce est correcte
   - **Dates** : Vérifier le format et la cohérence des dates
   - **Nombres** : Vérifier les compteurs (œufs, poussins)
   - **Localisation** : Vérifier commune, coordonnées
   - **Observations** : Relire les notes transcrites

5. **Enregistrement**
   - Sauvegarder les corrections
   - Historique des modifications enregistré

6. **Soumission pour validation**
   - Une fois la correction terminée, soumettre la fiche pour validation
   - Passage au statut "en_cours"
   - Affichage du pourcentage de complétion (généralement élevé pour les transcriptions)

### Erreurs courantes de transcription

- **Confusion de caractères** : O/0, I/1, S/5, etc.
- **Dates mal formatées** : Mauvais ordre jour/mois/année
- **Nombres mal lus** : Écriture manuscrite peu lisible
- **Noms d'espèces** : Noms scientifiques complexes
- **Coordonnées GPS** : Décimales mal placées

**Conseil :** Toujours comparer avec l'image originale pour chaque donnée critique.

---

## Permissions et restrictions

### Permissions par rôle

| Action | Observateur (auteur) | Observateur (autre) | Reviewer | Administrateur |
|--------|----------------------|---------------------|----------|----------------|
| **Créer une fiche** | ✅ Oui | ✅ Oui | ✅ Oui | ✅ Oui |
| **Modifier sa fiche (nouveau/en_edition)** | ✅ Oui | ❌ Non | ✅ Oui | ✅ Oui |
| **Modifier fiche autre auteur (nouveau/en_edition)** | ❌ Non | ❌ Non | ✅ Oui | ✅ Oui |
| **Modifier fiche (en_cours)** | ❌ Non | ❌ Non | ✅ Oui | ✅ Oui |
| **Modifier fiche (valide)** | ❌ Non | ❌ Non | ✅ Oui | ✅ Oui |
| **Soumettre sa fiche** | ✅ Oui | ❌ Non | ✅ Oui | ✅ Oui |
| **Valider une fiche** | ❌ Non | ❌ Non | ✅ Oui | ✅ Oui |
| **Voir l'historique** | ✅ Oui | ✅ Oui* | ✅ Oui | ✅ Oui |

*Note :* L'historique peut être visible par tous selon la configuration.

### Restrictions d'accès

**Tentative de modification d'une fiche non autorisée :**
- Message d'erreur : "Vous n'êtes pas autorisé à modifier cette fiche. Seul l'auteur ({username}) peut continuer la saisie."
- Redirection vers la vue de détail (lecture seule)

**Fiche en cours de correction :**
- L'observateur ne peut plus modifier la fiche après soumission
- Redirection vers la vue de détail si tentative d'accès à la page de modification

### Champs en lecture seule

Certains champs sont toujours en lecture seule ou le deviennent selon le contexte :

| Champ | Lecture seule | Condition |
|-------|---------------|-----------|
| **N° Fiche** | ✅ Toujours | Généré automatiquement |
| **Observateur** | ✅ Presque toujours | Modifiable uniquement par admin/reviewer |
| **Département** | ✅ Toujours | Auto-rempli via autocomplétion commune |
| **Date de création** | ✅ Toujours | Timestamp automatique |
| **Date des remarques** | ✅ Toujours | Timestamp automatique |

---

## Historique des modifications

### Concept

Toutes les modifications apportées à une fiche sont enregistrées dans un **historique de modifications** (`HistoriqueModification`). Cela permet de tracer qui a modifié quoi et quand.

### Accès à l'historique

**URL :** `http://127.0.0.1:8000/observations/historique/{num_fiche}/`

**Bouton :** "Voir l'historique" dans la page de modification

### Informations enregistrées

Pour chaque modification, l'historique contient :

| Champ | Description |
|-------|-------------|
| **Fiche** | Numéro de la fiche modifiée |
| **Champ modifié** | Nom du champ (ex: "commune", "nombre_oeufs", etc.) |
| **Ancienne valeur** | Valeur avant modification |
| **Nouvelle valeur** | Valeur après modification |
| **Catégorie** | Type de modification (fiche, localisation, observation, remarque, nid, causes_echec, resume_observation) |
| **Modifié par** | Utilisateur ayant effectué la modification |
| **Date de modification** | Horodatage de la modification |

### Types d'événements enregistrés

1. **Modification de champ**
   - Changement de valeur d'un champ existant
   - Exemple : "commune" modifiée de "Paris" à "Lyon"

2. **Ajout d'observation**
   - Création d'une nouvelle observation
   - Enregistre tous les champs de la nouvelle observation

3. **Suppression d'observation**
   - Suppression d'une observation existante
   - Champ : `observation_supprimee`
   - Ancienne valeur : Détails de l'observation supprimée
   - Nouvelle valeur : vide

4. **Ajout de remarque**
   - Création d'une nouvelle remarque
   - Champ : `remarque_ajoutee`
   - Nouvelle valeur : Texte de la remarque

5. **Suppression de remarque**
   - Suppression d'une remarque existante
   - Champ : `remarque_supprimee`
   - Ancienne valeur : Texte de la remarque
   - Nouvelle valeur : vide

6. **Modification de l'année de la fiche**
   - Changement de l'année de la fiche
   - Entraîne une mise à jour automatique de l'année de toutes les observations liées

### Consultation de l'historique

**Page d'historique :**
- Liste chronologique (du plus récent au plus ancien)
- Groupement par modification (toutes les modifications d'une même sauvegarde)
- Affichage de l'utilisateur et de la date pour chaque groupe
- Détail de chaque champ modifié avec ancienne et nouvelle valeur

**Utilité :**
- Audit des modifications
- Résolution de conflits
- Traçabilité des corrections
- Analyse de l'activité des utilisateurs

---

## Annexes

### Raccourcis clavier disponibles

| Action | Raccourci | Contexte |
|--------|-----------|----------|
| Navigation dans les suggestions | ↑ / ↓ | Autocomplétion commune ou espèce |
| Sélectionner une suggestion | Entrée | Autocomplétion commune ou espèce |
| Fermer les suggestions | Échap | Autocomplétion commune ou espèce |

### Messages d'erreur courants

| Message | Cause | Solution |
|---------|-------|----------|
| "Ce champ est obligatoire." | Champ requis non rempli | Remplir le champ obligatoire (ex: date_observation) |
| "Vous n'êtes pas autorisé à modifier cette fiche." | Tentative de modification d'une fiche d'un autre auteur | Seul l'auteur ou un admin peut modifier |
| "Erreurs dans les informations de localisation" | Coordonnées invalides ou autre erreur de validation | Vérifier les valeurs saisies (latitude, longitude, altitude) |
| "Une erreur est survenue lors de la sauvegarde" | Erreur serveur ou base de données | Vérifier les logs, contacter l'administrateur |
| Constraint violation (base de données) | Violation de contrainte (ex: jour sans mois, nombre d'éclos > nombre pondus) | Vérifier la cohérence des données saisies |

### Bonnes pratiques

1. **Saisie de nouvelles fiches**
   - Remplir au minimum l'espèce et une observation avant d'enregistrer
   - Compléter progressivement les différentes sections
   - Enregistrer régulièrement pour éviter les pertes de données
   - Viser un pourcentage de complétion ≥ 75% avant soumission

2. **Modification de fiches**
   - Toujours consulter l'image originale (si disponible) avant de modifier une transcription
   - Vérifier la cohérence des données (dates, compteurs)
   - Enregistrer après chaque bloc de modifications pour éviter les pertes

3. **Utilisation des observations**
   - Créer une observation par visite sur le terrain
   - Renseigner la date et l'heure précises
   - Décocher "Heure connue" si l'heure est incertaine

4. **Soumission pour validation**
   - Vérifier que toutes les sections importantes sont remplies
   - Consulter le pourcentage de complétion
   - Ne soumettre que lorsque la fiche est prête pour review (≥ 75% recommandé)

5. **Remarques**
   - Utiliser les remarques pour des commentaires généraux sur la fiche
   - Ne pas confondre avec le champ "Observations" (observations de terrain)
   - Les remarques sont horodatées automatiquement

6. **Augmentation du pourcentage de complétion**
   - Utiliser l'autocomplétion pour la commune (remplit automatiquement le département)
   - Remplir systématiquement "Nombre d'œufs pondus" dans le résumé
   - Ajouter une description dans "Détails du nid"
   - Renseigner la hauteur du nid (en cm)

### Fichiers de code concernés

Pour les développeurs ou pour aller plus loin :

| Fichier | Description |
|---------|-------------|
| `observations/views/saisie_observation_view.py` | Vue principale (lignes 150-597) |
| `observations/forms.py` | Définition des formulaires |
| `observations/models.py` | Modèles de données (FicheObservation, Observation, EtatCorrection, etc.) - Lignes 311-370 pour `calculer_pourcentage_completion()` |
| `observations/templates/saisie/saisie_observation_optimise.html` | Template HTML de la page |
| `observations/static/Observations/js/saisie_observation.js` | JavaScript client (autocomplétion, GPS, gestion des suppressions) |
| `observations/urls.py` | Configuration des URLs |

---

## Résumé visuel du workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   CRÉATION D'UNE NOUVELLE FICHE                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  /observations/ (GET)
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Formulaire vide avec         │
              │  valeurs par défaut           │
              │  - Observateur = user         │
              │  - Année = année courante     │
              │  - Statut = "nouveau"         │
              │  - Pourcentage = 0%           │
              └───────────────────────────────┘
                              │
                              ▼
                   Remplir les champs
                   (espèce, observations, etc.)
                              │
                              ▼
                     Clic sur "Enregistrer"
                              │
                              ▼
                  /observations/ (POST)
                              │
                    ┌─────────┴─────────┐
                    │                   │
            Validation OK          Validation KO
                    │                   │
                    ▼                   ▼
         Transaction atomique      Affichage erreurs
         ─────────────────────      Reste sur la page
         1. Créer FicheObservation
         2. Créer objets liés
            - Localisation
            - Nid
            - ResumeObservation
            - CausesEchec
            - EtatCorrection (statut=nouveau, %=0)
         3. Sauvegarder observations
         4. Sauvegarder remarques
         5. Calculer % complétion
            → Si % > 0 : statut passe en "en_edition"
         6. Enregistrer historique
                    │
                    ▼
          Redirection vers
          /observations/modifier/{num_fiche}/
          (fiche créée, num_fiche attribué)
                    │
                    ▼
┌───────────────────────────────────────────────────────────────────┐
│              MODIFICATION DE LA FICHE EXISTANTE                   │
└───────────────────────────────────────────────────────────────────┘
                    │
                    ▼
    /observations/modifier/{num_fiche}/ (GET)
                    │
          ┌─────────┴─────────┐
          │                   │
    Vérification          Fiche non trouvée
    permissions           ou pas autorisé
          │                   │
    Autorisé                  ▼
          │              Page d'erreur
          ▼              ou redirection
┌─────────────────────────┐
│ Formulaire pré-rempli   │
│ avec données existantes │
│ - Fiche                 │
│ - Localisation          │
│ - Nid                   │
│ - Observations          │
│ - Résumé                │
│ - Causes d'échec        │
│ - Remarques             │
│ + Pourcentage actuel    │
└─────────────────────────┘
          │
          ▼
   Modifier les champs
   (ajouter/supprimer observations, etc.)
          │
          ▼
   Clic sur "Enregistrer"
          │
          ▼
   /observations/modifier/{num_fiche}/ (POST)
          │
    ┌─────┴─────┐
    │           │
Validation   Validation
   OK           KO
    │           │
    ▼           ▼
Transaction  Affichage
atomique     erreurs
─────────
1. Récupérer état avant modification
2. Mettre à jour FicheObservation
3. Mettre à jour objets liés
4. Sauvegarder observations
   - Nouvelles : créer
   - Modifiées : mettre à jour
   - Supprimées : supprimer
5. Sauvegarder remarques
6. Calculer nouveau % complétion
   → Mise à jour statut si nécessaire
7. Enregistrer historique (diff)
8. Mettre à jour année observations
    │
    ▼
Redirection vers
/observations/modifier/{num_fiche}/
(modifications sauvegardées, nouveau % affiché)
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│             SOUMISSION POUR VALIDATION (optionnel)            │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
Clic sur "Soumettre pour correction"
    │
    ▼
/observations/soumettre/{num_fiche}/ (POST)
    │
    ▼
Vérifications :
- Auteur ou admin ?
- Statut = "nouveau" ou "en_edition" ?
    │
    ▼
Calcul pourcentage complétion
(score/8 × 100)
    │
    ▼
Statut ← "en_cours"
    │
    ▼
Message : "Fiche soumise. Complétion : XX%"
    │
    ▼
Redirection vers
/observations/{num_fiche}/ (lecture seule)
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  FICHE EN COURS DE CORRECTION/VALIDATION                      │
│  (lecture seule pour l'observateur)                           │
│  (éditable par reviewers/admins)                              │
└───────────────────────────────────────────────────────────────┘
```

---

**Fin du guide d'utilisation**

Pour toute question ou problème, consultez l'historique des modifications ou contactez un administrateur.
