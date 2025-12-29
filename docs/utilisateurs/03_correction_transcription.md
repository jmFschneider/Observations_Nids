# Guide utilisateur - Correction et Transcription

## Vue d'ensemble

Ce guide vous accompagne dans l'utilisation de l'outil de **transcription automatique** et de **correction** des fiches d'observation issues de carnets papier numérisés.

---

## Table des matières

1. [Qu'est-ce que la transcription ?](#1-quest-ce-que-la-transcription)
2. [Préparer vos images](#2-preparer-vos-images)
3. [Étape 1 : Upload et sélection du dossier](#3-etape-1-upload-et-selection-du-dossier)
4. [Étape 2 : Lancement de la transcription](#4-etape-2-lancement-de-la-transcription)
5. [Étape 3 : Suivi du traitement](#5-etape-3-suivi-du-traitement)
6. [Étape 4 : Résultats de la transcription](#6-etape-4-resultats-de-la-transcription)
7. [Étape 5 : Corriger une fiche](#7-etape-5-corriger-une-fiche)
8. [Visualiser les fichiers source (JPEG et JSON)](#8-visualiser-les-fichiers-source-jpeg-et-json)
9. [Ajouter des observations et remarques](#9-ajouter-des-observations-et-remarques)
10. [Logique commune avec la saisie manuelle](#10-logique-commune-avec-la-saisie-manuelle)
11. [Questions fréquentes](#11-questions-frequentes)

---

## 1. Qu'est-ce que la transcription ?

### Principe

La transcription permet de **numériser automatiquement** des carnets d'observations papier scannés.

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Carnet    │  →    │  Scanner/   │  →    │   Fichier   │
│   Papier    │       │   Photo     │       │    JPEG     │
└─────────────┘       └─────────────┘       └─────────────┘
                                                    ↓
                                            ┌─────────────┐
                                            │     IA      │
                                            │  (Gemini)   │
                                            └─────────────┘
                                                    ↓
                                            ┌─────────────┐
                                            │  Fichier    │
                                            │   JSON      │
                                            └─────────────┘
                                                    ↓
                                            ┌─────────────┐
                                            │  Correction │
                                            │   Humaine   │
                                            └─────────────┘
                                                    ↓
                                            ┌─────────────┐
                                            │   Fiche     │
                                            │  Validée    │
                                            └─────────────┘
```

### Technologie utilisée

- **OCR intelligent** : Google Gemini 2.0 Flash
- **Compréhension contextuelle** : L'IA lit et interprète les données manuscrites
- **Structuration automatique** : Génération de fiches au format JSON

---

## 2. Préparer vos images

### Format des images

| Critère | Recommandation | Accepté |
|---------|----------------|---------|
| **Format** | JPEG (`.jpg`, `.jpeg`) | PNG |
| **Résolution** | 1600-2000 pixels de largeur | 800-4000 pixels |
| **Qualité** | Haute qualité, bonne lisibilité | Moyenne acceptable |
| **Taille de fichier** | < 5 MB par image | < 10 MB |

---

### Conseils pour de bons résultats

✅ **Bonne pratique** :
- Éclairage uniforme, sans ombres
- Texte bien lisible
- Image nette (pas de flou)
- Contraste suffisant
- Page entière visible
- Orientation correcte

❌ **À éviter** :
- Photos floues ou pixelisées
- Mauvais éclairage (trop sombre/trop clair)
- Reflets ou ombres importantes
- Texte coupé ou masqué
- Feuille pliée ou froissée

---

### Organisation des fichiers

**Créez un dossier par campagne** :

```
/media/
├── campagne_2024_printemps/
│   ├── carnet_page_01.jpg
│   ├── carnet_page_02.jpg
│   ├── carnet_page_03.jpg
│   └── ...
│
├── campagne_2024_ete/
│   ├── observations_juillet_01.jpg
│   ├── observations_juillet_02.jpg
│   └── ...
│
└── campagne_2025_hiver/
    └── ...
```

---

## 3. Étape 1 : Upload et sélection du dossier

### Accéder à l'outil de transcription

1. **Depuis le menu principal** : Menu "Transcription" → "Transcription d'images"
2. **Ou depuis** : Menu "Transcription" → "Préparer des images" (pour le pré-traitement)

---

### Uploader vos images

1. **Page de sélection**
   - Vous arrivez sur la page de sélection de répertoire
   - Vous pouvez voir les dossiers déjà uploadés

2. **Uploader un nouveau dossier** (si nécessaire)
   - Cliquez sur "📤 Upload des images"
   - Sélectionnez toutes les images d'une campagne
   - Attendez la fin de l'upload
   - Les images sont organisées automatiquement par date

3. **Sélectionner un dossier existant**
   - Liste des dossiers disponibles
   - Aperçu du nombre d'images dans chaque dossier
   - Cliquez sur le dossier à traiter

---

### Validation de la sélection

Une fois le dossier sélectionné :

- **Nom du dossier** : `campagne_2024_printemps`
- **Nombre de fichiers** : 15 images JPEG
- **Estimation du temps** : ~1-2 minutes (selon le nombre d'images)

Cliquez sur **"➡️ Suivant"** pour continuer.

---

## 4. Étape 2 : Lancement de la transcription

### Vérification avant le lancement

Avant de lancer la transcription, assurez-vous :

- ✅ Toutes les images sont présentes
- ✅ Les images sont de bonne qualité
- ✅ Le dossier sélectionné est le bon

---

### Démarrer le traitement

1. **Cliquez sur "🚀 Lancer la transcription"**
   - Le traitement démarre immédiatement
   - Vous êtes redirigé vers la page de suivi

2. **Traitement asynchrone**
   - Le traitement se fait en arrière-plan par **Celery**
   - Vous pouvez fermer la page et revenir plus tard
   - Les résultats sont sauvegardés automatiquement

---

## 5. Étape 3 : Suivi du traitement

### Page de progression

```
┌──────────────────────────────────────────┐
│  Transcription en cours...               │
│                                          │
│  📊 Progression                          │
│  ████████████░░░░░░░░  60%              │
│                                          │
│  📄 Fichier en cours :                   │
│  carnet_page_09.jpg                     │
│                                          │
│  ✅ Traités : 9 / 15                     │
│  ⏱️ Temps écoulé : 1 min 23 s            │
│  ⌛ Temps estimé restant : 55 s          │
│                                          │
└──────────────────────────────────────────┘
```

---

### Informations affichées

| Information | Description |
|-------------|-------------|
| **Barre de progression** | Pourcentage global de complétion |
| **Fichier en cours** | Nom de l'image actuellement traitée |
| **Nombre traités** | X / Total |
| **Temps écoulé** | Depuis le début du traitement |
| **Temps restant** | Estimation basée sur la vitesse moyenne |

---

### Que se passe-t-il pendant le traitement ?

Pour chaque image :

1. **Chargement** : L'image est envoyée à l'API Gemini
2. **Analyse OCR** : L'IA lit le texte manuscrit/imprimé
3. **Extraction** : Les données sont extraites (espèce, date, lieu, observations)
4. **Structuration** : Un fichier JSON est généré
5. **Validation** : La structure JSON est vérifiée
6. **Correction** : Si nécessaire, le JSON est corrigé automatiquement
7. **Sauvegarde** : Le JSON est enregistré dans le dossier de résultats

---

### En cas de problème

Si une image pose problème :
- Elle est marquée comme "erreur"
- Le traitement continue avec les autres images
- Vous pourrez consulter les erreurs dans les résultats

---

## 6. Étape 4 : Résultats de la transcription

### Page de résultats

Une fois le traitement terminé :

```
┌──────────────────────────────────────────┐
│  ✅ Transcription terminée !              │
│                                          │
│  📊 Statistiques                         │
│  • Total d'images : 15                   │
│  • Réussies : 14                         │
│  • Échecs : 1                            │
│  • Taux de réussite : 93.3%             │
│  • Durée totale : 2 min 18 s            │
│                                          │
│  📁 Résultats disponibles dans :         │
│  /media/transcription_results/...        │
│                                          │
└──────────────────────────────────────────┘
```

---

### Liste des fichiers traités

| Fichier | Statut | JSON généré | Actions |
|---------|--------|-------------|---------|
| carnet_page_01.jpg | ✅ Succès | ✓ Disponible | 👁️ Voir  📝 Corriger |
| carnet_page_02.jpg | ✅ Succès | ✓ Disponible | 👁️ Voir  📝 Corriger |
| carnet_page_03.jpg | ❌ Erreur | - | 🔄 Retraiter |
| ... | ... | ... | ... |

---

### Télécharger les résultats

Vous pouvez télécharger :
- **Fichiers JSON individuels** : Un par image
- **Archive complète** : Tous les JSON en un seul fichier ZIP
- **Rapport de transcription** : Statistiques et détails

---

## 7. Étape 5 : Corriger une fiche

### Accéder à la correction

Depuis la page de résultats :

1. **Cliquez sur "📝 Corriger"** à côté de la fiche
2. Vous arrivez sur la page de correction

---

### Interface de correction

La page de correction ressemble à la page de saisie manuelle, avec des sections supplémentaires :

```
┌─────────────────────────────────────────────────┐
│  Correction de fiche - carnet_page_01.jpg       │
├─────────────────────────────────────────────────┤
│  📷 Image source      📄 JSON source            │
│  [Aperçu JPEG]       [Aperçu JSON]             │
├─────────────────────────────────────────────────┤
│  📋 Informations générales                      │
│  Fiche ID : 12345 (grisé = non modifiable)     │
│  N° perso de fiche : 2024-001                   │
│  Observateur : Jean Dupont                      │
├─────────────────────────────────────────────────┤
│  📍 Localisation                                │
│  Commune : Strasbourg                           │
│  Coordonnées : 48.5734, 7.7521                  │
├─────────────────────────────────────────────────┤
│  🐦 Description du Nid                          │
│  Espèce : Cigogne blanche                       │
│  Année : 2024                                   │
├─────────────────────────────────────────────────┤
│  📊 Observations                                │
│  [Liste des observations extraites]             │
│  + Ajouter une observation                      │
├─────────────────────────────────────────────────┤
│  📝 Causes d'échec et remarques                 │
│  [Remarques de transcription]                   │
│  + Ajouter/Modifier                             │
├─────────────────────────────────────────────────┤
│  [💾 Enregistrer]  [✓ Valider la correction]   │
│  ↑ Boutons aussi en barre flottante mobile     │
└─────────────────────────────────────────────────┘
```

💡 **Nouveau** : Sur mobile/tablette, une **barre flottante** reste visible en bas pour un accès rapide aux boutons, même quand vous scrollez dans le long formulaire !

---

### Vérifier et corriger les données

Pour chaque section, vérifiez et corrigez si nécessaire :

#### 1. Localisation
- **Vérifier la commune** : L'IA peut se tromper
  - 💡 **Astuce** : La recherche de communes est optimisée - tapez quelques lettres et les résultats s'affichent par ordre de pertinence
  - Les communes à nom court (Ur, Ger, Eu) apparaissent en premier dans les résultats
- **Corriger les coordonnées** : Si imprécises
- **Préciser le lieu-dit** : Si manquant

#### 2. Informations du nid
- **Vérifier l'espèce** : L'OCR peut confondre des noms proches
- **Corriger l'année** : Si mal lue
- **Compléter les informations** : Ajouter ce qui manque

#### 3. Observations
- **Vérifier les dates** : Format correct ?
- **Vérifier les nombres** : Œufs et poussins corrects ?
- **Corriger le texte** : Erreurs de lecture OCR

#### 4. Remarques
- **Lire les remarques auto-générées** : L'IA peut ajouter des notes
- **Ajouter vos propres remarques** : Pour les correcteurs suivants

---

## 8. Visualiser les fichiers source (JPEG et JSON)

### Afficher l'image source

1. **Cliquez sur "📷 Voir l'image source"**
   - Une fenêtre popup s'ouvre
   - L'image JPEG scannée est affichée en grand
   - Vous pouvez zoomer pour voir les détails

2. **Utilité**
   - Comparer avec les données extraites
   - Vérifier les zones illisibles
   - Corriger les erreurs de lecture

---

### Afficher le JSON source

1. **Cliquez sur "📄 Voir le JSON"**
   - Le JSON brut est affiché
   - Format structuré et lisible

2. **Exemple de JSON**

```json
{
  "espece": "Cigogne blanche",
  "annee": 2024,
  "localisation": {
    "commune": "Strasbourg",
    "coordonnees": "48.5734, 7.7521",
    "lieu_dit": "La Robertsau"
  },
  "observations": [
    {
      "date": "2024-04-15",
      "nombre_oeufs": 3,
      "nombre_poussins": 0,
      "notes": "Ponte terminée"
    },
    {
      "date": "2024-05-01",
      "nombre_oeufs": 0,
      "nombre_poussins": 3,
      "notes": "Éclosion réussie"
    }
  ],
  "remarques": [
    "Nid visible depuis la rue"
  ]
}
```

3. **Utilité**
   - Voir exactement ce que l'IA a extrait
   - Comprendre les erreurs de structure
   - Référence pour les corrections

---

### Télécharger les fichiers

- **Télécharger le JPEG** : Bouton "⬇️ Télécharger l'image"
- **Télécharger le JSON** : Bouton "⬇️ Télécharger le JSON"

---

## 9. Ajouter des observations et remarques

### ⚠️ Important : Même logique que la saisie manuelle

**La correction fonctionne exactement comme la saisie manuelle** !

Référez-vous au guide de saisie pour les détails : [Saisir une nouvelle observation](./02_saisie_nouvelle_observation.md)

---

### Ajouter une observation

1. **La fiche doit être enregistrée au moins une fois**
   - Comme pour la saisie manuelle
   - Cliquez sur "💾 Enregistrer" si ce n'est pas déjà fait
   - 💡 **Astuce mobile** : Utilisez la barre flottante en bas pour accéder rapidement au bouton Enregistrer

2. **Cliquez sur "+ Ajouter une observation"**
   - Formulaire identique à la saisie manuelle
   - Remplissez les champs (date, œufs, poussins, notes)
   - Enregistrez l'observation

3. **Modifier une observation existante**
   - Cliquez sur ✏️ à côté de l'observation
   - Modifiez les champs
   - Enregistrez

4. **Supprimer une observation**
   - Cliquez sur 🗑️
   - Confirmez la suppression

---

### Ajouter une remarque

1. **Cliquez sur "+ Ajouter une remarque"**
   - Zone de texte libre
   - Saisissez votre remarque

2. **Types de remarques utiles en correction**

| Type | Exemple |
|------|---------|
| **Correction OCR** | "Date corrigée : 15/04 au lieu de 15/01 (erreur de lecture)" |
| **Donnée manquante** | "Nombre d'œufs illisible sur l'image source" |
| **Incertitude** | "Espèce probablement Cigogne blanche, à confirmer" |
| **Amélioration** | "Coordonnées GPS ajoutées manuellement" |

---

## 10. Logique commune avec la saisie manuelle

### Workflows identiques

```
┌─────────────────────────────────────────────┐
│                                             │
│  Saisie manuelle    ↔️    Correction        │
│                                             │
│  1. Localisation    ↔️    1. Localisation   │
│  2. Enregistrer     ↔️    2. Enregistrer    │
│  3. Observations    ↔️    3. Observations   │
│  4. Remarques       ↔️    4. Remarques      │
│  5. Valider         ↔️    5. Valider        │
│                                             │
└─────────────────────────────────────────────┘
```

### Différences mineures

| Aspect | Saisie manuelle | Correction transcription |
|--------|----------------|--------------------------|
| **Données initiales** | Vides | Pré-remplies par l'IA |
| **Fiche ID** | Attribué automatiquement | Attribué automatiquement |
| **Image source** | Non disponible | Disponible (JPEG scanné) |
| **JSON source** | Non applicable | Disponible |
| **Remarques auto** | Non | Oui (générées par l'IA) |
| **Barre flottante** | Oui (mobile) | Oui (mobile) |
| **Workflow** | Identique | Identique |

---

### Règles identiques

✅ **Enregistrer avant d'ajouter des observations**
✅ **Enregistrer régulièrement**
✅ **Vérifier avant de valider**
✅ **Historique des modifications tracé**

---

## 11. Questions fréquentes

### "Combien de temps prend la transcription ?"

**Réponse** : Environ **5-10 secondes par image**

Exemples :
- 10 images ≈ 50 secondes - 2 minutes
- 50 images ≈ 4-8 minutes
- 100 images ≈ 8-15 minutes

Sur Raspberry Pi, comptez **2-3x plus long** que sur un PC puissant.

---

### "La transcription est très lente"

**Solutions** :
- Vérifiez votre connexion internet (appels API vers Google)
- Réduisez le nombre d'images par batch (traiter par lots de 20-30)
- Évitez les images trop lourdes (> 5 MB)



---

### "L'IA a mal lu certaines données"

**C'est normal !** L'OCR n'est jamais parfait à 100%.

**Taux de réussite attendu** : 80-95%

**Données souvent mal lues** :
- Dates manuscrites (confusion 1/7, 3/8, etc.)
- Nombres (0/O, 1/I/l, 5/S, etc.)
- Noms d'espèces proches
- Coordonnées GPS (virgules, points)

**Solution** : C'est pour ça que la correction humaine est indispensable !

---

### "Puis-je retraiter une image ?"

**Réponse** : Oui

1. Depuis la page de résultats
2. Cliquez sur "🔄 Retraiter" à côté de la fiche en erreur
3. Le traitement est relancé pour cette image uniquement

---

### "Le JSON est invalide"

**Raison** : L'IA a généré un JSON mal formaté

**Solution automatique** :
- L'application tente de corriger automatiquement
- Un fichier `*_raw.json` est sauvegardé (JSON brut)
- Un fichier `*_result.json` est sauvegardé (JSON corrigé)

**Si ça ne fonctionne toujours pas** :
- Consultez les logs
- Contactez un administrateur
- Retraitez l'image

---

### "Puis-je traiter plusieurs dossiers en même temps ?"

**Réponse** : Oui, mais pas recommandé

- Celery peut traiter plusieurs dossiers en parallèle
- Mais sur Raspberry Pi, ça peut ralentir considérablement
- **Recommandation** : Traitez un dossier à la fois

---

### "Où sont stockés les résultats ?"

**Emplacement** : `/media/transcription_results/[nom_du_dossier]/`

**Contenu** :
```
/media/transcription_results/campagne_2024_printemps/
├── carnet_page_01_result.json
├── carnet_page_02_result.json
├── carnet_page_03_raw.json      ← JSON brut (si correction auto)
├── carnet_page_03_result.json   ← JSON corrigé
└── ...
```

---

### "Comment savoir si une fiche a été corrigée ?"

**Consultez l'historique** :
- Chaque modification est tracée
- Qui a corrigé quoi et quand
- Visualisez les changements entre l'extraction IA et la version finale

---

## Récapitulatif du workflow

```
1. Préparer et scanner les carnets (JPEG)
   ↓
2. Uploader les images dans un dossier
   ↓
3. Sélectionner le dossier à traiter
   ↓
4. Lancer la transcription automatique (Gemini IA)
   ↓
5. Suivre la progression en temps réel
   ↓
6. Consulter les résultats (JSON générés)
   ↓
7. Visualiser les fichiers source (JPEG + JSON)
   ↓
8. Corriger les fiches une par une
   • Vérifier la localisation
   • Corriger les informations du nid
   • Vérifier/ajouter/modifier les observations
   • Ajouter des remarques de correction
   ↓
9. Enregistrer régulièrement
   ↓
10. Valider les fiches corrigées
```

---

## Aide supplémentaire

- **[Guide de navigation](./01_navigation_generale.md)**
- **[Guide de saisie](./02_saisie_nouvelle_observation.md)**

- **Support** : Contactez un administrateur

---

*Version 1.1 - Décembre 2025*

---

## 🆕 Nouveautés (Décembre 2025)

### Améliorations de l'interface de correction

1. **Barre d'actions flottante**
   - Boutons Enregistrer/Valider toujours accessibles en bas d'écran
   - Particulièrement utile sur mobile et tablette
   - Se masque automatiquement quand vous arrivez en bas de page

2. **Recherche de communes optimisée**
   - Tri intelligent par pertinence
   - Les communes à nom court (Ur, Ger, Eu, Ay) apparaissent en premier
   - Plus besoin de scroller pour trouver votre commune !

3. **Terminologie clarifiée**
   - **Fiche ID** : Numéro unique attribué automatiquement (non modifiable, affiché en gris)
   - **N° perso de fiche** : Votre numéro de référence personnel (modifiable)

4. **Menu restructuré**
   - Section "Fiches Observations" pour plus de clarté
   - "Nouvelle fiche" au lieu de "Nouvelle observation"
