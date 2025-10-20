# Optimisations futures - Transcription Gemini

Ce document résume les optimisations possibles pour améliorer les performances de transcription d'images avec Gemini 2.0 Flash.

## Contexte actuel

- **Technologie** : Google Gemini 2.0 Flash API (OCR intelligent)
- **Usage** : Transcription d'images de carnets d'observations vers JSON structuré
- **Traitement** : Séquentiel (une image à la fois)
- **Concurrency Celery** : 2 workers
- **Plateforme de production** : Raspberry Pi

## Coûts Gemini 2.0 Flash (Tier Standard)

- **Entrée** : $0.10 par million de tokens (images + texte)
- **Sortie** : $0.40 par million de tokens (JSON)
- **Estimation** : ~$0.23 pour 1000 images/mois (23 centimes)
- **Mode Batch** : -50% si délai accepté (asynchrone)

**Conclusion** : Les coûts sont négligeables, les optimisations sont viables.

---

## Optimisation 1 : Traitement parallèle des images ⭐ (PRIORITAIRE)

### Problème actuel
Le code traite les images **séquentiellement** (boucle for ligne 78 de `observations/tasks.py`).

### Solution
Utiliser `concurrent.futures` ou `asyncio` pour traiter plusieurs images en parallèle.

### Gain attendu
- **3-5x plus rapide** selon le nombre d'images
- Exemple : 10 images × 5s = 50s → 15s avec 4 threads parallèles

### Implémentation suggérée

```python
import concurrent.futures
from functools import partial

def process_single_image(img_file, base_dir, model, prompt, results_dir):
    """Traite une seule image et retourne le résultat"""
    # Code actuel de la boucle extrait ici
    pass

# Dans la tâche principale :
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    process_func = partial(process_single_image,
                           base_dir=base_dir,
                           model=model,
                           prompt=prompt,
                           results_dir=results_dir)
    results = list(executor.map(process_func, image_files))
```

### Complexité
- **Difficulté** : Moyenne (refactoring du code existant)
- **Temps estimé** : 2-3h
- **Risque** : Faible (Gemini API supporte le parallélisme)

### Attention
- Vérifier les limites de rate limiting de l'API Gemini
- Ajuster `max_workers` selon la limite (généralement 10-15 requêtes/seconde)

---

## Optimisation 2 : Augmenter la concurrency Celery

### Problème actuel
Configuration conservative : `--concurrency=2` (pour économiser RAM sur Raspberry Pi)

### Solution
Pour des appels API (pas de calcul lourd local), on peut augmenter :
- Sur Raspberry Pi : `--concurrency=4` (sans risque)
- Sur PC plus puissant : `--concurrency=8-12`

### Gain attendu
- **2x plus rapide** si plusieurs dossiers traités simultanément
- Utile si plusieurs utilisateurs lancent des transcriptions en même temps

### Modification

Dans `deployment/celery-worker.service`, ligne 27 :
```bash
# Avant
--concurrency=2

# Après
--concurrency=4
```

### Complexité
- **Difficulté** : Très facile
- **Temps estimé** : 5 minutes
- **Risque** : Nul (tester et ajuster)

---

## Optimisation 3 : Réduire la taille des images (optionnel)

### Contexte
Si vos photos font >2000px, les redimensionner peut accélérer :
- Moins de données à envoyer
- Traitement plus rapide côté Gemini

### Solution
Redimensionner automatiquement avant envoi (max 1600px de largeur)

```python
from PIL import Image

def optimize_image(img_path, max_width=1600):
    img = Image.open(img_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    return img
```

### Gain attendu
- **10-30% plus rapide** selon la taille originale
- Économie de bande passante

### Complexité
- **Difficulté** : Facile
- **Temps estimé** : 30 minutes
- **Risque** : Vérifier que la qualité OCR reste bonne

---

## Optimisation 4 : Context Caching (avancé)

### Contexte
Le prompt de transcription est long et identique pour toutes les images.

### Solution
Utiliser le Context Caching de Gemini pour mettre le prompt en cache.

### Gain attendu
- **-75% du coût d'entrée** pour le prompt
- Légèrement plus rapide

### Tarifs avec caching
- Storage : $1.00 par million de tokens par heure
- Input depuis cache : $0.025 par million de tokens (au lieu de $0.10)

### Complexité
- **Difficulté** : Moyenne
- **Temps estimé** : 1-2h
- **Documentation** : https://ai.google.dev/gemini-api/docs/caching

---

## Architecture hybride PC de bureau (NON RECOMMANDÉ pour Gemini)

### Pourquoi c'était envisagé ?
Utilisation du PC de bureau (12 cœurs, GTX 1080) comme worker Celery distant.

### Pourquoi ce n'est pas utile ici ?
- **Gemini est une API cloud** : le calcul est chez Google, pas local
- Le Raspberry Pi et le PC ont les mêmes performances pour des appels API
- Architecture plus complexe sans gain réel

### Cas où ça serait utile
- Si vous utilisiez Whisper (transcription audio) en local
- Si vous faisiez du traitement ML local (PyTorch, TensorFlow)
- Si vous aviez des calculs CPU/GPU intensifs

### Verdict
**Ne pas implémenter** pour l'instant. L'optimisation parallèle suffit largement.

---

## Roadmap recommandée

### Phase 1 : Quick wins (1 semaine)
1. ✅ Recueillir retours utilisateurs
2. Augmenter `--concurrency=4` dans Celery
3. Tester la stabilité en production

### Phase 2 : Optimisation majeure (après retours utilisateurs)
1. Implémenter le traitement parallèle des images
2. Tester avec différents volumes (10, 50, 100 images)
3. Ajuster `max_workers` selon les performances
4. Monitorer les limites de rate limiting Gemini

### Phase 3 : Peaufinage (optionnel)
1. Réduire la taille des images si nécessaire
2. Implémenter le context caching si coûts élevés
3. Optimiser l'UI pour afficher la progression parallèle

---

## Métriques à surveiller

1. **Temps de traitement moyen par image**
   - Baseline actuel : ~5s/image ?
   - Objectif après parallélisme : ~1.5-2s/image

2. **Temps total pour 50 images**
   - Baseline : ~250s (4 min)
   - Objectif : ~75s (1 min 15s)

3. **Coûts mensuels Gemini**
   - Surveiller via Google AI Console
   - Alerter si >$5/mois

4. **Taux d'erreur API**
   - Rate limiting
   - Timeouts
   - Erreurs de parsing JSON

---

## Notes importantes

- **Priorité** : Optimisation 1 (parallélisme) = meilleur rapport gain/effort
- **Budget** : Les coûts Gemini sont négligeables, ne pas hésiter à paralléliser
- **Raspberry Pi** : Suffisant pour l'application web + appels API
- **PC de bureau** : Pas nécessaire pour Gemini (API cloud)

---

**Date de rédaction** : 16 octobre 2025
**Statut** : En attente de retours utilisateurs avant implémentation
