# Étapes manuelles pour compléter l'implémentation

Nous avons déjà mis en place les éléments suivants :

1. Création du modèle de configuration Pydantic dans `config.py`
2. Création des fichiers `.env` et `.env.example`
3. Mise à jour partielle de `settings.py` pour utiliser le modèle Pydantic
4. Documentation du nouveau système de configuration

## Étapes restantes à effectuer manuellement

En raison de problèmes techniques avec l'outil de recherche/remplacement, certaines modifications doivent être effectuées manuellement dans le fichier `settings.py`. Voici les changements à apporter :

1. Mettre à jour `SESSION_EXPIRE_AT_BROWSER_CLOSE` (ligne 54) :
   ```python
   # Remplacer
   SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Déconnexion si l'utilisateur ferme son navigateur
   
   # Par
   SESSION_EXPIRE_AT_BROWSER_CLOSE = settings.SESSION_EXPIRE_AT_BROWSER_CLOSE  # Déconnexion si l'utilisateur ferme son navigateur
   ```

2. Mettre à jour `MEDIA_ROOT` (ligne 172) :
   ```python
   # Remplacer
   MEDIA_ROOT = os.path.join(BASE_DIR, "media")
   
   # Par
   MEDIA_ROOT = settings.MEDIA_ROOT
   ```

3. Mettre à jour `STATIC_ROOT` (ligne 168) :
   ```python
   # Remplacer
   STATIC_ROOT = os.path.join(BASE_DIR, "static")
   
   # Par
   STATIC_ROOT = settings.STATIC_ROOT
   ```

## Vérification de l'installation

Après avoir effectué ces modifications, vous devriez vérifier que l'application fonctionne correctement :

1. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

2. Lancer le serveur de développement :
   ```bash
   python manage.py runserver
   ```

3. Vérifier que l'application fonctionne normalement et que les paramètres de configuration sont correctement chargés depuis le fichier `.env`.

## Tester différentes configurations

Pour tester différentes configurations, vous pouvez modifier les valeurs dans le fichier `.env` et redémarrer le serveur. Par exemple :

1. Modifier `DEBUG=False` pour tester le mode production
2. Modifier `USE_DEBUG_TOOLBAR=True` pour activer la barre de débogage
3. Modifier `DB_HOST` pour tester une connexion à une autre base de données

## Résumé des fichiers créés ou modifiés

1. **Nouveaux fichiers** :
   - `Observations_Nids/config.py` : Modèle Pydantic pour la validation des paramètres
   - `.env` : Variables d'environnement avec les valeurs actuelles
   - `.env.example` : Modèle pour créer le fichier `.env`
   - `docs/configuration.md` : Documentation du nouveau système de configuration
   - `docs/implementation_summary.md` : Résumé des changements effectués
   - `docs/manual_steps.md` : Ce document

2. **Fichiers modifiés** :
   - `requirements.txt` : Ajout de `pydantic-settings==2.2.1`
   - `Observations_Nids/settings.py` : Utilisation du modèle Pydantic pour la configuration