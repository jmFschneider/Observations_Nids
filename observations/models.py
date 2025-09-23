# observations/models.py
import logging

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q

# Importer le modèle Utilisateur depuis administration
from administration.models import Utilisateur

logger = logging.getLogger('observations')


class Ordre(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom


class Famille(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    ordre = models.ForeignKey(Ordre, on_delete=models.CASCADE, related_name='familles')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom


class Espece(models.Model):
    nom = models.CharField(max_length=100, unique=True)  # Remplace 'nom_français'
    nom_anglais = models.CharField(max_length=100, blank=True)
    nom_scientifique = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=50, blank=True)
    famille = models.ForeignKey(
        Famille, on_delete=models.SET_NULL, blank=True, null=True, related_name='especes'
    )
    commentaire = models.TextField(blank=True, default="")
    lien_oiseau_net = models.URLField(blank=True)
    valide_par_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.nom


class FicheObservation(models.Model):
    num_fiche = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    observateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="fiches", db_index=True
    )
    espece = models.ForeignKey(Espece, on_delete=models.PROTECT, related_name="observations")
    annee = models.IntegerField()
    chemin_image = models.CharField(max_length=255, blank=True)
    chemin_json = models.CharField(max_length=255, blank=True)
    transcription = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['observateur', 'date_creation']),
        ]

    def __str__(self):
        return f"Fiche {self.num_fiche} - {self.annee} ({self.espece.nom})"

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si c'est une nouvelle fiche, créer automatiquement les objets liés
        if is_new:
            # Créer l'objet Localisation s'il n'existe pas
            Localisation.objects.get_or_create(
                fiche=self,
                defaults={
                    'commune': 'Non spécifiée',
                    'lieu_dit': 'Non spécifiée',
                    'departement': '00',
                    'coordonnees': '0,0',
                    'altitude': '0',
                    'paysage': 'Non spécifié',
                    'alentours': 'Non spécifié',
                },
            )

            # Créer l'objet Nid s'il n'existe pas
            Nid.objects.get_or_create(
                fiche=self,
                defaults={
                    'nid_prec_t_meme_couple': False,
                    'hauteur_nid': 0,
                    'hauteur_couvert': 0,
                    'details_nid': 'Aucun détail',
                },
            )

            # Créer l'objet ResumeObservation s'il n'existe pas
            ResumeObservation.objects.get_or_create(
                fiche=self,
                defaults={
                    'nombre_oeufs_pondus': 0,
                    'nombre_oeufs_eclos': 0,
                    'nombre_oeufs_non_eclos': 0,
                    'nombre_poussins': 0,
                },
            )

            # Créer l'objet CausesEchec s'il n'existe pas
            CausesEchec.objects.get_or_create(
                fiche=self, defaults={'description': 'Aucune cause identifiée'}
            )

            logger.info(f"Fiche d'observation #{self.num_fiche} créée avec tous les objets liés")


class Localisation(models.Model):
    fiche = models.OneToOneField(
        FicheObservation, on_delete=models.CASCADE, related_name="localisation"
    )
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
    details_nid = models.TextField(blank=True, default='Aucun détail')

    def __str__(self):
        return f"Nid de la fiche {self.fiche.num_fiche}"


class Observation(models.Model):
    fiche = models.ForeignKey(
        'FicheObservation', on_delete=models.CASCADE, related_name="observations"
    )
    date_observation = models.DateTimeField(blank=False, null=False, db_index=True)
    nombre_oeufs = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    nombre_poussins = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    observations = models.TextField(blank=True, default='Aucune observation')

    def __str__(self):
        return f"Observation du {self.date_observation.strftime('%d/%m/%Y %H:%M')} (Fiche {self.fiche.num_fiche})"

    def save(self, *args, **kwargs):
        logger.info(
            f"Nouvelle observation ajoutée : Fiche {self.fiche.num_fiche} à {self.date_observation}"
        )
        super().save(*args, **kwargs)


class ResumeObservation(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="resume")

    # Dates partielles (jour/mois) : valeurs optionnelles + bornes
    premier_oeuf_pondu_jour = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    premier_oeuf_pondu_mois = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    premier_poussin_eclos_jour = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    premier_poussin_eclos_mois = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    premier_poussin_volant_jour = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    premier_poussin_volant_mois = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    # Compteurs (toujours non négatifs)
    nombre_oeufs_pondus = models.PositiveSmallIntegerField(default=0)
    nombre_oeufs_eclos = models.PositiveSmallIntegerField(default=0)
    nombre_oeufs_non_eclos = models.PositiveSmallIntegerField(default=0)
    nombre_poussins = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            # Paires jour/mois : soit les deux NULL, soit les deux renseignés
            models.CheckConstraint(
                name="resume_premier_oeuf_pondu_jour_mois_both_or_none",
                check=(
                    (
                        Q(premier_oeuf_pondu_jour__isnull=True)
                        & Q(premier_oeuf_pondu_mois__isnull=True)
                    )
                    | (
                        Q(premier_oeuf_pondu_jour__isnull=False)
                        & Q(premier_oeuf_pondu_mois__isnull=False)
                    )
                ),
            ),
            models.CheckConstraint(
                name="resume_premier_poussin_eclos_jour_mois_both_or_none",
                check=(
                    (
                        Q(premier_poussin_eclos_jour__isnull=True)
                        & Q(premier_poussin_eclos_mois__isnull=True)
                    )
                    | (
                        Q(premier_poussin_eclos_jour__isnull=False)
                        & Q(premier_poussin_eclos_mois__isnull=False)
                    )
                ),
            ),
            models.CheckConstraint(
                name="resume_premier_poussin_volant_jour_mois_both_or_none",
                check=(
                    (
                        Q(premier_poussin_volant_jour__isnull=True)
                        & Q(premier_poussin_volant_mois__isnull=True)
                    )
                    | (
                        Q(premier_poussin_volant_jour__isnull=False)
                        & Q(premier_poussin_volant_mois__isnull=False)
                    )
                ),
            ),
            # Compteurs cohérents
            models.CheckConstraint(
                name="resume_counts_non_negative",
                check=(
                    Q(nombre_oeufs_pondus__gte=0)
                    & Q(nombre_oeufs_eclos__gte=0)
                    & Q(nombre_oeufs_non_eclos__gte=0)
                    & Q(nombre_poussins__gte=0)
                ),
            ),
            models.CheckConstraint(
                name="resume_eclos_le_pondus",
                check=Q(nombre_oeufs_eclos__lte=models.F("nombre_oeufs_pondus")),
            ),
            models.CheckConstraint(
                name="resume_non_eclos_le_pondus",
                check=Q(nombre_oeufs_non_eclos__lte=models.F("nombre_oeufs_pondus")),
            ),
            models.CheckConstraint(
                name="resume_poussins_le_eclos",
                check=Q(nombre_poussins__lte=models.F("nombre_oeufs_eclos")),
            ),
        ]

    def __str__(self) -> str:
        return f"Résumé Fiche {self.fiche.num_fiche}"


class CausesEchec(models.Model):
    fiche = models.OneToOneField(
        FicheObservation, on_delete=models.CASCADE, related_name="causes_echec"
    )
    description = models.TextField(blank=True, default='Aucune cause identifiée')

    def __str__(self):
        return f"Causes d'échec Fiche {self.fiche.num_fiche}"


class Remarque(models.Model):
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="remarques")
    remarque = models.CharField(max_length=200, default='RAS')
    date_remarque = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Remarque du {self.date_remarque.strftime('%d/%m/%Y %H:%M')} (Fiche {self.fiche.num_fiche})"

    def save(self, *args, **kwargs):
        logger.info(f"Nouvelle remarque ajoutée : {self.remarque} à {self.date_remarque}")
        super().save(*args, **kwargs)


class Validation(models.Model):
    fiche = models.ForeignKey(
        FicheObservation, on_delete=models.CASCADE, related_name="validations"
    )
    reviewer = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'reviewer'}
    )

    STATUTS = [('en_cours', 'En cours'), ('validee', 'Validée'), ('rejete', 'Rejetée')]

    statut = models.CharField(max_length=10, choices=STATUTS, default='en_cours')

    date_modification = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_modification']  # Les plus récentes en premier

    def __str__(self):
        return f"Validation Fiche {self.fiche.num_fiche} par {self.reviewer.username}"

    def save(self, *args, **kwargs):
        # Vérifier si l'instance existe déjà pour récupérer l'ancien statut
        if self.pk:
            ancienne_instance = Validation.objects.filter(pk=self.pk).first()
            if ancienne_instance and ancienne_instance.statut != self.statut:
                HistoriqueValidation.objects.create(
                    validation=self,
                    ancien_statut=ancienne_instance.statut,
                    nouveau_statut=self.statut,
                    modifie_par=self.reviewer,
                )

        super().save(*args, **kwargs)


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
    fiche = models.ForeignKey(
        FicheObservation, on_delete=models.CASCADE, related_name="modifications"
    )
    champ_modifie = models.CharField(max_length=100)
    ancienne_valeur = models.TextField()
    nouvelle_valeur = models.TextField()
    date_modification = models.DateTimeField(auto_now_add=True)
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    CATEGORIES = [
        ('fiche', 'Fiche Observation'),
        ('observation', 'Observation'),
        ('validation', 'Validation'),
        ('localisation', 'Localisation'),
        ('nid', 'Nid'),
        ('resume_observation', 'Résumé Observation'),
        ('causes_echec', 'Causes d’échec'),
    ]
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default='fiche', db_index=True)

    class Meta:
        verbose_name = "Historique de modification"
        verbose_name_plural = "Historiques des modifications"
        ordering = ['-date_modification']

    def __str__(self):
        modifie_par_str = f" par {self.modifie_par.username}" if self.modifie_par else ""
        return f"Modification {self.champ_modifie} ({self.date_modification}){modifie_par_str}"
