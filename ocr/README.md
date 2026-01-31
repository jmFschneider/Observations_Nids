# 🤖 App OCR - Traitement & Optimisation

Cette application gère la transcription automatique des fiches d'observation via l'API Google Gemini et permet d'évaluer la qualité des différents modèles OCR.

## 📋 Objectif

L'app `ocr` est le moteur de transcription du projet. Elle a deux fonctions principales :

1. **Transcription Batch** : Traiter des lots d'images pour générer les fichiers JSON bruts.
2. **Évaluation Qualité** : Comparer les résultats OCR avec des fiches de référence (vérité terrain) pour mesurer la précision des modèles.

## 🗂️ Structure

```
ocr/
├── __init__.py
├── apps.py              # Configuration de l'app
├── models.py            # Modèle TranscriptionOCR
├── admin.py             # Interface d'administration
├── tasks.py             # Tâches Celery (traitement batch)
├── views.py             # Vues de lancement et suivi
├── urls.py              # Routes URL
└── services/            # Logique métier (comparateurs, matchers)
```

## 📊 Modèle `TranscriptionOCR`

Ce modèle stocke les métadonnées et les résultats d'évaluation d'une transcription.

### Champs principaux

- **Référence:** Lien vers la `FicheObservation` de référence (vérité terrain)
- **Métadonnées:** Chemin JSON, chemin image, type d'image, modèle OCR
- **Évaluation:** Statut, score global, taux de précision
- **Erreurs détaillées:** Par type (dates, nombres, texte, espèces, lieux)
- **Performance:** Temps de traitement
- **Détails:** JSON de comparaison détaillée

## 🎯 Utilisation

### Lancement d'un Batch OCR

L'interface de lancement est accessible via le menu **Transcription** > **Transcription Batch** (pour les administrateurs et reviewers).

1. Sélectionner un répertoire d'images dans `media/`.
2. Choisir un ou plusieurs modèles OCR (Gemini Flash, Pro, etc.).
3. Lancer le traitement.
4. Suivre la progression en temps réel.

### Tâches Celery

La tâche principale est `ocr.process_batch_transcription`. Elle :
1. Parcourt les répertoires sélectionnés.
2. Détermine le type de fiche (Ancienne/Nouvelle) pour choisir le bon prompt.
3. Envoie l'image à l'API Gemini.
4. Valide et corrige le JSON retourné.
5. Sauvegarde le résultat brut et corrigé.
6. Crée une entrée `TranscriptionOCR`.

## 📈 Analyses et statistiques

L'administration Django (`/admin/ocr/transcriptionocr/`) offre des filtres et des vues pour analyser les performances :

- Score moyen par modèle
- Taux d'erreur par type de champ
- Comparaison Image Brute vs Image Optimisée

## 🛠️ Développement

### Tests manuels

Un script utilitaire permet de tester rapidement l'API Gemini sur une image :

```bash
python ocr/test_gemini_simple.py "media/chemin/vers/image.jpg"
```

### Configuration

Les clés API et paramètres sont définis dans les variables d'environnement (voir `.env`).
L'application nécessite un worker Celery actif pour le traitement asynchrone.