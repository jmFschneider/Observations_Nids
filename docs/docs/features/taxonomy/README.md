# Documentation de la fonctionnalité : Taxonomie

L'application `taxonomy` est le cœur de la classification des espèces pour le projet. Son rôle est de fournir une base de données propre, structurée et référencée pour toutes les espèces d'oiseaux.

## 1. Modèles de Données

La taxonomie est hiérarchisée en 3 modèles principaux (`taxonomy/models.py`) :

1.  **`Ordre`** : Le plus haut niveau de classification (ex: *Passeriformes*).
2.  **`Famille`** : Le niveau intermédiaire (ex: *Turdidae*), lié à un Ordre.
3.  **`Espece`** : Le modèle principal, contenant les noms (français, scientifique, anglais), le statut, et un lien vers sa Famille.

## 2. Alimentation des Données : les Commandes de Gestion

La base de données taxonomique n'est pas conçue pour être entièrement gérée à la main. Elle est alimentée et enrichie via des commandes Django spécialisées.

Voici un résumé des commandes disponibles. **Cliquez sur le nom de chaque guide pour des instructions détaillées.**

### A. `charger_lof` (Méthode Recommandée)
- **Rôle :** Importe les espèces d'oiseaux depuis la **Liste des Oiseaux de France (LOF)**.
- **Avantages :** Source officielle française, fichier très léger (64KB), import ultra-rapide (10-30 secondes).
- **Guide détaillé :** [Import LOF](./README_LOF.md)

### B. `charger_taxref` (Méthode Alternative)
- **Rôle :** Importe les espèces depuis le référentiel **TaxRef** du Muséum national d'Histoire naturelle.
- **Inconvénients :** Nécessite un téléchargement manuel d'un fichier très lourd (150MB), import plus lent (1-3 minutes).
- **Guide détaillé :** [Import TaxRef](./README_TAXREF.md)

### C. `recuperer_liens_oiseaux_net` (Enrichissement)
- **Rôle :** Une fois les espèces importées, cette commande parcourt la base de données et trouve automatiquement les liens vers les fiches correspondantes sur le site [oiseaux.net](https://www.oiseaux.net).
- **Taux de réussite :** Environ 98%.
- **Guide détaillé :** [Récupération des liens oiseaux.net](./README_LIENS_OISEAUX_NET.md)

---

## 3. Gestion Manuelle (Interface d'Administration)

Bien que l'alimentation principale soit automatisée, une interface web est disponible pour les administrateurs afin de gérer manuellement les espèces.

**Accès :** `/taxonomy/especes/` (accessible depuis le menu principal pour les administrateurs).

### Fonctionnalités de l'interface

- **Liste des espèces (`/taxonomy/especes/`)**
  - Affichage paginé de toutes les espèces.
  - Outils de recherche et de filtre (par Ordre, Famille, Statut).

- **Détail d'une espèce (`/taxonomy/especes/<id>/`)**
  - Vue complète des informations taxonomiques.
  - Affiche le nombre de fiches d'observation qui utilisent cette espèce.

- **Création / Modification / Suppression**
  - Formulaires pour créer une nouvelle espèce ou modifier une espèce existante.
  - Protection contre la suppression d'une espèce si elle est déjà utilisée dans des fiches d'observation.

- **Portail d'import (`/taxonomy/importer/`)**
  - Page récapitulative qui fournit des instructions pour lancer les commandes d'import en masse.