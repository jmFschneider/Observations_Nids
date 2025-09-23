# Guide des Tests - Observations Nids

## Installation des dépendances de test

```bash
pip install pytest pytest-django pytest-cov
```

Ou via requirements-dev.txt :
```bash
pip install -r requirements-dev.txt
```

## Lancer les tests

### Tous les tests
```bash
pytest
```

### Tests avec couverture de code
```bash
pytest --cov
```

### Tests d'un module spécifique
```bash
pytest observations/tests/
pytest administration/tests/
pytest importation/tests/
```

### Tests d'un fichier spécifique
```bash
pytest observations/tests/test_models.py
```

### Tests avec un marqueur
```bash
pytest -m unit           # Tests unitaires uniquement
pytest -m integration    # Tests d'intégration uniquement
pytest -m "not slow"     # Exclure les tests lents
```

## Structure des tests

```
observations_nids/
├── conftest.py                          # Fixtures globales
├── pytest.ini                           # Configuration pytest
├── observations/tests/
│   ├── __init__.py
│   ├── conftest.py                     # Fixtures pour observations
│   └── test_models.py                  # Tests des modèles
├── administration/tests/
│   ├── __init__.py
│   ├── conftest.py                     # Fixtures pour administration
│   ├── test_models.py                  # Tests des modèles
│   └── test_auth.py                    # Tests d'authentification
└── importation/tests/
    ├── __init__.py
    ├── conftest.py                     # Fixtures pour importation
    └── test_importation_service.py     # Tests du service d'importation
```

## Fixtures disponibles

### Fixtures globales (conftest.py racine)

- **user_data** : Données de base pour créer un utilisateur
- **create_user** : Factory pour créer des utilisateurs personnalisés
- **user** : Utilisateur de test simple
- **admin_user** : Utilisateur administrateur
- **authenticated_client** : Client Django authentifié
- **admin_client** : Client Django authentifié en admin

### Fixtures observations (observations/tests/conftest.py)

- **famille** : Famille d'oiseaux de test
- **espece** : Espèce d'oiseau de test
- **fiche_observation** : Fiche d'observation de test

### Fixtures importation (importation/tests/conftest.py)

- **json_data_valid** : Données JSON valides pour test
- **transcription_brute** : Transcription brute de test
- **espece_candidate** : Espèce candidate de test

## Exemples d'utilisation

### Test simple avec fixture
```python
@pytest.mark.django_db
def test_creation_utilisateur(user):
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
```

### Test avec client authentifié
```python
@pytest.mark.django_db
def test_acces_profil(authenticated_client):
    response = authenticated_client.get(reverse('administration:mon_profil'))
    assert response.status_code == 200
```

### Test avec factory personnalisée
```python
@pytest.mark.django_db
def test_utilisateur_admin(create_user):
    admin = create_user(username='admin', role='administrateur')
    assert admin.role == 'administrateur'
```

## Marqueurs disponibles

- **@pytest.mark.django_db** : Accès à la base de données
- **@pytest.mark.unit** : Test unitaire
- **@pytest.mark.integration** : Test d'intégration
- **@pytest.mark.slow** : Test lent (API externe, etc.)
- **@pytest.mark.celery** : Test des tâches Celery

## Rapport de couverture

Après avoir lancé `pytest --cov`, consultez le rapport HTML :
```bash
# Générer le rapport HTML
pytest --cov --cov-report=html

# Ouvrir le rapport
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows
```

## Tests actuellement implémentés

### Observations (test_models.py)
- ✅ Création de FicheObservation
- ✅ Création automatique des objets liés
- ✅ Création d'Observation
- ✅ Validation des nombres négatifs
- ✅ Contraintes ResumeObservation
- ✅ Localisation par défaut

### Administration (test_models.py, test_auth.py)
- ✅ Création d'utilisateur
- ✅ Utilisateur de transcription
- ✅ Rôles disponibles
- ✅ Hashing du mot de passe
- ✅ Login/Logout
- ✅ Permissions admin

### Importation (test_importation_service.py)
- ✅ Création/récupération utilisateur
- ✅ Extraction espèces candidates
- ✅ Extraction utilisateurs
- ✅ Préparation des importations
- ✅ Workflow complet d'importation
- ✅ Réinitialisation d'importation

## Prochaines étapes

### Tests à ajouter (priorité haute)
- [ ] Tests des vues CRUD observations
- [ ] Tests des formulaires
- [ ] Tests de validation des données JSON
- [ ] Tests des tâches Celery (avec mock)

### Tests à ajouter (priorité moyenne)
- [ ] Tests de performance
- [ ] Tests des endpoints API
- [ ] Tests de sécurité (injection, XSS)
- [ ] Tests de régression

### Amélioration continue
- [ ] Atteindre 80% de couverture de code
- [ ] Ajouter tests de charge
- [ ] Intégration CI/CD (GitHub Actions)
- [ ] Tests end-to-end avec Selenium/Playwright