# Session du 20 décembre 2025 - Correctifs système OCR Batch

## Contexte initial

Suite à la mise en place de l'app `pilot` pour l'évaluation des modèles OCR, plusieurs problèmes ont été identifiés lors du premier test réel du système de transcription batch.

## Problèmes rencontrés

### 1. Modèles Gemini obsolètes
**Symptôme** : Erreur 404 "models/gemini-1.5-flash is not found"

**Cause** : Le code utilisait d'anciens noms de modèles Gemini (1.5, 2.0) qui n'existent plus dans l'API payante de l'utilisateur.

**Modèles disponibles** :
- gemini-3-flash-preview
- gemini-3-pro-preview
- gemini-2.5-pro
- gemini-2.5-flash-lite

### 2. Détection du prompt incorrecte
**Symptôme** : Logs Celery montrant "Prompt STANDARD sélectionné" pour les chemins contenant `TRI_ANCIEN`

**Cause** : La fonction `_determiner_type_fiche_et_traitement()` ne vérifiait que le premier segment du chemin (`jpeg_pdf`) au lieu du chemin complet (`jpeg_pdf\TRI_ANCIEN\FUSION_FULL`).

### 3. Interface web non implémentée
**Symptôme** : Bouton "Lancer la transcription" ne fait rien, résultats jamais affichés

**Cause** : La fonction JavaScript `lancerTranscription()` était un simple `alert()` placeholder qui n'appelait jamais le backend.

### 4. Page de résultats bloquée
**Symptôme** : Après lancement, redirection vers une page affichant "Aucun résultat disponible"

**Cause** : La vue Django `batch_results` ne gérait pas le mode `tracking=true`, et affichait immédiatement un message d'erreur avant que le JavaScript de polling ne puisse s'exécuter.

### 5. Flower non fonctionnel
**Symptôme** : Erreurs de connexion à Flower

**Causes** :
- Port 5555 déjà utilisé par une ancienne instance de Flower
- Flower démarré sans Redis (impossible de se connecter au broker)

## Solutions apportées

### 1. Mise à jour des modèles Gemini

#### Fichiers modifiés :

**`pilot/models.py` (lignes 62-72)** :
```python
modele_ocr = models.CharField(
    max_length=50,
    choices=[
        ('gemini_3_flash', 'Gemini 3 Flash'),
        ('gemini_3_pro', 'Gemini 3 Pro'),
        ('gemini_2.5_pro', 'Gemini 2.5 Pro'),
        ('gemini_2.5_flash_lite', 'Gemini 2.5 Flash-Lite'),
    ],
    ...
)
```

**`pilot/tasks.py` (lignes 636-642)** :
```python
modeles_mapping = {
    'gemini_3_flash': 'gemini-3-flash-preview',
    'gemini_3_pro': 'gemini-3-pro-preview',
    'gemini_2.5_pro': 'gemini-2.5-pro',
    'gemini_2.5_flash_lite': 'gemini-2.5-flash-lite',
}
```

**`pilot/templates/pilot/selection_repertoire_ocr.html` (lignes 95-100)** :
- Mis à jour le `<select>` avec les nouveaux modèles

**`pilot/templates/pilot/optimisation_ocr_home.html` (lignes 38-68)** :
- Mis à jour les checkboxes avec les nouveaux modèles
- Gemini 3 Flash coché par défaut (recommandé)

**`pilot/migrations/0003_update_gemini_models.py`** :
- Migration créée et appliquée pour mettre à jour le champ en base

### 2. Correction de la détection de prompt

**`pilot/tasks.py` (lignes 300-309)** :
```python
# AVANT - vérifiait seulement le premier segment
type_fiche, _ = _determiner_type_fiche_et_traitement(chemin_relatif)
if 'ancien' in type_fiche.lower():
    prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'

# APRÈS - vérifie le chemin complet
if 'ancien' in chemin_relatif.lower():
    prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'
    logger.info(f"📄 Prompt ANCIENNES FICHES sélectionné pour: {chemin_relatif}")
else:
    prompt_filename = 'prompt_gemini_transcription.txt'
    logger.info(f"📄 Prompt STANDARD sélectionné pour: {chemin_relatif}")
```

### 3. Implémentation de l'interface web

**`pilot/templates/pilot/selection_repertoire_ocr.html` (lignes 431-494)** :

Fonction `lancerTranscription()` complètement implémentée :
- Extraction des répertoires depuis les données d'analyse
- POST vers `/pilot/optimisation-ocr/lancer-transcription-batch/`
- Redirection vers `/pilot/optimisation-ocr/resultats/?tracking=true&task_id=XXX`
- Feedback visuel avec spinner pendant le lancement

### 4. Correction du mode tracking

**`pilot/views.py` (lignes 399-420)** :
```python
@transcription_required
def batch_results(request):
    """
    Affiche les résultats du traitement batch
    """
    # Vérifier si on est en mode tracking (suivi en temps réel)
    is_tracking = request.GET.get('tracking') == 'true'

    # Récupérer les résultats stockés en session
    results = request.session.get('pilot_batch_results', {})
    config = request.session.get('pilot_batch_config', {})

    # Si pas de résultats ET qu'on n'est pas en mode tracking, afficher un message d'erreur
    if not results and not is_tracking:
        messages.warning(
            request, "Aucun résultat disponible. Veuillez lancer un traitement batch d'abord."
        )
        return render(request, 'pilot/batch_results.html', {'no_results': True})

    # Si on est en mode tracking mais pas encore de résultats, afficher le template sans no_results
    # Le JavaScript va gérer le polling
    if is_tracking and not results:
        return render(request, 'pilot/batch_results.html', {'no_results': False})
```

**Fonctionnement** :
- Si `tracking=true` dans l'URL, le template s'affiche sans erreur
- Le JavaScript démarre un polling toutes les 2 secondes vers `/pilot/optimisation-ocr/verifier-progression/`
- Affichage en temps réel de la barre de progression, fichier en cours, logs colorés
- Redirection automatique vers les résultats finaux à la fin du traitement

### 5. Diagnostic Flower

**Problèmes identifiés** :
1. Port 5555 occupé par une ancienne instance → Instance arrêtée par l'utilisateur
2. Flower ne peut pas se connecter à Redis (Error 10061) → Redis n'était pas démarré

**Solution** : Utiliser `Start-DevStack.ps1` qui démarre les services dans le bon ordre :
```
Redis (6379) → Django (8000) → Celery Worker → Flower (5555)
```

## Outil de diagnostic créé

### `pilot/test_gemini_simple.py` (283 lignes)

Script autonome pour tester l'API Gemini indépendamment du système batch complet.

**Fonctionnalités** :
- Liste tous les modèles Gemini disponibles via l'API
- Charge le fichier `.env` pour récupérer `GEMINI_API_KEY`
- Teste la transcription d'une seule image
- Parse et valide le JSON retourné
- Teste séquentiellement plusieurs noms de modèles

**Usage** :
```bash
python pilot/test_gemini_simple.py "media/jpeg_pdf/TRI_ANCIEN/FUSION_FULL/fiche 25_FINAL.jpg"
```

**Résultat du test** :
- ✅ Modèle `gemini-3-flash-preview` fonctionne
- ✅ JSON valide retourné
- ✅ Espèce détectée : "Gravelot à col"
- ✅ Prompt ANCIEN correctement sélectionné

## Fichiers modifiés

### Code Python
- `pilot/models.py` - Choices des modèles OCR
- `pilot/tasks.py` - Mapping modèles + détection prompt
- `pilot/views.py` - Gestion mode tracking
- `pilot/test_gemini_simple.py` - **CRÉÉ** - Script de test

### Templates HTML
- `pilot/templates/pilot/selection_repertoire_ocr.html` - Select + fonction lancerTranscription()
- `pilot/templates/pilot/optimisation_ocr_home.html` - Checkboxes modèles

### Migrations
- `pilot/migrations/0003_update_gemini_models.py` - **CRÉÉE** - Migration des choix de modèles

## Résultats obtenus

### Tests réussis

1. ✅ **Script de test simple** :
   - Connexion API Gemini validée
   - Modèle `gemini-3-flash-preview` fonctionnel
   - JSON valide généré
   - Détection d'espèce correcte

2. ✅ **Traitement batch complet** :
   - Sélection de répertoire fonctionnelle
   - Lancement du batch via interface web
   - Redirection vers page de suivi en temps réel
   - Barre de progression affichée
   - Logs en temps réel colorés
   - **Fichiers JSON générés avec succès**

3. ✅ **Infrastructure Celery/Redis** :
   - Worker Celery en ligne (Flower)
   - Tâches traitées avec succès
   - Aucun échec détecté

### Statistiques Flower
```
Worker: celery@PortableHP
Status: Online
Processed: 2 tasks
Succeeded: 2
Failed: 0
```

## Architecture finale

### Flux de traitement batch

```
1. Utilisateur : Sélection répertoire(s)
   ↓
2. Interface web : Choix modèle(s) OCR
   ↓
3. Frontend JS : POST /pilot/optimisation-ocr/lancer-transcription-batch/
   ↓
4. Vue Django : Lance tâche Celery + stocke task_id en session
   ↓
5. Redirection : /pilot/optimisation-ocr/resultats/?tracking=true&task_id=XXX
   ↓
6. Template : Affiche section tracking (no_results=False)
   ↓
7. JavaScript : Polling GET /pilot/optimisation-ocr/verifier-progression/ (toutes les 2s)
   ↓
8. Vue Django : Récupère état tâche via AsyncResult(task_id)
   ↓
9. Celery Worker : Traite images une par une avec Gemini API
   ↓
10. Mise à jour progression : Affichage temps réel (barre, logs, fichier en cours)
   ↓
11. Fin de tâche : Redirection automatique vers résultats finaux
   ↓
12. Affichage final : Statistiques, résultats par répertoire, liens JSON et Admin
```

### Services démarrés

```powershell
.\Start-DevStack.ps1
```

Démarre dans l'ordre :
1. **Redis** (port 6379) - Message broker pour Celery
2. **Django** (port 8000) - Application web
3. **Celery Worker** - Traitement des tâches asynchrones
4. **Flower** (port 5555) - Monitoring temps réel de Celery

## Points techniques importants

### Gestion des quotas Gemini
- Compte gratuit : 15 requêtes/minute → Quota dépassé pendant les tests
- **Solution** : Compte payant activé → Pas de limite

### Détection automatique du type de fiche
- Basée sur la présence de `ancien` dans le chemin complet
- Sélectionne automatiquement le bon fichier prompt :
  - `prompt_gemini_transcription_Ancienne_Fiche.txt` pour TRI_ANCIEN
  - `prompt_gemini_transcription.txt` pour les autres

### Mode tracking vs résultats
- **Mode tracking** (`?tracking=true`) : Polling temps réel, pas de résultats en session requis
- **Mode résultats** (sans param) : Affiche résultats stockés en session après traitement

### Logging amélioré
- Logs Celery détaillés avec timestamp
- Logs colorés dans l'interface web (info/success/warning/error)
- Auto-scroll optionnel dans la zone de logs

## Prochaines étapes possibles

1. **Évaluation de la qualité** :
   - Comparer les transcriptions OCR avec les fiches de référence corrigées manuellement
   - Calculer les scores de similarité
   - Identifier les types d'erreurs (dates, nombres, espèces, lieux)

2. **Tests comparatifs** :
   - Tester les 4 modèles Gemini sur le même jeu d'images
   - Comparer images brutes vs images optimisées
   - Analyser le rapport qualité/coût/vitesse

3. **Optimisation** :
   - Traitement parallèle de plusieurs images (gestion du rate limiting)
   - Retry automatique en cas d'erreur temporaire
   - Cache des résultats pour éviter les retraitements

4. **Production** :
   - Retirer l'app `pilot` de `INSTALLED_APPS` en production
   - Intégrer les meilleurs paramètres trouvés dans l'app `observations`
   - Documenter les résultats de l'évaluation

## Conclusion

Session très productive qui a permis de :
- ✅ Identifier et corriger 5 problèmes majeurs
- ✅ Mettre à jour tous les composants pour les nouveaux modèles Gemini
- ✅ Implémenter complètement le flux de transcription batch
- ✅ Valider le fonctionnement de bout en bout avec génération de JSON
- ✅ Diagnostiquer et résoudre les problèmes d'infrastructure (Flower/Redis)

Le système de transcription OCR batch est maintenant **pleinement fonctionnel** et prêt pour l'évaluation comparative des modèles.
