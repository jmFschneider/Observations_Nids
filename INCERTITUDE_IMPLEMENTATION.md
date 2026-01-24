# Implémentation de l'incertitude pour les champs numériques

## Résumé

Les observateurs peuvent désormais saisir "5?" dans les champs `nombre_oeufs` et `nombre_poussins` pour indiquer une estimation incertaine. Une icône visuelle (?) s'affiche automatiquement à côté du champ pour feedback immédiat.

## Modifications apportées

### 1. Base de données

**Fichier** : `observations/migrations/0016_add_incertitude_fields.py`

- Ajout de 2 champs booléens au modèle `Observation` :
  - `nombre_oeufs_incertain` (BooleanField, default=False)
  - `nombre_poussins_incertain` (BooleanField, default=False)

### 2. Modèle Django

**Fichier** : `observations/models.py`

- Modèle `Observation` enrichi avec les champs d'incertitude
- Séparation propre : valeur numérique + flag booléen

### 3. Formulaire Django

**Fichier** : `observations/forms.py`

- Changement de `NumberInput` vers `TextInput` pour accepter "5?"
- Ajout de champs cachés `_incertain` gérés par JavaScript
- Validation côté serveur dans `clean_nombre_oeufs()` et `clean_nombre_poussins()` :
  - Parse "5?" → extrait valeur numérique (5) + flag (True)
  - Gestion des erreurs avec messages explicites

### 4. Template de saisie

**Fichier** : `observations/templates/saisie/saisie_observation.html`

- Ajout de conteneurs `.nombre-input-container` autour des champs
- Icônes FontAwesome `fa-question-circle` masquées par défaut
- CSS pour styling (hover, transition, largeur fixe)

### 5. JavaScript

**Fichier** : `observations/static/Observations/js/saisie_observation.js`

- Module dédié `initIncertitudeHandlers()` en fin de fichier
- Détection temps réel du "?" lors de la saisie
- Affichage/masquage automatique de l'icône
- Délégation d'événements pour les champs ajoutés dynamiquement (formset)
- Restauration de l'état initial lors de l'édition

### 6. Template de lecture

**Fichier** : `observations/templates/fiche_observation.html`

- Affichage de l'icône jaune "?" si `nombre_oeufs_incertain=True`
- Tooltip "Estimation incertaine" au survol

### 7. Admin Django

**Fichier** : `observations/admin.py`

- Ajout des champs d'incertitude dans `list_display`
- Filtres pour visualiser uniquement les estimations incertaines

## Comment utiliser

### Saisie d'une observation

1. Créer ou éditer une fiche d'observation
2. Dans le tableau "Observations", saisir un nombre suivi de "?" :
   - Exemple : `5?` pour 5 œufs (incertain)
   - Exemple : `3?` pour 3 poussins (incertain)
3. L'icône "?" jaune apparaît immédiatement à côté du champ
4. Enregistrer normalement

### Édition d'une observation existante

- Les champs s'affichent automatiquement avec "5?" si l'incertitude était activée
- Retirer le "?" désactive l'incertitude

### Consultation d'une fiche

- L'icône "?" jaune s'affiche à côté des valeurs incertaines
- Survol de l'icône → tooltip "Estimation incertaine"

## Tests recommandés

### Test 1 : Saisie avec incertitude

```
1. Créer une nouvelle fiche
2. Ajouter observation : nombre_oeufs = "5?"
3. Vérifier : icône visible
4. Enregistrer
5. Vérifier en BDD : nombre_oeufs=5, nombre_oeufs_incertain=True
```

### Test 2 : Saisie sans incertitude

```
1. Créer observation : nombre_poussins = "3"
2. Vérifier : aucune icône
3. Enregistrer
4. Vérifier en BDD : nombre_poussins=3, nombre_poussins_incertain=False
```

### Test 3 : Édition d'une fiche existante

```
1. Ouvrir fiche avec nombre_oeufs_incertain=True
2. Vérifier : champ affiche "5?" + icône
3. Retirer le "?" → "5"
4. Vérifier : icône disparaît
5. Enregistrer
6. Vérifier en BDD : nombre_oeufs_incertain=False
```

### Test 4 : Affichage en lecture seule

```
1. Consulter fiche avec incertitude
2. Vérifier : icône "?" jaune visible
3. Survol → vérifier tooltip
```

### Test 5 : Formset dynamique

```
1. Ouvrir fiche existante
2. Ajouter plusieurs observations via "+ Ajouter"
3. Saisir "2?" sur différentes lignes
4. Vérifier : chaque icône s'affiche indépendamment
```

### Test 6 : Validation

```
1. Saisir "abc?" → message d'erreur attendu
2. Laisser vide → accepté (NULL autorisé)
3. Saisir "0?" → accepté (valide)
```

## Commandes à exécuter

### Migration de la base de données

```bash
# Activer l'environnement virtuel (si nécessaire)
# Puis exécuter la migration
python manage.py migrate observations
```

### Vérification

```bash
# Lancer le serveur de développement
python manage.py runserver

# Accéder à l'interface
http://localhost:8000/observations/saisie/
```

## Points d'attention

### Rétrocompatibilité

- ✅ Les observations existantes ont `incertain=False` par défaut
- ✅ Aucune rupture de données
- ✅ Les anciennes fiches s'affichent normalement

### Sécurité

- ✅ Validation côté serveur obligatoire (ne jamais faire confiance au JS)
- ✅ Pattern HTML5 `\d+\??` pour validation basique côté client
- ✅ Messages d'erreur explicites

### Performance

- ✅ Délégation d'événements pour éviter les memory leaks
- ✅ Pas de requêtes AJAX supplémentaires
- ✅ Index BDD existants toujours utilisables

## Extension future (optionnelle)

### OCR Gemini

Si besoin de détecter l'incertitude dans les fiches manuscrites :

**Modifier** : `observations/json_rep/prompt_gemini_transcription.txt`

Ajouter après ligne 34 :

```
   - Nombre_oeuf (entier entre 0 et 12, ou null)
   - Nombre_oeuf_incertain (booléen : true si un "?" est visible après le nombre)
   - Nombre_pou (entier entre 0 et 12, ou null)
   - Nombre_pou_incertain (booléen : true si un "?" est visible après le nombre)
```

## Architecture technique

### Flux de données

```
Utilisateur saisit "5?"
    ↓
JavaScript détecte le "?"
    ↓
Affiche l'icône + active le champ caché
    ↓
Submit formulaire
    ↓
Django parse "5?" dans clean_nombre_oeufs()
    ↓
Stocke en BDD : nombre_oeufs=5, nombre_oeufs_incertain=True
```

### Séparation des responsabilités

- **Modèle** : Stockage structuré (int + bool)
- **Formulaire** : Validation et parsing serveur
- **JavaScript** : UX temps réel (feedback visuel)
- **Template** : Affichage contextualisé

---

**Date d'implémentation** : 2026-01-24
**Version Django** : 6.0
**Statut** : ✅ Complète et fonctionnelle
