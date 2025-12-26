# 🕵️ Revue Critique : Analyse Automatisation Transcription

**Document analysé** : `docs/ANALYSE_AUTOMATISATION_TRANSCRIPTION.md`
**Date de la revue** : 26 décembre 2025
**Statut** : ✅ Validé avec recommandations d'optimisation

---

## 1. Synthèse Globale

Le projet de passage à l'échelle est **solide et bien structuré**. L'analyse identifie correctement les goulots d'étranglement (validation espèce et finalisation manuelle). L'architecture proposée est réaliste pour le volume visé (50k fiches).

Cependant, certaines briques techniques (notamment le déclenchement par *Watcher Filesystem*) peuvent être simplifiées pour gagner en robustesse et facilité de maintenance.

---

## 2. Analyse détaillée par critères

### 🏗️ Efficacité de l'Architecture (+++++)

**Ce qui est excellent :**
*   **Découplage asynchrone :** L'utilisation de Celery est parfaite pour absorber la charge et gérer les temps de réponse de l'API Gemini.
*   **Transactions atomiques :** Le découpage en lots (batchs) pour les transactions DB est crucial pour la performance PostgreSQL.

**Points d'amélioration critiques :**

#### A. Remplacer le "Filesystem Watcher" par du "Chainage de Tâches"
L'architecture propose : `OCR -> Fichier JSON -> Watcher (ou Cron) -> Import`.
*   **Risque :** Les *Watchers* (bibliothèque `watchdog`) sont souvent fragiles en production (processus qui meurt, fuites mémoire, événements manqués sur certains OS). Le Cron ajoute une latence inutile.
*   **Recommandation :** Utiliser les **chaînes Celery (Canvas)**.
    Dès qu'une tâche OCR termine avec succès, elle devrait déclencher *immédiatement* la tâche d'importation.
    ```python
    # Pseudo-code conceptuel
    chain(
        process_single_image.s(image_path),
        import_json_task.s()  # Prend le résultat JSON directement ou le chemin fichier
    ).apply_async()
    ```
    *Avantage :* Plus réactif, moins de code "infrastructure" (watcher), traçabilité de bout en bout dans Celery.

#### B. Gestion des Prompts "Ancien" vs "Moderne"
*   **Constat :** Le document mentionne la détection "Ancien/Moderne", mais le code actuel (`process_images_task` dans `observations/tasks.py`) ne charge qu'un seul prompt (`prompt_gemini_transcription.txt`).
*   **Action :** Il faut implémenter cette logique de sélection de prompt *avant* l'appel Gemini dans la tâche Celery.

---

### 🛠️ Facilité de mise en place (++)

**Ce qui est bien vu :**
*   Réutilisation des services existants (`ImportationService`).
*   Pas de nouvelle infrastructure lourde (on reste sur Django/Celery/Postgres/Redis).

**Points de vigilance :**

#### A. Le "Score de Confiance"
*   **Complexité :** Implémenter un score composite (OCR + Espèce) est une excellente idée mais peut être complexe à calibrer au début.
*   **Conseil :** Commencer simple.
    1.  Score = Score de similarité espèce (c'est le prédicteur n°1 d'erreur).
    2.  Si JSON invalide ou structure cassée -> Rejet direct (déjà géré).
    3.  Ajouter les règles métier (œufs vs poussins) dans un second temps.

#### B. La table `EspeceEquivalence`
*   **C'est le "Game Changer" :** C'est la fonctionnalité qui aura le meilleur ROI (Retour sur Investissement) pour réduire la charge humaine.
*   **Implémentation :** Très simple à mettre en place (modèle clé-valeur). À prioriser en Sprint 1.

---

### 📊 Qualité du suivi des tâches (+++)

**Ce qui est excellent :**
*   La proposition de **DLQ (Dead Letter Queue)** via `ImportationErreur`. C'est indispensable pour ne pas perdre silencieusement des fiches parmi 50 000.
*   Le dashboard de monitoring dédié.

**Recommandations :**

#### A. Traçabilité Fichier -> Fiche
*   Assurez-vous que le lien `FicheObservation.chemin_image` et `FicheObservation.chemin_json` soit **indestructible**. En cas de re-scan ou de doublon, on doit savoir exactement quel JSON a généré quelle fiche (hash MD5 du fichier source éventuellement ?).

#### B. Logs Structurés
*   Dans Celery, utilisez `structlog` ou ajoutez un `task_id` dans tous les logs pour pouvoir suivre une fiche spécifique à travers les logs (grep facile).

---

### 💎 Qualité de la transcription (++++)

**Ce qui est validé :**
*   Le choix de **Gemini 2.0 Flash** est pertinent (bon ratio coût/qualité/vitesse).
*   L'auto-correction via JSON (validateurs) est une bonne première barrière.

**Recommandations pour l'excellence :**

#### A. Calibration du Seuil (Threshold)
*   Le document propose de passer de `0.8` à `0.7`.
*   **Risque :** Augmentation des faux positifs (ex: "Mesange bleue" validée comme "Mesange noire" si l'OCR bave).
*   **Action :** Faire un "Dry Run" (simulation) sur 1000 fiches.
    *   Lancer l'import SANS validation auto.
    *   Comparer le choix de l'algo vs le choix humain.
    *   Ajuster le seuil scientifiquement (Matrice de confusion).

#### B. Pré-traitement Image (Optionnel)
*   Si l'OCR échoue souvent, envisager un pré-traitement léger (augmentation contraste, passage en N&B) avec `Pillow` avant l'envoi à Gemini. Cela coûte peu en CPU et aide beaucoup les modèles sur les écritures manuscrites pâles.

---

## 3. Résumé des Actions Recommandées (Priorisées)

1.  🥇 **Priorité Absolue :** Implémenter `EspeceEquivalence` (Apprentissage des corrections). C'est ce qui rendra le système "intelligent".
2.  🥈 **Architecture :** Préférer le chaînage Celery (`link`) au *Watcher Filesystem* pour l'import.
3.  🥉 **Code :** Mettre à jour `process_images_task` pour gérer dynamiquement les prompts (Ancien/Moderne) selon le chemin du fichier.
4.  🛡️ **Sécurité :** Implémenter la table `ImportationErreur` avant de lancer le gros volume.

## 4. Avis Personnel

C'est un très bon plan d'attaque. L'approche est pragmatique. Le point fort est d'accepter que **l'IA n'est pas parfaite** et de construire le workflow autour de la gestion des exceptions (validation humaine post-process, scores de confiance) plutôt que d'essayer d'obtenir 100% de réussite OCR, ce qui est impossible sur des archives manuscrites.

**Go pour la Phase 1 !** 🚀
