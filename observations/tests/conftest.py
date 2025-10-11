"""Fixtures spécifiques au module observations."""
import pytest

from observations.models import FicheObservation
from taxonomy.models import Espece, Famille, Ordre


@pytest.fixture
def ordre():
    """Ordre d'oiseaux de test."""
    return Ordre.objects.create(nom='Accipitriformes')


@pytest.fixture
def famille(ordre):
    """Famille d'oiseaux de test."""
    return Famille.objects.create(nom='Accipitridae', ordre=ordre)


@pytest.fixture
def espece(famille):
    """Espèce d'oiseau de test."""
    return Espece.objects.create(
        nom='Buse variable',
        nom_scientifique='Buteo buteo',
        nom_anglais='Common Buzzard',
        famille=famille,
        valide_par_admin=True,
    )


@pytest.fixture
def fiche_observation(user, espece):
    """Fiche d'observation de test."""
    return FicheObservation.objects.create(
        observateur=user, espece=espece, annee=2024, transcription=False
    )