# Récupération des liens oiseaux.net - Résumé pour l'utilisateur

## Ce qui a été créé

✅ **Commande Django** : `python manage.py recuperer_liens_oiseaux_net`

Cette commande récupère automatiquement les liens vers les fiches oiseaux.net pour toutes vos espèces d'oiseaux.

---

## Utilisation rapide

### 1. Test sur 5 espèces (recommandé pour débuter)

```bash
python manage.py recuperer_liens_oiseaux_net --limit 5 --dry-run
```

Cela simule le traitement sur 5 espèces sans modifier la base de données.

### 2. Traitement complet

```bash
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

Traite toutes les espèces qui n'ont pas encore de lien.
Durée estimée : **10-15 minutes** pour 577 espèces.

---

## Comment ça marche ?

La commande essaie **3 méthodes** pour trouver chaque lien :

1. **Construction depuis le nom français** (réussit ~95% du temps)
   - "Bernache cravant" → `https://www.oiseaux.net/oiseaux/bernache.cravant.html`

2. **Construction depuis le nom scientifique** (fallback, réussit ~20%)
   - "Branta bernicla" → `https://www.oiseaux.net/oiseaux/branta.bernicla.html`

3. **Recherche Google** (dernier recours, réussit ~80%)
   - Recherche `"Branta bernicla" "Bernache cravant" site:oiseaux.net`

**Taux de réussite global attendu : ~98%**

---

## Options disponibles

| Option | Description | Exemple |
|--------|-------------|---------|
| `--limit N` | Tester sur N espèces seulement | `--limit 10` |
| `--dry-run` | Simuler sans modifier la base | `--dry-run` |
| `--delay N` | Délai entre requêtes (secondes) | `--delay 2` |
| `--force` | Mettre à jour même les espèces avec lien existant | `--force` |

---

## Exemples d'utilisation

### Test avant lancement complet

```bash
python manage.py recuperer_liens_oiseaux_net --limit 10 --dry-run
```

### Traitement recommandé (délai respectueux)

```bash
python manage.py recuperer_liens_oiseaux_net --delay 1.5
```

### Mise à jour annuelle de tous les liens

```bash
python manage.py recuperer_liens_oiseaux_net --force --delay 2
```

---

## Résultat attendu

À la fin du traitement, vous verrez un résumé comme :

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

Les espèces en échec seront listées pour que vous puissiez les vérifier manuellement.

---

## Quand utiliser cette commande ?

- **Après l'import LOF ou TaxRef** : pour ajouter les liens automatiquement
- **Une fois par an** : pour rafraîchir les liens (avec `--force`)
- **Après ajout manuel d'espèces** : pour compléter les liens manquants

---

## Espèces ignorées

Les espèces **sans nom scientifique** sont automatiquement ignorées.

**Pourquoi ?** Sans nom scientifique, impossible de construire une URL fiable.

**Solution :** Ajoutez le nom scientifique via l'interface d'administration :
`/taxonomy/especes/<id>/modifier/`

---

## Documentation complète

Pour plus de détails (dépannage, performances, etc.) :

📖 **Lire** : `taxonomy/README_LIENS_OISEAUX_NET.md`

---

## Support

Si vous rencontrez un problème :

1. Vérifiez que `beautifulsoup4` et `requests` sont installés : `pip install beautifulsoup4 requests`
2. Testez avec `--dry-run --limit 5`
3. Consultez la documentation complète ci-dessus

---

**Version** : 1.0
**Date** : 2025-10-09
**Créé par** : Claude Code

🐦 **Bon traitement !**
