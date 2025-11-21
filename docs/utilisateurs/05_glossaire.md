# 📖 Glossaire

> **Définitions des termes techniques et spécifiques**
> Ce glossaire vous aide à comprendre le vocabulaire utilisé dans l'application.

---

## A

### API (Application Programming Interface)
Interface de programmation permettant la communication entre différents logiciels. Dans Observations Nids, les API servent à interroger des services externes (communes, coordonnées GPS, etc.).

### Auto-complétion
Fonctionnalité qui suggère automatiquement des valeurs pendant la saisie. Utilisée pour les communes et les espèces.

### Audit
Système de traçabilité qui enregistre toutes les modifications apportées aux données (qui, quand, quoi).

---

## C

### Celery
Système de traitement de tâches asynchrones en arrière-plan. Utilisé pour la transcription automatique qui peut prendre plusieurs minutes.

### Correcteur
Rôle utilisateur avec des permissions étendues permettant de modifier les fiches d'autres utilisateurs et de valider les observations.

### Coordonnées GPS
Latitude et longitude définissant précisément un point sur la Terre. Format : `48.5734, 7.7521`

---

## D

### Django
Framework web Python sur lequel est construite l'application Observations Nids.

---

## E

### Envol
Moment où les jeunes oiseaux quittent définitivement le nid. Marque généralement la fin d'une observation de nidification.

---

## F

### Fiche d'observation
Document numérique contenant toutes les informations sur un nid : localisation, espèce, observations temporelles, remarques.

### Formset
Composant technique Django permettant d'ajouter dynamiquement plusieurs observations à une même fiche.

---

## G

### Géocodage
Processus de conversion d'une adresse ou d'un nom de commune en coordonnées GPS.

### Géolocalisation
Détermination automatique de votre position géographique via GPS ou autre technologie.

### Gemini
Intelligence artificielle de Google utilisée pour la transcription automatique (OCR) des carnets manuscrits.

---

## H

### Helpdesk
Système de support intégré permettant de créer et suivre des tickets d'assistance.

### Historique
Liste chronologique de toutes les modifications apportées à une fiche d'observation.

---

## I

### IA (Intelligence Artificielle)
Technologie utilisée pour la transcription automatique des carnets papier.

---

## J

### JSON (JavaScript Object Notation)
Format de données structurées utilisé pour stocker les résultats de transcription. Exemple :
```json
{
  "espece": "Cigogne blanche",
  "annee": 2025
}
```

---

## L

### Lieu-dit
Nom d'un endroit spécifique au sein d'une commune (ex: "La Robertsau", "Les Trois Chênes").

---

## M

### Metadata
Informations sur les données elles-mêmes (date de création, auteur, date de modification, etc.).

---

## N

### Nid
Structure construite par les oiseaux pour pondre leurs œufs et élever leurs petits. Objet central de l'application.

### Nidification
Période pendant laquelle les oiseaux construisent leur nid, pondent, couvent et élèvent leurs jeunes.

### Nominatim
Service de géocodage open-source utilisé comme solution de secours pour trouver les coordonnées d'une commune.

---

## O

### Observateur
Rôle utilisateur de base permettant de créer et gérer ses propres observations.

### OCR (Optical Character Recognition)
Reconnaissance optique de caractères. Technologie permettant de lire du texte sur une image (manuscrit ou imprimé).

---

## P

### Ponte
Période pendant laquelle la femelle pond ses œufs dans le nid.

### Poussin
Jeune oiseau encore au nid, après l'éclosion.

---

## R

### Remarque
Note textuelle libre ajoutée à une fiche d'observation pour préciser un contexte, signaler une incertitude, etc.

### Reverse geocoding
Processus inverse du géocodage : conversion de coordonnées GPS en nom de commune.

---

## S

### Statut (de fiche)
État actuel d'une fiche dans le workflow de validation. Les statuts sont :
- **NOUVEAU** : Fiche juste créée
- **EN_EDITION** : Fiche sauvegardée, modifiable
- **EN_COURS** : Fiche soumise pour correction
- **VALIDEE** : Fiche approuvée et finalisée

### Support
Élément physique sur lequel est construit le nid (arbre, bâtiment, pylône, etc.).

---

## T

### TaxRef
Référentiel taxonomique national français des espèces. Base de données de référence pour les noms scientifiques.

### Ticket
Demande d'assistance créée dans le système Helpdesk pour signaler un problème ou poser une question.

### Transcription
Processus de conversion automatique d'images de carnets papier en données numériques structurées.

---

## U

### Upload
Action de téléverser (envoyer) des fichiers depuis votre ordinateur vers l'application.

---

## V

### Validation
Processus de vérification et d'approbation d'une fiche d'observation par un correcteur ou administrateur.

---

## W

### Workflow
Enchaînement d'étapes dans un processus. Le workflow d'une observation : création → édition → soumission → correction → validation.

---

## Termes ornithologiques spécifiques

### Couvée
Ensemble des œufs pondus et couvés en une fois par un oiseau.

### Éclosion
Moment où le poussin sort de l'œuf.

### Espèce
Groupe d'organismes vivants partageant des caractéristiques communes. Dans l'application, référence les espèces d'oiseaux observées.

### Famille (taxonomie)
Niveau de classification biologique regroupant plusieurs espèces apparentées. Ex: Anatidés (canards, oies).

### Nichée
Ensemble des poussins issus d'une même couvée.

### Ordre (taxonomie)
Niveau de classification biologique au-dessus de la famille. Ex: Passériformes (passereaux).

### Prédation
Action d'un prédateur qui attaque et tue des proies. Cause possible d'échec de reproduction.

### Reproduction
Processus complet de nidification aboutissant (ou non) à l'envol de jeunes.

### Succès de reproduction
Indication si la reproduction a permis l'envol d'au moins un jeune.

---

## Acronymes et abréviations

| Acronyme | Signification |
|----------|---------------|
| **API** | Application Programming Interface |
| **CSV** | Comma-Separated Values (format de fichier) |
| **GPS** | Global Positioning System |
| **IA** | Intelligence Artificielle |
| **JSON** | JavaScript Object Notation |
| **LOF** | Liste des Oiseaux de France |
| **OCR** | Optical Character Recognition |
| **UI** | User Interface (Interface utilisateur) |
| **UX** | User Experience (Expérience utilisateur) |

---

## Termes techniques de l'interface

### Badge
Élément visuel (souvent coloré) indiquant un statut. Ex: Badge "VALIDEE" en vert.

### Champ obligatoire
Champ du formulaire qui doit absolument être rempli pour pouvoir enregistrer. Marqué par une astérisque (*) ou en rouge.

### Filtre
Critère de sélection permettant de réduire une liste de résultats. Ex: Filtrer par espèce, date, lieu.

### Formset
Ensemble de formulaires permettant d'ajouter plusieurs éléments similaires (ex: plusieurs observations pour un nid).

### Menu déroulant
Liste d'options qui apparaît quand on clique sur un champ. Permet de sélectionner une valeur.

### Pagination
Division d'une longue liste en plusieurs pages pour faciliter la navigation.

### Popup / Modale
Fenêtre qui s'affiche par-dessus le contenu principal pour afficher des informations ou demander une action.

### Toast / Message de confirmation
Petit message temporaire qui apparaît (généralement en haut ou en bas de l'écran) pour confirmer une action.

---

## Besoin d'une définition supplémentaire ?

Si un terme utilisé dans l'application n'est pas dans ce glossaire, n'hésitez pas à :
- [Créer un ticket](./04_support_tickets.md) avec la catégorie "Documentation"
- Demander à un administrateur
- Consulter les guides détaillés

---

**Retour à** : [Documentation complète](./README.md)

---

*Version 1.0 - Novembre 2025*
