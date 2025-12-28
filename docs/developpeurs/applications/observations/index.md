# Observations - Vue d'ensemble

> Application centrale du projet : gestion des fiches d'observation de nidification

## Responsabilité

L'application **observations** est le **cœur métier** du projet. Elle gère :
- Les fiches d'observation de nidification (modèle `FicheObservation`)
- Les relations 1:1 (Localisation, Nid, ResumeObservation, CausesEchec, EtatCorrection)
- Les relations 1:N (Observations ponctuelles, Remarques)
- Les formulaires de saisie et correction
- L'affichage des fiches
- 🔒 Le **verrouillage des corrections** pour empêcher les modifications concurrentes

## Position dans l'architecture

```
accounts → observations ← taxonomy
geo → observations
core → observations

observations → ingest (import OCR)
observations → review (validation)
observations → audit (historique)
```

## Modèles principaux

| Modèle | Description | Fichier |
|--------|-------------|---------|
| **FicheObservation** | Fiche de nidification (modèle pivot central) | `observations/models.py` |
| **Localisation** | Commune, GPS, altitude (1:1 avec FicheObservation) | `observations/models.py` |
| **Nid** | Caractéristiques physiques du nid (1:1) | `observations/models.py` |
| **ResumeObservation** | Données de nidification (dates, comptages) (1:1) | `observations/models.py` |
| **CausesEchec** | Causes d'échec de la nidification (1:1) | `observations/models.py` |
| **EtatCorrection** | 🔒 Statut de correction/validation + verrouillage (1:1) | `observations/models.py` |
| **ConfigurationVerrouillage** | 🔒 Configuration singleton du verrouillage | `observations/models.py` |
| **Observation** | Observation ponctuelle datée (1:N) | `observations/models.py` |
| **Remarque** | Remarques textuelles (1:N) | `observations/models.py` |

## Points d'entrée clés

### URLs principales
- `/observations/` - Liste des fiches
- `/observations/nouvelle/` - Saisie nouvelle fiche
- `/observations/<num_fiche>/` - Détail d'une fiche
- `/observations/<num_fiche>/corriger/` - Correction d'une fiche

### Vues principales
- `liste_observations` - Liste des fiches
- `saisie_observation` - Formulaire de saisie
- `fiche_observation` - Affichage détail
- `corriger_fiche` - Interface de correction

## Dépendances

### Applications Django
- **accounts** - Modèle Utilisateur (ForeignKey observateur)
- **taxonomy** - Modèle Espece (ForeignKey espece)
- **geo** - Validation des communes
- **core** - Modèles de base, utilitaires

## Documentation existante

Voir **[docs/developpeurs/architecture/domaines/02_observations_core.md](../../architecture/domaines/02_observations_core.md)** pour la documentation détaillée des modèles.

## Fichiers critiques

| Fichier | Sensibilité | Raison |
|---------|-------------|--------|
| `models.py` | 🔥 **Critique** | Modèle central avec création automatique d'objets liés |
| `forms.py` | ⚠️ Sensible | Logique de validation complexe |
| `views.py` | ⚠️ Sensible | Logique métier importante |

## Système de verrouillage des corrections 🔒

**Objectif** : Empêcher plusieurs reviewers de modifier simultanément la même fiche en statut "en_cours".

### Fonctionnement

Lorsqu'un reviewer sauvegarde pour la première fois une fiche en statut `en_cours` :
1. ✅ La fiche est **verrouillée** pour ce reviewer
2. ✅ Les autres reviewers voient un message et sont **redirigés en lecture seule**
3. ✅ Un **badge jaune** affiche qui corrige la fiche et depuis quand

### Déblocage

**Automatique** :
- Après une durée configurable : 1, 2, 5 (défaut), 10 jours, ou jamais
- Configuration via `/admin/observations/configurationverrouillage/`

**Manuel** :
- Le reviewer peut débloquer **sa propre** fiche via le bouton "Débloquer"
- Un administrateur peut **forcer le déblocage** de n'importe quelle fiche

### Modèles impliqués

- **`EtatCorrection`** : Champs `en_correction_par`, `date_debut_correction`
  - Méthodes : `est_verrouillee()`, `liberer_verrou()`, `verrouiller_pour(reviewer)`
- **`ConfigurationVerrouillage`** : Singleton pour la configuration de la durée

### Vues impliquées

- **`saisie_observation`** (GET) : Contrôle d'accès, redirection si verrouillée
- **`saisie_observation`** (POST) : Verrouillage automatique lors de la 1ère sauvegarde
- **`liberer_verrou_fiche`** : Déblocage manuel

### Documentation détaillée

Voir **[models.md](models.md#modèle--etatcorrection)** pour :
- Workflow de verrouillage complet
- Exemples de code
- Détails des méthodes

## Voir aussi

- **[Architecture domaine observations](../../architecture/domaines/02_observations_core.md)** - Documentation détaillée
- **[gotchas.md](gotchas.md)** - Pièges à éviter

---

*Dernière mise à jour : 2025-12-28*
