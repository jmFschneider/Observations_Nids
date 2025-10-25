# Architecture du Projet - Observations Nids

## 1. Vue d'ensemble

**Observations Nids** est une application Django pour la gestion d'observations ornithologiques de nidification. L'application permet la transcription OCR automatique de fiches papier, la saisie manuelle, la correction collaborative et la validation des données avec traçabilité complète.

### Objectifs principaux
1.  **Numérisation automatisée** : OCR des fiches papier via Google Vision API
2.  **Saisie et correction** : Interface web intuitive pour gérer les observations
3.  **Workflow collaboratif** : Système de rôles (observateur, correcteur, validateur, admin)
4.  **Traçabilité** : Historique complet de toutes les modifications
5.  **Qualité des données** : Validation stricte et workflow de révision

---

## 2. Structure des applications Django

Le projet est organisé en applications Django distinctes pour une meilleure séparation des responsabilités.

```
observations_nids/
├── accounts/              # Authentification et gestion utilisateurs
├── audit/                 # Historique et traçabilité des modifications
├── core/                  # Fonctionnalités communes et utilitaires
├── geo/                   # Gestion des localisations géographiques
├── ingest/                # Ingestion et traitement de données externes
├── observations/          # Application principale - gestion des observations
├── review/                # Système de révision et validation
├── taxonomy/              # Classification taxonomique des espèces
└── observations_nids/     # Configuration Django principale
```

### Responsabilités des Applications

#### **accounts/** - Gestion des utilisateurs
- Modèle `Utilisateur` (AUTH_USER_MODEL personnalisé)
- Rôles : observateur, correcteur, validateur, administrateur
- Authentification et permissions

#### **audit/** - Traçabilité
- Modèle `HistoriqueModification` : enregistre toutes les modifications
- Tracking automatique au niveau du champ via les signaux Django
- Interface de consultation de l'historique

#### **core/** - Utilitaires partagés
- Fonctions communes à plusieurs applications
- Mixins et décorateurs réutilisables
- Configuration partagée

#### **geo/** - Données géographiques
- Modèle `Localisation` : coordonnées, commune, lieu-dit, département
- Gestion des sites d'observation
- Validation des coordonnées GPS

#### **ingest/** - Traitement des données externes
- Import de données depuis fichiers JSON
- Parsing et normalisation des données
- Gestion des candidats (espèces, observateurs)

#### **observations/** - Application principale
- Modèles centraux : `FicheObservation`, `Observation`, `Nid`, `ResumeObservation`, `CausesEchec`
- Vues de saisie, modification, consultation
- Système de transcription OCR (Celery + Google Vision API)
- Interface principale de l'application

#### **review/** - Révision et validation
- Workflow de correction et validation
- États de correction : nouveau, en_cours, corrigé, validé, rejeté
- Suivi de la progression

#### **taxonomy/** - Taxonomie
- Modèles `Ordre`, `Famille`, `Espece` : classification taxonomique complète
- Nomenclature scientifique et vernaculaire (français, anglais)
- Commandes d'import de référentiels (`TaxRef`, `LOF`).

---

## 3. Modèles de Données Principaux

### FicheObservation (`observations/models.py`)
C'est le **modèle central** représentant une fiche d'observation complète.

**Champs principaux :**
- `num_fiche` : AutoField (clé primaire)
- `observateur` : ForeignKey vers `Utilisateur`
- `espece` : ForeignKey vers `Espece`
- `annee` : Année de l'observation
- `chemin_image` : Chemin vers l'image scannée
- `chemin_json` : Chemin vers les données OCR JSON
- `transcription` : Boolean indiquant si issue de la transcription OCR

**Relations OneToOne :**
- `Localisation` : où se trouve le nid
- `Nid` : caractéristiques du nid
- `ResumeObservation` : synthèse des données de reproduction
- `CausesEchec` : causes d'échec de la nidification
- `EtatCorrection` : état du workflow de correction

**Particularités :**
- Création automatique des objets liés lors du `save()` d'une nouvelle fiche pour garantir l'intégrité des données.

### Observation (`observations/models.py`)
Représente les **observations individuelles** au sein d'une fiche (relation OneToMany).

**Champs :**
- `fiche` : ForeignKey vers `FicheObservation`
- `date_observation` : Date
- `heure_observation` : Time
- `nombre_oeufs` : IntegerField
- `nombre_poussins` : IntegerField
- `notes` : TextField pour remarques

### Modèles Taxonomiques (`taxonomy/models.py`)

#### **Ordre**
- `nom` : CharField(max_length=100, unique=True)

#### **Famille**
- `nom` : CharField(max_length=100, unique=True)
- `ordre` : ForeignKey vers `Ordre`

#### **Espece**
- `nom` : CharField(max_length=100, unique=True) - Nom vernaculaire français
- `nom_scientifique` : CharField - Nom latin
- `nom_anglais` : CharField - Nom anglais
- `famille` : ForeignKey vers `Famille`
- `statut` : CharField - Statut de présence en France
- `lien_oiseau_net` : URLField

---

## 4. Points Techniques Notables

### Gestion automatique des objets liés
Lors de la création d'une `FicheObservation`, les objets liés (`Localisation`, `Nid`, `ResumeObservation`, etc.) sont automatiquement créés avec des valeurs par défaut. Cela simplifie la logique métier et garantit la cohérence.

### Optimisations de performance
- **Index de base de données** sur les champs fréquemment filtrés.
- Utilisation de **`select_related()`** et **`prefetch_related()`** pour réduire les requêtes N+1.
- **Pagination** pour les listes longues.
- **Cache** pour les données de référence (espèces, utilisateurs).

### Sécurité
- **CSRF Protection** activée sur tous les formulaires POST.
- **Expiration de session** automatique.
- **Permissions** vérifiées dans chaque vue via des décorateurs (`@login_required`, `@user_passes_test`).
- **Prévention des injections SQL** par l'utilisation exclusive de l'ORM Django.
- **Auto-échappement XSS** dans les templates Django.

### Configuration
- **Pydantic Settings** (`observations_nids/config.py`) est utilisé pour valider et typer les variables d'environnement, offrant une configuration robuste et documentée.
- Les secrets et les configurations spécifiques à l'environnement sont gérés dans un fichier `.env`, à partir du template `.env.example`.
