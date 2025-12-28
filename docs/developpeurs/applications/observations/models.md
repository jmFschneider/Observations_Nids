# Observations - Modèles de données

Ce fichier documente les modèles de l'application **observations**, qui est le **cœur métier** du projet.

**Fichier source** : `observations/models.py`

---

## Architecture des modèles

### Relations 1:1 (créées automatiquement)

Lors de la création d'une `FicheObservation`, **5 objets liés sont créés automatiquement** :

```
FicheObservation (1)
    ├── Localisation (1:1)
    ├── Nid (1:1)
    ├── ResumeObservation (1:1)
    ├── CausesEchec (1:1)
    └── EtatCorrection (1:1)
```

### Relations 1:N (ajoutées manuellement)

```
FicheObservation (1)
    ├── Observation (N) - observations ponctuelles datées
    └── Remarque (N) - remarques textuelles
```

---

## Modèle : FicheObservation

**Fichier** : `observations/models.py:14-111`

### Responsabilité

Le modèle **pivot central** de toute l'application. Représente une fiche d'observation de nidification pour une espèce et une année données.

### Champs principaux

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `num_fiche` | AutoField (PK) | Numéro unique de la fiche | Auto-incrémenté |
| `date_creation` | DateTimeField | Date/heure de création | Auto (auto_now_add) |
| `observateur` | ForeignKey | Utilisateur créateur | → `Utilisateur`, **CASCADE**, indexé |
| `espece` | ForeignKey | Espèce observée | → `Espece`, **PROTECT** |
| `annee` | IntegerField | Année d'observation | Année (YYYY) |
| `numero_personnel` | IntegerField | Numéro attribué par l'observateur | Nullable, optionnel |
| `chemin_image` | CharField(255) | Chemin vers l'image scannée | Optionnel |
| `chemin_json` | CharField(255) | Chemin vers les données OCR JSON | Optionnel |
| `transcription` | BooleanField | Issue d'une transcription OCR | Défaut: False |

### Relations

#### ForeignKey

```python
observateur = models.ForeignKey(
    Utilisateur,
    on_delete=models.CASCADE,  # ⚠️ Si utilisateur supprimé → fiches supprimées
    related_name="fiches",
    db_index=True
)

espece = models.ForeignKey(
    Espece,
    on_delete=models.PROTECT,  # ⚠️ Empêche suppression d'espèce avec observations
    related_name="observations"
)
```

**Différence CASCADE vs PROTECT** :
- **CASCADE** (observateur) : Acceptable car si un utilisateur est supprimé, on veut supprimer ses données
- **PROTECT** (espece) : Empêche la suppression accidentelle d'une espèce qui a des observations

#### Reverse relations (1:1)

```python
# Accès aux objets liés créés automatiquement
fiche.localisation  # → Localisation
fiche.nid           # → Nid
fiche.resume        # → ResumeObservation
fiche.causes_echec  # → CausesEchec
fiche.etat_correction  # → EtatCorrection
```

#### Reverse relations (1:N)

```python
# Collections
fiche.observations.all()  # → QuerySet[Observation]
fiche.remarques.all()     # → QuerySet[Remarque]
```

### Index

```python
class Meta:
    indexes = [
        models.Index(fields=['observateur', 'date_creation']),
    ]
```

**Optimisation** : Requêtes fréquentes filtrées par observateur et triées par date.

### Méthode : `save()`

**Fichier** : `observations/models.py:42-97`

```python
@transaction.atomic
def save(self, *args, **kwargs):
    is_new = self.pk is None

    super().save(*args, **kwargs)

    # Si c'est une nouvelle fiche, créer automatiquement les objets liés
    if is_new:
        Localisation.objects.get_or_create(fiche=self, defaults={...})
        Nid.objects.get_or_create(fiche=self, defaults={...})
        ResumeObservation.objects.get_or_create(fiche=self, defaults={...})
        CausesEchec.objects.get_or_create(fiche=self, defaults={...})
        EtatCorrection.objects.get_or_create(fiche=self, defaults={...})
```

**Points clés** :
- ✅ Utilise `@transaction.atomic` : Tout ou rien
- ✅ Utilise `get_or_create` : Évite les doublons si save() appelé plusieurs fois
- ⚠️ **Critique** : Ne jamais modifier sans tests ([voir gotchas](gotchas.md))

### Méthode : `mettre_a_jour_etat_correction()`

**Fichier** : `observations/models.py:99-110`

```python
def mettre_a_jour_etat_correction(self):
    """Met à jour l'état de correction de la fiche"""
    etat_correction, created = EtatCorrection.objects.get_or_create(
        fiche=self,
        defaults={'statut': 'nouveau', 'pourcentage_completion': 0}
    )
    etat_correction.calculer_pourcentage_completion()
    etat_correction.save(skip_auto_calculation=False)
    return etat_correction
```

**Usage** : Recalculer le pourcentage de complétion après modification des données.

### Exemple d'utilisation

```python
# Créer une fiche
fiche = FicheObservation.objects.create(
    observateur=utilisateur,
    espece=espece,
    annee=2025
)

# Les objets liés sont créés automatiquement
assert fiche.localisation is not None
assert fiche.nid is not None
assert fiche.resume is not None
assert fiche.causes_echec is not None
assert fiche.etat_correction is not None

# Accès aux données
fiche.localisation.commune = "Grenoble"
fiche.localisation.save()

fiche.nid.hauteur_nid = 150
fiche.nid.save()
```

---

## Modèle : Nid

**Fichier** : `observations/models.py:113-129`

### Responsabilité

Caractéristiques physiques du nid observé (1:1 avec FicheObservation).

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `fiche` | OneToOneField | Fiche parente | → `FicheObservation`, CASCADE |
| `nid_prec_t_meme_couple` | BooleanField | Nid précédent du même couple | Défaut: False |
| `fiche_precedente` | ForeignKey | Référence vers fiche précédente | → `FicheObservation`, SET_NULL, nullable |
| `hauteur_nid` | IntegerField | Hauteur du nid (cm) | Nullable |
| `hauteur_couvert` | IntegerField | Hauteur du couvert végétal (cm) | Nullable |
| `details_nid` | TextField | Description libre | Défaut: '' |

### Points d'attention

**Nullable vs 0** :
- `NULL` = Non observé / Non renseigné
- `0` = Valeur observée de 0 (nid au sol par exemple)

### Exemple

```python
nid = fiche.nid
nid.hauteur_nid = 250  # 2,5 m
nid.hauteur_couvert = 1500  # 15 m
nid.details_nid = "Nid situé dans un chêne, à la fourche de deux branches"
nid.save()

# Lien vers fiche précédente
if nid.nid_prec_t_meme_couple:
    fiche_precedente = FicheObservation.objects.get(num_fiche=42)
    nid.fiche_precedente = fiche_precedente
    nid.save()
```

---

## Modèle : Observation

**Fichier** : `observations/models.py:132-169`

### Responsabilité

Observation ponctuelle datée au sein d'une fiche. Une fiche peut contenir **plusieurs observations** (visites successives du nid).

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `fiche` | ForeignKey | Fiche parente | → `FicheObservation`, CASCADE |
| `date_observation` | DateTimeField | Date/heure de l'observation | **Obligatoire**, indexé |
| `heure_connue` | BooleanField | Indique si l'heure est connue | Défaut: True |
| `nombre_oeufs` | IntegerField | Nombre d'œufs observés | ≥ 0, nullable |
| `nombre_poussins` | IntegerField | Nombre de poussins observés | ≥ 0, nullable |
| `observations` | TextField | Notes libres | Défaut: '' |

### Tri

```python
class Meta:
    ordering = ['date_observation']  # Tri chronologique
```

### Affichage (`__str__()`)

```python
def __str__(self):
    if self.heure_connue:
        date_str = self.date_observation.strftime('%d/%m/%Y %H:%M')
    else:
        date_str = self.date_observation.strftime('%d/%m/%Y')
    return f"Observation du {date_str} (Fiche {self.fiche.num_fiche})"
```

**Résultat** :
- Si heure connue : `"Observation du 15/04/2025 10:30 (Fiche 123)"`
- Si heure inconnue : `"Observation du 15/04/2025 (Fiche 123)"`

### Exemple d'utilisation

```python
# 3 visites successives d'un même nid
fiche = FicheObservation.objects.get(num_fiche=123)

# Visite 1 : Début de ponte
Observation.objects.create(
    fiche=fiche,
    date_observation=datetime(2025, 4, 15, 10, 30),
    heure_connue=True,
    nombre_oeufs=2,
    nombre_poussins=0,
    observations="Nid en construction, 2 œufs"
)

# Visite 2 : Ponte complète
Observation.objects.create(
    fiche=fiche,
    date_observation=datetime(2025, 4, 25, 14, 0),
    heure_connue=True,
    nombre_oeufs=4,
    nombre_poussins=0,
    observations="4 œufs, adulte couve"
)

# Visite 3 : Éclosion
Observation.objects.create(
    fiche=fiche,
    date_observation=datetime(2025, 5, 10),  # Heure inconnue
    heure_connue=False,
    nombre_oeufs=1,
    nombre_poussins=3,
    observations="3 poussins éclos, 1 œuf non éclos"
)

# Récupérer toutes les observations, triées par date
observations = fiche.observations.all()
for obs in observations:
    print(obs)
```

---

## Modèle : ResumeObservation

**Fichier** : `observations/models.py:172-273`

### Responsabilité

Données de synthèse sur la nidification : dates partielles (jour/mois) et compteurs (1:1 avec FicheObservation).

### Champs : Dates partielles

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `premier_oeuf_pondu_jour` | PositiveSmallIntegerField | Jour (1-31) | Nullable, 1-31 |
| `premier_oeuf_pondu_mois` | PositiveSmallIntegerField | Mois (1-12) | Nullable, 1-12 |
| `premier_poussin_eclos_jour` | PositiveSmallIntegerField | Jour (1-31) | Nullable, 1-31 |
| `premier_poussin_eclos_mois` | PositiveSmallIntegerField | Mois (1-12) | Nullable, 1-12 |
| `premier_poussin_volant_jour` | PositiveSmallIntegerField | Jour (1-31) | Nullable, 1-31 |
| `premier_poussin_volant_mois` | PositiveSmallIntegerField | Mois (1-12) | Nullable, 1-12 |

### Champs : Compteurs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `nombre_oeufs_pondus` | PositiveSmallIntegerField | Nombre total d'œufs pondus | Nullable |
| `nombre_oeufs_eclos` | PositiveSmallIntegerField | Nombre d'œufs éclos | Nullable |
| `nombre_oeufs_non_eclos` | PositiveSmallIntegerField | Nombre d'œufs non éclos | Nullable |
| `nombre_poussins` | PositiveSmallIntegerField | Nombre de poussins | Nullable |

**Convention NULL** :
- `NULL` = Non observé / Non renseigné
- `0` = Valeur observée de 0 (ex: aucun œuf pondu)

### Contraintes de cohérence

**1. Paires jour/mois** : Soit les deux NULL, soit les deux renseignés

```python
models.CheckConstraint(
    name="resume_premier_oeuf_pondu_jour_mois_both_or_none",
    condition=(
        (Q(premier_oeuf_pondu_jour__isnull=True) & Q(premier_oeuf_pondu_mois__isnull=True))
        | (Q(premier_oeuf_pondu_jour__isnull=False) & Q(premier_oeuf_pondu_mois__isnull=False))
    )
)
```

**Résultat** :
- ✅ `jour=15, mois=4` (OK)
- ✅ `jour=NULL, mois=NULL` (OK)
- ❌ `jour=15, mois=NULL` (ERREUR)

**2. Compteurs cohérents**

```python
# nombre_oeufs_eclos ≤ nombre_oeufs_pondus
models.CheckConstraint(
    name="resume_eclos_le_pondus",
    condition=(
        Q(nombre_oeufs_eclos__isnull=True)
        | Q(nombre_oeufs_pondus__isnull=True)
        | Q(nombre_oeufs_eclos__lte=models.F("nombre_oeufs_pondus"))
    )
)

# nombre_oeufs_non_eclos ≤ nombre_oeufs_pondus
models.CheckConstraint(
    name="resume_non_eclos_le_pondus",
    condition=(...)
)

# nombre_poussins ≤ nombre_oeufs_eclos
models.CheckConstraint(
    name="resume_poussins_le_eclos",
    condition=(...)
)
```

**Résultat** :
- ✅ `pondus=4, eclos=3, non_eclos=1, poussins=2` (OK)
- ❌ `pondus=4, eclos=5` (ERREUR : éclos > pondus)
- ❌ `eclos=3, poussins=4` (ERREUR : poussins > éclos)

### Exemple d'utilisation

```python
resume = fiche.resume

# Dates partielles
resume.premier_oeuf_pondu_jour = 15
resume.premier_oeuf_pondu_mois = 4  # 15 avril

resume.premier_poussin_eclos_jour = 10
resume.premier_poussin_eclos_mois = 5  # 10 mai

# Compteurs
resume.nombre_oeufs_pondus = 4
resume.nombre_oeufs_eclos = 3
resume.nombre_oeufs_non_eclos = 1
resume.nombre_poussins = 2

resume.save()  # Validation automatique des contraintes
```

---

## Modèle : CausesEchec

**Fichier** : `observations/models.py:276-283`

### Responsabilité

Documente les causes d'échec de la nidification (prédation, conditions météo, abandon, etc.).

### Champs

| Champ | Type | Description | Défaut |
|-------|------|-------------|--------|
| `fiche` | OneToOneField | Fiche parente | → `FicheObservation`, CASCADE |
| `description` | TextField | Description des causes | '' |

### Exemple

```python
causes = fiche.causes_echec
causes.description = "Prédation par une pie. Nid détruit le 12/05/2025."
causes.save()
```

---

## Modèle : Remarque

**Fichier** : `observations/models.py:286-296`

### Responsabilité

Remarques textuelles libres associées à une fiche (1:N).

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `fiche` | ForeignKey | Fiche parente | → `FicheObservation`, CASCADE |
| `remarque` | CharField | Texte de la remarque | Max 200 caractères |
| `date_remarque` | DateTimeField | Date/heure de la remarque | Auto (auto_now_add) |

### Exemple

```python
# Ajouter plusieurs remarques
Remarque.objects.create(
    fiche=fiche,
    remarque="Mâle portant une bague bleue"
)

Remarque.objects.create(
    fiche=fiche,
    remarque="Nid situé à proximité d'un chemin forestier"
)

# Récupérer toutes les remarques, triées par date
remarques = fiche.remarques.all().order_by('-date_remarque')
for rem in remarques:
    print(f"{rem.date_remarque}: {rem.remarque}")
```

---

## Modèle : EtatCorrection

**Fichier** : `observations/models.py:299-467`

### Responsabilité

Gère le workflow de correction/validation d'une fiche, calcule automatiquement le pourcentage de complétion, et **gère le verrouillage pour empêcher les modifications concurrentes**.

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `fiche` | OneToOneField | Fiche parente | → `FicheObservation`, CASCADE |
| `statut` | CharField(20) | Statut de la fiche | Choix: STATUTS_CHOICES |
| `pourcentage_completion` | IntegerField | Pourcentage de complétion (0-100%) | 0-100, auto-calculé |
| `date_derniere_modification` | DateTimeField | Date de dernière modification | Auto (auto_now) |
| `validee_par` | ForeignKey | Valideur de la fiche | → `Utilisateur`, SET_NULL, nullable |
| `date_validation` | DateTimeField | Date de validation | Nullable |
| `en_correction_par` | ForeignKey | 🔒 Reviewer qui a verrouillé la fiche | → `Utilisateur`, SET_NULL, nullable |
| `date_debut_correction` | DateTimeField | 🔒 Date de début du verrouillage | Nullable |

### Statuts

```python
STATUTS_CHOICES = [
    ('nouveau', 'Nouvelle fiche'),
    ('en_edition', "En cours d'édition"),
    ('en_cours', 'En cours de correction'),
    ('valide', 'Validée'),
]
```

**Workflow** :
```
nouveau → en_edition → en_cours → valide
```

### Méthode : `calculer_pourcentage_completion()`

**Fichier** : `observations/models.py:337-396`

Calcule automatiquement le pourcentage de complétion basé sur **8 critères** :

| # | Critère | Point |
|---|---------|-------|
| 1 | Observateur renseigné | 1 |
| 2 | Espèce renseignée | 1 |
| 3 | Localisation complète (commune + département ≠ '00') | 1 |
| 4 | Au moins une observation avec date | 1 |
| 5 | Résumé avec données d'œufs (nombre_oeufs_pondus > 0) | 1 |
| 6 | Détails du nid renseignés | 1 |
| 7 | Hauteur du nid renseignée (> 0) | 1 |
| 8 | Image associée (chemin_image) | 1 |

**Calcul** : `pourcentage = (score / 8) * 100`

**Mise à jour automatique du statut** :
```python
if pourcentage > 0 and self.statut == 'nouveau':
    self.statut = 'en_edition'
```

### Méthode : `save()`

```python
def save(self, *args, **kwargs):
    # Calculer automatiquement le pourcentage avant la sauvegarde
    if not kwargs.pop('skip_auto_calculation', False):
        self.calculer_pourcentage_completion()
    super().save(*args, **kwargs)
```

**skip_auto_calculation** : Permet de désactiver le calcul automatique si besoin.

### Méthodes de verrouillage 🔒

**Fichier** : `observations/models.py:423-467`

#### `est_verrouillee()` → bool

Vérifie si la fiche est actuellement verrouillée pour correction. Gère également le **déblocage automatique** après expiration du délai configuré.

```python
def est_verrouillee(self):
    """
    Retourne True si la fiche est verrouillée.
    Gère le déblocage automatique si la durée configurée est dépassée.
    """
    if not self.en_correction_par or not self.date_debut_correction:
        return False

    # Vérifier expiration via ConfigurationVerrouillage
    config = ConfigurationVerrouillage.get_instance()
    if config.duree_verrouillage_jours > 0:
        duree_max = timedelta(days=config.duree_verrouillage_jours)
        temps_ecoule = timezone.now() - self.date_debut_correction

        if temps_ecoule > duree_max:
            self.liberer_verrou()  # Déblocage automatique
            return False

    return True
```

**Comportement** :
- ✅ Retourne `False` si aucun verrou actif
- ✅ Déblocage automatique si durée expirée (1, 2, 5, 10 jours selon configuration)
- ✅ Si `duree_verrouillage_jours = 0` : verrouillage permanent (jamais de déblocage auto)

#### `liberer_verrou()`

Libère manuellement le verrou de correction.

```python
def liberer_verrou(self):
    """Libère le verrou de correction de la fiche"""
    self.en_correction_par = None
    self.date_debut_correction = None
    self.save(update_fields=['en_correction_par', 'date_debut_correction'])
```

**Utilisations** :
- Déblocage automatique (appelé par `est_verrouillee()`)
- Déblocage manuel par le reviewer ou un administrateur
- Action groupée dans l'admin Django

#### `verrouiller_pour(reviewer)`

Verrouille la fiche pour un reviewer spécifique.

```python
def verrouiller_pour(self, reviewer):
    """
    Verrouille la fiche pour un reviewer.
    Appelé lors de la première sauvegarde en statut 'en_cours'.
    """
    if not self.en_correction_par:
        self.en_correction_par = reviewer
        self.date_debut_correction = timezone.now()
        self.save(update_fields=['en_correction_par', 'date_debut_correction'])
```

**Comportement** :
- ✅ Verrouille **uniquement** si pas déjà verrouillée (idempotent)
- ✅ Enregistre le reviewer et l'horodatage

### Workflow de verrouillage

```mermaid
graph TD
    A[Fiche en statut 'en_cours'] --> B{Est verrouillée ?}
    B -->|Non| C[Reviewer A édite et sauvegarde]
    C --> D[verrouiller_pour(Reviewer A)]
    D --> E[Fiche verrouillée pour A]

    B -->|Oui| F{Qui tente d'accéder ?}
    F -->|Reviewer A| G[Peut modifier]
    F -->|Reviewer B| H[Redirection lecture seule]
    F -->|Admin| I{Veut modifier ?}
    I -->|Oui| J[Doit d'abord débloquer]
    I -->|Non| H

    E --> K{Durée expirée ?}
    K -->|Oui| L[Déblocage auto via est_verrouillee]
    K -->|Non| M[Reste verrouillée]

    E --> N[Déblocage manuel]
    N --> O[liberer_verrou]
```

### Exemple d'utilisation

```python
# Récupérer l'état de correction
etat = fiche.etat_correction

# Vérifier si verrouillée
if etat.est_verrouillee():
    print(f"Verrouillée par {etat.en_correction_par.username}")
    print(f"Depuis le {etat.date_debut_correction}")
else:
    print("Fiche disponible")

# Verrouiller pour un reviewer
etat.verrouiller_pour(request.user)

# Libérer le verrou
etat.liberer_verrou()

# Workflow classique
etat = fiche.etat_correction
print(f"Complétion: {etat.pourcentage_completion}%")
print(f"Statut: {etat.get_statut_display()}")

# Changer le statut manuellement
etat.statut = 'en_cours'
etat.save()

# Valider la fiche (libère automatiquement le verrou)
etat.statut = 'valide'
etat.validee_par = valideur
etat.date_validation = timezone.now()
etat.save()
```

---

## Modèle : ConfigurationVerrouillage

**Fichier** : `observations/models.py:470-509`

### Responsabilité

**Singleton** qui configure la durée de verrouillage automatique des fiches en correction. Un seul enregistrement existe dans la base.

### Champs

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `duree_verrouillage_jours` | IntegerField | Durée avant déblocage automatique | Choix: DUREE_CHOICES, défaut: 5 |
| `date_modification` | DateTimeField | Date de dernière modification | Auto (auto_now) |

### Durées disponibles

```python
DUREE_CHOICES = [
    (1, '1 jour'),
    (2, '2 jours'),
    (5, '5 jours'),
    (10, '10 jours'),
    (0, 'Jamais (verrouillage permanent)'),
]
```

**Comportement** :
- `duree_verrouillage_jours > 0` : Déblocage automatique après N jours
- `duree_verrouillage_jours = 0` : **Jamais de déblocage automatique** (verrouillage permanent)

### Pattern Singleton

```python
@classmethod
def get_instance(cls):
    """Retourne l'instance unique de configuration"""
    instance, created = cls.objects.get_or_create(pk=1)
    return instance

def save(self, *args, **kwargs):
    """Force l'ID à 1 pour garantir un seul enregistrement"""
    self.pk = 1
    super().save(*args, **kwargs)
```

### Configuration Admin

L'admin Django empêche :
- ❌ La création de multiples instances (`has_add_permission` retourne False si existe)
- ❌ La suppression de la configuration (`has_delete_permission` retourne False)

### Utilisation

```python
# Récupérer la configuration (toujours la même instance)
config = ConfigurationVerrouillage.get_instance()

print(f"Durée : {config.get_duree_verrouillage_jours_display()}")
# Sortie : "5 jours" (par défaut)

# Modifier la durée (via admin Django recommandé)
config.duree_verrouillage_jours = 10
config.save()

# Utilisation dans EtatCorrection.est_verrouillee()
if config.duree_verrouillage_jours > 0:
    duree_max = timedelta(days=config.duree_verrouillage_jours)
    # ... vérification expiration
```

### Administration

Accessible via Django admin : `/admin/observations/configurationverrouillage/`

**Fonctionnalités** :
- ✅ Modification de la durée de verrouillage
- ✅ Un seul enregistrement visible
- ✅ Bouton "Ajouter" désactivé si configuration existe
- ✅ Suppression impossible

---

## Requêtes ORM courantes

### Récupérer une fiche avec tous ses objets liés (optimisé)

```python
fiche = FicheObservation.objects.select_related(
    'observateur',
    'espece',
    'espece__famille',
    'localisation',
    'nid',
    'resume',
    'causes_echec',
    'etat_correction'
).get(num_fiche=123)

# Accès sans requête supplémentaire
print(fiche.observateur.username)
print(fiche.espece.nom)
print(fiche.localisation.commune)
print(fiche.resume.nombre_oeufs_pondus)
```

### Récupérer les fiches avec leurs collections (1:N)

```python
fiches = FicheObservation.objects.prefetch_related(
    'observations',
    'remarques'
).filter(annee=2025)

for fiche in fiches:
    print(f"Fiche {fiche.num_fiche} : {fiche.observations.count()} observations")
    for obs in fiche.observations.all():
        print(f"  - {obs.date_observation}: {obs.nombre_oeufs} œufs")
```

### Fiches validées d'une espèce

```python
fiches_validees = FicheObservation.objects.filter(
    espece__nom='Mésange bleue',
    etat_correction__statut='valide'
).select_related('etat_correction')
```

### Statistiques par observateur

```python
from django.db.models import Count, Avg

stats = FicheObservation.objects.values('observateur__username').annotate(
    nb_fiches=Count('num_fiche'),
    completion_moyenne=Avg('etat_correction__pourcentage_completion')
).order_by('-nb_fiches')
```

---

## Voir aussi

- **[Vue d'ensemble](index.md)** - Architecture globale
- **[Pièges à éviter](gotchas.md)** - Erreurs courantes
- **[Documentation détaillée](../../architecture/domaines/02_observations_core.md)** - Version longue

---

*Dernière mise à jour : 2025-12-28*
