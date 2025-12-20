# 🧪 App Pilot - Expérimentation OCR

⚠️ **App temporaire dans la branche `feature/optimisation-ocr-batch`**

Cette app permet d'évaluer différents modèles OCR sur les images de fiches.
Elle sera supprimée une fois les tests terminés.

## 📋 Objectif

L'app `pilot` permet d'évaluer et de comparer différents modèles OCR (Gemini Flash, 1.5 Pro, 2.0 Pro) et configurations d'images (brute vs optimisée).

### Fonctionnalités

- **Stockage des métadonnées** des transcriptions OCR automatiques
- **Comparaison avec la vérité terrain** (fiches corrigées manuellement)
- **Évaluation de la qualité** avec scores et métriques détaillées
- **Interface d'administration** complète avec filtres et statistiques

## 🗂️ Structure

```
pilot/
├── __init__.py
├── apps.py              # Configuration de l'app
├── models.py            # Modèle TranscriptionOCR
├── admin.py             # Interface d'administration
├── migrations/          # Migrations de base de données
└── README.md            # Ce fichier
```

## 📊 Modèle `TranscriptionOCR`

### Champs principaux

- **Référence:** Lien vers la `FicheObservation` de référence
- **Métadonnées:** Chemin JSON, chemin image, type d'image, modèle OCR
- **Évaluation:** Statut, score global, taux de précision
- **Erreurs détaillées:** Par type (dates, nombres, texte, espèces, lieux)
- **Performance:** Temps de traitement
- **Détails:** JSON de comparaison détaillée, notes manuelles

### Propriétés calculées

- `taux_precision`: (champs corrects / total) × 100
- `nombre_erreurs_total`: Somme de toutes les erreurs

## 🎯 Utilisation

### Créer une transcription OCR

```python
from pilot.models import TranscriptionOCR
from observations.models import FicheObservation

# Créer une entrée pour une transcription OCR
transcription = TranscriptionOCR.objects.create(
    fiche=fiche_reference,
    chemin_json='transcription_results/fiche_123_optimisee.json',
    chemin_image='prepared_images/fiche_123_optimisee.jpg',
    type_image='optimisee',
    modele_ocr='gemini_2_pro',
    temps_traitement_secondes=2.5
)
```

### Évaluer la qualité

```python
# Après comparaison avec la vérité terrain
transcription.statut_evaluation = 'evaluee'
transcription.score_global = 92.5
transcription.nombre_champs_corrects = 37
transcription.nombre_champs_total = 40
transcription.nombre_erreurs_dates = 1
transcription.nombre_erreurs_texte = 2
transcription.save()
```

### Interface d'administration

Accès: `/admin/pilot/transcriptionocr/`

**Fonctionnalités:**
- Liste avec badges colorés (modèle, type, statut, score)
- Filtres par modèle, type d'image, statut, dates
- Actions groupées (marquer comme évaluée/non évaluée)
- Vue détaillée avec tous les champs

## 🗑️ Suppression après tests

Une fois les tests d'évaluation OCR terminés:

1. **Supprimer la branche** `feature/optimisation-ocr-batch`
2. L'app `pilot` et toutes ses données seront supprimées automatiquement
3. Conserver uniquement les conclusions de l'évaluation (quel modèle est le meilleur)

## 📈 Analyses et statistiques

### Requêtes SQL utiles

```sql
-- Score moyen par modèle
SELECT modele_ocr, AVG(score_global) as score_moyen
FROM pilot_transcription_ocr
WHERE statut_evaluation = 'evaluee'
GROUP BY modele_ocr;

-- Comparaison image brute vs optimisée
SELECT type_image, AVG(score_global) as score_moyen
FROM pilot_transcription_ocr
WHERE statut_evaluation = 'evaluee'
GROUP BY type_image;

-- Modèle avec le moins d'erreurs
SELECT modele_ocr,
       AVG(nombre_erreurs_dates + nombre_erreurs_nombres +
           nombre_erreurs_texte + nombre_erreurs_especes +
           nombre_erreurs_lieux) as erreurs_moyennes
FROM pilot_transcription_ocr
WHERE statut_evaluation = 'evaluee'
GROUP BY modele_ocr
ORDER BY erreurs_moyennes;
```

### Analyses Django ORM

```python
from pilot.models import TranscriptionOCR
from django.db.models import Avg, Count

# Score moyen par modèle
stats = TranscriptionOCR.objects.filter(
    statut_evaluation='evaluee'
).values('modele_ocr').annotate(
    score_moyen=Avg('score_global'),
    nombre_tests=Count('id')
)

for stat in stats:
    print(f"{stat['modele_ocr']}: {stat['score_moyen']:.2f}% ({stat['nombre_tests']} tests)")
```

## 🔧 Maintenance

### Nettoyer les données de test

```python
# Supprimer toutes les transcriptions non évaluées
TranscriptionOCR.objects.filter(statut_evaluation='non_evaluee').delete()

# Supprimer les transcriptions d'un modèle spécifique
TranscriptionOCR.objects.filter(modele_ocr='gemini_flash').delete()
```

## 📝 Notes

- Les fichiers JSON des transcriptions restent sur le disque
- Seules les métadonnées et métriques sont en base de données
- La table utilise le préfixe `pilot_` pour identification claire
- Les index sont optimisés pour les requêtes de statistiques

## 🆘 Support

Pour toute question sur l'utilisation de cette app, consulter la documentation du projet principal.

---

**Rappel:** Cette app est UNIQUEMENT pour le pilote. Ne pas déployer en production!
