# TODO : Configuration MkDocs

**Date de création :** 2025-10-12
**Date de mise à jour :** 2025-10-13
**Priorité :** Terminée
**Statut :** ✅ **Terminé**

---

## Objectif

Mettre en place MkDocs pour centraliser et faciliter l'accès à toute la documentation du projet.

## Tâches Réalisées

- [x] ~~Organiser la structure des répertoires docs/~~ (Fait lors du refactoring de la documentation)
- [x] ~~Créer le fichier de configuration `mkdocs.yml`~~ (Fait)
- [x] ~~Organiser la navigation (sidebar) pour tous les documents existants~~ (Fait, dans `mkdocs.yml`)

## Prochaines Étapes Pour Vous

Le travail de configuration est terminé. Pour voir le site de documentation :

1.  **Installez MkDocs et le thème Material** (si ce n'est pas déjà fait) :
    ```bash
    pip install mkdocs mkdocs-material
    ```

2.  **Lancez le serveur de développement local :**
    À la racine du projet, lancez la commande :
    ```bash
    mkdocs serve
    ```

3.  **Consultez votre site de documentation** à l'adresse [http://127.0.0.1:8000](http://127.0.0.1:8000).

Le site se mettra à jour automatiquement lorsque vous modifierez un fichier `.md`.

## Tâches restantes (Optionnel)

- [ ] (Optionnel) Configurer le déploiement sur GitHub Pages.
- [ ] (Optionnel) Mettre à jour le `README.md` principal du projet avec un lien vers la documentation.