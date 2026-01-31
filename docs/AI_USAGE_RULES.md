# Gestion du Contexte et des Règles pour les Agents IA

Ce document résume les bonnes pratiques concernant l'interaction entre les agents IA (comme Gemini CLI) et les fichiers de configuration de projet, notamment le dossier `.cursor/rules`.

## 1. Visibilité des fichiers (.cursor/rules)

### Le constat
Les agents autonomes "à la demande" (CLI) ne fonctionnent pas comme l'IA intégrée dans l'éditeur Cursor.
*   **Cursor** : Injecte automatiquement le contenu des règles dans le contexte à chaque requête.
*   **Agent CLI** : Voit que le dossier existe lors d'un `ls`, mais **ne lit pas le contenu** tant qu'on ne lui demande pas explicitement.

### Pourquoi ?
C'est une stratégie d'économie de ressources. Lire l'intégralité d'un projet au démarrage consommerait inutilement des tokens et du temps. L'agent va chercher l'information uniquement si elle est nécessaire au contexte actuel.

## 2. Analyse des Coûts (Tokens)

Lorsqu'on demande à l'agent de lire un fichier de règles (ex: `.cursor/rules/guardrails.mdc`), deux types de coûts s'appliquent :

1.  **Le coût de lecture unique (One-shot) :**
    *   C'est le coût pour traiter le fichier une fois.
    *   *Exemple pour `guardrails.mdc` (3.5kb)* : Environ **1 000 tokens**.
    *   C'est un coût négligeable comparé aux quotas des modèles actuels.

2.  **Le coût de maintenance du contexte (Context Window) :**
    *   Une fois lu, le contenu du fichier fait partie de l'historique de la conversation.
    *   Il est renvoyé au modèle à chaque nouvelle question.
    *   *Impact* : Chaque question suivante "coûte" 1 000 tokens de plus que si le fichier n'avait pas été lu.
    *   *Verdict* : Avec les fenêtres de contexte modernes (Gemini 1.5 Pro gère > 1M tokens), cet impact est minime pour des fichiers de documentation standards.

## 3. Stratégies recommandées

Pour s'assurer que l'agent respecte les conventions du projet :

*   **Option A (Instruction Explicite)** : En début de session, demander : *"Lis le fichier .cursor/rules/guardrails.mdc et applique ces règles pour la suite."*
*   **Option B (Fichier Central)** : Utiliser un fichier `CLAUDE.md` ou `AI_RULES.md` à la racine qui résume les points critiques (style, tests, architecture). L'agent a tendance à vérifier ces fichiers racines plus spontanément.
*   **Option C (Mémoire à long terme)** : Utiliser la commande `save_memory` de l'agent pour enregistrer des préférences critiques (ex: *"Souviens-toi que je veux toujours des docstrings en français"*).

## 4. Conclusion
Ne pas supposer que l'agent connaît les règles implicites définies dans des sous-dossiers spécifiques à d'autres outils. Il est toujours préférable (et peu coûteux) de lui demander explicitement de les lire en début de tâche complexe.
