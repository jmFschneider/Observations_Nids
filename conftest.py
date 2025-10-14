"""Configuration globale pour pytest."""

import pytest
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()


@pytest.fixture
def user_data():
    """Données de base pour créer un utilisateur."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def create_user(db, user_data):
    """Factory pour créer un utilisateur."""

    def make_user(**kwargs):
        data = user_data.copy()
        data.update(kwargs)
        password = data.pop('password')
        user = Utilisateur.objects.create(**data)
        user.set_password(password)
        user.save()
        return user

    return make_user


@pytest.fixture
def user(create_user):
    """Utilisateur de test simple."""
    return create_user()


@pytest.fixture
def admin_user(create_user):
    """Utilisateur administrateur."""
    return create_user(username='admin', email='admin@example.com', role='administrateur')


@pytest.fixture
def authenticated_client(client, user):
    """Client Django authentifié."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Client Django authentifié en tant qu'admin."""
    client.force_login(admin_user)
    return client
