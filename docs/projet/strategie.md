# Strategie de documentation - A reprendre quand l'application sera terminee

*Note: Ce fichier a ete cree le 16 janvier 2026 pour conserver la strategie de refonte de la documentation.*

## Contexte

L'ancienne documentation a ete archivee (backup) car elle etait devenue trop complexe avec des recoupements entre fichiers et repertoires. Ce document decrit l'approche a suivre pour la reconstruire.

## Approche recommandee : Repartir du code

**Pourquoi pas recuperer les anciens fichiers :**
- Ils contenaient des redondances et incoherences
- Le code a evolue, la doc est probablement desynchronisee
- On reproduirait les memes problemes structurels

**Pourquoi repartir du code :**
- Documentation garantie synchronisee avec l'etat actuel
- Structure coherente des le depart
- Opportunite de definir une architecture de doc claire

## Structure suggeree

```
docs/
├── README.md                    # Vue d'ensemble projet
├── installation.md              # Setup dev/prod
├── architecture.md              # Schema global des apps
└── applications/
    ├── accounts.md              # 1 fichier par app Django
    ├── observations.md
    ├── ingest.md
    ├── pilot.md
    ├── taxonomy.md
    └── ...
```

**Principe : 1 application = 1 fichier** (sauf si vraiment trop gros)

## Choix de l'outil : Gemini vs Claude

| Critere | Gemini 2.5 Pro | Claude Opus |
|---------|----------------|-------------|
| Contexte | 1M tokens | 200K tokens |
| Analyse code | Excellent | Excellent |
| Redaction structuree | Bon | Tres bon |
| Cout | Moins cher | Plus cher |

**Recommandation :**
- **Gemini** : Meilleur si on veut injecter tout le code d'un coup
- **Claude** : Meilleur pour une documentation progressive, app par app, avec plus de nuance dans la redaction

Pour un projet Django de cette taille (~15-20 fichiers principaux par app), les deux fonctionnent bien.

## Processus concret

1. **Definir le template** de documentation (structure commune pour chaque app)
2. **Generer app par app** en fournissant : models.py, views/, urls.py, forms.py
3. **Relire et valider** avant de passer a l'app suivante
4. **Documenter les flux transverses** a la fin (OCR workflow, etc.)

## Template suggere pour une application

```markdown
# Application [NOM]

## Objectif
[Description en 2-3 phrases]

## Modeles
[Liste des modeles avec leurs champs principaux et relations]

## Vues principales
[Endpoints et leur fonction]

## Formulaires
[Formulaires disponibles]

## Permissions
[Qui peut faire quoi]

## Points d'attention
[Gotchas, particularites]
```

## Applications a documenter

- [ ] accounts (authentification, utilisateurs)
- [ ] observations (fiches d'observation, saisie)
- [ ] ingest (import JSON, workflow batch)
- [ ] pilot (OCR, transcription)
- [ ] taxonomy (especes, codes GONM)
- [ ] geo (communes, geolocalisation)
- [ ] review (validation, correction)
- [ ] audit (historique, tracabilite)
- [ ] core (utilitaires partages)
