# 📝 Guide de Saisie - Formulaires Observations

> **Résumé** : Guide détaillé sur les fonctionnalités avancées de saisie dans les formulaires d'observation : correction de l'observateur, autocomplétion des espèces et des communes.

---

## 🎯 Vue d'Ensemble

Ce document décrit les trois fonctionnalités clés de saisie :

| Fonctionnalité | Description |
|----------------|-------------|
| [Correction de l'Observateur](#correction-de-lobservateur) | Gestion des noms OCR mal transcrits |
| [Sélection d'Espèce](#selection-despece) | Recherche intelligente avec autocomplétion |
| [Sélection de Commune](#selection-de-commune) | Autocomplétion avec géolocalisation |

---

## 👤 Correction de l'Observateur

### Contexte : Le Problème des Transcriptions OCR

Lors de la transcription OCR d'une fiche papier, le nom de l'observateur est extrait automatiquement par Gemini. Ce nom est stocké dans le fichier JSON et utilisé pour créer un utilisateur temporaire.

**Problèmes fréquents :**

- Erreurs de reconnaissance (ex: "Dupond" → "Dupont")
- Noms partiels (prénom manquant)
- Doublons avec des utilisateurs existants

!!! warning "Observateurs temporaires"
    Les utilisateurs créés par OCR ont le flag `est_transcription=True` et doivent être corrigés ou fusionnés avec un compte existant.

---

### Détection Automatique

Au chargement d'une fiche, le système vérifie automatiquement :

1. Si l'observateur actuel a été créé par transcription OCR
2. S'il existe des observateurs similaires (score ≥ 80%)

Si ces conditions sont remplies, une **alerte jaune** s'affiche :

```
⚠️ L'observateur de cette fiche semble avoir été créé par transcription.
   Des correspondances similaires ont été trouvées.
   [Voir les suggestions]
```

---

### Ouverture de la Modale de Correction

**Deux façons d'ouvrir la modale :**

1. Cliquer sur le bouton **"Corriger l'observateur"** à côté du champ observateur
2. Cliquer sur **"Voir les suggestions"** dans l'alerte jaune

---

### Structure de la Modale

La modale de correction est organisée en plusieurs sections :

```
┌─────────────────────────────────────────────────────────────┐
│  🔧 Correction de l'observateur                         [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📌 OBSERVATEUR ACTUEL                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Nom actuel : Jean Dupond                            │   │
│  │ Statistiques : 3 fiche(s) - Transcription OCR      │   │
│  │ Nom OCR original : J. DUPOND                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  💡 SUGGESTIONS AUTOMATIQUES                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Jean Dupont          92%   15 fiches  [Sélectionner]│   │
│  │ Jeanne Dupond        85%    2 fiches  [Sélectionner]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🔍 RECHERCHE MANUELLE                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Saisir le nom correct : [_____________________]     │   │
│  │                                     [Rechercher]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📋 RÉSULTATS DE RECHERCHE                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Nom          │ Similarité │ Type  │ Fiches │ Action │   │
│  │─────────────────────────────────────────────────────│   │
│  │ ...          │    ...     │  ...  │  ...   │  [✓]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ➕ CRÉER UN NOUVEL OBSERVATEUR                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Aucun résultat trouvé.                              │   │
│  │ Créer "Jean Dupont" ?     [Créer cet observateur]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 1 : Observateur Actuel

Affiche les informations sur l'observateur actuellement associé à la fiche :

| Information | Description |
|-------------|-------------|
| **Nom actuel** | Nom affiché dans le select |
| **Statistiques** | Nombre de fiches + type (OCR ou validé) |
| **Nom OCR original** | Nom extrait du fichier JSON de transcription |

!!! tip "Nom OCR original"
    Le nom OCR est lu depuis `informations_generales.observateur` dans le fichier JSON associé à la fiche. Il permet de voir ce que Gemini a réellement transcrit.

---

### Section 2 : Suggestions Automatiques

Le système recherche automatiquement les observateurs similaires :

**Algorithme de similarité :**

- Utilise `difflib.SequenceMatcher` (fuzzy matching)
- Seuil par défaut : **80%** de similarité
- Compare le nom complet (prénom + nom)

**Affichage des suggestions :**

- Triées par score décroissant
- Limitées à 10 résultats
- Badge de pourcentage coloré (vert ≥ 90%)

**Actions :**

- Cliquer sur **[Sélectionner]** ouvre la modale de confirmation

---

### Section 3 : Recherche Manuelle

Permet de rechercher un observateur par son nom :

**Fonctionnement :**

1. Taper au moins 2 caractères
2. Recherche avec **debounce de 300ms**
3. Résultats affichés dans le tableau

**Logique de recherche :**

1. Priorité aux noms qui **commencent par** le terme
2. Puis noms qui **contiennent** le terme
3. Exclusion de l'observateur actuel

**API utilisée :** `/api/observateurs/rechercher/?q=terme&reference_id=123`

---

### Section 4 : Créer un Nouvel Observateur

Si aucun résultat n'est trouvé, propose de créer un nouvel observateur :

**Création :**

- Username généré : `prenom.nom` (avec suffixe numérique si doublon)
- Email : `username@observateur.local`
- Flag : `est_transcription=False` (créé manuellement)
- Rôle : `observateur`
- Statut : `est_valide=True`, `is_active=True`

!!! warning "Permissions requises"
    Seuls les **reviewers** et **administrateurs** peuvent créer de nouveaux observateurs.

---

### Modale de Confirmation de Fusion

Après sélection d'un observateur cible, une modale de confirmation s'affiche :

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ Confirmer le remplacement                           [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Voulez-vous remplacer Jean Dupond par Jean Dupont ?        │
│                                                             │
│  ○ Cette fiche uniquement                                   │
│  ● Toutes les fiches (3 fiches concernées)                 │
│                                                             │
│  ⚠️ Si vous fusionnez toutes les fiches, l'ancien          │
│     observateur sera supprimé ou désactivé.                 │
│                                                             │
│                    [Annuler]  [Confirmer la fusion]         │
└─────────────────────────────────────────────────────────────┘
```

**Options de fusion :**

| Option | Comportement |
|--------|--------------|
| **Cette fiche uniquement** | Transfère uniquement la fiche courante |
| **Toutes les fiches** | Transfère toutes les fiches de l'ancien observateur |

**Après fusion complète (toutes les fiches) :**

- Si `est_transcription=True` ou email `@observateur.local` → **Suppression** de l'ancien compte
- Sinon → **Désactivation** (`is_active=False`)

---

### API Utilisées

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/observateurs/similaires/` | GET | Recherche d'observateurs similaires |
| `/api/observateurs/rechercher/` | GET | Recherche par nom (autocomplétion) |
| `/api/observateurs/fusionner/` | POST | Exécution de la fusion |
| `/api/observateurs/nom-ocr/` | GET | Lecture du nom OCR depuis le JSON |
| `/api/observateurs/creer/` | POST | Création d'un nouvel observateur |

---

## 🐦 Sélection d'Espèce

### Fonctionnement

Le champ espèce utilise une recherche intelligente avec autocomplétion :

1. Le `<select>` HTML est masqué
2. Un champ de texte de recherche le remplace visuellement
3. Les options sont filtrées localement (pas d'appel API)

---

### Utilisation

**Étapes de saisie :**

1. Cliquer dans le champ "Tapez pour rechercher une espèce..."
2. Commencer à taper le nom de l'espèce
3. Attendre **800ms** (debounce) pour voir les résultats
4. Sélectionner l'espèce avec la souris ou le clavier

**Navigation au clavier :**

| Touche | Action |
|--------|--------|
| `↓` | Élément suivant |
| `↑` | Élément précédent |
| `Entrée` | Sélectionner |
| `Échap` | Fermer la liste |

---

### Affichage des Résultats

```
┌─────────────────────────────────────────────────┐
│ Mésange                                         │
├─────────────────────────────────────────────────┤
│ Mésange bleue (MESBLE)                          │
│ Mésange charbonnière (MESCHA)                   │
│ Mésange huppée (MESHUP)                         │
│ Mésange noire (MESNOI)                          │
└─────────────────────────────────────────────────┘
```

**Caractéristiques :**

- Terme recherché en **gras** dans les résultats
- Maximum 300px de hauteur (scroll si nécessaire)
- Ombre portée pour visibilité

---

## 🏘️ Sélection de Commune

### Fonctionnement

Le champ commune utilise une autocomplétion connectée à l'API :

1. Taper au moins **2 caractères**
2. Recherche avec **debounce de 300ms**
3. Appel à `/geo/rechercher-communes/`
4. Affichage des résultats

---

### Utilisation

**Étapes de saisie :**

1. Cliquer dans le champ "Commune"
2. Commencer à taper le nom de la commune
3. Les résultats s'affichent automatiquement
4. Cliquer sur une commune pour la sélectionner

---

### Affichage des Résultats

```
┌─────────────────────────────────────────────────┐
│ Paris (75) - Paris                              │
│ Paris 1er Arrondissement (75) - Paris           │
│ Paris 2e Arrondissement (75) - Paris            │
└─────────────────────────────────────────────────┘
```

Format : **Nom commune** (code département) - Nom département

---

### Remplissage Automatique

À la sélection d'une commune, les champs suivants sont **automatiquement remplis** (si vides ou à "00") :

| Champ | Valeur |
|-------|--------|
| **Commune** | Nom de la commune |
| **Département** | Code département (ex: "75") |
| **Latitude** | Latitude du centre de la commune |
| **Longitude** | Longitude du centre de la commune |
| **Altitude** | Altitude moyenne (avec confirmation) |

!!! note "Altitude"
    Pour l'altitude, une confirmation est demandée avant le remplissage :
    "Utiliser l'altitude de la commune Paris : 35m ?"

---

### Intégration GPS

Si les coordonnées GPS sont déjà renseignées (via le bouton "Ma position"), elles sont envoyées à l'API :

```
/geo/rechercher-communes/?q=Paris&lat=48.8566&lon=2.3522
```

**Avantage :** Les résultats sont filtrés dans un rayon de **10 km** autour de la position GPS.

---

### Navigation au Clavier

| Touche | Action |
|--------|--------|
| `↓` | Commune suivante |
| `↑` | Commune précédente |
| `Entrée` | Sélectionner |
| `Échap` | Fermer la liste |

---

## 🔗 Voir Aussi

- [📦 Application Observations](./observations.md) - Documentation principale
- [📦 Application Geo](./geo.md) - API des communes
- [📦 Application Accounts](./accounts.md) - Gestion des utilisateurs
- [📦 Application Taxonomy](./taxonomy.md) - Gestion des espèces
