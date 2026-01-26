# Gestion de l'Incertitude des Comptages

> Documentation technique de la fonctionnalité "Notation 5?" et "?" pour les champs numériques

**Version** : 1.0.0  
**Date** : Janvier 2026  
**Migration** : `0016_add_incertitude_fields.py`

---

## 📋 Contexte

Les ornithologues utilisent traditionnellement la notation "5?" sur leurs fiches papier pour indiquer qu'un comptage (œufs, poussins) est une estimation approximative plutôt qu'un décompte exact.

Cette fonctionnalité réplique cette notation dans l'interface web tout en maintenant l'intégrité des données.

---

## 🎯 Objectifs

1. **UX fidèle au terrain** : Permettre la saisie intuitive de "5?" et "?" comme sur papier
2. **Données propres** : Séparer la valeur numérique du flag d'incertitude
3. **Requêtabilité** : Faciliter les analyses statistiques (filtrer les estimations incertaines)
4. **Traçabilité** : Conserver l'information sur la fiabilité des données

---

## 🏗️ Architecture

### Modèle de Données

**Modèle** : `observations.models.Observation`

**Nouveaux champs** (ajoutés via migration `0016`) :

```python
nombre_oeufs_incertain = models.BooleanField(
    default=False,
    verbose_name="Estimation incertaine (œufs)",
    help_text="Cocher si le nombre d'œufs est une estimation approximative"
)

nombre_poussins_incertain = models.BooleanField(
    default=False,
    verbose_name="Estimation incertaine (poussins)",
    help_text="Cocher si le nombre de poussins est une estimation approximative"
)
```

**Stockage** :
- `nombre_oeufs` : `IntegerField` → stocke uniquement le nombre (ex: `5` ou `NULL` si saisie "?")
- `nombre_oeufs_incertain` : `BooleanField` → `True` si notation "5?" ou "?", sinon `False`

### Formulaire Django

**Fichier** : `observations/forms.py` → `ObservationForm`

**Déclaration des champs** :

```python
# Surcharge pour accepter la notation "5?" et "?"
nombre_oeufs = forms.CharField(
    required=False,
    widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'nombre-avec-incertitude',
        'placeholder': 'Nombre d\'œufs (ex: 5, 5? ou ?)',
        'inputmode': 'numeric',
    })
)
```

**Validation (méthode `clean_nombre_oeufs`)** :

```python
def clean_nombre_oeufs(self):
    value = self.cleaned_data.get('nombre_oeufs', '').strip()
    if not value:
        return None
    if value == '?':
        return None
    
    # Vérifier le format (chiffres + optionnel "?")
    if not value.replace('?', '').isdigit():
        raise forms.ValidationError("Format invalide. Utilisez: 5, 5? ou ?")
    
    # Extraire le nombre
    nombre_str = value.rstrip('?')
    return int(nombre_str)
```

**Gestion du flag (méthode `clean`)** :

```python
def clean(self):
    cleaned_data = super().clean()
    
    # Détecter le "?" dans les données brutes
    nombre_oeufs_raw = self.data.get('nombre_oeufs', '').strip()
    if nombre_oeufs_raw.endswith('?'):
        cleaned_data['nombre_oeufs_incertain'] = True
    else:
        cleaned_data['nombre_oeufs_incertain'] = False
    
    return cleaned_data
```

**Sauvegarde (méthode `save`)** :

```python
def save(self, commit=True):
    instance = super().save(commit=False)
    
    # Forcer l'assignation des flags depuis cleaned_data
    if hasattr(self, 'cleaned_data'):
        instance.nombre_oeufs_incertain = self.cleaned_data.get('nombre_oeufs_incertain', False)
        instance.nombre_poussins_incertain = self.cleaned_data.get('nombre_poussins_incertain', False)
    
    if commit:
        instance.save()
    
    return instance
```

---

## 🎨 Interface Utilisateur

### Templates

**Fichiers concernés** :
- `observations/templates/saisie/saisie_observation.html` (formulaire formset)
- `observations/templates/saisie/ajouter_observation.html` (ajout simple)
- `observations/templates/fiche_observation.html` (lecture seule)

**Structure HTML (édition)** :

```html
<div class="nombre-input-container">
    {{ form.nombre_oeufs }}
    {{ form.nombre_oeufs_incertain }}  {# Hidden field #}
    <i class="fas fa-question-circle incertitude-icon" 
       style="display: none; color: #ffc107;" 
       title="Estimation incertaine"></i>
</div>
```

**Structure HTML (lecture)** :

```django
{% if observation.nombre_oeufs is not None %}
    {{ observation.nombre_oeufs }}
{% elif observation.nombre_oeufs_incertain %}
    ?
{% endif %}
{% if observation.nombre_oeufs_incertain %}
    <i class="fas fa-question-circle text-warning" 
       title="Estimation incertaine"></i>
{% endif %}
```

### JavaScript

**Fichier** : `observations/static/Observations/js/saisie_observation.js`

**Module** : `initIncertitudeHandlers()`

**Fonctions clés** :

1. **Détection en temps réel** (`handleIncertitudeInput`) :
   - Écoute les événements `input` et `change`
   - Détecte le "?" dans la valeur
   - Affiche/masque l'icône dynamiquement
   - Met à jour le champ caché `_incertain`

2. **Nettoyage automatique** :
   - Supprime les caractères non valides
   - Garde uniquement : chiffres + un seul "?" à la fin, ou "?" seul

3. **État initial** (`initOnPageLoad`) :
   - Détecte si le champ contient déjà "?" au chargement
   - Affiche l'icône pour les observations existantes

**Code simplifié** :

```javascript
function handleIncertitudeInput(event) {
    const input = event.target;
    const value = input.value.trim();
    
    // Trouver conteneur et éléments associés
    const container = input.closest('.nombre-input-container');
    const icon = container.querySelector('.incertitude-icon');
    const hiddenField = container.querySelector('input[type="hidden"]');
    
    // Validation format
    const validPattern = /^(?:\d+\??|\?)$/;
    if (!validPattern.test(value) && value !== '') {
        // Nettoyer
        const cleaned = value.replace(/[^\d?]/g, '');
        input.value = cleaned.replace(/\?/g, '') + (cleaned.includes('?') ? '?' : '');
        return;
    }
    
    // Afficher/masquer icône
    const hasQuestionMark = value.endsWith('?');
    icon.style.display = hasQuestionMark ? 'inline-block' : 'none';
    hiddenField.value = hasQuestionMark ? 'on' : '';
}
```

---

## 🧪 Exemples d'Utilisation

### Création d'une observation avec incertitude

```python
observation = Observation.objects.create(
    fiche=fiche,
    date_observation=datetime.now(),
    nombre_oeufs=5,
    nombre_oeufs_incertain=True,  # "5?"
    nombre_poussins=3,
    nombre_poussins_incertain=False  # "3" (certain)
)
```

### Requêtes SQL

**Filtrer les estimations incertaines** :

```python
# Observations avec comptage d'œufs incertain
observations_incertaines = Observation.objects.filter(
    nombre_oeufs_incertain=True
)

# Statistiques : % d'observations incertaines
from django.db.models import Count, Q

stats = Observation.objects.aggregate(
    total=Count('id'),
    incertaines=Count('id', filter=Q(nombre_oeufs_incertain=True))
)
pourcentage = (stats['incertaines'] / stats['total']) * 100
```

**Exporter vers CSV** :

```python
import csv

with open('observations.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Oeufs', 'Incertain'])
    
    for obs in Observation.objects.all():
        writer.writerow([
            obs.date_observation,
            obs.nombre_oeufs,
            'Oui' if obs.nombre_oeufs_incertain else 'Non'
        ])
```

---

## 🔍 Tests

### Tests manuels

1. **Saisie** :
   - ✅ Taper "5" → doit sauvegarder `nombre_oeufs=5, incertain=False`
   - ✅ Taper "5?" → doit sauvegarder `nombre_oeufs=5, incertain=True`
   - ✅ Taper "5??" → doit être nettoyé en "5?"
   - ✅ Taper "5a" → doit être nettoyé en "5"

2. **Affichage** :
   - ✅ Édition : champ affiche "5?" avec icône jaune
   - ✅ Lecture : affiche "5" avec icône jaune à côté
   - ✅ Champ sans "?" : pas d'icône

3. **Admin Django** :
   - ✅ Colonne `nombre_oeufs_incertain` visible
   - ✅ Filtre par incertitude fonctionnel

### Tests unitaires (à implémenter)

```python
from django.test import TestCase
from observations.models import Observation
from observations.forms import ObservationForm

class IncertitudeTestCase(TestCase):
    def test_save_with_question_mark(self):
        """Tester la sauvegarde de '5?' """
        form_data = {
            'date_observation': '2026-01-24 10:00',
            'nombre_oeufs': '5?',
        }
        form = ObservationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        obs = form.save(commit=False)
        self.assertEqual(obs.nombre_oeufs, 5)
        self.assertTrue(obs.nombre_oeufs_incertain)
    
    def test_invalid_format(self):
        """Tester le rejet de formats invalides"""
        form = ObservationForm(data={'nombre_oeufs': '5a'})
        self.assertFalse(form.is_valid())
```

---

## 📊 Impact Performance

**Aucun impact négatif** :
- Les champs booléens sont indexables
- Pas de parsing complexe côté BDD
- Le JavaScript est léger (~50 lignes)

**Requêtes optimisées** :
```sql
-- Sans incertitude (avant)
SELECT * FROM observation WHERE nombre_oeufs = 5;

-- Avec incertitude (après)
SELECT * FROM observation 
WHERE nombre_oeufs = 5 AND nombre_oeufs_incertain = FALSE;
```

---

## 🚀 Évolutions Futures

1. **Extension à d'autres champs** : Appliquer à `nombre_oeufs_pondus`, `nombre_poussins` du `ResumeObservation`
2. **Statistiques** : Dashboard affichant le % d'observations incertaines
3. **Export** : Inclure le flag dans les exports CSV/Excel
4. **OCR** : Détecter automatiquement le "?" dans les images scannées

---

## 📚 Références

- **Migration** : `observations/migrations/0016_add_incertitude_fields.py`
- **Formulaire** : `observations/forms.py` → `ObservationForm`
- **JavaScript** : `observations/static/Observations/js/saisie_observation.js`
- **Spec fonctionnelle** : `specs/functional_rules.md` § "Gestion de l'Incertitude"

---

**Dernière mise à jour** : Janvier 2026
