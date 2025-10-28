"""Fixtures pour les tests du module audit."""

# Les fixtures globales (user, etc.) sont dans conftest.py à la racine
# Les fixtures spécifiques observations (espece, fiche_observation) sont importées ici

from observations.tests.conftest import espece, famille, fiche_observation, ordre  # noqa: F401
