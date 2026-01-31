# 🧪 Guide de Test : Qualité et Statistiques OCR

Ce guide explique comment mettre en œuvre le pipeline d'évaluation OCR pour mesurer la performance des modèles (Gemini 3 Flash, Pro, etc.) en comparant leurs transcriptions avec les données validées en base.

## 📋 Prérequis

1.  **Accès au serveur** (ou environnement local configuré).
2.  **Clé API Gemini** configurée dans le fichier `.env`.
3.  **Redis** lancé (pour les tâches de fond).
4.  **Données de "Vérité Terrain"** : Pour évaluer une transcription, la fiche correspondante doit **déjà exister dans la base de données SQL** (saisie manuellement et validée).

---

## 1️⃣ Préparation des Données

### Où placer les images ?
Les images à tester doivent être placées dans le dossier `media/`. Une structure organisée est recommandée pour que le système détecte automatiquement le contexte.

**Structure recommandée :**
```text
media/
└── TEST_CAMPAGNE_01/          <-- Nom du lot
    ├── Ancienne_fiche/        <-- Type de fiche (déclenche le prompt "ancien")
    │   └── Image_optimisee/   <-- Type d'image
    │       ├── fiche_19_FINAL.jpg
    │       └── fiche_34_FINAL.jpg
    └── Nouvelle_fiche/
        └── ...
```

### Vérification de la liaison
Le système essaie de lier automatiquement l'image à une fiche en base via le nom de fichier.
*   **Exemple** : Si le fichier s'appelle `fiche_19_FINAL.jpg`, le système cherchera une `FicheObservation` dont le champ `chemin_image` contient "fiche_19".

---

## 2️⃣ Lancement de la Transcription (OCR)

Cette étape envoie les images à Gemini et génère les fichiers JSON.

### Via l'Interface Web (Recommandé)
1.  Allez sur : `http://votre-serveur:8000/ocr/selection-repertoire/`
2.  Naviguez pour sélectionner votre dossier (ex: `TEST_CAMPAGNE_01`).
3.  Cochez les modèles à tester (ex: `Gemini 3 Flash`, `Gemini 2.5 Pro`).
4.  Cliquez sur **"Lancer la transcription batch"**.
5.  Attendez la fin de la barre de progression.

### Résultat
Des entrées sont créées dans la table `TranscriptionOCR` avec le statut "Non évaluée".

---

## 3️⃣ Gestion et Calcul des Scores

Une fois les transcriptions terminées (ou si vous avez des fichiers JSON existants), utilisez les scripts utilitaires fournis dans `scripts/` pour gérer l'évaluation.

### A. Importer/Synchroniser les résultats (Réparation)
Si vous avez des fichiers JSON dans `media/transcription_results` mais qu'ils n'apparaissent pas dans l'admin (ou si vous avez supprimé la table), lancez ce script pour tout recréer :

```bash
python scripts/sync_json_to_db.py
```
*Ce script détecte automatiquement les nouveaux fichiers et les lie à la bonne fiche BDD grâce à un matcher intelligent.*

### B. Lancer le Calcul des Scores
Pour calculer les scores (Global, Texte, Numérique) de toutes les fiches en attente :

```bash
python scripts/calculate_ocr_scores.py
```
*Ce script traite toutes les fiches ayant le statut "Non évaluée".*

---

## 4️⃣ Analyse des Résultats

C'est ici que vous visualisez la performance.

### Accès au Tableau de Bord
Allez dans l'administration : `http://votre-serveur:8000/admin/ocr/transcriptionocr/`

### Comprendre les Colonnes
Le tableau présente désormais 3 indicateurs de performance distincts :

1.  **Global** (Vert/Orange/Rouge) :
    *   Moyenne générale de tous les champs.
    *   *Utilité* : Indication rapide de la qualité globale.

2.  **Score Texte** (Nouveau) :
    *   Mesure la capacité de l'IA à **lire l'écriture manuscrite**.
    *   Champs concernés : Espèce, Commune, Observations, Remarques.
    *   *Analyse* : Si ce score est bas, le modèle a du mal avec la graphie ou le vocabulaire.

3.  **Score Numérique** (Nouveau) :
    *   Mesure la capacité de l'IA à **structurer les données**.
    *   Champs concernés : Dates (Jours/Mois), Nombres d'œufs/poussins.
    *   *Analyse* : Si ce score est bas, le modèle fait des décalages de colonnes ou confond des chiffres (ex: 3 vs 8).

### Filtres Utiles (Colonne de droite)
*   **Modèle OCR** : Pour comparer `Gemini Flash` vs `Pro`.
*   **Type d'image** : Pour voir si le prétraitement de l'image améliore le score.
*   **Score Global** : Pour isoler les échecs (< 50%).

---

## 🛠️ Dépannage

**Q: Le score est à 0% alors que le JSON semble bon ?**
R: Vérifiez que la **Fiche de référence** (BDD) est bien remplie. Si la fiche en base est vide, le comparateur ne trouve aucune correspondance.

**Q: "Pas de fiche liée" lors du script de comparaison ?**
R: Le nom de l'image ne permet pas de retrouver la fiche en base.
*   *Solution* : Allez dans l'admin, ouvrez la `TranscriptionOCR`, et sélectionnez manuellement la "Fiche de référence" dans la liste déroulante, puis relancez le script.

**Q: Comment voir le détail précis d'une erreur ?**
R: Dans l'admin, cliquez sur une ligne, puis ouvrez la section **"📝 Détails et notes"** tout en bas. Le champ `Détails de comparaison` contient le JSON complet du diff (ce que l'IA a vu vs ce qu'il y a en base).
