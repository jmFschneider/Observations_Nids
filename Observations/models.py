from django.contrib.auth.models import AbstractUser
from django.db import models
import logging
from django.core.validators import MinValueValidator

logger = logging.getLogger('Observations')


class Utilisateur(AbstractUser):  # On étend l'utilisateur Django
    ROLES = [
        ('observateur', 'Observateur'),
        ('reviewer', 'Reviewer'),
        ('administrateur', 'Administrateur')
    ]

    role = models.CharField(max_length=15, choices=ROLES, default='observateur')
    est_valide = models.BooleanField(default=False)  # Validation par l'administrateur

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

class Espece(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    commentaire = models.TextField(blank=True, null=True)
    lien_oiseau_net = models.URLField(blank=True, null=True)
    valide_par_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.nom


class FicheObservation(models.Model):
    num_fiche = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    observateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="fiches")
    espece = models.ForeignKey(Espece, on_delete=models.PROTECT, related_name="observations")
    annee = models.IntegerField()
    chemin_image = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not hasattr(self, 'localisation'):
            Localisation.objects.create(fiche=self)
        if not hasattr(self, 'resume'):
            ResumeObservation.objects.create(fiche=self)
        if not hasattr(self, 'nid'):
            Nid.objects.create(fiche=self)
        if not hasattr(self, 'causes_echec'):
            CausesEchec.objects.create(fiche=self)

    def __str__(self):
        return f"Fiche {self.num_fiche} - {self.annee} ({self.espece.nom})"

class Localisation(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="localisation")
    commune = models.CharField(max_length=30, default='Non spécifiée')
    lieu_dit = models.CharField(max_length=30, default='Non spécifiée')
    departement = models.CharField(max_length=5, default='00')
    coordonnees = models.CharField(max_length=30, default='0,0')
    latitude = models.CharField(max_length=15, default='0.0')
    longitude = models.CharField(max_length=15, default='0.0')
    altitude = models.CharField(max_length=10, default='0')
    paysage = models.TextField(default='Non spécifié')
    alentours = models.TextField(default='Non spécifié')

    def __str__(self):
        return f"Localisation {self.commune} ({self.departement})"

class Nid(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="nid")
    nid_prec_t_meme_couple = models.BooleanField(default=False)
    hauteur_nid = models.IntegerField(null=True, blank=True, default=0)
    hauteur_couvert = models.IntegerField(null=True, blank=True, default=0)
    details_nid = models.TextField(null=True, blank=True, default='Aucun détail')

    def __str__(self):
        return f"Nid de la fiche {self.fiche.num_fiche}"


class Observation(models.Model):
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="observations")
    date_observation = models.DateTimeField(auto_now_add=True)
    nombre_oeufs = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    nombre_poussins = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    observations = models.TextField(blank=True, null=True, default='Aucune observation')

    def save(self, *args, **kwargs):
        logger.info(f"Nouvelle observation ajoutée : {self.nom} à {self.date_observation}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Observation du {self.date_observation.strftime('%d/%m/%Y %H:%M')} (Fiche {self.fiche.num_fiche})"


class ResumeObservation(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="resume")
    premier_oeuf_pondu_jour = models.IntegerField(blank=True, null=True)
    premier_oeuf_pondu_mois = models.IntegerField(blank=True, null=True)
    premier_poussin_eclos_jour = models.IntegerField(blank=True, null=True)
    premier_poussin_eclos_mois = models.IntegerField(blank=True, null=True)
    premier_poussin_volant_jour = models.IntegerField(blank=True, null=True)
    premier_poussin_volant_mois = models.IntegerField(blank=True, null=True)
    nombre_oeufs_pondus = models.IntegerField(default=0)
    nombre_oeufs_eclos = models.IntegerField(default=0)
    nombre_oeufs_non_eclos = models.IntegerField(default=0)
    nombre_poussins = models.IntegerField(default=0)

    def __str__(self):
        return f"Résumé Fiche {self.fiche.num_fiche}"

class CausesEchec(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="causes_echec")
    description = models.TextField(blank=True, null=True, default='Aucune cause identifiée')

    def __str__(self):
        return f"Causes d'échec Fiche {self.fiche.num_fiche}"

class Remarque(models.Model):  # Correction du nom (majuscule par convention)
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="remarques")
    remarque = models.CharField(max_length=200, default='RAS')  # Correction de la valeur par défaut
    date_remarque = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        logger.info(f"Nouvelle remarque ajoutée : {self.remarque} à {self.date_remarque}")  # Correction ici
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Remarque du {self.date_remarque.strftime('%d/%m/%Y %H:%M')} (Fiche {self.fiche.num_fiche})"


class Validation(models.Model):
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="validations")
    reviewer = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'reviewer'})

    STATUTS = [
        ('en_cours', 'En cours'),
        ('validee', 'Validée'),
        ('rejete', 'Rejetée')
    ]

    date_modification = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=STATUTS, default='en_cours')

    def save(self, *args, **kwargs):
        # Vérifier si l'instance existe déjà pour récupérer l'ancien statut
        if self.pk:
            ancienne_instance = Validation.objects.filter(pk=self.pk).first()
            if ancienne_instance and ancienne_instance.statut != self.statut:
                HistoriqueValidation.objects.create(
                    validation=self,
                    ancien_statut=ancienne_instance.statut,
                    nouveau_statut=self.statut,
                    modifie_par=self.reviewer
                )

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_modification']  # Les plus récentes en premier

    def __str__(self):
        return f"Validation Fiche {self.fiche.num_fiche} par {self.reviewer.nom}"


class HistoriqueValidation(models.Model):
    validation = models.ForeignKey(Validation, on_delete=models.CASCADE, related_name="historique")
    ancien_statut = models.CharField(max_length=10, choices=Validation.STATUTS)
    nouveau_statut = models.CharField(max_length=10, choices=Validation.STATUTS)
    date_modification = models.DateTimeField(auto_now_add=True)
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_modification']  # Les plus récentes en premier

    def __str__(self):
        return f"Changement de {self.ancien_statut} à {self.nouveau_statut} (Fiche {self.validation.fiche.num_fiche})"


class HistoriqueModification(models.Model):
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="modifications")
    champ_modifie = models.CharField(max_length=100)
    ancienne_valeur = models.TextField()
    nouvelle_valeur = models.TextField()
    date_modification = models.DateTimeField(auto_now_add=True)

    CATEGORIES = [
        ('fiche', 'Fiche Observation'),
        ('observation', 'Observation'),
        ('validation', 'Validation'),
        ('localisation', 'Localisation'),
        ('nid', 'Nid'),
        ('resume_observation', 'Résumé Observation'),
        ('causes_echec', 'Causes d’échec')
    ]
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default='fiche', db_index=True)

    class Meta:
        verbose_name = "Historique de modification"
        verbose_name_plural = "Historiques des modifications"
        ordering = ['-date_modification']

    def __str__(self):
        return f"Modification {self.champ_modifie} ({self.date_modification})"
