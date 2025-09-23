"""Tests des modèles du module administration."""
import pytest
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()


@pytest.mark.django_db
class TestUtilisateur:
    """Tests pour le modèle Utilisateur."""

    def test_creation_utilisateur(self):
        """Test de création d'un utilisateur."""
        user = Utilisateur.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='observateur',
        )

        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'observateur'
        assert user.est_valide is False  # Par défaut

    def test_utilisateur_transcription(self):
        """Test de création d'un utilisateur depuis transcription."""
        user = Utilisateur.objects.create(
            username='transcription_user',
            email='trans@example.com',
            first_name='Jean',
            last_name='Dupont',
            est_transcription=True,
            est_valide=True,
        )

        assert user.est_transcription is True
        assert user.est_valide is True

    def test_roles_disponibles(self):
        """Test des différents rôles disponibles."""
        roles = ['observateur', 'reviewer', 'administrateur']

        for role in roles:
            user = Utilisateur.objects.create(
                username=f'user_{role}',
                email=f'{role}@example.com',
                role=role,
            )
            assert user.role == role

    def test_str_representation(self, user):
        """Test de la représentation string."""
        expected = f"{user.first_name} {user.last_name}"
        assert str(user) == expected

    def test_password_hashing(self):
        """Test que le mot de passe est hashé."""
        user = Utilisateur.objects.create(username='hashtest', email='hash@example.com')
        user.set_password('SecurePassword123!')
        user.save()

        assert user.password != 'SecurePassword123!'
        assert user.check_password('SecurePassword123!')