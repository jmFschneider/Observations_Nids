# Taxonomy - Vue d'ensemble

> Gestion des espèces d'oiseaux, familles et codes de référence (GONM)

## Responsabilité

L'application **taxonomy** gère le référentiel taxonomique :
- Espèces d'oiseaux (nom scientifique, nom vernaculaire)
- Familles d'oiseaux
- Codes GONM (Groupe Ornithologique Normand)
- Import depuis sources externes

## Modèles principaux

| Modèle | Description | Fichier |
|--------|-------------|---------|
| **Espece** | Espèce d'oiseau avec code GONM | `taxonomy/models.py` |
| **Famille** | Famille ornithologique | `taxonomy/models.py` |

### Champ `code_gonm` dans le modèle Espece

Le champ `code_gonm` stocke le code du Groupe Ornithologique Normand pour chaque espèce :

```python
code_gonm = models.CharField(
    max_length=10,
    blank=True,
    help_text="Code GONM de l'espèce"
)
```

**Caractéristiques** :
- Facultatif (peut être vide)
- Maximum 10 caractères
- Format : Lettre(s) + numéro (ex: `A01`, `C08`, `V16`)
- 425 espèces sur 576 ont un code GONM (74%)

**Catégories de codes** :
- **A** : Plongeons, Pétrels
- **B** : Hérons, Cigognes
- **C-D** : Anatidés (canards, oies)
- **E** : Rapaces
- **F-G-H** : Limicoles
- **J-K** : Laridés, Sternes
- **L-M** : Pics, Rapaces nocturnes
- **N-P-Q-R-S-T** : Passereaux
- **U-V** : Granivores, Corvidés

## Commandes management

### `import_codes_gonm`

Importe les codes GONM depuis un fichier TSV validé.

```bash
# Import avec le fichier par défaut
python manage.py import_codes_gonm

# Import avec un fichier personnalisé
python manage.py import_codes_gonm --file /chemin/vers/fichier.tsv

# Mode dry-run (simulation sans modification)
python manage.py import_codes_gonm --dry-run
```

**Fichier source** : `analyse-correspondances-gonm____80%.xlsx - analyse-correspondances-gonm.tsv`

**Format du fichier TSV** :
- Délimiteur : Tabulation (`\t`)
- Encodage : UTF-8
- Colonnes requises : `code_gonm`, `espece_trouvee_id`, `espece_trouvee_nom`

### `analyser_correspondances_gonm`

Analyse et compare les espèces du CSV GONM avec la base de données.

```bash
python manage.py analyser_correspondances_gonm
```

**Sortie** : Génère un fichier CSV avec scores de correspondance

## Affichage des codes GONM dans l'interface

Les codes GONM sont affichés dans plusieurs endroits de l'application :

### 1. Liste des espèces (`/taxonomy/especes/`)

**Template** : `taxonomy/templates/taxonomy/liste_especes.html`

Une colonne "Code GONM" affiche le code dans un badge gris :
- Badge `bg-secondary` si le code existe
- Tiret grisé `-` si absent

```html
<td>
    {% if espece.code_gonm %}
    <span class="badge bg-secondary">{{ espece.code_gonm }}</span>
    {% else %}
    <span class="text-muted">-</span>
    {% endif %}
</td>
```

### 2. Détail d'une observation (`/observations/<id>/`)

**Template** : `observations/templates/fiche_observation.html`

Le code GONM apparaît dans le tableau des informations générales, entre "Espèce" et "Année" :

| Fiche ID | Observateur | N° perso | Espèce | **Code GONM** | Année |
|----------|-------------|----------|---------|---------------|-------|
| 6 | Jean Dupont | 2024-001 | Plongeon arctique | **A01** | 2024 |

### 3. Modification d'une observation (`/observations/modifier/<id>/`)

**Template** : `observations/templates/saisie/saisie_observation.html`

Le code GONM s'affiche dans :
- Le tableau principal des informations générales
- La modale de recherche de fiches (colonne supplémentaire)

**API de recherche** : `observations/views/saisie_observation_view.py:rechercher_fiches()`

La fonction retourne maintenant le champ `code_gonm` dans les résultats JSON :

```python
resultats.append({
    'num_fiche': fiche.num_fiche,
    'observateur': f"{fiche.observateur.first_name} {fiche.observateur.last_name}",
    'espece': fiche.espece.nom,
    'code_gonm': fiche.espece.code_gonm or '-',  # ← Ajouté
    'annee': fiche.annee,
    'numero_personnel': fiche.numero_personnel or '',
    'commune': commune,
})
```

## Historique des modifications

### Janvier 2026 - Intégration des codes GONM

**Date** : 10 janvier 2026

**Changements** :
1. ✅ Migration ajoutée : `taxonomy/migrations/0002_espece_code_gonm.py`
2. ✅ Commande d'import corrigée pour utiliser le TSV validé (≥80% de confiance)
3. ✅ 425 codes GONM importés en base de données
4. ✅ Affichage ajouté dans 3 pages de l'interface
5. ✅ API de recherche mise à jour

**Fichiers modifiés** :
- `taxonomy/models.py` - Ajout du champ `code_gonm`
- `taxonomy/management/commands/import_codes_gonm.py` - Correction pour TSV
- `taxonomy/templates/taxonomy/liste_especes.html` - Colonne ajoutée
- `observations/templates/fiche_observation.html` - Colonne ajoutée
- `observations/templates/saisie/saisie_observation.html` - Colonne ajoutée
- `observations/views/saisie_observation_view.py` - API mise à jour

## Documentation existante

- **[codes_gonm.md](codes_gonm.md)** - Guide complet sur les codes GONM (nouveau)
- **[docs/developpeurs/guides/gestion_especes_taxonomie.md](../../guides/gestion_especes_taxonomie.md)**
- **[docs/INTEGRATION_CODES_GONM.md](../../../INTEGRATION_CODES_GONM.md)**

## Dépendances

- **core** - Modèles de base

## Voir aussi

- **[gotchas.md](gotchas.md)**
- **[codes_gonm.md](codes_gonm.md)** - Guide détaillé des codes GONM

---

*Dernière mise à jour : 2026-01-10*
