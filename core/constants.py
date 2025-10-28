STATUT_VALIDATION_CHOICES = [
    ('en_cours', 'En cours'),
    ('validee', 'Validée'),
    ('rejete', 'Rejetée'),
]

STATUT_IMPORTATION_CHOICES = [
    ('en_attente', 'En attente de validation'),
    ('erreur', 'Erreur détectée'),
    ('complete', 'Importation complétée'),
]

ROLE_CHOICES = [
    ('observateur', 'Observateur'),
    ('reviewer', 'Reviewer'),
    ('administrateur', 'Administrateur'),
]

CATEGORIE_MODIFICATION_CHOICES = [
    ('fiche', 'Fiche Observation'),
    ('observation', 'Observation'),
    ('validation', 'Validation'),
    ('localisation', 'Localisation'),
    ('nid', 'Nid'),
    ('resume_observation', 'Résumé Observation'),
    ('causes_echec', 'Causes d\'échec'),
    ('remarque', 'Remarque'),
]
