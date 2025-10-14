from django.db import models


class CommuneFrance(models.Model):
    """
    Cache des communes françaises pour géocodage rapide
    Source : API Géoplateforme (data.gouv.fr)
    """

    # Identification
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True, help_text="Code INSEE de la commune")
    code_postal = models.CharField(max_length=5, db_index=True)

    # Localisation administrative
    departement = models.CharField(max_length=100)
    code_departement = models.CharField(max_length=3, db_index=True)
    region = models.CharField(max_length=100, blank=True)

    # Coordonnées GPS (centre de la commune)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.IntegerField(
        null=True, blank=True, help_text="Altitude en mètres (centre de la commune)"
    )

    # Métadonnées
    population = models.IntegerField(null=True, blank=True)
    superficie = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Superficie en km²"
    )
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'geo_commune_france'
        verbose_name = 'Commune française'
        verbose_name_plural = 'Communes françaises'
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom', 'code_departement']),
            models.Index(fields=['code_postal']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.code_departement})"

    @property
    def coordonnees_gps(self):
        """Retourne les coordonnées au format 'lat,lon'"""
        return f"{self.latitude},{self.longitude}"


class Localisation(models.Model):
    fiche = models.OneToOneField(
        'observations.FicheObservation', on_delete=models.CASCADE, related_name="localisation"
    )
    commune = models.CharField(max_length=100, default='Non spécifiée')
    lieu_dit = models.CharField(max_length=100, default='Non spécifiée', blank=True)
    departement = models.CharField(max_length=100, default='00')
    coordonnees = models.CharField(max_length=30, default='0,0')
    latitude = models.CharField(max_length=15, default='0.0')
    longitude = models.CharField(max_length=15, default='0.0')
    altitude = models.IntegerField(default=0, help_text="Altitude en mètres")
    paysage = models.TextField(default='Non spécifié')
    alentours = models.TextField(default='Non spécifié')

    # Nouveaux champs pour le géocodage
    precision_gps = models.IntegerField(
        default=5000,
        help_text="Précision estimée en mètres (ex: 10m pour GPS terrain, 5000m pour commune)",
    )
    source_coordonnees = models.CharField(
        max_length=50,
        choices=[
            ('gps_terrain', 'GPS de terrain'),
            ('geocodage_auto', 'Géocodage automatique'),
            ('geocodage_manuel', 'Géocodage manuel'),
            ('carte', 'Pointé sur carte'),
            ('base_locale', 'Base locale des communes'),
            ('nominatim', 'Nominatim (OSM)'),
        ],
        default='geocodage_auto',
    )
    code_insee = models.CharField(max_length=5, blank=True, help_text="Code INSEE de la commune")

    def __str__(self):
        return f"Localisation {self.commune} ({self.departement})"
