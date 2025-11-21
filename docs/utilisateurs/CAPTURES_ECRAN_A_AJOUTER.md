# 📷 Liste des captures d'écran à ajouter

> **Document de travail**
> Ce fichier liste toutes les captures d'écran à réaliser pour améliorer la documentation utilisateur.

---

## 📋 Instructions générales

### Format recommandé
- **Format** : PNG ou JPG
- **Résolution** : 1920x1080 (Full HD) ou équivalent
- **Annotations** : Utilisez des flèches/cercles rouges pour mettre en évidence les éléments importants
- **Qualité** : Haute qualité, texte lisible
- **Noms de fichiers** : Descriptifs (ex: `page_accueil_tableau_bord.png`)

### Emplacement
Créer un dossier : `docs/utilisateurs/images/` pour stocker toutes les captures

### Intégration dans la doc
Syntaxe Markdown : `![Texte alternatif](./images/nom_fichier.png)`

---

## 🏠 Guide 01 - Navigation générale

### Page d'accueil et authentification

- [ ] **01_page_connexion.png**
  - Description : Page de connexion avec formulaire
  - Emplacement dans la doc : Section "1. Inscription et connexion"
  - Éléments à montrer : Champs login/password, boutons

- [ ] **02_page_inscription.png**
  - Description : Formulaire d'inscription complet
  - Emplacement : Section "1. Inscription et connexion"
  - Éléments : Tous les champs du formulaire

### Tableau de bord principal

- [ ] **03_tableau_bord_principal.png**
  - Description : Vue d'ensemble du tableau de bord après connexion
  - Emplacement : Section "2. Page d'accueil et navigation"
  - Éléments : Menu principal, cartes d'action, statistiques

- [ ] **04_menu_navigation.png**
  - Description : Menu de navigation (barre supérieure)
  - Emplacement : Section "2. Page d'accueil et navigation"
  - Éléments : Tous les liens du menu, icône utilisateur

- [ ] **05_menu_utilisateur.png**
  - Description : Menu déroulant de l'utilisateur (clic sur nom)
  - Emplacement : Section "Se déconnecter"
  - Éléments : Profil, Paramètres, Déconnexion

### Gestion des observations

- [ ] **06_liste_observations.png**
  - Description : Page listant toutes les observations
  - Emplacement : Section "3. Consulter les observations"
  - Éléments : Tableau, filtres, pagination

- [ ] **07_filtres_observations.png**
  - Description : Panneau de filtres (date, espèce, lieu, etc.)
  - Emplacement : Section "3. Consulter les observations"
  - Éléments : Tous les filtres disponibles

- [ ] **08_fiche_detail_observation.png**
  - Description : Vue détaillée d'une fiche d'observation
  - Emplacement : Section "3. Consulter les observations"
  - Éléments : Toutes les infos, carte, observations, remarques

### Statuts et workflow

- [ ] **09_statuts_fiches.png**
  - Description : Exemple de fiches avec différents statuts (badges colorés)
  - Emplacement : Section "4. Cycle de vie d'une fiche"
  - Éléments : Badges NOUVEAU, EN_COURS, VALIDEE

---

## 📝 Guide 02 - Saisie nouvelle observation

### Formulaire de localisation

- [ ] **10_formulaire_localisation.png**
  - Description : Section localisation du formulaire
  - Emplacement : Section "2. Étape 1 : Localisation"
  - Éléments : Champ commune, coordonnées, bouton géolocalisation

- [ ] **11_autocompletion_commune.png**
  - Description : Menu déroulant d'auto-complétion des communes
  - Emplacement : Section "Méthode A : Recherche par commune"
  - Éléments : Liste de suggestions avec résultats

- [ ] **12_bouton_geolocalisation.png**
  - Description : Bouton "Me géolocaliser" et son action
  - Emplacement : Section "Méthode B : Géolocalisation GPS"
  - Éléments : Bouton, éventuellement popup de demande d'autorisation

### Informations du nid

- [ ] **13_formulaire_infos_nid.png**
  - Description : Section "Informations du nid"
  - Emplacement : Section "4. Étape 3 : Informations du nid"
  - Éléments : Tous les champs (espèce, année, hauteur, support, etc.)

- [ ] **14_autocompletion_espece.png**
  - Description : Auto-complétion du champ espèce
  - Emplacement : Section "4. Étape 3 : Informations du nid"
  - Éléments : Menu déroulant avec suggestions d'espèces

- [ ] **15_champs_details_nid.png**
  - Description : Détails du nid (hauteur, support, exposition, habitat)
  - Emplacement : Section "Détails du nid"
  - Éléments : Tous les champs de cette section

### Ajout d'observations

- [ ] **16_bouton_ajouter_observation.png**
  - Description : Bouton "+ Ajouter une observation"
  - Emplacement : Section "5. Étape 4 : Ajouter des observations"
  - Éléments : Bouton bien visible

- [ ] **17_formulaire_observation.png**
  - Description : Formulaire d'ajout d'une observation
  - Emplacement : Section "5. Étape 4 : Ajouter des observations"
  - Éléments : Date, nombre œufs, poussins, notes

- [ ] **18_liste_observations_ajoutees.png**
  - Description : Liste des observations déjà ajoutées à une fiche
  - Emplacement : Section "Exemple de suivi chronologique"
  - Éléments : Tableau avec plusieurs observations, boutons éditer/supprimer

### Remarques

- [ ] **19_section_remarques.png**
  - Description : Section remarques avec bouton d'ajout
  - Emplacement : Section "6. Étape 5 : Ajouter des remarques"
  - Éléments : Zone de texte, bouton "Ajouter"

- [ ] **20_liste_remarques.png**
  - Description : Liste de remarques existantes
  - Emplacement : Section "6. Étape 5 : Ajouter des remarques"
  - Éléments : Plusieurs remarques avec auteur et date

### Validation

- [ ] **21_bouton_enregistrer.png**
  - Description : Bouton "Enregistrer" en bas du formulaire
  - Emplacement : Section "3. Étape 2 : Enregistrer la fiche"
  - Éléments : Bouton bien visible

- [ ] **22_bouton_soumettre_correction.png**
  - Description : Bouton "Soumettre pour correction"
  - Emplacement : Section "7. Étape 6 : Résumé et validation"
  - Éléments : Bouton avec éventuel pourcentage de complétion

- [ ] **23_message_confirmation.png**
  - Description : Message de confirmation après enregistrement
  - Emplacement : Sections d'enregistrement
  - Éléments : Toast/message de succès

---

## ✏️ Guide 03 - Correction et transcription

### Préparation et upload

- [ ] **24_page_selection_dossier.png**
  - Description : Page de sélection de dossier d'images
  - Emplacement : Section "3. Étape 1 : Upload et sélection"
  - Éléments : Liste des dossiers, bouton upload

- [ ] **25_bouton_upload_images.png**
  - Description : Interface d'upload d'images
  - Emplacement : Section "Uploader vos images"
  - Éléments : Zone de drag & drop ou sélecteur de fichiers

- [ ] **26_liste_dossiers_disponibles.png**
  - Description : Liste des dossiers avec nombre d'images
  - Emplacement : Section "Sélectionner un dossier existant"
  - Éléments : Cartes de dossiers avec infos

### Transcription en cours

- [ ] **27_page_progression_transcription.png**
  - Description : Page de suivi de progression
  - Emplacement : Section "5. Étape 3 : Suivi du traitement"
  - Éléments : Barre de progression, fichier en cours, statistiques

- [ ] **28_barre_progression_detaillee.png**
  - Description : Détails de la progression (temps écoulé, estimé)
  - Emplacement : Section "Informations affichées"
  - Éléments : Tous les détails de progression

### Résultats

- [ ] **29_page_resultats_transcription.png**
  - Description : Page de résultats finaux
  - Emplacement : Section "6. Étape 4 : Résultats"
  - Éléments : Statistiques globales, liste des fichiers

- [ ] **30_tableau_resultats_fichiers.png**
  - Description : Tableau listant tous les fichiers traités
  - Emplacement : Section "Liste des fichiers traités"
  - Éléments : Colonnes fichier, statut, JSON, actions

### Correction de fiche

- [ ] **31_interface_correction_complete.png**
  - Description : Vue d'ensemble de l'interface de correction
  - Emplacement : Section "7. Étape 5 : Corriger une fiche"
  - Éléments : Formulaire, aperçu image, aperçu JSON

- [ ] **32_boutons_visualisation_sources.png**
  - Description : Boutons "Voir l'image source" et "Voir le JSON"
  - Emplacement : Section "8. Visualiser les fichiers source"
  - Éléments : Boutons bien visibles

- [ ] **33_popup_image_source.png**
  - Description : Popup montrant l'image JPEG source
  - Emplacement : Section "Afficher l'image source"
  - Éléments : Image en grand avec zoom possible

- [ ] **34_popup_json_source.png**
  - Description : Popup affichant le JSON brut
  - Emplacement : Section "Afficher le JSON source"
  - Éléments : JSON formaté et lisible

### Exemples de qualité

- [ ] **35_exemple_bonne_image.png**
  - Description : Exemple de bonne image à scanner (lisible, nette)
  - Emplacement : Section "2. Préparer vos images"
  - Éléments : Image de carnet bien scannée

- [ ] **36_exemple_mauvaise_image.png**
  - Description : Exemple d'image à éviter (floue, sombre)
  - Emplacement : Section "À éviter"
  - Éléments : Image de mauvaise qualité avec annotations

---

## 🎫 Guide 04 - Support et tickets

### Système de tickets

- [ ] **37_tableau_bord_helpdesk.png**
  - Description : Vue d'ensemble du tableau de bord Helpdesk
  - Emplacement : Section "2. Accéder au système de support"
  - Éléments : Liste des tickets, statistiques

- [ ] **38_formulaire_creation_ticket.png**
  - Description : Formulaire de création de ticket
  - Emplacement : Section "3. Créer un ticket"
  - Éléments : Tous les champs (catégorie, résumé, description, priorité)

- [ ] **39_categories_tickets.png**
  - Description : Menu déroulant des catégories
  - Emplacement : Section "Choisissez une catégorie"
  - Éléments : Bug, Nouvelle fonctionnalité, Support, Documentation

- [ ] **40_liste_tickets_utilisateur.png**
  - Description : Liste des tickets de l'utilisateur
  - Emplacement : Section "6. Suivre vos tickets"
  - Éléments : Tableau avec statuts, priorités

- [ ] **41_detail_ticket.png**
  - Description : Vue détaillée d'un ticket
  - Emplacement : Section "Voir un ticket"
  - Éléments : Historique, messages, statut, ajout de suivi

- [ ] **42_statuts_tickets_exemples.png**
  - Description : Exemples de tickets avec différents statuts
  - Emplacement : Section "9. Statuts des tickets"
  - Éléments : Badges de statuts colorés

---

## 🏠 Page d'accueil README

- [ ] **43_page_accueil_doc.png**
  - Description : Capture de la page d'accueil de la documentation
  - Emplacement : En haut du README
  - Éléments : Vue d'ensemble, logo si disponible

---

## 📊 Statistiques (bonus)

- [ ] **44_page_statistiques.png**
  - Description : Page de statistiques (si disponible)
  - Emplacement : À créer dans la doc si pertinent
  - Éléments : Graphiques, tableaux, analyses

---

## 📝 Notes

### Ordre de priorité suggéré

**Priorité haute** (essentielles) :
1. Tableau de bord principal (03)
2. Formulaire de saisie complet (10, 13)
3. Interface de correction (31)
4. Liste des observations (06)
5. Création de ticket (38)

**Priorité moyenne** (utiles) :
6. Auto-complétion (11, 14)
7. Progression transcription (27, 29)
8. Détail d'observation (08)
9. Filtres (07)
10. Visualisation sources (33, 34)

**Priorité basse** (nice to have) :
11. Exemples de qualité d'image (35, 36)
12. Badges de statuts (09, 42)
13. Messages de confirmation (23)

### Conseils de réalisation

1. **Utilisez un compte de démonstration** avec des données fictives réalistes
2. **Masquez les données sensibles** (noms réels, emails, coordonnées précises)
3. **Annotez les captures** pour mettre en évidence les éléments importants
4. **Cohérence visuelle** : Utilisez le même compte/thème pour toutes les captures
5. **Format cohérent** : Même résolution pour toutes les captures d'une même catégorie

---

**Total : 44 captures d'écran à réaliser**

*Document créé : Janvier 2025*
