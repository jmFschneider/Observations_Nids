 Parfait ! La configuration double MkDocs a été commitée avec succès.

  ✅ Commit réalisé : 726c1cf

  Résumé des changements :
  - ✅ mkdocs.yml - Modifié pour documentation utilisateurs (thème vert, port 8001)
  - ✅ mkdocs-dev.yml - Nouveau pour documentation développeurs (thème bleu, port 8002)
  - ✅ index-dev.md - Nouvelle page d'accueil développeurs (282 lignes)

  🚀 Utilisation

  Vous pouvez maintenant lancer les deux documentations simultanément :

  # Terminal 1 - Documentation Utilisateurs
  mkdocs serve -f mkdocs.yml
  # → http://127.0.0.1:8001

  # Terminal 2 - Documentation Développeurs
  mkdocs serve -f mkdocs-dev.yml
  # → http://127.0.0.1:8002

  📊 Différences clés

| Aspect   | Utilisateurs (mkdocs.yml) | Développeurs (mkdocs-dev.yml)         |
| -------- | ------------------------- | ------------------------------------- |
| Thème    | Vert clair                | Bleu foncé (slate)                    |
| Sections | 6 sections                | 11 sections                           |
| Focus    | Guides, workflows, aide   | Architecture, API, tests, déploiement |
| Homepage | index.md                  | index-dev.md                          |

  Les deux configurations partagent le même répertoire docs/docs/ - aucune duplication de fichiers
  !