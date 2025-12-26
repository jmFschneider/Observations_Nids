# 📊 Analyse et Proposition d'Automatisation du Pipeline de Transcription

**Date de création** : 25 décembre 2025
**Objectif** : Concevoir un processus automatisé pour traiter plusieurs dizaines de milliers de fiches d'observation sans intervention humaine

---

## 📋 Table des matières

1. [Contexte et Objectifs](#1-contexte-et-objectifs)
2. [Analyse du Processus Actuel](#2-analyse-du-processus-actuel)
3. [Points de Blocage pour le Passage à l'Échelle](#3-points-de-blocage-pour-le-passage-à-léchelle)
4. [Architecture Proposée pour l'Automatisation](#4-architecture-proposée-pour-lautomatisation)
5. [Stratégie de Gestion des Erreurs](#5-stratégie-de-gestion-des-erreurs)
6. [Feuille de Route d'Implémentation](#6-feuille-de-route-dimplémentation)

---

## 1. Contexte et Objectifs

### 1.1 Reformulation de la Demande

#### Situation Actuelle
Nous disposons d'un **processus de transcription segmenté en plusieurs étapes manuelles** :
1. Images de fiches → Transcription OCR (Gemini) → Fichiers JSON
2. Import JSON → Extraction candidats → Validation espèces → Préparation importations → Finalisation
3. Chaque étape nécessite une **intervention humaine** pour passer à la suivante

#### Contrainte d'Échelle
- ✅ **Fonctionne bien** : quelques dizaines ou centaines de fiches
- ❌ **Ne passe pas à l'échelle** : plusieurs dizaines de milliers de fiches

#### Objectif Recherché
Concevoir un **processus automatisé de bout en bout** qui :

1. **Minimise les erreurs** au maximum
2. **Fonctionne sans intervention humaine** de l'image jusqu'à la base de données
3. L'humain n'intervient **qu'APRÈS** : pour la relecture/validation des fiches déjà en base

### 1.2 Périmètre

**En entrée** : Plusieurs dizaines de milliers d'images de fiches d'observation
**En sortie** : Fiches complètes en base de données, prêtes pour relecture humaine
**Contrainte forte** : Aucune intervention humaine pendant le processus

---

## 2. Analyse du Processus Actuel

### 2.1 Vue d'Ensemble du Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PILOT APP - OCR/TRANSCRIPTION                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    Images (media/) │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  1. Sélection des répertoires d'images       │ ← MANUEL
        │     (selection_repertoire_ocr)               │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  2. Lancement de la transcription batch      │ ← MANUEL
        │     (lancer_transcription_batch)             │
        │     - Sélection des modèles Gemini           │
        │     - Configuration du batch                  │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  3. Traitement OCR asynchrone (Celery)       │ ← AUTOMATIQUE
        │     process_batch_transcription_task         │
        │     - Détection auto du type de fiche        │
        │     - Appel Gemini API (timeout + retry)     │
        │     - Validation JSON                         │
        │     - Correction automatique                  │
        │     - Sauvegarde JSON + TranscriptionOCR      │
        └──────────────────────────────────────────────┘
                                    │
                    JSON Files créés │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        INGEST APP - IMPORT EN BASE                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌──────────────────────────────────────────────┐
        │  4. Import des fichiers JSON                 │ ← MANUEL
        │     (importer_json)                          │
        │     - Sélection du répertoire                │
        │     - Création TranscriptionBrute            │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  5. Extraction des candidats                 │ ← MANUEL
        │     (extraire_candidats)                     │
        │     - Extraction espèces (auto-match 0.8)    │
        │     - Création utilisateurs auto             │
        │     - Géocodage communes                      │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  6. Validation des espèces                   │ ← MANUEL ⚠️
        │     (liste_especes_candidates)               │
        │     - Revue des correspondances auto         │
        │     - Validation manuelle                     │
        │     - Lien vers Espece validée                │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  7. Préparation des importations             │ ← MANUEL
        │     (preparer_importations)                  │
        │     - Création ImportationEnCours            │
        │     - Statut: en_attente                      │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  8. Revue optionnelle                        │ ← MANUEL (optionnel)
        │     (liste_importations)                     │
        │     - Visualisation JSON                      │
        │     - Contrôle qualité pré-finalisation       │
        └──────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  9. Finalisation                             │ ← MANUEL ⚠️
        │     (finaliser_importation)                  │
        │     - Création FicheObservation              │
        │     - Création objets liés                    │
        │     - Transaction atomique                    │
        └──────────────────────────────────────────────┘
                                    │
                Fiches en base de données │
                                    ↓
        ┌──────────────────────────────────────────────┐
        │  10. Relecture et correction                 │ ← POST-IMPORT
        │      (view_transcription)                    │
        │      - Correction manuelle si nécessaire      │
        │      - Validation finale                      │
        └──────────────────────────────────────────────┘
```

### 2.2 Détail des Étapes Automatiques

#### Étape 3 : Traitement OCR (process_batch_transcription_task)

**Fichier** : `pilot/tasks.py`

**Processus** :
```python
For each OCR model (gemini_3_flash, gemini_3_pro, etc.):
    For each directory:
        For each image:
            1. Détection automatique du type de fiche
               - Recherche "ancien"/"Ancien" dans le chemin
               - Charge prompt_gemini_transcription.txt (moderne)
               - OU prompt_gemini_transcription_Ancienne_Fiche.txt (années 70-80)

            2. Appel API Gemini
               - Timeout: 120 secondes
               - Retry: 3 tentatives avec backoff exponentiel (2s → 4s → 8s → 16s)
               - Rate limiting: 60 req/min

            3. Validation JSON
               - validate_json_structure() retourne liste d'erreurs
               - Vérifie structure attendue (informations_generales, nid, etc.)

            4. Correction automatique
               - corriger_json() corrige noms de champs courants
               - Sauvegarde _raw.json si corrections appliquées

            5. Sauvegarde
               - {image_name}_result.json (JSON corrigé)
               - Création TranscriptionOCR (métadonnées d'évaluation)
               - Suivi progression dans session + Redis
```

**Structure JSON Attendue** :
```json
{
  "informations_generales": {
    "n_fiche": "...",
    "observateur": "...",
    "n_espece": "...",
    "espece": "...",
    "annee": "..."
  },
  "nid": {
    "nid_prec_t_meme_c_ple": true/false,
    "haut_nid": "...",
    "h_c_vert": "...",
    "nid": "description..."
  },
  "localisation": {
    "IGN_50000": "...",
    "commune": "...",
    "dep_t": "...",
    "coordonnees_et_ou_lieu_dit": "...",
    "altitude": "...",
    "paysage": "...",
    "alentours": "..."
  },
  "tableau_donnees": [
    {
      "Jour": 17,
      "Mois": 7,
      "Heure": 12,
      "Nombre_oeuf": 0,
      "Nombre_pou": 3,
      "age": null,
      "observations": "..."
    }
  ],
  "tableau_donnees_2": {
    "1er_o_pondu": {"jour": null, "Mois": null, "Precision": null},
    "1er_p_eclos": {"jour": null, "Mois": null, "Precision": null},
    "1er_p_volant": {"jour": null, "Mois": null, "Precision": null},
    "nombre_oeufs": {"pondus": null, "eclos": null, "n_ecl": null},
    "nombre_poussins": {"1/2": null, "3/4": "3", "vol_t": "3"}
  },
  "causes_echec": {
    "causes_d_echec": "..."
  },
  "remarque": "..." (optionnel)
}
```

**Gestion des Erreurs** :
| Erreur | Action | Impact |
|--------|--------|--------|
| Timeout API | Retry 3x avec backoff | Image sautée si échec total |
| JSON Parse Error | Log + continue | Sauvegarde réponse brute |
| JSON invalide | Auto-correction | Sauvegarde raw + corrigé |
| Rate limit | Attente 1s entre requêtes | Prévention ban API |
| Fichier introuvable | Log + continue | Image ignorée |

#### Étape 5 : Extraction des Candidats (extraire_donnees_candidats)

**Fichier** : `ingest/importation_service.py`

**Processus** :
```python
For each TranscriptionBrute (traite=False):
    1. Extraction Espèce
       - nom_espece = json['informations_generales']['espece']
       - Création/récupération EspeceCandidate
       - Auto-matching avec SequenceMatcher (threshold: 0.8)
       - Recherche dans toutes les Espece de la base
       - Score de similarité stocké
       - Si score ≥ 0.8 → espece_validee auto-remplie
       - Si score < 0.8 → espece_validee = None (validation manuelle requise)

    2. Extraction Observateur
       - nom_observateur = json['informations_generales']['observateur']
       - Appel creer_ou_recuperer_utilisateur(nom_observateur)
       - Parsing intelligent :
         * "Prénom Nom" → first_name="Prénom", last_name="Nom"
         * "NOM" → first_name="NOM", last_name="NOM"
       - Recherche utilisateur existant (first_name + last_name, case-insensitive)
       - Si trouvé → mise à jour est_transcription=True
       - Si pas trouvé → création automatique :
         * username: prenom.nom (unique avec compteur si collision)
         * email: prenom.nom@transcription.trans (avec fallback si collision)
         * est_transcription=True, est_valide=True
         * role='observateur'

    3. Géocodage Commune
       - commune = json['localisation']['commune'] ou json['localisation']['IGN_50000']
       - departement = json['localisation']['dep_t']
       - Appel geocodeur.geocoder_commune(commune, departement)
       - Recherche via API Google Maps ou IGN
       - Récupération : lat, lon, altitude, adresse complète
       - Si échec → utilise nom brut, log warning
       - Création/mise à jour CommuneFrance si succès
```

**Auto-Matching d'Espèces** :
```python
def _trouver_correspondance_espece(self, espece_candidate):
    """
    Auto-match avec SequenceMatcher (difflib)
    Threshold: 0.8 (80% de similarité)
    """
    nom_transcrit = espece_candidate.nom_transcrit.lower()
    meilleure_correspondance = None
    meilleur_score = 0

    for espece in Espece.objects.all():
        # Compare avec nom_commun et nom_scientifique
        score_commun = SequenceMatcher(None, nom_transcrit, espece.nom_commun.lower()).ratio()
        score_sci = SequenceMatcher(None, nom_transcrit, espece.nom_scientifique.lower()).ratio()
        score = max(score_commun, score_sci)

        if score > meilleur_score:
            meilleur_score = score
            meilleure_correspondance = espece

    if meilleur_score >= 0.8:
        espece_candidate.espece_validee = meilleure_correspondance
        espece_candidate.score_similarite = round(meilleur_score * 100, 1)
        espece_candidate.save()
```

**Statistiques Retournées** :
- `especes_ajoutees` : Nombre de nouveaux EspeceCandidate créés
- `utilisateurs_crees` : Nombre de nouveaux Utilisateur créés
- `communes_geocodees` : Nombre de communes géocodées avec succès

#### Étape 9 : Finalisation (finaliser_importation)

**Fichier** : `ingest/importation_service.py`

**Transaction Atomique** (tout ou rien) :
```python
@transaction.atomic
def finaliser_importation(self, importation_id):
    importation = ImportationEnCours.objects.select_for_update().get(id=importation_id)

    # 1. VALIDATIONS BLOQUANTES
    if not importation.espece_candidate or not importation.espece_candidate.espece_validee:
        → importation.statut = 'erreur'
        → return False, "Espèce non validée"

    if not importation.observateur:
        → importation.statut = 'erreur'
        → return False, "Observateur non trouvé"

    # 2. EXTRACTION DONNÉES
    donnees = importation.transcription.json_brut
    annee = donnees['informations_generales'].get('annee') or timezone.now().year

    # 3. CRÉATION FICHE OBSERVATION
    fiche = FicheObservation.objects.create(
        observateur=importation.observateur,
        espece=importation.espece_candidate.espece_validee,
        annee=annee,
        chemin_image=...,  # Extrait du nom de fichier
        chemin_json=...,   # Extrait du nom de fichier
        transcription=True  # Marque comme issu d'OCR
    )

    # 4. CRÉATION OBJETS LIÉS (auto-créés)

    # 4.1 Localisation
    localisation = Localisation.objects.create(
        fiche=fiche,
        commune=donnees['localisation'].get('commune'),
        code_insee=...,  # Récupéré via géocodage
        departement=donnees['localisation'].get('dep_t'),
        lieu_dit=donnees['localisation'].get('coordonnees_et_ou_lieu_dit'),
        altitude=donnees['localisation'].get('altitude'),
        latitude=...,    # Récupéré via géocodage
        longitude=...,   # Récupéré via géocodage
        source_coordonnees='geocodage_auto',
        precision_gps='commune'
    )

    # 4.2 Nid
    nid = Nid.objects.create(
        fiche=fiche,
        hauteur_nid=donnees['nid'].get('haut_nid'),
        hauteur_sol_vegetation=donnees['nid'].get('h_c_vert'),
        nid_precedent_meme_couple=donnees['nid'].get('nid_prec_t_meme_c_ple'),
        description=donnees['nid'].get('nid')
    )

    # 4.3 Observations (multiple)
    for obs_data in donnees['tableau_donnees']:
        try:
            Observation.objects.create(
                fiche=fiche,
                date=construct_date(obs_data['Jour'], obs_data['Mois'], annee),
                heure=obs_data.get('Heure'),
                nombre_oeufs=obs_data.get('Nombre_oeuf'),
                nombre_poussins=obs_data.get('Nombre_pou'),
                observations=obs_data.get('observations')
            )
        except (ValueError, KeyError) as e:
            # Entrée invalide → skip, log warning
            logger.warning(f"Observation invalide ignorée: {e}")
            continue

    # 4.4 ResumeObservation (avec auto-correction contraintes)
    resume_data = donnees['tableau_donnees_2']
    nombre_oeufs = resume_data['nombre_oeufs']
    nombre_poussins = resume_data['nombre_poussins']

    # Auto-correction logique
    pondus = nombre_oeufs.get('pondus') or 0
    eclos = nombre_oeufs.get('eclos') or 0
    volants = int(nombre_poussins.get('vol_t') or 0)

    # Contrainte: volants <= eclos <= pondus
    if volants > eclos:
        logger.warning(f"Correction: {volants} volants > {eclos} éclos → ajustement")
        eclos = volants
    if eclos > pondus:
        logger.warning(f"Correction: {eclos} éclos > {pondus} pondus → ajustement")
        pondus = eclos

    ResumeObservation.objects.create(
        fiche=fiche,
        oeufs_pondus=pondus,
        oeufs_eclos=eclos,
        poussins_volants=volants,
        # ... autres champs
    )

    # 4.5 CausesEchec
    if donnees['causes_echec'].get('causes_d_echec'):
        CausesEchec.objects.create(
            fiche=fiche,
            cause=donnees['causes_echec']['causes_d_echec']
        )

    # 4.6 Remarque (optionnel)
    if donnees.get('remarque'):
        Remarque.objects.create(
            fiche=fiche,
            texte=donnees['remarque']
        )

    # 4.7 EtatCorrection (pour workflow de correction)
    EtatCorrection.objects.create(
        fiche=fiche,
        statut='en_cours'  # Prêt pour relecture manuelle
    )

    # 5. MISE À JOUR IMPORTATION
    importation.fiche_observation = fiche
    importation.statut = 'complete'
    importation.save()

    return True, f"Fiche {fiche.id} créée avec succès"
```

**Gestion des Erreurs en Finalisation** :
| Erreur | Action | Statut | Rollback |
|--------|--------|--------|----------|
| Espèce non validée | Bloque | erreur | N/A (pas créé) |
| Observateur manquant | Bloque | erreur | N/A (pas créé) |
| Contrainte BD violée | Auto-correction si possible | Logs | Continue |
| Exception transaction | Annule tout | erreur | OUI (atomique) |
| Géocodage échoué | Utilise nom brut | Warning | Continue |

### 2.3 Détail des Étapes Manuelles

#### 🚫 Étape 6 : Validation des Espèces (BLOQUANTE)

**Fichier** : `ingest/views/especes.py`

**Pourquoi c'est manuel** :
- Auto-matching peut échouer (score < 0.8)
- Variantes orthographiques : "Gravelot à collier" vs "Gravelot à coll�er" (OCR)
- Noms vernaculaires multiples : "Mésange charbonnière" = "Parus major"
- Nouvelles espèces non en base

**Interface** :
```
┌─────────────────────────────────────────────────────────────┐
│ Espèces Candidates                                          │
├─────────────────────────────────────────────────────────────┤
│ Nom Transcrit          | Score | Espèce Validée | Action    │
├─────────────────────────────────────────────────────────────┤
│ Gobemouche gris        | 100%  | Gobemouche gris | ✓ Validé │
│ Gravelot à coll�er     | 75%   | [À valider]     | [SELECT] │
│ LINOTTE                | 68%   | [À valider]     | [SELECT] │
└─────────────────────────────────────────────────────────────┘
```

**Actions disponibles** :
- Lier à une espèce existante (dropdown avec recherche)
- Créer nouvelle espèce si inexistante
- Validation en masse (si score ≥ seuil)

**Impact si non validé** :
→ Impossible de finaliser l'importation (erreur bloquante)

#### 🚫 Étape 9 : Finalisation (ACTION MANUELLE)

**Pourquoi c'est manuel** :
- Bouton "Finaliser" à cliquer pour chaque ImportationEnCours
- Ou sélection multiple + "Finaliser les importations sélectionnées"

**Interface** :
```
┌─────────────────────────────────────────────────────────────┐
│ Importations En Attente                                     │
├─────────────────────────────────────────────────────────────┤
│ [✓] ID 123 | Gobemouche gris | Alexandre Delasalle | ✓     │
│ [✓] ID 124 | Accenteur mouchet | ALE | ✓                   │
│ [ ] ID 125 | Moineau domestique | C. JACOB | ✗ (erreur)    │
├─────────────────────────────────────────────────────────────┤
│ [Finaliser les sélectionnées]                               │
└─────────────────────────────────────────────────────────────┘
```

**Pourquoi ce n'est pas automatique** :
- Permet revue optionnelle avant création en base
- Contrôle qualité pré-finalisation
- Historiquement conçu pour validation humaine

---

## 3. Points de Blocage pour le Passage à l'Échelle

### 3.1 Interventions Manuelles Obligatoires

| Étape | Type | Fréquence | Impact sur Scalabilité |
|-------|------|-----------|------------------------|
| **1. Sélection répertoires OCR** | Navigation UI | Par batch | ⚠️ Moyen - automatisable |
| **2. Lancement transcription** | Clic bouton | Par batch | ⚠️ Moyen - automatisable |
| **4. Import JSON** | Sélection répertoire | Par batch | ⚠️ Moyen - automatisable |
| **5. Extraction candidats** | Clic bouton | Par batch | ⚠️ Moyen - automatisable |
| **6. Validation espèces** | Revue manuelle | **Par espèce unique** | 🔴 **CRITIQUE** - bloquant |
| **7. Préparation importations** | Clic bouton | Par batch | ⚠️ Moyen - automatisable |
| **9. Finalisation** | Clic bouton | **Par fiche** | 🔴 **CRITIQUE** - bloquant |

### 3.2 Analyse de l'Impact

#### 🔴 Validation des Espèces (Étape 6)

**Volume estimé** :
- 50 000 fiches × ~150 espèces différentes = ~150 espèces candidates uniques
- Auto-match à 80% = ~30 espèces à valider manuellement
- Temps : ~2 min/espèce = **~1 heure de travail manuel**

**Impact** : ✅ **Gérable** avec l'automatisation actuelle

**Mais** : Bloque le processus → nécessite intervention avant finalisation

#### 🔴 Finalisation des Importations (Étape 9)

**Volume estimé** :
- 50 000 fiches × 1 clic = **50 000 clics** (ou sélection en masse)
- Temps : ~2 sec/fiche en masse = **~28 heures de clics**

**Impact** : 🔴 **INACCEPTABLE** pour passage à l'échelle

**Solution requise** : Finalisation automatique en masse

### 3.3 Goulots d'Étranglement Techniques

#### 3.3.1 Performance OCR (Gemini API)

**Limites actuelles** :
- Rate limit : 60 requêtes/minute
- Timeout : 120 secondes/image
- Retry : 3 tentatives max

**Calcul pour 50 000 images** :
```
Temps théorique minimum (60 req/min) :
50 000 images ÷ 60 images/min = 833 minutes = ~14 heures

Temps réel avec retries et erreurs (~10% échec) :
14 heures × 1.3 (overhead) = ~18 heures
```

**Conclusion** : ✅ Acceptable (peut tourner en arrière-plan sur 24-48h)

#### 3.3.2 Performance Base de Données (Finalisation)

**Volume par fiche finalisée** :
- 1 FicheObservation
- 1 Localisation (avec géocodage)
- 1 Nid
- ~5-10 Observation (moyenne)
- 1 ResumeObservation
- ~0.5 CausesEchec (si applicable)
- ~0.3 Remarque (si applicable)
- 1 EtatCorrection

**Total** : ~10-15 INSERT par fiche

**Calcul pour 50 000 fiches** :
```
50 000 fiches × 12 INSERT/fiche = 600 000 INSERT

Avec PostgreSQL optimisé :
- Bulk insert : ~5000 INSERT/sec
- Transaction par fiche : ~100 fiches/sec

Temps estimé :
- Bulk : 600 000 ÷ 5000 = 120 secondes = 2 minutes
- Séquentiel : 50 000 ÷ 100 = 500 secondes = 8 minutes
```

**Conclusion** : ✅ Performance BD non limitante

#### 3.3.3 Géocodage API (Google Maps / IGN)

**Limites** :
- Google Maps : ~50 requêtes/sec (avec clé API payante)
- IGN : ~10 requêtes/sec (gratuit)

**Volume** :
- 50 000 fiches × 1 géocodage/fiche = 50 000 requêtes
- Beaucoup de communes en double → cache efficace

**Optimisation avec cache** :
```
Communes uniques en France : ~35 000
Communes dans fiches : ~500 (estimation)
Cache hit rate : ~99% après 500 premières

Temps :
- 500 nouvelles communes ÷ 10 req/sec = 50 secondes
- Cache pour le reste = instantané
```

**Conclusion** : ✅ Géocodage non limitant avec cache

---

## 4. Architecture Proposée pour l'Automatisation

### 4.1 Principe Directeur

**Pipeline Entièrement Automatisé** :
```
Images → OCR → JSON → Import → Extraction → Validation Auto → Finalisation Auto → Base de Données
         ↓                                           ↓                    ↓
     Celery Task                              Auto-Matching         Bulk Processing
                                              (threshold 0.7)      (transaction/batch)
```

**Intervention humaine** : Uniquement APRÈS finalisation, pour relecture des fiches en base

### 4.2 Architecture Détaillée

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 1 : PRÉPARATION DES IMAGES                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │  1.1 Scan automatique du répertoire media/           │
        │      - Détection récursive de toutes les images      │
        │      - Filtrage par extension (.jpg, .png)           │
        │      - Groupement par répertoire                      │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  1.2 Détection du type de fiche                      │
        │      - Analyse du chemin (regex: ancien/Ancien)      │
        │      - Attribution du prompt approprié                │
        │      - Tag metadata dans PreparationImage            │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2 : TRANSCRIPTION OCR BATCH                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────────────────────────────────┐
        │  2.1 Lancement automatique Celery                    │
        │      - Queue : high_priority (OCR)                   │
        │      - Concurrency : 10 workers parallèles           │
        │      - Modèle : gemini-2.5-flash-lite (rapide)       │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  2.2 Traitement parallèle avec gestion d'erreurs     │
        │      - Timeout : 120s avec retry exponentiel         │
        │      - Rate limiting : 60 req/min auto-throttle      │
        │      - Validation JSON + auto-correction             │
        │      - Sauvegarde _result.json + _raw.json           │
        │      - Création TranscriptionOCR (métadonnées)       │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  2.3 Monitoring et alertes                           │
        │      - Dashboard temps réel (Celery Flower)          │
        │      - Alertes si taux d'échec > 5%                  │
        │      - Logs détaillés des erreurs                     │
        └───────────────────────────────────────────────────────┘
                                    │
                    JSON Files prêts │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 3 : IMPORT AUTOMATIQUE                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────────────────────────────────┐
        │  3.1 Détection automatique nouveaux JSON             │
        │      - Watcher filesystem (watchdog library)         │
        │      - OU Cron job toutes les 5 minutes              │
        │      - Filtre : *_result.json non importés           │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  3.2 Import batch TranscriptionBrute                 │
        │      - Bulk create (500 fiches/batch)                │
        │      - Skip duplicates (check fichier_source)        │
        │      - Transaction par batch                          │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  3.3 Extraction automatique candidats                │
        │      - Trigger automatique après import              │
        │      - Extraction espèces + auto-matching            │
        │      - Création utilisateurs automatique              │
        │      - Géocodage avec cache (Redis)                  │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4 : VALIDATION INTELLIGENTE                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────────────────────────────────┐
        │  4.1 Auto-validation des espèces                     │
        │      - Seuil abaissé : 0.7 (au lieu de 0.8)          │
        │      - Validation automatique si score ≥ 0.7         │
        │      - Flag pour revue manuelle si score < 0.7       │
        │      - Machine learning : amélioration du matching   │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  4.2 Dictionnaire d'équivalences                     │
        │      - Table : EspeceEquivalence                     │
        │      - Mapping : "LINOTTE" → "Linotte mélodieuse"    │
        │      - Apprentissage : sauvegarde validations manu.  │
        │      - Auto-application des équivalences connues     │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  4.3 File d'attente de validation manuelle           │
        │      - Queue : species_to_validate                   │
        │      - Filtrage : score < 0.7                        │
        │      - Priorisation : espèces fréquentes en premier  │
        │      - Interface dédiée pour validation rapide       │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 5 : FINALISATION AUTOMATIQUE                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────────────────────────────────┐
        │  5.1 Trigger automatique de finalisation             │
        │      - Condition : espece_validee IS NOT NULL        │
        │      - Celery task : auto_finalize_importations      │
        │      - Fréquence : toutes les 10 minutes             │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  5.2 Finalisation en batch                           │
        │      - Sélection : ImportationEnCours (en_attente)   │
        │      - Batch size : 100 fiches/transaction           │
        │      - Transaction atomique par batch                 │
        │      - Rollback si erreur dans le batch              │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  5.3 Gestion des erreurs de finalisation             │
        │      - Retry 3x avec backoff si erreur technique     │
        │      - Marquage 'erreur' si échec définitif          │
        │      - Alerte email/Slack pour erreurs persistantes  │
        │      - Dead letter queue pour analyse manuelle       │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 6 : CONTRÔLE QUALITÉ POST-IMPORT               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────────────────────────────────┐
        │  6.1 Marquage EtatCorrection                         │
        │      - Toutes fiches : statut='en_cours'             │
        │      - Prêtes pour relecture humaine                  │
        │      - Interface de correction existante (no change) │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  6.2 Scoring automatique de confiance                │
        │      - Score OCR : qualité JSON (0-100)              │
        │      - Score espèce : similarité auto-match          │
        │      - Score global : moyenne pondérée               │
        │      - Priorisation relecture : score faible d'abord │
        └───────────────────────────────────────────────────────┘
                                    │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  6.3 Dashboard de monitoring                          │
        │      - Taux de réussite par étape                    │
        │      - Distribution des scores de confiance          │
        │      - Espèces problématiques récurrentes            │
        │      - Temps de traitement moyen                      │
        └───────────────────────────────────────────────────────┘
                                    │
                Fiches en base, prêtes pour relecture │
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │  INTERVENTION HUMAINE : Relecture et validation      │
        │  - Interface : view_transcription (existante)        │
        │  - Priorisation : fiches score < 80                  │
        │  - Correction manuelle si nécessaire                  │
        │  - Validation finale : statut='valide'               │
        └───────────────────────────────────────────────────────┘
```

### 4.3 Composants à Développer

#### 4.3.1 Watcher Filesystem (Nouveau)

**Fichier** : `pilot/watcher.py`

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class JSONWatcher(FileSystemEventHandler):
    """
    Surveille media/transcription_results/ pour nouveaux JSON
    Déclenche import automatique
    """

    def on_created(self, event):
        if event.src_path.endswith('_result.json'):
            # Déclenche import_json_auto.delay(event.src_path)
            pass

def start_watcher():
    observer = Observer()
    observer.schedule(JSONWatcher(), path="media/transcription_results", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

**Alternative** : Cron job Django (`django-cron` ou Celery Beat)

```python
# ingest/tasks.py
from celery import shared_task

@shared_task
def auto_import_new_json():
    """
    Cron : toutes les 5 minutes
    Scanne transcription_results/ pour nouveaux JSON
    """
    base_dir = settings.MEDIA_ROOT / 'transcription_results'

    for json_file in base_dir.rglob('*_result.json'):
        if not TranscriptionBrute.objects.filter(fichier_source=json_file.name).exists():
            # Import automatique
            ImportationService().importer_fichier_json(json_file)
```

#### 4.3.2 Auto-Finalisation Celery (Nouveau)

**Fichier** : `ingest/tasks.py`

```python
@shared_task
def auto_finalize_pending_importations():
    """
    Cron : toutes les 10 minutes
    Finalise toutes ImportationEnCours (en_attente) avec espèce validée
    """
    service = ImportationService()

    # Sélection des importations prêtes
    pending = ImportationEnCours.objects.filter(
        statut='en_attente',
        espece_candidate__espece_validee__isnull=False,
        observateur__isnull=False
    )

    results = {
        'success': 0,
        'errors': 0,
        'error_details': []
    }

    # Finalisation en batch de 100
    for batch in chunked(pending, 100):
        for importation in batch:
            try:
                success, message = service.finaliser_importation(importation.id)
                if success:
                    results['success'] += 1
                else:
                    results['errors'] += 1
                    results['error_details'].append({
                        'id': importation.id,
                        'error': message
                    })
            except Exception as e:
                results['errors'] += 1
                results['error_details'].append({
                    'id': importation.id,
                    'error': str(e)
                })
                logger.error(f"Auto-finalization error for {importation.id}: {e}")

    # Alerte si taux d'erreur > 10%
    if results['errors'] / (results['success'] + results['errors']) > 0.1:
        send_alert_email(
            subject="Taux d'erreur élevé dans auto-finalisation",
            body=f"Erreurs : {results['errors']}, Succès : {results['success']}\n"
                 f"Détails : {results['error_details']}"
        )

    return results
```

#### 4.3.3 Table EspeceEquivalence (Nouveau modèle)

**Fichier** : `ingest/models.py`

```python
class EspeceEquivalence(models.Model):
    """
    Dictionnaire d'apprentissage pour matching espèces
    Sauvegarde les validations manuelles pour réutilisation
    """
    nom_transcrit = models.CharField(max_length=200, unique=True, db_index=True)
    espece_validee = models.ForeignKey('taxonomy.Espece', on_delete=models.CASCADE)
    score_confiance = models.FloatField(default=100.0)  # 100 = validation manuelle
    nombre_utilisations = models.IntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_utilisation = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ingest_espece_equivalence'
        verbose_name = "Équivalence d'espèce"
        indexes = [
            models.Index(fields=['nom_transcrit']),
        ]

    def __str__(self):
        return f"{self.nom_transcrit} → {self.espece_validee.nom_commun}"
```

**Utilisation dans auto-matching** :

```python
def _trouver_correspondance_espece_amelioree(self, espece_candidate):
    """
    Auto-matching amélioré avec apprentissage
    1. Cherche dans EspeceEquivalence (exact match)
    2. SequenceMatcher avec threshold 0.7 (au lieu de 0.8)
    3. Machine learning (optionnel, phase 2)
    """
    nom_transcrit = espece_candidate.nom_transcrit

    # 1. Exact match dans dictionnaire
    equivalence = EspeceEquivalence.objects.filter(nom_transcrit__iexact=nom_transcrit).first()
    if equivalence:
        espece_candidate.espece_validee = equivalence.espece_validee
        espece_candidate.score_similarite = equivalence.score_confiance
        espece_candidate.save()

        # Incrémenter compteur d'utilisation
        equivalence.nombre_utilisations += 1
        equivalence.save()
        return True

    # 2. SequenceMatcher avec threshold abaissé
    meilleure_correspondance = None
    meilleur_score = 0

    for espece in Espece.objects.all():
        score_commun = SequenceMatcher(None, nom_transcrit.lower(), espece.nom_commun.lower()).ratio()
        score_sci = SequenceMatcher(None, nom_transcrit.lower(), espece.nom_scientifique.lower()).ratio()
        score = max(score_commun, score_sci)

        if score > meilleur_score:
            meilleur_score = score
            meilleure_correspondance = espece

    # Threshold abaissé à 0.7 pour automatisation
    if meilleur_score >= 0.7:
        espece_candidate.espece_validee = meilleure_correspondance
        espece_candidate.score_similarite = round(meilleur_score * 100, 1)
        espece_candidate.save()

        # Créer équivalence pour apprentissage
        EspeceEquivalence.objects.get_or_create(
            nom_transcrit=nom_transcrit,
            defaults={
                'espece_validee': meilleure_correspondance,
                'score_confiance': espece_candidate.score_similarite
            }
        )
        return True

    # Score < 0.7 → validation manuelle requise
    return False
```

#### 4.3.4 Système de Scoring de Confiance (Nouveau)

**Fichier** : `ingest/models.py` (ajout de champs)

```python
class ImportationEnCours(models.Model):
    # ... champs existants ...

    # NOUVEAUX CHAMPS
    score_ocr = models.FloatField(null=True, blank=True)  # Qualité JSON (0-100)
    score_espece = models.FloatField(null=True, blank=True)  # Score auto-match
    score_confiance_global = models.FloatField(null=True, blank=True)  # Moyenne pondérée

    def calculer_score_confiance(self):
        """
        Calcule un score de confiance global
        score_ocr : 40% (qualité JSON)
        score_espece : 60% (matching espèce)
        """
        if not self.score_ocr or not self.score_espece:
            return None

        score = (self.score_ocr * 0.4) + (self.score_espece * 0.6)
        self.score_confiance_global = round(score, 1)
        self.save()
        return score
```

**Calcul score OCR** :

```python
def calculer_score_ocr(json_data):
    """
    Évalue la qualité du JSON OCR
    - Champs obligatoires remplis : +10 points chacun
    - Pas d'erreurs de validation : +30 points
    - Dates cohérentes : +10 points
    - Nombres valides : +10 points
    """
    score = 0

    # Champs obligatoires (6 × 10 = 60 points)
    required_fields = [
        ('informations_generales', 'espece'),
        ('informations_generales', 'observateur'),
        ('informations_generales', 'annee'),
        ('localisation', 'commune'),
        ('tableau_donnees', None),  # Au moins une observation
        ('nid', 'nid')
    ]

    for section, field in required_fields:
        if section in json_data:
            if field is None:
                if json_data[section]:
                    score += 10
            elif field in json_data[section] and json_data[section][field]:
                score += 10

    # Pas d'erreurs de validation (+30 points)
    erreurs = validate_json_structure(json_data)
    if not erreurs:
        score += 30

    # Cohérence des dates (+10 points)
    if 'tableau_donnees' in json_data and json_data['tableau_donnees']:
        dates_valides = all(
            1 <= obs.get('Jour', 0) <= 31 and 1 <= obs.get('Mois', 0) <= 12
            for obs in json_data['tableau_donnees']
        )
        if dates_valides:
            score += 10

    return min(score, 100)  # Cap à 100
```

#### 4.3.5 Dashboard de Monitoring (Nouveau)

**Fichier** : `ingest/views/monitoring.py`

```python
@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard_automatisation(request):
    """
    Dashboard de suivi du pipeline automatisé
    """
    # Métriques globales
    total_transcriptions = TranscriptionBrute.objects.count()
    transcriptions_24h = TranscriptionBrute.objects.filter(
        date_creation__gte=timezone.now() - timedelta(hours=24)
    ).count()

    # Métriques d'importation
    importations_pending = ImportationEnCours.objects.filter(statut='en_attente').count()
    importations_complete_24h = ImportationEnCours.objects.filter(
        statut='complete',
        date_finalisation__gte=timezone.now() - timedelta(hours=24)
    ).count()
    importations_erreur = ImportationEnCours.objects.filter(statut='erreur').count()

    # Métriques d'auto-matching
    especes_auto_validees = EspeceCandidate.objects.filter(
        espece_validee__isnull=False,
        validation_manuelle=False
    ).count()
    especes_validation_manuelle = EspeceCandidate.objects.filter(
        espece_validee__isnull=True
    ).count()

    # Distribution des scores de confiance
    scores_distribution = ImportationEnCours.objects.filter(
        score_confiance_global__isnull=False
    ).aggregate(
        score_moyen=Avg('score_confiance_global'),
        score_min=Min('score_confiance_global'),
        score_max=Max('score_confiance_global')
    )

    # Espèces problématiques (fréquentes mais score faible)
    especes_problematiques = EspeceCandidate.objects.filter(
        score_similarite__lt=70
    ).values('nom_transcrit').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Taux de réussite par étape
    taux_reussite_ocr = (
        (total_transcriptions - TranscriptionOCR.objects.filter(erreur__isnull=False).count())
        / total_transcriptions * 100
        if total_transcriptions > 0 else 0
    )

    taux_finalisation = (
        ImportationEnCours.objects.filter(statut='complete').count()
        / ImportationEnCours.objects.count() * 100
        if ImportationEnCours.objects.count() > 0 else 0
    )

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_24h': transcriptions_24h,
        'importations_pending': importations_pending,
        'importations_complete_24h': importations_complete_24h,
        'importations_erreur': importations_erreur,
        'especes_auto_validees': especes_auto_validees,
        'especes_validation_manuelle': especes_validation_manuelle,
        'scores_distribution': scores_distribution,
        'especes_problematiques': especes_problematiques,
        'taux_reussite_ocr': round(taux_reussite_ocr, 1),
        'taux_finalisation': round(taux_finalisation, 1),
    }

    return render(request, 'ingest/dashboard_automatisation.html', context)
```

---

## 5. Stratégie de Gestion des Erreurs

### 5.1 Typologie des Erreurs

| Type d'Erreur | Fréquence | Stratégie | Action Automatique |
|---------------|-----------|-----------|-------------------|
| **OCR - Timeout API** | 5-10% | Retry 3x avec backoff | Skip si échec total |
| **OCR - JSON invalide** | 2-5% | Auto-correction | Sauvegarde raw + corrigé |
| **Import - Espèce inconnue** | 1-3% | Auto-match ou queue | Validation manuelle si score < 0.7 |
| **Import - Commune inconnue** | 5-10% | Utilise nom brut | Log pour amélioration géocodeur |
| **Finalisation - Contrainte BD** | <1% | Auto-correction logique | Log + ajustement (ex: œufs/poussins) |
| **Finalisation - Transaction fail** | <1% | Rollback + retry | 3 tentatives, puis erreur définitive |

### 5.2 Niveaux de Criticité

#### 🟢 Niveau 1 : Auto-Récupérable (pas d'intervention)

**Exemples** :
- Timeout API avec retry réussi
- JSON corrigé automatiquement
- Commune géocodée au 2e essai
- Contraintes BD auto-corrigées

**Action** : Log informatif, continue

#### 🟡 Niveau 2 : Dégradé (fonctionne mais qualité réduite)

**Exemples** :
- OCR échoué après 3 retries → image sautée
- Géocodage échoué → utilise nom brut
- Auto-match espèce < 0.7 → validation manuelle requise

**Action** : Log warning, marque pour revue, continue

#### 🔴 Niveau 3 : Bloquant (intervention requise)

**Exemples** :
- Taux d'échec OCR > 20% (problème API Gemini)
- Transaction BD échoue 3x de suite (problème infrastructure)
- Espace disque plein

**Action** : Alerte email/Slack, arrêt du pipeline

### 5.3 Dead Letter Queue (DLQ)

**Pour les erreurs persistantes** :

```python
# ingest/models.py
class ImportationErreur(models.Model):
    """
    File d'attente des erreurs non récupérables
    Nécessite intervention manuelle
    """
    importation = models.ForeignKey(ImportationEnCours, on_delete=models.CASCADE)
    type_erreur = models.CharField(max_length=50, choices=[
        ('espece_invalide', 'Espèce non validée'),
        ('transaction_failed', 'Transaction échouée'),
        ('data_corruption', 'Données corrompues'),
        ('constraint_violation', 'Violation de contrainte'),
    ])
    message_erreur = models.TextField()
    tentatives = models.IntegerField(default=0)
    date_derniere_tentative = models.DateTimeField(auto_now=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    resolu = models.BooleanField(default=False)

    class Meta:
        db_table = 'ingest_importation_erreur'
        ordering = ['-date_creation']
```

**Processus de récupération** :

```python
@shared_task
def retry_failed_importations():
    """
    Cron : toutes les heures
    Retente les importations en erreur (max 3 tentatives)
    """
    erreurs = ImportationErreur.objects.filter(
        resolu=False,
        tentatives__lt=3
    )

    for erreur in erreurs:
        erreur.tentatives += 1
        erreur.save()

        try:
            service = ImportationService()
            success, message = service.finaliser_importation(erreur.importation.id)

            if success:
                erreur.resolu = True
                erreur.save()
                logger.info(f"Erreur {erreur.id} résolue après {erreur.tentatives} tentatives")
        except Exception as e:
            logger.error(f"Retry failed for erreur {erreur.id}: {e}")

            # Alerte si 3 tentatives échouées
            if erreur.tentatives >= 3:
                send_alert_email(
                    subject=f"Importation {erreur.importation.id} en échec définitif",
                    body=f"Type : {erreur.type_erreur}\nMessage : {erreur.message_erreur}"
                )
```

### 5.4 Système d'Alertes

**Configuration alertes** :

```python
# settings.py
ALERTING_CONFIG = {
    'email': {
        'enabled': True,
        'recipients': ['admin@observation-nids.fr'],
        'thresholds': {
            'ocr_failure_rate': 0.20,  # >20% échec OCR
            'finalization_failure_rate': 0.10,  # >10% échec finalisation
            'pending_manual_validation': 50,  # >50 espèces en attente
        }
    },
    'slack': {
        'enabled': True,
        'webhook_url': 'https://hooks.slack.com/...',
        'channels': {
            'critical': '#alerts-critical',
            'warning': '#alerts-warning',
            'info': '#pipeline-status'
        }
    }
}
```

**Alertes déclenchées** :

| Condition | Canal | Niveau |
|-----------|-------|--------|
| Taux échec OCR > 20% | Email + Slack | 🔴 Critical |
| Taux échec finalisation > 10% | Email + Slack | 🔴 Critical |
| > 50 espèces en attente validation | Slack | 🟡 Warning |
| Pipeline bloqué > 1h | Email + Slack | 🔴 Critical |
| Espace disque < 10% | Email + Slack | 🔴 Critical |
| Import réussi (batch) | Slack | 🟢 Info |

---

## 6. Feuille de Route d'Implémentation

### 6.1 Phase 1 : Automatisation de Base (2-3 semaines)

**Objectif** : Éliminer les clics manuels, conserver validation espèces

#### Sprint 1.1 : Watcher et Import Auto (1 semaine)

**Tâches** :
1. Développer `JSONWatcher` ou Cron job `auto_import_new_json`
2. Modifier `ImportationService.importer_fichiers_json()` pour supporter batch
3. Ajouter trigger automatique `extraire_candidats()` après import
4. Tests unitaires + intégration

**Livrables** :
- ✅ JSON détectés automatiquement
- ✅ TranscriptionBrute créées automatiquement
- ✅ Espèces et utilisateurs extraits automatiquement

#### Sprint 1.2 : Auto-Finalisation (1 semaine)

**Tâches** :
1. Développer Celery task `auto_finalize_pending_importations()`
2. Configurer Celery Beat (cron toutes les 10 min)
3. Ajouter gestion d'erreurs robuste avec retry
4. Tests de charge (100, 1000, 10000 fiches)

**Livrables** :
- ✅ Finalisation automatique des ImportationEnCours valides
- ✅ Gestion des erreurs avec retry
- ✅ Performance validée jusqu'à 10k fiches/jour

#### Sprint 1.3 : Monitoring et Alertes (1 semaine)

**Tâches** :
1. Développer `dashboard_automatisation()`
2. Créer modèle `ImportationErreur` (DLQ)
3. Configurer alertes email + Slack
4. Documentation utilisateur

**Livrables** :
- ✅ Dashboard temps réel du pipeline
- ✅ Alertes configurées
- ✅ DLQ opérationnelle

**Résultat Phase 1** :
→ Pipeline automatisé SAUF validation espèces (reste manuelle)
→ Capacité : ~10 000 fiches/jour

---

### 6.2 Phase 2 : Auto-Matching Intelligent (2-3 semaines)

**Objectif** : Réduire à <5% le besoin de validation manuelle d'espèces

#### Sprint 2.1 : Dictionnaire d'Équivalences (1 semaine)

**Tâches** :
1. Créer modèle `EspeceEquivalence`
2. Migrer validations manuelles existantes vers équivalences
3. Modifier `_trouver_correspondance_espece()` pour utiliser dictionnaire
4. Interface admin pour gérer équivalences

**Livrables** :
- ✅ Exact match via dictionnaire
- ✅ Apprentissage des validations manuelles
- ✅ Réutilisation automatique

#### Sprint 2.2 : Amélioration Auto-Matching (1 semaine)

**Tâches** :
1. Abaisser threshold à 0.7 (au lieu de 0.8)
2. Ajouter fuzzy matching (Levenshtein distance)
3. Gérer variantes orthographiques ("Mésange" vs "Mesange")
4. Tests avec dataset réel

**Livrables** :
- ✅ Taux d'auto-match > 95%
- ✅ Faux positifs < 2%

#### Sprint 2.3 : Machine Learning (Optionnel - 1 semaine)

**Tâches** :
1. Entraîner modèle de classification (scikit-learn ou TensorFlow)
2. Features : nom transcrit, contexte (localisation, date)
3. Intégration dans pipeline
4. Monitoring précision

**Livrables** :
- ✅ Modèle ML opérationnel (si ROI positif)
- ✅ Taux d'auto-match > 98%

**Résultat Phase 2** :
→ Validation manuelle < 5% des espèces
→ Pipeline quasi-totalement automatisé

---

### 6.3 Phase 3 : Optimisation et Scaling (1-2 semaines)

**Objectif** : Supporter 50 000+ fiches sans dégradation

#### Sprint 3.1 : Performance OCR (1 semaine)

**Tâches** :
1. Parallélisation accrue (20 workers au lieu de 10)
2. Optimisation rate limiting Gemini
3. Cache Redis pour prompts et configs
4. Monitoring Celery avec Flower

**Livrables** :
- ✅ Throughput OCR doublé
- ✅ Temps traitement 50k images : <24h

#### Sprint 3.2 : Performance Base de Données (1 semaine)

**Tâches** :
1. Bulk insert pour TranscriptionBrute (500/batch)
2. Bulk create pour Observations (éviter N+1 queries)
3. Index BD optimisés (fichier_source, statut, date_creation)
4. Connection pooling PostgreSQL

**Livrables** :
- ✅ Finalisation 1000 fiches/min
- ✅ Temps finalisation 50k fiches : <1h

**Résultat Phase 3** :
→ 50 000 fiches traitées en <30h (OCR + import)
→ Performance stable jusqu'à 100k fiches

---

### 6.4 Phase 4 : Système de Scoring et Priorisation (1 semaine)

**Objectif** : Prioriser la relecture humaine sur les fiches douteuses

#### Sprint 4.1 : Scoring de Confiance

**Tâches** :
1. Ajouter champs `score_ocr`, `score_espece`, `score_confiance_global`
2. Implémenter `calculer_score_ocr()` et `calculer_score_confiance()`
3. Calcul automatique lors de finalisation
4. Interface de tri par score

**Livrables** :
- ✅ Chaque fiche a un score de confiance (0-100)
- ✅ Interface de relecture priorisée (score < 80 en premier)

**Résultat Phase 4** :
→ Relecture humaine efficace (focus sur 20% de fiches à faible score)
→ Validation rapide des 80% haute qualité

---

### 6.5 Calendrier Global

```
Semaine 1-3   : Phase 1 - Automatisation de Base
                ├─ S1 : Watcher + Import Auto
                ├─ S2 : Auto-Finalisation
                └─ S3 : Monitoring + Alertes

Semaine 4-6   : Phase 2 - Auto-Matching Intelligent
                ├─ S4 : Dictionnaire Équivalences
                ├─ S5 : Amélioration Matching
                └─ S6 : ML (optionnel)

Semaine 7-8   : Phase 3 - Optimisation Scaling
                ├─ S7 : Performance OCR
                └─ S8 : Performance BD

Semaine 9     : Phase 4 - Scoring et Priorisation

Semaine 10    : Tests de charge, Documentation, Déploiement
```

**Durée totale** : 10 semaines (2,5 mois)

**Effort estimé** :
- 1 développeur full-time : 10 semaines
- OU 2 développeurs : 5-6 semaines

---

### 6.6 Risques et Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|-----------|
| **Gemini API rate limit** | Moyenne | 🔴 Élevé | Négocier quota élevé, backup avec modèle local |
| **Faux positifs auto-matching** | Faible | 🟡 Moyen | Threshold conservateur 0.7, revue périodique |
| **Performance BD dégradée** | Faible | 🔴 Élevé | Tests de charge préalables, scaling horizontal |
| **Complexité maintenance** | Moyenne | 🟡 Moyen | Documentation exhaustive, monitoring proactif |
| **Bugs en production** | Moyenne | 🔴 Élevé | Tests end-to-end, déploiement progressif (10%, 50%, 100%) |

---

## 7. Métriques de Succès

### 7.1 KPIs de Performance

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| **Throughput OCR** | >2000 images/heure | Images traitées/heure |
| **Taux de réussite OCR** | >95% | (Images OK / Images totales) × 100 |
| **Throughput finalisation** | >1000 fiches/heure | Fiches finalisées/heure |
| **Temps total 50k fiches** | <30 heures | De l'image à la BD |

### 7.2 KPIs de Qualité

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| **Taux auto-matching espèces** | >95% | Espèces validées auto / Espèces totales |
| **Taux de faux positifs** | <2% | Espèces corrigées manuellement / Auto-validées |
| **Score confiance moyen** | >85 | Moyenne des scores de confiance |
| **Taux d'erreurs bloquantes** | <1% | Importations en erreur définitive / Total |

### 7.3 KPIs d'Automatisation

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| **Taux d'automatisation** | >98% | Fiches sans intervention / Total |
| **Intervention manuelle requise** | <50 espèces | Espèces à valider manuellement |
| **Temps intervention humaine** | <2 heures | Pour 50k fiches |

---

## 8. Conclusion et Recommandations

### 8.1 Résumé de l'Approche

**Pipeline Actuel** :
- ❌ 9 étapes dont 5 nécessitent une action manuelle
- ❌ Ne passe pas à l'échelle pour >1000 fiches

**Pipeline Proposé** :
- ✅ Entièrement automatisé de l'image à la BD
- ✅ Intervention humaine uniquement POST-import (relecture)
- ✅ Capacité : 50 000+ fiches sans dégradation
- ✅ Temps traitement : <30 heures

### 8.2 Avantages de l'Automatisation

1. **Scalabilité** : Traiter 50 000 fiches aussi facilement que 50
2. **Rapidité** : Réduction du temps de traitement de 90%+
3. **Cohérence** : Élimination des erreurs humaines de saisie
4. **Coût** : Libération du temps humain pour tâches à forte valeur (analyse, recherche)
5. **Qualité** : Scoring automatique permet de focaliser sur les cas douteux

### 8.3 Recommandations de Déploiement

#### Déploiement Progressif (Blue/Green)

**Phase Pilote** (100 fiches) :
- Tester pipeline complet sur un petit batch
- Comparer qualité vs processus manuel
- Ajuster seuils et paramètres

**Phase Beta** (1000 fiches) :
- Activer pour un sous-ensemble d'utilisateurs
- Monitoring intensif
- Collecte feedback

**Phase Production** (50 000+ fiches) :
- Déploiement complet
- Monitoring continu
- Itérations d'amélioration

#### Infrastructure Requise

**Serveur Application** :
- CPU : 8+ cores (Celery workers)
- RAM : 16 GB+ (cache Redis + workers)
- Stockage : 500 GB+ (images + JSON)

**Base de Données** :
- PostgreSQL 14+
- SSD : 100 GB+
- Connection pool : 50+ connexions

**Celery** :
- Redis : 4 GB RAM
- Workers : 10-20 parallèles
- Queues : `ocr`, `import`, `finalization`

**APIs Externes** :
- Gemini API : quota élevé (>10k req/jour)
- Google Maps API : quota géocodage (si utilisé)

### 8.4 Points de Vigilance

1. **Qualité auto-matching** : Monitorer faux positifs, ajuster threshold si nécessaire
2. **Coût API Gemini** : Évaluer coût pour 50k images, négocier tarifs si possible
3. **Charge BD** : Prévoir scaling si >100k fiches (sharding, read replicas)
4. **Maintenance** : Prévoir 10% du temps pour maintenance/amélioration continue

### 8.5 Évolutions Futures (Post-MVP)

**Machine Learning Avancé** :
- Modèle de classification espèces avec contexte (géographique, temporel)
- Détection d'anomalies (observations incohérentes)
- Prédiction de qualité OCR avant finalisation

**Feedback Loop** :
- Apprentissage continu depuis corrections manuelles
- Amélioration automatique du matching
- Adaptation aux nouvelles espèces

**Intégration API Publique** :
- Webhook pour notifications temps réel
- API REST pour déclenchement programmatique
- Export automatique vers plateformes externes (INPN, eBird)

---

## 9. Annexes

### 9.1 Fichiers Clés à Modifier

| Fichier | Modifications | Complexité |
|---------|---------------|-----------|
| `pilot/tasks.py` | Ajout auto-trigger OCR | 🟢 Faible |
| `ingest/tasks.py` | Création tasks Celery auto | 🟡 Moyenne |
| `ingest/importation_service.py` | Amélioration auto-matching | 🟡 Moyenne |
| `ingest/models.py` | Nouveaux modèles (Équivalence, Erreur) | 🟡 Moyenne |
| `ingest/views/monitoring.py` | Nouveau dashboard | 🟢 Faible |
| `settings.py` | Config Celery Beat, alertes | 🟢 Faible |

### 9.2 Dépendances Externes

**Nouvelles librairies Python** :
```
# requirements.txt
watchdog==3.0.0  # Filesystem watcher
celery[redis]==5.3.0  # Déjà présent
flower==2.0.1  # Monitoring Celery
scikit-learn==1.3.0  # ML (optionnel phase 2)
python-Levenshtein==0.21.0  # Fuzzy matching
```

**Services Externes** :
- Redis (déjà présent pour Celery)
- Slack webhook (optionnel, pour alertes)
- Service email (déjà présent Django)

### 9.3 Commandes Utiles

**Lancer le pipeline automatisé** :
```bash
# Démarrer workers Celery
celery -A observations_nids worker -l info -Q ocr,import,finalization -c 20

# Démarrer Celery Beat (cron tasks)
celery -A observations_nids beat -l info

# Monitoring avec Flower
celery -A observations_nids flower

# Watcher filesystem (si utilisé)
python manage.py run_json_watcher
```

**Monitoring en temps réel** :
```bash
# Logs Celery
tail -f logs/celery.log

# Dashboard web
http://localhost:5555  # Flower

# Dashboard automatisation
http://localhost:8000/ingest/dashboard/
```

---

**Document créé le** : 25 décembre 2025
**Version** : 1.0
**Auteur** : Analyse automatisée du système de transcription
**Contact** : Pour questions ou ajustements, se référer à ce document lors de la phase de réalisation

---

*Ce document est conçu pour être utilisé comme référence lors de l'implémentation. Chaque phase peut être réalisée indépendamment, permettant un déploiement progressif et itératif.*
