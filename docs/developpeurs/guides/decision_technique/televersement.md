# Décision Technique : Gestion du Téléversement des Fiches d'Observation

Ce document décrit l'approche choisie pour implémenter le téléversement des fiches d'observation, en réponse à deux cas d'usage distincts : le téléversement unitaire par un utilisateur et le téléversement en masse par un administrateur.

## 1. Problématique

Le besoin initial était de permettre l'ajout de fiches d'observation scannées (images) dans le système pour qu'elles soient transcrites. Deux scénarios ont été identifiés :

1.  **Cas d'usage 1 (Utilisateur)** : Un observateur souhaite téléverser une ou quelques fiches directement depuis le site web.
2.  **Cas d'usage 2 (Administrateur)** : L'équipe projet a besoin de traiter plusieurs milliers de fiches d'un coup, de manière automatisée.

La contrainte principale était de ne pas modifier le modèle `FicheObservation` existant pour y stocker directement les images brutes.

## 2. Décision Architecturale

Pour répondre à ces besoins tout en respectant les contraintes, la décision a été de créer une **étape de "staging"** (pré-traitement) via un nouveau modèle Django.

**Modèle choisi : `ImageSource`**

Ce modèle, ajouté dans `observations/models.py`, sert de conteneur temporaire pour les images téléversées. Il découple le processus de téléversement du processus de transcription et de la fiche de données finale.

Ses champs principaux sont :
- `observateur`: Un lien vers l'utilisateur qui a téléversé l'image.
- `image`: Un `ImageField` qui gère le stockage du fichier sur le serveur (`media/images_sources/`).
- `est_transcrite`: Un booléen (`False` par défaut) pour suivre l'état du traitement.
- `fiche_observation`: Un lien (optionnel) vers la `FicheObservation` qui sera créée après la transcription, assurant une traçabilité complète.

## 3. Implémentation Réalisée (Cas d'usage 1)

La première phase de l'implémentation a couvert le cas d'usage de l'utilisateur unique.

- **Modèle** : Le modèle `ImageSource` a été créé et la migration de base de données a été appliquée.
- **Interface Web** : Une interface web complète a été développée pour permettre à un utilisateur connecté de téléverser une image.
    - **Formulaire** : `ImageSourceForm` dans `observations/forms.py`.
    - **Vues** : `upload_image_source` et `upload_success` dans `observations/views.py`.
    - **URLs** : Les routes `/observations/upload-image/` et `/observations/upload-success/` ont été ajoutées.
    - **Templates** : Des templates HTML pour le formulaire et la page de succès ont été créés.

## 4. Prochaines Étapes

Le travail suivant est nécessaire pour finaliser la fonctionnalité et l'intégrer au système existant.

### a. Configuration et Test

- **Vérifier `django-crispy-forms`** : Si le projet l'utilise, s'assurer qu'il est bien installé et configuré. Sinon, modifier le template pour utiliser `{{ form.as_p }}`.
- **Configurer `MEDIA_ROOT` et `MEDIA_URL`** : Indispensable pour que le stockage des fichiers téléversés fonctionne.
- **Tester** : Lancer le serveur de développement et tester le parcours de téléversement via l'URL `/observations/upload-image/`.

### b. Intégration avec le Système de Transcription

C'est l'étape la plus importante. Le processus de transcription existant, qui lit les images depuis un répertoire, doit être modifié.

**Logique à implémenter :**
1.  **Interroger la base de données** : Le script de transcription doit maintenant récupérer les `ImageSource` où `est_transcrite` est `False`.
    
    ```python
    from observations.models import ImageSource
    images_a_traiter = ImageSource.objects.filter(est_transcrite=False)
    ```
2.  **Traiter chaque image** : Pour chaque objet `ImageSource` récupéré, le script doit accéder au fichier image via `image.path` et lancer la transcription.
3.  **Créer la `FicheObservation`** : Une fois la transcription terminée, le script crée l'instance de `FicheObservation` avec les données extraites.
4.  **Mettre à jour `ImageSource`** : Après la création de la fiche, le script doit mettre à jour l'objet `ImageSource` original :
    
    - `est_transcrite` passe à `True`.
    - `fiche_observation` est lié à la nouvelle `FicheObservation` créée.
    - Sauvegarder l'objet `ImageSource`.

### c. Intégration Front-end

- **Ajouter un lien** : Pour rendre la page accessible, il faut ajouter un lien vers la page de téléversement (`{% url 'observations:upload_image_source' %}`) dans la navigation du site (par exemple, dans le menu principal, le tableau de bord de l'utilisateur, etc.).

### d. Implémentation du Cas d'Usage 2 (Futur)

Une fois l'intégration avec le système de transcription terminée, le cas d'usage du téléversement en masse sera grandement simplifié. Il suffira de créer une **commande de gestion Django** (`management command`) qui :
1.  Prend un répertoire en argument.
2.  Parcourt les images de ce répertoire.
3.  Pour chaque image, crée une instance `ImageSource` et l'associe à un utilisateur administrateur.

Le système de transcription existant (modifié à l'étape 4.b) se chargera automatiquement de traiter ces nouvelles images.



## 5. Mise en place 

✦ Tous les composants nécessaires pour l'interface de téléversement web sont maintenant en place :

   * Modèle `ImageSource` a été ajouté à observations/models.py et les migrations ont été
     appliquées.
   * Formulaire `ImageSourceForm` a été ajouté à observations/forms.py.
   * Vues `upload_image_source` et `upload_success` ont été créées dans observations/views.py.
   * URLs `/observations/upload-image/` et `/observations/upload-success/` ont été ajoutées à
     observations/urls.py.
   * Templates `upload_image_source.html` et `upload_success.html` ont été créés dans
     observations/templates/observations/.

  Pour tester cette nouvelle fonctionnalité, voici les étapes à suivre :

      1. Vérifiez les dépendances :
       * Si vous n'utilisez pas django-crispy-forms, vous devrez soit l'installer (pip install
         django-crispy-forms et l'ajouter à INSTALLED_APPS), soit modifier
         observations/templates/observations/upload_image_source.html en remplaçant {{ form|crispy
         }} par {{ form.as_p }}.
      2. Configurez `MEDIA_ROOT` et `MEDIA_URL` : Assurez-vous que ces paramètres sont correctement
      définis dans votre fichier observations_nids/settings.py pour que les fichiers téléversés
      soient stockés correctement.
         1     # Exemple dans settings.py
         2     import os
         3
         4     MEDIA_URL = '/media/'
         5     MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
      3. Démarrez le serveur de développement :
         1     python manage.py runserver
      4. Accédez à la page de téléversement : Ouvrez votre navigateur et allez à l'adresse
      http://127.0.0.1:8000/observations/upload-image/ (ou l'adresse de votre serveur). Vous devrez
      être connecté pour accéder à cette page.
      5. Testez le téléversement : Essayez de téléverser une image. Vous devriez être redirigé vers la
      page de succès après un téléversement réussi.



============================================================================

✦ Vous avez raison, django-crispy-forms est une solution très robuste et flexible pour la gestion
  des formulaires, c'est pourquoi elle est souvent privilégiée dans les projets Django. Elle offre
  un contrôle plus fin sur la mise en page et s'intègre parfaitement avec les frameworks CSS
  modernes.

  Si vous êtes d'accord, je peux procéder à son installation et à sa configuration dans votre
  projet. Cela impliquera les étapes suivantes :

   1. Ajouter `'crispy_forms'` à `INSTALLED_APPS` dans observations_nids/settings.py.
   2. Définir le `CRISPY_TEMPLATE_PACK` (par exemple, sur 'bootstrap5') dans
      observations_nids/settings.py.
   3. (Vous devrez ensuite exécuter pip install django-crispy-forms si ce n'est pas déjà fait).

  Commençons par la modification de settings.py. Je vais relire le fichier pour m'assurer d'avoir
   le bloc INSTALLED_APPS exact.

╭───────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✓  ReadFile observations_nids\settings.py                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
✦ J'ai le contenu de settings.py.

  Je vais maintenant modifier settings.py pour :

   1. Ajouter 'crispy_forms' et 'crispy_bootstrap5' à INSTALLED_APPS, juste après 'bootstrap4form'.
   2. Ajouter CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5" et CRISPY_TEMPLATE_PACK = "bootstrap5" à
      la fin du fichier, après la définition de HELPDESK_TICKET_FORM_CLASS.

  Je vais effectuer ces deux opérations de remplacement. D'abord, la modification de
  INSTALLED_APPS.

╭───────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✓  Edit observations_nids\settings.py:     'bootstrap4form',  # Requi... =>     'bootstrap4f… │
│                                                                                               │
│     94   'ingest.apps.IngestConfig',                                                          │
│     95   'audit.apps.AuditConfig',                                                            │
│     96   'bootstrap4form',  # Required for nicer formatting of forms with the default         │
│          templates                                                                            │
│     97 + 'crispy_forms', # Add crispy_forms                                                   │
│     98 + 'crispy_bootstrap5', # Add crispy_bootstrap5 for Bootstrap 5 integration             │
│     99   'rest_framework',  # required for the API                                            │
│    100   'helpdesk',                                                                          │
│    101   'helpdesk_custom.apps.HelpdeskCustomConfig',  # Personnalisation de Helpdesk         │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
✦ crispy_forms et crispy_bootstrap5 ont été ajoutés à INSTALLED_APPS.

  Je vais maintenant ajouter les paramètres CRISPY_ALLOWED_TEMPLATE_PACKS et CRISPY_TEMPLATE_PACK
   à settings.py.

╭───────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✓  Edit observations_nids\settings.py: HELPDESK_TICKET_FORM_CLASS = '... => HELPDESK_TICKET_… │
│                                                                                               │
│    330   # Utiliser nos formulaires personnalisés                                             │
│    331   HELPDESK_PUBLIC_TICKET_FORM_CLASS = 'helpdesk_custom.forms.CustomPublicTicketForm'   │
│    332   HELPDESK_TICKET_FORM_CLASS = 'helpdesk_custom.forms.CustomTicketForm'                │
│    333 +                                                                                      │
│    334 + # Crispy Forms Settings                                                              │
│    335 + CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"                                         │
│    336 + CRISPY_TEMPLATE_PACK = "bootstrap5"                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
✦ Le fichier settings.py a été mis à jour pour inclure crispy_forms dans INSTALLED_APPS et pour
  définir le CRISPY_TEMPLATE_PACK.

  Prochaines étapes pour vous :

   1. Installer les paquets Python nécessaires :
      1     pip install django-crispy-forms crispy-bootstrap5
   2. Redémarrer votre serveur de développement : Après l'installation des paquets, le tag {{
      form|crispy }} dans upload_image_source.html devrait maintenant fonctionner correctement et
      afficher le formulaire avec le style Bootstrap 5.

  N'hésitez pas si vous avez d'autres questions ou si vous rencontrez des problèmes.



# Todo 

sera-t-il possible de modifier les formes existantes pour remplacer par

✦ Oui, absolument. C'est une excellente idée et l'un des principaux avantages de l'adoption de
  django-crispy-forms. Remplacer le rendu des formulaires existants permettra d'uniformiser
  l'apparence et la gestion de tous les formulaires de votre application.

  Le processus de migration d'un formulaire existant vers crispy-forms est généralement simple.

  Processus général de migration d'un formulaire :

   1. Identifier le template : Trouver le fichier HTML où le formulaire est actuellement affiché.
   2. Modifier le template :
       * S'assurer que {% load crispy_forms_tags %} est présent en haut du fichier.
       * Repérer le bloc de code qui affiche le formulaire (que ce soit une boucle manuelle {% for
         field in form %} ou un tag d'une autre librairie comme {% bootstrap_form form %}).
       * Remplacer tout ce bloc par la simple balise : {{ form|crispy }}.

  C'est tout. crispy-forms se chargera du reste.

  Pour les formulaires plus complexes, on peut également ajouter un FormHelper dans le fichier
  forms.py pour personnaliser la mise en page, mais pour une simple conversion, la modification
  du template est souvent suffisante.

  Souhaitez-vous que je modifie l'un de vos formulaires existants en guise d'exemple ? Nous
  pourrions commencer par un formulaire simple pour que vous puissiez voir le processus et le
  résultat.
