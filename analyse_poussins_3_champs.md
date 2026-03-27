# Analyse : Éclatement de `nombre_poussins` en 3 champs (1/2 · 3/4 · Vol't)

**Date** : 2026-03-27
**Portée** : `ResumeObservation` uniquement — le modèle `Observation` (par visite) conserve son champ `nombre_poussins` unique, car la distinction 1/2 / 3/4 / vol't est un résumé de saison, pas une donnée de visite.

---

## Contexte

Le JSON OCR a **toujours** eu 3 sous-valeurs pour les poussins (json_sanitizer.py l.146) :
```json
"nombre_poussins": {"1/2": null, "3/4": null, "vol_t": null}
```
Mais `ResumeObservation` n'a qu'un seul champ `nombre_poussins`, et le service ingest ne lisait que `vol_t` (importation_service.py l.1023). La saisie manuelle et l'affichage ont le même défaut : une seule cellule au lieu de trois.

---

## Nouveaux noms de champs Django

| Catégorie     | Clé JSON | Nouveau champ Django           |
|---------------|----------|-------------------------------|
| 1 à 2 semaines | `1/2`   | `nombre_poussins_1_2`         |
| 3 à 4 semaines | `3/4`   | `nombre_poussins_3_4`         |
| Volants       | `vol_t`  | `nombre_poussins_vol_t`       |

---

## Inventaire complet des fichiers à modifier

### 1. `observations/models.py`

**Ligne 212** — `ResumeObservation` :
```python
# AVANT
nombre_poussins = models.PositiveSmallIntegerField(blank=True, null=True)

# APRÈS : remplacer par 3 champs
nombre_poussins_1_2   = models.PositiveSmallIntegerField(blank=True, null=True)
nombre_poussins_3_4   = models.PositiveSmallIntegerField(blank=True, null=True)
nombre_poussins_vol_t = models.PositiveSmallIntegerField(blank=True, null=True)
```

**Lignes 273-280** — CheckConstraint `resume_poussins_le_eclos` :
```python
# AVANT
models.CheckConstraint(
    name="resume_poussins_le_eclos",
    condition=(
        Q(nombre_poussins__isnull=True)
        | Q(nombre_oeufs_eclos__isnull=True)
        | Q(nombre_poussins__lte=models.F("nombre_oeufs_eclos"))
    ),
),

# APRÈS : contrainte sur vol_t uniquement (étape finale, biologiquement la plus significative)
models.CheckConstraint(
    name="resume_poussins_vol_t_le_eclos",
    condition=(
        Q(nombre_poussins_vol_t__isnull=True)
        | Q(nombre_oeufs_eclos__isnull=True)
        | Q(nombre_poussins_vol_t__lte=models.F("nombre_oeufs_eclos"))
    ),
),
```

**Note sur la migration** : il faudra supprimer l'ancienne contrainte `resume_poussins_le_eclos` avant de supprimer le champ `nombre_poussins`.

---

### 2. Migration à créer

Créer `observations/migrations/0017_split_nombre_poussins.py` avec les étapes :
1. Supprimer la contrainte `resume_poussins_le_eclos`
2. Ajouter les 3 nouveaux champs (`nombre_poussins_1_2`, `nombre_poussins_3_4`, `nombre_poussins_vol_t`)
3. Migrer les données existantes : `nombre_poussins_vol_t = nombre_poussins` (les valeurs existantes étaient du vol_t)
4. Supprimer l'ancien champ `nombre_poussins`
5. Ajouter la nouvelle contrainte `resume_poussins_vol_t_le_eclos`

---

### 3. `observations/forms.py`

**Classe `ResumeObservationForm`** :

**(a) `Meta.fields` (l.389)** — remplacer `'nombre_poussins'` par 3 entrées :
```python
# AVANT
'nombre_poussins',

# APRÈS
'nombre_poussins_1_2',
'nombre_poussins_3_4',
'nombre_poussins_vol_t',
```

**(b) `Meta.widgets` (l.417)** — remplacer le widget unique par 3 :
```python
# AVANT
'nombre_poussins': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Non observé'}),

# APRÈS
'nombre_poussins_1_2':   forms.NumberInput(attrs={'min': 0, 'placeholder': 'Non observé'}),
'nombre_poussins_3_4':   forms.NumberInput(attrs={'min': 0, 'placeholder': 'Non observé'}),
'nombre_poussins_vol_t': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Non observé'}),
```

**(c) Méthode `clean_nombre_poussins` (l.432-434)** — remplacer par 3 méthodes :
```python
# AVANT
def clean_nombre_poussins(self):
    value = self.cleaned_data.get('nombre_poussins')
    return None if value == '' or value is None else value

# APRÈS
def clean_nombre_poussins_1_2(self):
    value = self.cleaned_data.get('nombre_poussins_1_2')
    return None if value == '' or value is None else value

def clean_nombre_poussins_3_4(self):
    value = self.cleaned_data.get('nombre_poussins_3_4')
    return None if value == '' or value is None else value

def clean_nombre_poussins_vol_t(self):
    value = self.cleaned_data.get('nombre_poussins_vol_t')
    return None if value == '' or value is None else value
```

---

### 4. `observations/templates/saisie/saisie_observation.html`

**Réduction des titres (l.756-762)** — la table a 7 colonnes, en ajouter 2 exige de raccourcir les titres existants pour éviter l'écrasement. Proposition :

```html
<!-- AVANT -->
<th>Premier œuf pondu</th>
<th>Premier poussin éclos</th>
<th>Premier poussin volant</th>
<th>Œufs pondus</th>
<th>Œufs éclos</th>
<th>Œufs non éclos</th>
<th>Nombre de poussins</th>

<!-- APRÈS (9 colonnes) -->
<th>1er œuf pondu</th>
<th>1er pouss. éclos</th>
<th>1er pouss. volant</th>
<th>Œufs pondus</th>
<th>Œufs éclos</th>
<th>Œufs non éclos</th>
<th>Poussins 1/2</th>
<th>Poussins 3/4</th>
<th>Poussins vol't</th>
```

**Cellules de données (l.827-833)** — remplacer la `<td>` unique par 3 :
```html
<!-- AVANT -->
<td>
    <div class="form-field">
        {{ resume_form.nombre_poussins.errors }}
        {{ resume_form.nombre_poussins }}
        <small style="display: block; color: #6c757d; font-size: 0.8em;">Vide = non observé</small>
    </div>
</td>

<!-- APRÈS -->
<td>
    <div class="form-field">
        {{ resume_form.nombre_poussins_1_2.errors }}
        {{ resume_form.nombre_poussins_1_2 }}
        <small style="display: block; color: #6c757d; font-size: 0.8em;">Vide = non observé</small>
    </div>
</td>
<td>
    <div class="form-field">
        {{ resume_form.nombre_poussins_3_4.errors }}
        {{ resume_form.nombre_poussins_3_4 }}
        <small style="display: block; color: #6c757d; font-size: 0.8em;">Vide = non observé</small>
    </div>
</td>
<td>
    <div class="form-field">
        {{ resume_form.nombre_poussins_vol_t.errors }}
        {{ resume_form.nombre_poussins_vol_t }}
        <small style="display: block; color: #6c757d; font-size: 0.8em;">Vide = non observé</small>
    </div>
</td>
```

---

### 5. `observations/templates/fiche_observation.html`

**Ligne 377** — même remplacement de `<th>` (mêmes titres raccourcis) :
```html
<!-- AVANT -->
<th>Nombre de poussins</th>

<!-- APRÈS -->
<th>Poussins 1/2</th>
<th>Poussins 3/4</th>
<th>Poussins vol't</th>
```

**Ligne 406** — remplacer la `<td>` unique par 3 :
```html
<!-- AVANT -->
<td>{% if fiche.resume.nombre_poussins is not None %}{{ fiche.resume.nombre_poussins }}{% else %}<span class="text-muted">-</span>{% endif %}</td>

<!-- APRÈS -->
<td>{% if fiche.resume.nombre_poussins_1_2 is not None %}{{ fiche.resume.nombre_poussins_1_2 }}{% else %}<span class="text-muted">-</span>{% endif %}</td>
<td>{% if fiche.resume.nombre_poussins_3_4 is not None %}{{ fiche.resume.nombre_poussins_3_4 }}{% else %}<span class="text-muted">-</span>{% endif %}</td>
<td>{% if fiche.resume.nombre_poussins_vol_t is not None %}{{ fiche.resume.nombre_poussins_vol_t }}{% else %}<span class="text-muted">-</span>{% endif %}</td>
```

**Titres du résumé (l.371-377)** — même raccourcissement :
```html
<!-- AVANT -->
<th>Premier œuf pondu</th>
<th>Premier poussin éclos</th>
<th>Premier poussin volant</th>
<th>Œufs pondus</th>
<th>Œufs éclos</th>
<th>Œufs non éclos</th>
<th>Nombre de poussins</th>

<!-- APRÈS -->
<th>1er œuf pondu</th>
<th>1er pouss. éclos</th>
<th>1er pouss. volant</th>
<th>Œufs pondus</th>
<th>Œufs éclos</th>
<th>Œufs non éclos</th>
<th>Poussins 1/2</th>
<th>Poussins 3/4</th>
<th>Poussins vol't</th>
```

---

### 6. Templates accounts (3 fichiers)

Ces templates affichent le résumé des fiches dans la page profil utilisateur.

**`accounts/templates/accounts/user_detail.html` (l.22 et l.33)**
**`accounts/templates/accounts/user_detail_partial.html` (l.22 et l.32)**
**`accounts/templates/accounts/mon_profil.html` (l.39 et l.49)**

Dans chacun, même transformation (1 `<th>` → 3 `<th>`, 1 `<td>` → 3 `<td>`) :
```html
<!-- AVANT (th) -->
<th>Nombre de poussins</th>
<!-- AVANT (td) -->
<td>{{ fiche.resume.nombre_poussins }}</td>

<!-- APRÈS (th) -->
<th>Poussins 1/2</th>
<th>Poussins 3/4</th>
<th>Poussins vol't</th>
<!-- APRÈS (td) -->
<td>{{ fiche.resume.nombre_poussins_1_2|default:"-" }}</td>
<td>{{ fiche.resume.nombre_poussins_3_4|default:"-" }}</td>
<td>{{ fiche.resume.nombre_poussins_vol_t|default:"-" }}</td>
```

---

### 7. `ingest/importation_service.py`

**Lignes 1018-1080** — lire les 3 sous-valeurs et sauvegarder les 3 champs :

```python
# AVANT (l.1018-1023)
nombre_poussins_dict = resume_data.get('nombre_poussins') or {}
nombre_poussins = safe_int(nombre_poussins_dict.get('vol_t'))

# APRÈS
nombre_poussins_dict   = resume_data.get('nombre_poussins') or {}
nombre_poussins_1_2    = safe_int(nombre_poussins_dict.get('1/2'))
nombre_poussins_3_4    = safe_int(nombre_poussins_dict.get('3/4'))
nombre_poussins_vol_t  = safe_int(nombre_poussins_dict.get('vol_t'))
```

**Log l.1028** — adapter le message :
```python
# AVANT
f"poussins={nombre_poussins}"
# APRÈS
f"poussins 1/2={nombre_poussins_1_2}, 3/4={nombre_poussins_3_4}, vol't={nombre_poussins_vol_t}"
```

**Logique de correction automatique (l.1033-1048)** — adapter pour utiliser `vol_t` (la valeur finale) dans la comparaison avec `nombre_oeufs_eclos` :
```python
# AVANT
if (nombre_poussins and nombre_poussins > 0 and ...):
    nombre_oeufs_eclos = nombre_poussins
if nombre_poussins and nombre_oeufs_eclos and nombre_poussins > nombre_oeufs_eclos:
    nombre_oeufs_eclos = nombre_poussins

# APRÈS (utiliser vol_t comme référence)
if (nombre_poussins_vol_t and nombre_poussins_vol_t > 0 and ...):
    nombre_oeufs_eclos = nombre_poussins_vol_t
if nombre_poussins_vol_t and nombre_oeufs_eclos and nombre_poussins_vol_t > nombre_oeufs_eclos:
    nombre_oeufs_eclos = nombre_poussins_vol_t
```

**Attribution finale (l.1080)** :
```python
# AVANT
resume.nombre_poussins = nombre_poussins

# APRÈS
resume.nombre_poussins_1_2   = nombre_poussins_1_2
resume.nombre_poussins_3_4   = nombre_poussins_3_4
resume.nombre_poussins_vol_t = nombre_poussins_vol_t
```

---

### 8. `observations/admin.py`

Lignes ~37-40 — `ObservationAdmin` référence `nombre_poussins` et `nombre_poussins_incertain` (ces champs sont sur `Observation`, pas `ResumeObservation` — **pas de changement nécessaire ici**).

S'il existe un `ResumeObservationAdmin` (à vérifier), adapter ses champs.

---

### 9. `observations/views/saisie_observation_view.py`

**Logs d'audit (l.658 et l.828)** — ces lignes référencent `obs.nombre_poussins` qui est sur le modèle `Observation` (par visite), **pas** `ResumeObservation`. **Pas de changement.**

---

### 10. Tests

**`observations/tests/test_views.py`** — les données de test `'nombre_poussins': ''` et `nombre_poussins=2` sont sur `Observation` (par visite). **Pas de changement.**

S'il existe des tests sur `ResumeObservation.nombre_poussins`, les adapter pour les 3 nouveaux champs.

**`observations/tests/test_models.py`** (l.63, 69) — idem, concerne `Observation`. **Pas de changement.**

**`observations/tests/test_json_sanitizer.py`** — les données JSON ont déjà `"nombre_poussins": {"1/2": ..., "3/4": ..., "vol_t": ...}`. **Pas de changement dans les données de test**, mais si des tests vérifient que l'ingest ne lit que `vol_t`, les adapter.

---

### 11. `scripts/reset_et_jeu_test.py`

**Ligne 109** : `fiche.resume.nombre_poussins = 4`

```python
# AVANT
fiche.resume.nombre_poussins = 4

# APRÈS
fiche.resume.nombre_poussins_1_2   = None
fiche.resume.nombre_poussins_3_4   = 2
fiche.resume.nombre_poussins_vol_t = 4
```

---

### 12. Documentation (optionnel — à faire en dernier)

- `docs/applications/observations.md` l.60 et l.88
- `docs/guides/utilisateur/saisie_observation.md`
- `docs/guides/ocr_gemini.md` l.84
- `specs/functional_rules.md` l.53, 111, 125
- `CLAUDE.md` l.72

---

## Récapitulatif des fichiers à modifier

| Fichier | Nature de la modification |
|---------|--------------------------|
| `observations/models.py` | 1 champ → 3 champs + contrainte |
| `observations/migrations/0017_...py` | À créer (migration données) |
| `observations/forms.py` | 1 field + 1 widget + 1 clean → 3+3+3 |
| `observations/templates/saisie/saisie_observation.html` | 1 th → 3 + 1 td → 3 + raccourcir titres |
| `observations/templates/fiche_observation.html` | Idem |
| `accounts/templates/accounts/user_detail.html` | 1 th+td → 3+3 |
| `accounts/templates/accounts/user_detail_partial.html` | 1 th+td → 3+3 |
| `accounts/templates/accounts/mon_profil.html` | 1 th+td → 3+3 |
| `ingest/importation_service.py` | Lire 3 clés + sauvegarder 3 champs |
| `scripts/reset_et_jeu_test.py` | Adapter les valeurs de test |

**Fichiers NON modifiés** (concernent `Observation` par visite, pas `ResumeObservation`) :
- `observations/forms.py` — `ObservationForm` (nombre_poussins par visite reste identique)
- `observations/admin.py` — `ObservationAdmin` (idem)
- `observations/views/saisie_observation_view.py` — logs d'audit (idem)
- `observations/tests/test_views.py`, `test_models.py` — (idem)
- `observations/static/.../UncertaintyInput.js` — gère l'incertitude par visite (idem)
- `observations/json_rep/json_sanitizer.py` — déjà correct avec les 3 clés
- Templates `saisie/ajouter_observation.html` — formulaire par visite (idem)

---

## Ordre d'implémentation recommandé

1. `models.py` (champs + contrainte)
2. Migration `0017_...py` (avec données)
3. `forms.py`
4. `ingest/importation_service.py`
5. Templates saisie et fiche (2 fichiers `observations/templates/`)
6. Templates accounts (3 fichiers)
7. `scripts/reset_et_jeu_test.py`
8. Tests (si nécessaire)
9. Documentation
