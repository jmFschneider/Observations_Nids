"""Fixtures spécifiques au module accounts."""

import pytest
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()


@pytest.fixture
def user_observateur(db):
    """Utilisateur avec rôle observateur validé et actif."""
    return Utilisateur.objects.create_user(
        username='observateur',
        email='observateur@test.com',
        password='TestPass123!',
        first_name='Jean',
        last_name='Observateur',
        role='observateur',
        est_valide=True,
        is_active=True,
    )


@pytest.fixture
def user_admin(db):
    """Utilisateur avec rôle administrateur."""
    return Utilisateur.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='TestPass123!',
        first_name='Admin',
        last_name='User',
        role='administrateur',
        est_valide=True,
        is_active=True,
    )


@pytest.fixture
def user_superuser(db):
    """Superuser pour tests de permissions."""
    return Utilisateur.objects.create_superuser(
        username='superuser',
        email='superuser@test.com',
        password='TestPass123!',
        first_name='Super',
        last_name='User',
    )


@pytest.fixture
def user_inactif(db):
    """Utilisateur désactivé (soft delete)."""
    return Utilisateur.objects.create_user(
        username='inactif',
        email='inactif@test.com',
        password='TestPass123!',
        first_name='User',
        last_name='Inactif',
        role='observateur',
        est_valide=True,
        is_active=False,
    )


@pytest.fixture
def user_non_valide(db):
    """Utilisateur en attente de validation admin."""
    return Utilisateur.objects.create_user(
        username='pending',
        email='pending@test.com',
        password='TestPass123!',
        first_name='User',
        last_name='Pending',
        role='observateur',
        est_valide=False,
        is_active=False,
    )
