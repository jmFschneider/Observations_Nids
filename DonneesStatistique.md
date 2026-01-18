# Données Statistiques - Application Observations de Nids

## 1. Tableau de Bord Global (Admin/Superviseur)

### 1.1 Stats de Volume

#### Total de fiches
**Pourquoi ?** Vue d'ensemble de la base de données, indicateur de croissance globale.
```python
from observations.models import FicheObservation

total_fiches = FicheObservation.objects.count()
```

#### Fiches par statut
**Pourquoi ?** Permet de visualiser la répartition du workflow et identifier les goulots d'étranglement.
```python
from django.db.models import Count, Q
from observations.models import FicheObservation

stats_statuts = FicheObservation.objects.values(
    'etat_correction__statut'
).annotate(
    count=Count('num_fiche')
)

# Ou plus détaillé :
fiches_nouvelles = FicheObservation.objects.filter(
    etat_correction__statut='nouveau'
).count()

fiches_en_edition = FicheObservation.objects.filter(
    etat_correction__statut='en_edition'
).count()

fiches_en_correction = FicheObservation.objects.filter(
    etat_correction__statut='en_cours'
).count()

fiches_validees = FicheObservation.objects.filter(
    etat_correction__statut='valide'
).count()
```

#### Fiches créées dans les 30 derniers jours
**Pourquoi ?** Mesure l'activité récente et la dynamique de saisie.
```python
from django.utils import timezone
from datetime import timedelta

il_y_a_30_jours = timezone.now() - timedelta(days=30)
fiches_recentes = FicheObservation.objects.filter(
    date_creation__gte=il_y_a_30_jours
).count()
```

#### Nombre total d'observations terrain
**Pourquoi ?** Mesure la richesse des données collectées (plusieurs observations par fiche).
```python
from observations.models import Observation

total_observations = Observation.objects.count()
```

#### Taux de completion moyen
**Pourquoi ?** Indicateur de qualité des données saisies.
```python
from django.db.models import Avg

completion_moyenne = FicheObservation.objects.aggregate(
    avg_completion=Avg('etat_correction__pourcentage_completion')
)['avg_completion']
```

### 1.2 Stats de Performance

#### Temps moyen de validation (création → validation)
**Pourquoi ?** Mesure l'efficacité du processus de correction/validation.
```python
from django.db.models import Avg, F, ExpressionWrapper, fields
from django.db.models.functions import Extract

# Calculer la durée en jours
duree_validation_moyenne = FicheObservation.objects.filter(
    etat_correction__statut='valide',
    etat_correction__date_validation__isnull=False
).annotate(
    duree=ExpressionWrapper(
        F('etat_correction__date_validation') - F('date_creation'),
        output_field=fields.DurationField()
    )
).aggregate(
    avg_duree=Avg('duree')
)['avg_duree']

# Convertir en jours si besoin
if duree_validation_moyenne:
    jours = duree_validation_moyenne.total_seconds() / 86400
```

#### Taux de validation (% de fiches validées)
**Pourquoi ?** Mesure la progression globale du projet.
```python
total = FicheObservation.objects.count()
validees = FicheObservation.objects.filter(etat_correction__statut='valide').count()
taux_validation = (validees / total * 100) if total > 0 else 0
```

#### Nombre de fiches validées ce mois
**Pourquoi ?** Suivi de la productivité mensuelle.
```python
from django.utils import timezone
from datetime import datetime

debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
validations_ce_mois = FicheObservation.objects.filter(
    etat_correction__date_validation__gte=debut_mois
).count()
```

#### Nombre de modifications (activité de correction)
**Pourquoi ?** Mesure l'intensité du travail de correction.
```python
from audit.models import HistoriqueModification
from datetime import timedelta

il_y_a_30_jours = timezone.now() - timedelta(days=30)
modifications_recentes = HistoriqueModification.objects.filter(
    date_modification__gte=il_y_a_30_jours
).count()
```

### 1.3 Stats de Charge

#### Nombre de correcteurs actifs
**Pourquoi ?** Identifier les ressources humaines disponibles.
```python
from accounts.models import Utilisateur

correcteurs_actifs = Utilisateur.objects.filter(
    Q(role='correcteur') | Q(role='administrateur'),
    est_valide=True
).count()
```

#### Correcteurs avec fiches en cours
**Pourquoi ?** Voir qui travaille actuellement.
```python
correcteurs_occupes = Utilisateur.objects.filter(
    fiches_en_correction__isnull=False
).distinct().count()
```

#### Moyenne de fiches en cours par correcteur
**Pourquoi ?** Équilibrage de la charge de travail.
```python
from django.db.models import Count

charge_correcteurs = Utilisateur.objects.filter(
    fiches_en_correction__isnull=False
).annotate(
    nb_fiches=Count('fiches_en_correction')
).aggregate(
    moyenne=Avg('nb_fiches')
)['moyenne']
```

#### Fiches verrouillées depuis plus de 5 jours
**Pourquoi ?** Détecter les fiches bloquées.
```python
il_y_a_5_jours = timezone.now() - timedelta(days=5)
fiches_bloquees = FicheObservation.objects.filter(
    etat_correction__en_correction_par__isnull=False,
    etat_correction__date_debut_correction__lt=il_y_a_5_jours
).count()
```

---

## 2. Classement / Monitoring (Goulots d'étranglement)

### 2.1 Classement des Correcteurs

#### Top correcteurs (par nombre de validations)
**Pourquoi ?** Reconnaître les contributeurs les plus actifs.
```python
top_correcteurs = Utilisateur.objects.filter(
    validations__isnull=False
).annotate(
    nb_validations=Count('validations')
).order_by('-nb_validations')[:10]
```

#### Correcteurs les plus chargés (fiches en cours)
**Pourquoi ?** Redistribuer la charge si besoin.
```python
correcteurs_charges = Utilisateur.objects.filter(
    fiches_en_correction__isnull=False
).annotate(
    nb_en_cours=Count('fiches_en_correction')
).order_by('-nb_en_cours')[:10]
```

#### Temps moyen de validation par correcteur
**Pourquoi ?** Identifier les correcteurs rapides vs méticuleux.
```python
stats_correcteurs = Utilisateur.objects.filter(
    validations__isnull=False
).annotate(
    nb_validations=Count('validations'),
    duree_moyenne=Avg(
        ExpressionWrapper(
            F('validations__date_validation') - F('validations__fiche__date_creation'),
            output_field=fields.DurationField()
        )
    )
).order_by('-nb_validations')
```

### 2.2 Analyse Géographique

#### Départements avec le plus de fiches en attente
**Pourquoi ?** Identifier les zones géographiques nécessitant plus de ressources.
```python
departements_en_retard = FicheObservation.objects.filter(
    Q(etat_correction__statut='nouveau') | Q(etat_correction__statut='en_edition')
).values(
    'localisation__departement'
).annotate(
    nb_fiches=Count('num_fiche')
).order_by('-nb_fiches')[:10]
```

#### Taux de validation par département
**Pourquoi ?** Comparer la progression entre régions.
```python
from django.db.models import Case, When, FloatField, IntegerField

stats_departements = FicheObservation.objects.values(
    'localisation__departement'
).annotate(
    total=Count('num_fiche'),
    validees=Count(
        Case(
            When(etat_correction__statut='valide', then=1),
            output_field=IntegerField()
        )
    )
).annotate(
    taux_validation=ExpressionWrapper(
        F('validees') * 100.0 / F('total'),
        output_field=FloatField()
    )
).order_by('-taux_validation')
```

### 2.3 Analyse Temporelle

#### Fiches les plus anciennes non validées
**Pourquoi ?** Prioriser le traitement des fiches en retard.
```python
fiches_anciennes = FicheObservation.objects.exclude(
    etat_correction__statut='valide'
).order_by('date_creation')[:20]
```

#### Distribution par mois de création
**Pourquoi ?** Identifier les pics d'activité et les périodes creuses.
```python
from django.db.models.functions import TruncMonth

fiches_par_mois = FicheObservation.objects.annotate(
    mois=TruncMonth('date_creation')
).values('mois').annotate(
    count=Count('num_fiche')
).order_by('mois')
```

### 2.4 Analyse par Espèce

#### Espèces avec le plus de fiches en attente
**Pourquoi ?** Prioriser certaines espèces prioritaires.
```python
especes_en_attente = FicheObservation.objects.filter(
    Q(etat_correction__statut='nouveau') | Q(etat_correction__statut='en_edition')
).values(
    'espece__nom'
).annotate(
    nb_fiches=Count('num_fiche')
).order_by('-nb_fiches')[:10]
```

---

## 3. Profil Public d'un Membre (Gamification)

### 3.1 Profil Correcteur

#### Nombre total de validations
**Pourquoi ?** Indicateur principal de contribution.
```python
def stats_correcteur(correcteur_id):
    correcteur = Utilisateur.objects.get(id=correcteur_id)
    nb_validations = correcteur.validations.count()
    return nb_validations
```

#### Fiches actuellement en cours de correction
**Pourquoi ?** Montrer l'activité en cours.
```python
fiches_en_cours = correcteur.fiches_en_correction.count()
```

#### Ancienneté en tant que correcteur
**Pourquoi ?** Badge d'expérience.
```python
date_inscription = correcteur.date_joined
anciennete_jours = (timezone.now() - date_inscription).days
```

#### Date de dernière validation
**Pourquoi ?** Indicateur d'activité récente.
```python
derniere_validation = correcteur.validations.order_by(
    '-date_validation'
).first()

if derniere_validation:
    date_derniere = derniere_validation.date_validation
```

#### Temps moyen de validation (personnel)
**Pourquoi ?** Performance individuelle.
```python
duree_moyenne_perso = FicheObservation.objects.filter(
    etat_correction__validee_par=correcteur
).annotate(
    duree=ExpressionWrapper(
        F('etat_correction__date_validation') - F('date_creation'),
        output_field=fields.DurationField()
    )
).aggregate(avg_duree=Avg('duree'))['avg_duree']
```

#### Nombre de modifications apportées
**Pourquoi ?** Mesure de l'implication dans les corrections.
```python
nb_modifications = HistoriqueModification.objects.filter(
    modifie_par=correcteur
).count()
```

#### Espèces validées (diversité)
**Pourquoi ?** Expertise taxonomique.
```python
especes_validees = FicheObservation.objects.filter(
    etat_correction__validee_par=correcteur
).values('espece__nom').distinct().count()
```

#### Classement parmi les correcteurs
**Pourquoi ?** Gamification compétitive.
```python
classement = Utilisateur.objects.filter(
    validations__isnull=False
).annotate(
    nb_validations=Count('validations')
).filter(
    nb_validations__gt=correcteur.validations.count()
).count() + 1  # Position du correcteur
```

### 3.2 Profil Observateur

#### Nombre total de fiches créées
**Pourquoi ?** Indicateur principal de contribution.
```python
def stats_observateur(observateur_id):
    observateur = Utilisateur.objects.get(id=observateur_id)
    nb_fiches = observateur.fiches.count()
    return nb_fiches
```

#### Fiches validées (reconnaissance qualité)
**Pourquoi ?** Valorise la qualité du travail de saisie.
```python
fiches_validees = observateur.fiches.filter(
    etat_correction__statut='valide'
).count()
```

#### Nombre d'espèces différentes observées
**Pourquoi ?** Diversité des observations.
```python
especes_observees = observateur.fiches.values(
    'espece'
).distinct().count()
```

#### Liste des espèces observées
**Pourquoi ?** Détail de l'expertise.
```python
liste_especes = observateur.fiches.values_list(
    'espece__nom', flat=True
).distinct().order_by('espece__nom')
```

#### Nombre total d'observations terrain
**Pourquoi ?** Mesure l'assiduité sur le terrain.
```python
total_observations = Observation.objects.filter(
    fiche__observateur=observateur
).count()
```

#### Départements couverts
**Pourquoi ?** Portée géographique.
```python
departements = observateur.fiches.values(
    'localisation__departement'
).distinct().count()
```

#### Date de première fiche
**Pourquoi ?** Ancienneté comme contributeur.
```python
premiere_fiche = observateur.fiches.order_by('date_creation').first()
if premiere_fiche:
    date_premiere = premiere_fiche.date_creation
```

#### Date de dernière fiche
**Pourquoi ?** Activité récente.
```python
derniere_fiche = observateur.fiches.order_by('-date_creation').first()
if derniere_fiche:
    date_derniere = derniere_fiche.date_creation
```

#### Taux de completion moyen de ses fiches
**Pourquoi ?** Qualité de la saisie.
```python
completion_moyenne = observateur.fiches.aggregate(
    avg_completion=Avg('etat_correction__pourcentage_completion')
)['avg_completion']
```

#### Nombre de fiches avec images
**Pourquoi ?** Valorise l'effort de documentation photographique.
```python
fiches_avec_images = observateur.fiches.exclude(
    chemin_image=''
).count()
```

#### Images téléversées (en attente de transcription)
**Pourquoi ?** Contribution à la base d'images.
```python
images_uploadees = observateur.images_sources.count()
images_transcrites = observateur.images_sources.filter(
    est_transcrite=True
).count()
```

#### Années d'observation couvertes
**Pourquoi ?** Continuité temporelle.
```python
annees_observations = observateur.fiches.values(
    'annee'
).distinct().order_by('annee')
```

#### Classement parmi les observateurs
**Pourquoi ?** Gamification compétitive.
```python
classement_obs = Utilisateur.objects.filter(
    fiches__isnull=False
).annotate(
    nb_fiches=Count('fiches')
).filter(
    nb_fiches__gt=observateur.fiches.count()
).count() + 1
```

---

## 4. Indicateurs Complémentaires

### 4.1 Qualité des Données

#### Fiches avec localisation complète
**Pourquoi ?** Mesure la complétude géographique.
```python
fiches_localisees = FicheObservation.objects.filter(
    localisation__departement__isnull=False,
    localisation__commune__isnull=False
).exclude(
    localisation__departement='00'
).exclude(
    localisation__commune=''
).count()
```

#### Fiches avec données de reproduction complètes
**Pourquoi ?** Richesse scientifique.
```python
fiches_reproduction_complete = FicheObservation.objects.filter(
    resume__nombre_oeufs_pondus__isnull=False,
    resume__nombre_oeufs_eclos__isnull=False,
    resume__nombre_poussins__isnull=False
).count()
```

### 4.2 Activité Système

#### Utilisateurs inscrits en attente de validation
**Pourquoi ?** Suivi des demandes administratives.
```python
demandes_en_attente = Utilisateur.objects.filter(
    est_valide=False,
    est_refuse=False
).count()
```

#### Taux de refus de demandes
**Pourquoi ?** Qualité des demandes d'inscription.
```python
total_demandes = Utilisateur.objects.exclude(role='administrateur').count()
demandes_refusees = Utilisateur.objects.filter(est_refuse=True).count()
taux_refus = (demandes_refusees / total_demandes * 100) if total_demandes > 0 else 0
```

---

## Notes d'Implémentation

### Optimisation des Requêtes

Pour éviter les requêtes N+1, utilisez systématiquement :
- `select_related()` pour les relations ForeignKey
- `prefetch_related()` pour les relations ManyToMany et reverse ForeignKey
- `annotate()` avec `Count()`, `Avg()`, etc. pour les agrégations

### Mise en Cache

Les statistiques globales devraient être mises en cache :
```python
from django.core.cache import cache

def get_stats_globales():
    stats = cache.get('stats_globales')
    if stats is None:
        stats = calculer_stats_globales()
        cache.set('stats_globales', stats, 3600)  # 1 heure
    return stats
```

### Tâches Asynchrones

Pour les calculs lourds, utilisez Celery :
```python
from celery import shared_task

@shared_task
def calculer_statistiques_hebdomadaires():
    # Calculs lourds ici
    pass
```

---

## Prochaines Étapes

1. **Créer les fonctions de calcul** dans `observations/stats.py`
2. **Créer les vues** pour afficher ces statistiques
3. **Créer les templates** avec des graphiques (Chart.js, Plotly)
4. **Ajouter la mise en cache** pour les statistiques coûteuses
5. **Créer des tâches Celery** pour les calculs périodiques
6. **Ajouter des badges** et éléments de gamification dans les profils
