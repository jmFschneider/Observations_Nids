# Migration Feedback : Système de Discussion

Ce document décrit les étapes nécessaires pour déployer la mise à jour de l'application `feedback` (passage d'un système de notes statiques à un fil de discussion complet).

## Changements Majeurs
1. **Modèle de données** : Ajout de la table `FeedbackMessage` pour l'historique des échanges.
2. **Workflow** : Nouveau statut `WAITING_USER` (En attente d'infos) et tri par `last_activity`.
3. **Interface** : Vue détaillée de type "Ticket" pour chaque retour.

## Étapes de déploiement (Pilote)

### 1. Mise à jour du code
Récupérer les derniers changements via Git sur le serveur pilote.

### 2. Application des schémas de base de données
Exécuter les migrations Django classiques :
```bash
python manage.py migrate feedback
```

### 3. Migration des données existantes (Important)
Une commande personnalisée a été créée pour transformer les anciennes `admin_note` en messages de discussion afin de ne perdre aucun historique.

**Lancer la migration en mode réel :**
```bash
python manage.py migrate_feedback_notes --commit
```
*(Sans l'option `--commit`, la commande affiche simplement ce qu'elle ferait sans modifier la base).*

### 4. Vérification
- Accéder à `/feedback/list/` : les retours doivent être triés par activité.
- Accéder à un détail de feedback : le message initial et les éventuels messages migrés doivent apparaître.
- Tester une réponse : le champ `last_activity` du feedback doit se mettre à jour automatiquement.

## Support
En cas de problème avec la migration des données, les anciennes notes restent stockées dans le champ `admin_note` (renommé "Legacy" dans l'admin) par sécurité.
