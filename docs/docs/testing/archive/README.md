# Guide des Tests

Ce document explique comment lancer et écrire des tests pour le projet "Observations Nids".

## 1. Vue d'ensemble

Le projet utilise **Pytest** avec **pytest-django** comme framework de test. Cette combinaison permet d'écrire des tests clairs, concis et puissants.

- **Qualité du code :** Les tests sont exécutés automatiquement par notre [intégration continue (CI)](../learning/ci-cd/README.md) à chaque modification du code.
- **Couverture de code :** La couverture des tests est mesurée avec **pytest-cov** pour identifier les parties du code qui ne sont pas testées.

## 2. Configuration

La configuration principale de `pytest` se trouve dans le fichier `pytest.ini` à la racine du projet.

**Points importants de `pytest.ini` :**
- `DJANGO_SETTINGS_MODULE` est défini pour que `pytest` puisse charger l'environnement Django.
- La section `addopts` configure des options par défaut. Notamment, elle active automatiquement la **mesure de la couverture de code** (`--cov`) à chaque fois que vous lancez `pytest`.

`pytest` est configuré pour découvrir automatiquement tous les fichiers `test_*.py` ou `*_test.py` dans le projet, il n'est donc pas nécessaire de lister manuellement les répertoires de test.

## 3. Lancer les Tests

Assurez-vous d'avoir installé les dépendances de développement :
```bash
pip install -r requirements-dev.txt
```

### Lancer tous les tests

La commande est simple. À la racine du projet, lancez :
```bash
pytest
```
Cette commande va découvrir et lancer tous les tests, et affichera un résumé de la couverture de code directement dans le terminal.

### Lancer des tests spécifiques

Vous pouvez cibler une application, un répertoire, un fichier ou même un test spécifique.

```bash
# Lancer tous les tests de l'application 'geo'
pytest geo/

# Lancer uniquement les tests d'un fichier spécifique
pytest geo/tests/test_api_communes.py

# Lancer un test spécifique par son nom
pytest -k "test_regression_selection_commune"
```

### Utiliser les Marqueurs

Des marqueurs (`markers`) sont définis dans `pytest.ini` pour catégoriser les tests.

```bash
# Lancer uniquement les tests unitaires
pytest -m unit

# Lancer tous les tests sauf ceux marqués comme lents
pytest -m "not slow"
```

## 4. Consulter le Rapport de Couverture

Après avoir lancé les tests, vous pouvez générer un rapport HTML détaillé pour explorer visuellement les lignes de code qui sont couvertes par les tests.

1.  **Générez le rapport :**
    ```bash
    pytest --cov-report=html
    ```

2.  **Ouvrez le rapport :**
    Un répertoire `htmlcov/` a été créé. Ouvrez le fichier `index.html` dans votre navigateur.

---

## 5. Écrire des Tests

### Structure des Fichiers

Les tests pour une application doivent être placés dans le répertoire de cette application. Deux structures sont possibles :

1.  **Un seul fichier :** Pour un petit nombre de tests, vous pouvez les placer dans `VOTRE_APP/tests.py`.
2.  **Un répertoire dédié (recommandé) :** Pour une meilleure organisation, créez un répertoire `VOTRE_APP/tests/` et placez-y vos fichiers de test, en les nommant `test_*.py` (ex: `test_models.py`, `test_views.py`).

### Utiliser les Fixtures

Les fixtures sont des fonctions qui fournissent des données ou des objets de test réutilisables. Elles sont définies dans les fichiers `conftest.py`.

**Fixtures principales disponibles :**

-   `user` : Un objet `Utilisateur` simple.
-   `admin_user` : Un utilisateur avec les droits administrateur (`is_staff=True`).
-   `client` : Un client de test Django de base.
-   `authenticated_client` : Un client de test déjà authentifié avec l'utilisateur `user`.

**Exemple d'utilisation d'une fixture dans un test :**

```python
# Dans un fichier de test, par exemple geo/tests/test_views.py

import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_page_geocoder_requires_login(client):
    """Vérifie que la page de géocodage redirige si l'utilisateur n'est pas connecté."""
    url = reverse('geo:geocoder_commune')
    response = client.post(url)
    # On s'attend à une redirection vers la page de login
    assert response.status_code == 302
    assert '/auth/login/' in response.url

@pytest.mark.django_db
def test_page_geocoder_works_for_logged_in_user(authenticated_client):
    """Vérifie que la page est accessible pour un utilisateur connecté."""
    url = reverse('geo:geocoder_commune')
    # On fait un POST avec des données invalides, mais on s'attend à un code 200 ou 400, pas 302.
    response = authenticated_client.post(url)
    assert response.status_code != 302
```

N'oubliez pas d'ajouter le marqueur `@pytest.mark.django_db` à tous les tests qui interagissent avec la base de données.
