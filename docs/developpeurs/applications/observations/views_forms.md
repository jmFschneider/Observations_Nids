# Observations - Vues et formulaires

Ce fichier documente l'organisation des vues et formulaires de l'application observations.

---

## Organisation des vues

Les vues sont organisées dans le répertoire `observations/views/` :

```
observations/views/
├── __init__.py                      # Expose toutes les vues
├── saisie_observation_view.py       # Saisie de nouvelles fiches
├── views_observation.py             # Affichage et correction des fiches
├── views_home.py                    # Page d'accueil et listes
├── view_transcription.py            # Gestion des transcriptions OCR
└── upload_views.py                  # Upload de fichiers
```

---

## Vues principales

### `views_home.py` - Accueil et listes

| Vue | Route | Rôle |
|-----|-------|------|
| `home` | `/` | Page d'accueil |
| `liste_observations` | `/observations/` | Liste des fiches |

### `saisie_observation_view.py` - Saisie

| Vue | Route | Rôle |
|-----|-------|------|
| `saisie_observation` | `/observations/nouvelle/` | Formulaire de saisie nouvelle fiche |

### `views_observation.py` - Affichage et correction

| Vue | Route | Rôle |
|-----|-------|------|
| `fiche_observation` | `/observations/<num_fiche>/` | Affichage détail d'une fiche |
| `corriger_fiche` | `/observations/<num_fiche>/corriger/` | Interface de correction |

### `view_transcription.py` - Transcriptions OCR

| Vue | Route | Rôle |
|-----|-------|------|
| TODO | `/observations/transcriptions/` | Gestion des transcriptions |

### `upload_views.py` - Upload

| Vue | Route | Rôle |
|-----|-------|------|
| TODO | `/observations/upload/` | Upload d'images |

---

## Formulaires

**Fichier** : `observations/forms.py`

### Organisation

TODO : Documenter les formulaires principaux après lecture du fichier

Formulaires attendus :
- `FicheObservationForm` - Formulaire principal
- `LocalisationForm` - Localisation (commune, GPS)
- `NidForm` - Caractéristiques du nid
- `ResumeObservationForm` - Données de nidification
- `ObservationForm` - Observation ponctuelle

### Validation

Les formulaires doivent implémenter la méthode `clean()` pour valider les contraintes de cohérence :

```python
class ResumeObservationForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        # Validation paires jour/mois
        jour = cleaned_data.get('premier_oeuf_pondu_jour')
        mois = cleaned_data.get('premier_oeuf_pondu_mois')

        if (jour is not None) != (mois is not None):
            raise ValidationError(
                "Le jour et le mois doivent être renseignés ensemble ou laissés vides"
            )

        # Validation compteurs
        eclos = cleaned_data.get('nombre_oeufs_eclos')
        pondus = cleaned_data.get('nombre_oeufs_pondus')

        if eclos and pondus and eclos > pondus:
            raise ValidationError(
                "Le nombre d'œufs éclos ne peut pas dépasser le nombre d'œufs pondus"
            )

        return cleaned_data
```

---

## Templates

**Répertoire** : `observations/templates/`

### Organisation

```
observations/templates/
├── base.html                        # Template de base
├── observations/
│   ├── liste.html                   # Liste des fiches
│   ├── fiche_detail.html            # Détail d'une fiche
│   └── corriger.html                # Interface de correction
├── saisie/
│   └── saisie_observation.html      # Formulaire de saisie
└── ...
```

---

## Points d'attention

### ⚠️ Validation des contraintes

Les formulaires **doivent** valider les contraintes **avant** la sauvegarde en base :
- Paires jour/mois (ResumeObservation)
- Compteurs cohérents (œufs pondus ≥ œufs éclos ≥ poussins)

**Pourquoi** : Éviter les erreurs `IntegrityError` en base de données.

### ⚠️ Mise à jour du pourcentage de complétion

Après modification d'une fiche via un formulaire, **toujours** recalculer le pourcentage :

```python
def corriger_fiche(request, num_fiche):
    fiche = get_object_or_404(FicheObservation, num_fiche=num_fiche)

    if request.method == 'POST':
        form = FicheObservationForm(request.POST, instance=fiche)
        if form.is_valid():
            form.save()

            # ✅ Recalculer le pourcentage
            fiche.mettre_a_jour_etat_correction()

            return redirect('fiche_observation', num_fiche=num_fiche)
```

### ⚠️ Permissions

Vérifier les permissions avant modification :
- L'utilisateur peut-il modifier cette fiche ?
- La fiche est-elle déjà validée ?

---

## TODO : À compléter

Cette documentation sera complétée progressivement avec :
- Liste détaillée des formulaires
- Liste détaillée des templates
- Logique métier des vues principales
- Gestion des permissions

---

## Voir aussi

- **[Modèles](models.md)** - Structure des données
- **[Pièges à éviter](gotchas.md)** - Erreurs courantes

---

*Dernière mise à jour : 2025-12-27*
