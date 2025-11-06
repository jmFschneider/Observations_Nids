# Gestion des comptes utilisateurs

Ce guide explique le processus d'inscription, de validation et de gestion des comptes utilisateurs dans l'application.

## Processus d'inscription d'un nouvel utilisateur

Le processus est conçu pour que chaque nouveau compte soit validé par un administrateur avant d'être activé.

1.  **Formulaire d'inscription** : L'utilisateur remplit le formulaire d'inscription publique (`/accounts/inscription-publique/`).

2.  **Création de l'utilisateur** :
    *   Une nouvelle instance de `Utilisateur` est créée en base de données.
    *   Les champs `est_valide` and `is_active` sont initialisés à `False`. Le compte ne peut donc pas être utilisé pour se connecter.

3.  **Notifications** :
    *   **Email à l'administrateur** : Un e-mail est envoyé à l'adresse définie dans `ADMIN_EMAIL` pour l'informer de la nouvelle demande.
    *   **Email à l'utilisateur** : Un e-mail de confirmation est envoyé à l'utilisateur pour l'informer que sa demande a bien été enregistrée et qu'elle est en cours d'examen.
    *   **Notification en base de données** : Une `Notification` est créée pour chaque administrateur actif, visible depuis leur interface.

4.  **Page de confirmation** : L'utilisateur est redirigé vers une page de confirmation (`/accounts/inscription-completee/`) qui résume les prochaines étapes.

## Processus de connexion d'un utilisateur en attente

Si un utilisateur dont le compte n'a pas encore été validé essaie de se connecter :

1.  **Tentative de connexion** : L'utilisateur remplit le formulaire de connexion.
2.  **Détection du statut** : La vue `CustomLoginView` détecte que le compte est inactif (`is_active=False`) et non validé (`est_valide=False`).
3.  **Redirection** : L'utilisateur est redirigé vers une page de statut dédiée (`/accounts/compte-en-attente/<user_id>/`).
4.  **Page de statut et relance** :
    *   Cette page informe l'utilisateur que son compte est toujours en attente de validation.
    *   Elle propose un bouton "Renvoyer la notification à l'administrateur".
    *   En cliquant sur ce bouton, l'e-mail et la notification à l'administrateur sont envoyés à nouveau.
    *   Pour éviter le spam, cette action est limitée à une fois toutes les 24 heures (logique gérée dans la session de l'utilisateur).

## Processus de validation par l'administrateur

1.  **Tableau de bord** : L'administrateur voit les demandes en attente sur son tableau de bord.
2.  **Validation** : L'administrateur peut valider le compte. Cette action passe les champs `est_valide` et `is_active` à `True`.
3.  **Notification de validation** : L'utilisateur reçoit un e-mail final l'informant que son compte est désormais actif et qu'il peut se connecter.

## Fichiers clés

*   **Logique métier (Vues)** :
    *   `accounts/views/auth.py` : Contient `inscription_publique`, `CustomLoginView`, `compte_en_attente`, `renvoyer_notification_admin`.
*   **URLs** :
    *   `observations/urls.py` : Définit la route de connexion qui utilise `CustomLoginView`.
    *   `accounts/urls.py` : Contient les URLs pour l'inscription, la page de confirmation, la page de statut et la relance.
*   **Emails** :
    *   `accounts/utils/email_service.py` : Centralise l'envoi de tous les e-mails transactionnels.
    *   `accounts/templates/accounts/emails/` : Contient les templates HTML pour les e-mails.
*   **Templates (Pages)** :
    *   `accounts/templates/accounts/inscription_publique.html`
    *   `accounts/templates/accounts/inscription_completee.html`
    *   `accounts/templates/accounts/compte_en_attente.html`
    *   `templates/login.html` (template principal de connexion)
