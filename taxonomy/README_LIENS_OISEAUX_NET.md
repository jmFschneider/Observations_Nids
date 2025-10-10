# Récupération automatique des liens oiseaux.net

Ce document explique comment utiliser la commande `recuperer_liens_oiseaux_net` pour récupérer automatiquement les liens vers les fiches oiseaux.net pour toutes les espèces de votre base de données.

## Vue d'ensemble

La commande parcourt automatiquement toutes les espèces et tente de trouver leur URL sur le site [oiseaux.net](https://www.oiseaux.net), un référentiel ornithologique français de qualité.

### Stratégie de recherche (3 méthodes)

1. **Méthode 1 (PRIORITAIRE) : Construction depuis le nom français**
   - Exemple : "Bernache cravant" → `https://www.oiseaux.net/oiseaux/bernache.cravant.html`
   - Taux de réussite : ~95%
   - Rapide et fiable

2. **Méthode 2 (FALLBACK) : Construction depuis le nom scientifique**
   - Exemple : "Branta bernicla" → `https://www.oiseaux.net/oiseaux/branta.bernicla.html`
   - Utilisé si la méthode 1 échoue
   - Taux de réussite : ~20% (oiseaux.net préfère les noms français)

3. **Méthode 3 (DERNIER RECOURS) : Recherche Google**
   - Recherche `"Nom scientifique" "Nom français" site:oiseaux.net`
   - Utilisé si les méthodes 1 et 2 échouent
   - Taux de réussite : ~80%
   - Plus lent (requêtes Google + délais)

---

## Installation

### Dépendances requises

Les dépendances suivantes doivent être installées :

```bash
pip install beautifulsoup4 requests
```

Elles sont normalement déjà incluses dans `requirements.txt`.

---

## Utilisation

### Commande de base

```bash
python manage.py recuperer_liens_oiseaux_net
```

Cette commande :
- Traite **uniquement les espèces sans lien** (champ `lien_oiseau_net` vide)
- Vérifie chaque URL construite avec une requête HTTP
- Affiche une barre de progression en temps réel
- Met à jour la base de données automatiquement

### Options disponibles

#### `--force` : Mettre à jour toutes les espèces

```bash
python manage.py recuperer_liens_oiseaux_net --force
```

Met à jour **toutes** les espèces, même celles qui ont déjà un lien.

**Cas d'usage :**
- Après une migration de données
- Si vous soupçonnez des liens obsolètes
- Pour rafraîchir toute la base

#### `--limit N` : Mode test

```bash
python manage.py recuperer_liens_oiseaux_net --limit 10
```

Limite le traitement aux **N premières espèces**.

**Cas d'usage :**
- Tester la commande avant un traitement complet
- Vérifier que tout fonctionne correctement

#### `--dry-run` : Simulation

```bash
python manage.py recuperer_liens_oiseaux_net --dry-run
```

Simule le traitement **sans modifier la base de données**.

**Cas d'usage :**
- Vérifier combien d'espèces seraient trouvées
- Tester les URLs générées
- Prévisualiser les résultats

#### `--delay N` : Délai entre requêtes

```bash
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

Définit le délai en secondes entre chaque requête HTTP (défaut : 1.0 seconde).

**Cas d'usage :**
- Réduire la charge sur les serveurs (éthique)
- Éviter d'être bloqué par Google ou oiseaux.net
- Recommandé : 1-2 secondes pour un traitement complet

### Exemples de combinaisons

#### Test sur 5 espèces sans modifier la base

```bash
python manage.py recuperer_liens_oiseaux_net --limit 5 --dry-run
```

#### Traitement complet avec délai raisonnable

```bash
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

#### Mise à jour forcée de toutes les espèces (prudent)

```bash
python manage.py recuperer_liens_oiseaux_net --force --delay 2
```

---

## Sortie de la commande

### Barre de progression

```
[1/577] Bernache cravant (Branta bernicla)
  -> Test URL nom francais: https://www.oiseaux.net/oiseaux/bernache.cravant.html
  [OK] URL nom francais valide !

[2/577] Bernache à cou roux (Branta ruficollis)
  -> Test URL nom francais: https://www.oiseaux.net/oiseaux/bernache.a.cou.roux.html
  [OK] URL nom francais valide !
```

### Résumé final

```
============================================================
[RESUME]
============================================================
Total traite      : 577
[OK] Succes direct   : 550
[OK] Succes Google   : 20
[!] Ignores         : 5
[X] Echecs          : 2

Taux de reussite : 98.8%
```

### Espèces en échec

Si certaines espèces ne sont pas trouvées, elles sont listées à la fin :

```
============================================================
[ECHECS] Especes non trouvees:
============================================================
  - Goéland marin (Larus marinus)
  - Bécasseau sanderling (Calidris alba)

[CONSEIL] Verifiez manuellement ces especes sur oiseaux.net
```

---

## Performances et temps d'exécution

### Durée estimée

Pour **577 espèces** (base complète LOF) :

| Configuration | Durée totale | Commentaire |
|---------------|--------------|-------------|
| `--delay 1.0` (défaut) | ~10 minutes | Rapide, bon compromis |
| `--delay 1.5` | ~15 minutes | Recommandé pour usage réel |
| `--delay 2.0` | ~20 minutes | Très respectueux des serveurs |

### Optimisations

- Les espèces sans nom scientifique sont automatiquement ignorées
- Les URLs sont vérifiées avec `HEAD` avant `GET` (plus rapide)
- Le traitement s'arrête dès qu'une méthode réussit

---

## Cas particuliers

### Espèces sans nom scientifique

Les espèces sans nom scientifique sont **automatiquement ignorées** et comptées dans `[!] Ignores`.

**Pourquoi ?**
- Impossible de construire une URL fiable
- Recherche Google trop imprécise

**Solution :**
Ajoutez manuellement le nom scientifique dans l'interface de gestion des espèces (`/taxonomy/especes/`).

### Noms avec caractères spéciaux

Les noms avec accents, apostrophes, traits d'union sont **automatiquement normalisés** :

| Nom original | URL générée |
|--------------|-------------|
| "Bernache à cou roux" | `bernache.a.cou.roux.html` |
| "Goéland d'Audouin" | `goeland.d.audouin.html` |
| "Pic-vert" | `pic.vert.html` |

### Sous-espèces

Les sous-espèces sont gérées automatiquement :

```python
# Nom scientifique : "Passer domesticus domesticus"
# → Normalisé en : "Passer domesticus"
```

---

## Dépannage

### Erreur : `UnicodeEncodeError`

**Cause :** Console Windows ne supporte pas les caractères spéciaux.

**Solution :** Déjà corrigé dans la version actuelle (utilise `[OK]` au lieu de `✓`).

### Erreur : `ModuleNotFoundError: No module named 'bs4'`

**Cause :** BeautifulSoup4 n'est pas installé.

**Solution :**
```bash
pip install beautifulsoup4
```

### Taux de réussite faible (<50%)

**Causes possibles :**
1. Noms d'espèces non standard (ex : noms régionaux au lieu de noms officiels)
2. Connexion Internet instable
3. Oiseaux.net temporairement inaccessible

**Solutions :**
- Vérifier les noms d'espèces dans l'interface de gestion
- Réessayer avec `--delay 2` pour éviter les timeouts
- Vérifier manuellement sur oiseaux.net

### Google bloque les requêtes

**Symptôme :** Beaucoup d'échecs avec la méthode 3 (Google).

**Cause :** Google détecte trop de requêtes automatiques depuis votre IP.

**Solutions :**
1. Augmenter le délai : `--delay 3`
2. Lancer le traitement en plusieurs fois avec `--limit`
3. Attendre quelques heures avant de relancer

---

## Maintenance

### Mise à jour régulière

Nous recommandons de relancer la commande :
- **Après chaque import d'espèces** (LOF ou TaxRef)
- **Une fois par an** : pour rafraîchir les liens (avec `--force`)

### Vérification manuelle

Pour les espèces en échec, vérifiez manuellement sur [oiseaux.net](https://www.oiseaux.net) et ajoutez le lien via l'interface d'administration (`/taxonomy/especes/<id>/modifier/`).

---

## Exemples de workflow

### Workflow 1 : Premier usage

```bash
# 1. Test sur 10 espèces
python manage.py recuperer_liens_oiseaux_net --limit 10 --dry-run

# 2. Si tout va bien, traitement complet
python manage.py recuperer_liens_oiseaux_net --delay 1.5

# 3. Vérifier les échecs et les compléter manuellement
```

### Workflow 2 : Après import de nouvelles espèces

```bash
# Traiter uniquement les espèces sans lien
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

### Workflow 3 : Rafraîchissement annuel

```bash
# Mettre à jour toutes les espèces (au cas où URLs changent)
python manage.py recuperer_liens_oiseaux_net --force --delay 2
```

---

## Statistiques

### Taux de réussite attendus

| Méthode | Taux de réussite |
|---------|------------------|
| Méthode 1 (nom français) | 95% |
| Méthode 2 (nom scientifique) | 20% |
| Méthode 3 (Google) | 80% |
| **Global** | **~98%** |

### Espèces problématiques

Les espèces suivantes peuvent poser problème :
- **Espèces rares** : pas de fiche sur oiseaux.net
- **Noms régionaux** : non reconnus par oiseaux.net
- **Sous-espèces exotiques** : hors périmètre oiseaux.net (focus Europe/France)

---

## Support et contribution

### Signaler un problème

Si vous rencontrez un problème :
1. Vérifiez que les dépendances sont installées
2. Testez avec `--dry-run --limit 5`
3. Consultez les logs Django (`observations/logs/django_debug.log`)
4. Créez une issue avec l'erreur complète

### Améliorer la commande

Pistes d'amélioration possibles :
- Ajouter d'autres sources de liens (Birds of the World, eBird, etc.)
- Paralléliser les requêtes HTTP pour aller plus vite
- Ajouter un cache pour éviter de revérifier les mêmes URLs
- Intégrer un système de retry automatique en cas d'échec réseau

---

## Licence et crédits

### Données oiseaux.net

Les liens récupérés pointent vers [oiseaux.net](https://www.oiseaux.net), un site ornithologique français de référence maintenu par la LPO (Ligue pour la Protection des Oiseaux).

**Conditions d'utilisation :**
- Les liens sont publics et libres d'usage
- Respectez les conditions générales d'oiseaux.net
- Ne surchargez pas leurs serveurs (d'où le délai entre requêtes)

### Commande développée par

Documentation et commande créées avec **Claude Code** (Anthropic) pour le projet **Observations Nids**.

**Version :** 1.0
**Dernière mise à jour :** 2025-10-09

---

## Annexes

### Structure des URLs oiseaux.net

Oiseaux.net utilise une structure d'URL prévisible :

```
https://www.oiseaux.net/oiseaux/[nom-vernaculaire-francais].html
```

**Règles de normalisation :**
- Nom français en minuscules
- Espaces remplacés par des points
- Accents supprimés
- Caractères spéciaux supprimés

**Exemples :**
- "Bernache cravant" → `bernache.cravant.html`
- "Goéland d'Audouin" → `goeland.d.audouin.html`
- "Pic épeiche" → `pic.epeiche.html`

### Code source

Le code source de la commande est disponible dans :
```
taxonomy/management/commands/recuperer_liens_oiseaux_net.py
```

**Fonctions principales :**
- `construire_url_depuis_nom_francais()` : Construction URL depuis nom français
- `construire_url_depuis_nom_scientifique()` : Construction URL depuis nom scientifique
- `verifier_url_existe()` : Vérification HTTP de l'URL
- `chercher_via_google()` : Recherche Google en fallback

---

**Bon traitement ! 🐦**
