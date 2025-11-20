import logging

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Utilisateur
from geo.models import Localisation
from taxonomy.models import Espece

logger = logging.getLogger('observations')


class FicheObservation(models.Model):
    num_fiche = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    observateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="fiches", db_index=True
    )
    espece = models.ForeignKey(Espece, on_delete=models.PROTECT, related_name="observations")
    annee = models.IntegerField()
    numero_personnel = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Numéro personnel',
        help_text='Numéro attribué par l\'observateur',
    )
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
            Localisation.objects.get_or_create(
                fiche=self,
                defaults={
                    'commune': '',
                    'lieu_dit': '',
                    'departement': '00',
                    'coordonnees': '0,0',
                    'altitude': '0',
                    'paysage': '',
                    'alentours': '',
                },
            )

            # Créer l'objet Nid s'il n'existe pas
            Nid.objects.get_or_create(
                fiche=self,
                defaults={
                    'nid_prec_t_meme_couple': False,
                    'hauteur_nid': None,
                    'hauteur_couvert': None,
                    'details_nid': '',
                },
            )

            # Créer l'objet ResumeObservation s'il n'existe pas
            # Les valeurs NULL indiquent "non observé"
            ResumeObservation.objects.get_or_create(
                fiche=self,
                defaults={
                    'nombre_oeufs_pondus': None,
                    'nombre_oeufs_eclos': None,
                    'nombre_oeufs_non_eclos': None,
                    'nombre_poussins': None,
                },
            )

            # Créer l'objet CausesEchec s'il n'existe pas
            CausesEchec.objects.get_or_create(fiche=self, defaults={'description': ''})

            # Créer l'objet EtatCorrection s'il n'existe pas
            EtatCorrection.objects.get_or_create(
                fiche=self,
                defaults={
                    'statut': 'nouveau',
                    'pourcentage_completion': 0,
                },
            )

            logger.info(f"Fiche d'observation #{self.num_fiche} créée avec tous les objets liés")

    def mettre_a_jour_etat_correction(self):
        """Met à jour l'état de correction de la fiche"""
        etat_correction, created = EtatCorrection.objects.get_or_create(
            fiche=self,
            defaults={
                'statut': 'nouveau',
                'pourcentage_completion': 0,
            },
        )
        etat_correction.calculer_pourcentage_completion()
        etat_correction.save(skip_auto_calculation=False)
        return etat_correction


class Nid(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="nid")
    nid_prec_t_meme_couple = models.BooleanField(default=False)
    fiche_precedente = models.ForeignKey(
        FicheObservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nids_suivants',
        verbose_name='Fiche précédente',
    )
    hauteur_nid = models.IntegerField(null=True, blank=True, default=None)
    hauteur_couvert = models.IntegerField(null=True, blank=True, default=None)
    details_nid = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Nid de la fiche {self.fiche.num_fiche}"


class Observation(models.Model):
    fiche = models.ForeignKey(
        'FicheObservation', on_delete=models.CASCADE, related_name="observations"
    )
    date_observation = models.DateTimeField(blank=False, null=False, db_index=True)
    heure_connue = models.BooleanField(
        default=True, help_text="Indique si l'heure d'observation est connue"
    )
    nombre_oeufs = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Laisser vide si non observé",
    )
    nombre_poussins = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Laisser vide si non observé",
    )
    observations = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['date_observation']

    def __str__(self):
        if self.heure_connue:
            date_str = self.date_observation.strftime('%d/%m/%Y %H:%M')
        else:
            date_str = self.date_observation.strftime('%d/%m/%Y')
        return f"Observation du {date_str} (Fiche {self.fiche.num_fiche})"

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

    # Compteurs (NULL = non observé, 0+ = valeur observée)
    nombre_oeufs_pondus = models.PositiveSmallIntegerField(blank=True, null=True)
    nombre_oeufs_eclos = models.PositiveSmallIntegerField(blank=True, null=True)
    nombre_oeufs_non_eclos = models.PositiveSmallIntegerField(blank=True, null=True)
    nombre_poussins = models.PositiveSmallIntegerField(blank=True, null=True)

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
            # Compteurs cohérents (uniquement si valeurs renseignées)
            models.CheckConstraint(
                name="resume_eclos_le_pondus",
                check=(
                    Q(nombre_oeufs_eclos__isnull=True)
                    | Q(nombre_oeufs_pondus__isnull=True)
                    | Q(nombre_oeufs_eclos__lte=models.F("nombre_oeufs_pondus"))
                ),
            ),
            models.CheckConstraint(
                name="resume_non_eclos_le_pondus",
                check=(
                    Q(nombre_oeufs_non_eclos__isnull=True)
                    | Q(nombre_oeufs_pondus__isnull=True)
                    | Q(nombre_oeufs_non_eclos__lte=models.F("nombre_oeufs_pondus"))
                ),
            ),
            models.CheckConstraint(
                name="resume_poussins_le_eclos",
                check=(
                    Q(nombre_poussins__isnull=True)
                    | Q(nombre_oeufs_eclos__isnull=True)
                    | Q(nombre_poussins__lte=models.F("nombre_oeufs_eclos"))
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"Résumé Fiche {self.fiche.num_fiche}"


class CausesEchec(models.Model):
    fiche = models.OneToOneField(
        FicheObservation, on_delete=models.CASCADE, related_name="causes_echec"
    )
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Causes d'échec Fiche {self.fiche.num_fiche}"


class Remarque(models.Model):
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="remarques")
    remarque = models.CharField(max_length=200, blank=True, default='')
    date_remarque = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Remarque du {self.date_remarque.strftime('%d/%m/%Y %H:%M')} (Fiche {self.fiche.num_fiche})"

    def save(self, *args, **kwargs):
        logger.info(f"Nouvelle remarque ajoutée : {self.remarque} à {self.date_remarque}")
        super().save(*args, **kwargs)


class EtatCorrection(models.Model):
    STATUTS_CHOICES = [
        ('nouveau', 'Nouvelle fiche'),
        ('en_edition', 'En cours d\'édition'),
        ('en_cours', 'En cours de correction'),
        ('valide', 'Validée'),
    ]

    fiche = models.OneToOneField(
        FicheObservation, on_delete=models.CASCADE, related_name="etat_correction"
    )
    statut = models.CharField(max_length=20, choices=STATUTS_CHOICES, default='nouveau')
    pourcentage_completion = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    date_derniere_modification = models.DateTimeField(auto_now=True)
    validee_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name="validations"
    )
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="etat_correction_pourcentage_valide",
                check=Q(pourcentage_completion__gte=0) & Q(pourcentage_completion__lte=100),
            ),
        ]

    def __str__(self):
        return f"État correction Fiche {self.fiche.num_fiche} - {self.get_statut_display()}"

    def save(self, *args, **kwargs):
        # Calculer automatiquement le pourcentage avant la sauvegarde
        if not kwargs.pop('skip_auto_calculation', False):
            self.calculer_pourcentage_completion()
        super().save(*args, **kwargs)

    def calculer_pourcentage_completion(self):
        """Calcule automatiquement le pourcentage de completion basé sur les données de la fiche"""
        score = 0
        total_criteres = 8

        # Critère 1: Observateur renseigné (1 point)
        if self.fiche.observateur:
            score += 1

        # Critère 2: Espèce renseignée (1 point)
        if self.fiche.espece:
            score += 1

        # Critère 3: Localisation complète (1 point)
        if hasattr(self.fiche, 'localisation'):
            loc = self.fiche.localisation
            if (
                loc.commune
                and loc.commune.strip()  # Vérifier que la commune n'est pas vide
                and loc.departement
                and loc.departement != '00'
            ):
                score += 1

        # Critère 4: Au moins une observation avec date (1 point)
        if self.fiche.observations.exists():
            score += 1

        # Critère 5: Résumé avec données d'œufs (1 point)
        if hasattr(self.fiche, 'resume'):
            resume = self.fiche.resume
            if resume.nombre_oeufs_pondus is not None and resume.nombre_oeufs_pondus > 0:
                score += 1

        # Critère 6: Détails du nid renseignés (1 point)
        if hasattr(self.fiche, 'nid'):
            nid = self.fiche.nid
            if nid.details_nid and nid.details_nid != 'Aucun détail':
                score += 1

        # Critère 7: Hauteur du nid renseignée (1 point)
        if hasattr(self.fiche, 'nid'):
            nid = self.fiche.nid
            if nid.hauteur_nid is not None and nid.hauteur_nid > 0:
                score += 1

        # Critère 8: Image associée (1 point)
        if self.fiche.chemin_image:
            score += 1

        pourcentage = int((score / total_criteres) * 100)

        # Mettre à jour le statut automatiquement
        # Passer en "en_edition" si la fiche est en cours de saisie par l'observateur
        if pourcentage > 0 and self.statut == 'nouveau':
            self.statut = 'en_edition'
        # Ne pas changer le statut si déjà en_edition, en_cours ou valide

        self.pourcentage_completion = pourcentage
        return pourcentage

    def valider(self, utilisateur):
        """Marque la fiche comme validée par un utilisateur"""
        self.statut = 'valide'
        self.validee_par = utilisateur
        self.date_validation = timezone.now()
        self.save()


class ImageSource(models.Model):
    """
    Représente une image de fiche d'observation téléversée par un utilisateur,
    en attente de transcription.
    """

    # LIEN VERS L'UTILISATEUR
    observateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="images_sources",
        verbose_name="Observateur",
    )

    # GESTION DU FICHIER IMAGE
    image = models.ImageField(upload_to='images_sources/%Y/%m/%d/', verbose_name="Fichier image")

    # STATUT DE LA TRANSCRIPTION
    est_transcrite = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Est transcrite",
        help_text="Indique si une FicheObservation a été créée à partir de cette image.",
    )

    # INFORMATIONS DE SUIVI
    date_televersement = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de téléversement"
    )

    # LIEN VERS LA FICHE FINALE (Optionnel mais recommandé)
    fiche_observation = models.OneToOneField(
        FicheObservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="image_source_originale",
        verbose_name="Fiche d'observation associée",
    )

    class Meta:
        verbose_name = "Image source"
        verbose_name_plural = "Images sources"
        ordering = ['-date_televersement']

    def __str__(self):
        return f"Image {self.id} de {self.observateur.username} ({'transcrite' if self.est_transcrite else 'en attente'})"
