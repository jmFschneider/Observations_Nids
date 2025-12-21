# Guide de configuration et déploiement de la documentation (MkDocs)

> **Résumé** : Ce guide explique comment rédiger, tester et déployer la documentation utilisateur du projet, qui est basée sur **MkDocs**.

## 1. Vue d'ensemble

Le système de documentation repose sur deux modes de fonctionnement distincts selon l'environnement :

| Environnement | Mode | URL d'accès | Comportement |
| :--- | :--- | :--- | :--- |
| **Développement** | **Serveur Live** | `http://127.0.0.1:8001/` | Modification en temps réel (Hot Reload) |
| **Test Local** | **Statique** | `/static/docs/index.html` | Simulation du comportement de production |
| **Production/Pilote** | **Statique** | `/static/docs/index.html` | Fichiers HTML servis par Apache/Nginx |

L'application Django détecte automatiquement l'environnement et adapte le lien "Aide" du menu en conséquence.

---

## 2. Environnement de Rédaction (Développement)

Pour rédiger la documentation avec un retour visuel immédiat.

### Prérequis
```bash
pip install -r requirements-dev.txt
# Installe mkdocs, mkdocs-material, pymdown-extensions
```

### Lancer le serveur de documentation
Ouvrez un terminal dédié et lancez :
```bash
cd docs
mkdocs serve --config-file=mkdocs.yml
```
La documentation est accessible sur `http://127.0.0.1:8001`.

### Structure des fichiers
*   **Contenu** : `docs/utilisateurs/*.md`
*   **Configuration** : `docs/mkdocs.yml`
*   **Assets** : `docs/assets/` (images, css, js)

---

## 3. Tester le rendu Production en local

Avant de déployer, il est utile de vérifier que la version statique (HTML) se génère correctement.

1.  **Générer le site statique** :
    ```bash
    bash scripts/build_docs.sh
    ```
    *Cela compile les fichiers Markdown en HTML dans `staticfiles/docs/`.*

2.  **Configurer Django pour utiliser les fichiers statiques** :
    Ajoutez temporairement dans votre `.env` :
    ```env
    MKDOCS_USE_STATIC=True
    ```

3.  **Lancer Django** :
    ```bash
    python manage.py runserver
    ```
    Le lien "Aide" pointera désormais vers les fichiers locaux dans `staticfiles/docs/`.

---

## 4. Déploiement en Production / Pilote

Le déploiement se fait en "pushant" les fichiers HTML générés. Le serveur de production n'a **pas** besoin de Python/MkDocs pour servir la documentation, seulement d'un serveur web (Apache/Nginx).

### Procédure de mise à jour

1.  **Sur votre machine de développement** :
    ```bash
    # 1. Builder la documentation
    bash scripts/build_docs.sh

    # 2. Vérifier que des fichiers ont changé dans staticfiles/docs/
    git status

    # 3. Committer les fichiers sources ET les fichiers générés
    git add docs/ staticfiles/docs/
    git commit -m "docs: Mise à jour et rebuild de la documentation"
    git push origin main
    ```

2.  **Sur le serveur (Raspberry Pi)** :
    ```bash
    # 1. Récupérer les modifications
    cd /path/to/observations_nids
    git pull

    # 2. Collecter les fichiers statiques (copie vers le dossier final servi par Apache)
    source venv/bin/activate
    python manage.py collectstatic --noinput

    # 3. (Optionnel) Redémarrer Gunicorn si nécessaire
    sudo systemctl restart gunicorn
    ```

### Configuration Serveur (Apache)
Apache doit être configuré pour servir le dossier `staticfiles`.
Exemple de configuration `VirtualHost` :
```apache
Alias /static/ /path/to/observations_nids/staticfiles/
<Directory /path/to/observations_nids/staticfiles>
    Require all granted
</Directory>
```

---

## 5. Dépannage (Troubleshooting)

### Le lien "Aide" redirige vers 127.0.0.1:8001 en production
**Cause** : `DEBUG=True` est resté activé sur le serveur.
**Solution** : Mettre `DEBUG=False` dans le `.env` de production.

### Les modifications n'apparaissent pas en production
**Cause** : Oubli de lancer `build_docs.sh` avant le commit, ou oubli de `collectstatic` sur le serveur.
**Solution** : Refaire le cycle de déploiement complet (Build -> Commit -> Pull -> Collectstatic).

### Erreur "mkdocs not found"
**Cause** : Vous essayez de builder sur le serveur de production sans les dépendances dev.
**Solution** : Le build doit se faire sur la machine de développement. Le serveur ne sert que des fichiers HTML statiques.
