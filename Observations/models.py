from django.db import models


class Utilisateur(models.Model):
    ROLES = [
        ('observateur', 'Observateur'),
        ('reviewer', 'Reviewer'),
        ('administrateur', 'Administrateur')
    ]

    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=15, choices=ROLES, default='observateur')
    est_valide = models.BooleanField(default=False)  # Validation par l'administrateur

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"


class Espece(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    commentaire = models.TextField(blank=True, null=True)
    lien_oiseau_net = models.URLField(blank=True, null=True)
    valide_par_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.nom


class FicheObservation(models.Model):
    num_fiche = models.AutoField(primary_key=True)  # Numéro de fiche auto-incrémenté
    observateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="fiches")
    espece = models.ForeignKey(Espece, on_delete=models.PROTECT, related_name="observations")
    annee = models.IntegerField()
    chemin_image = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Fiche {self.num_fiche} - {self.annee} ({self.espece.nom})"


class Localisation(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="localisation")
    commune = models.CharField(max_length=100)
    departement = models.CharField(max_length=10)
    coordonnees = models.CharField(max_length=100, blank=True, null=True)
    altitude = models.CharField(max_length=10, blank=True, null=True)
    paysage = models.TextField(blank=True, null=True)
    alentours = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Localisation {self.commune} ({self.departement})"


class Nid(models.Model):
    fiche = models.OneToOneField(FicheObservation, on_delete=models.CASCADE, related_name="nid")
    nid_prec_t_meme_couple = models.BooleanField(default=False)
    hauteur_nid = models.IntegerField(null=True, blank=True)
    hauteur_couvert = models.IntegerField(null=True, blank=True)
    details_nid = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Nid de la fiche {self.fiche.num_fiche}"


class Observation(models.Model):
    fiche = models.ForeignKey(FicheObservation, on_delete=models.CASCADE, related_name="observations")
    jour = models.IntegerField()
    mois = models.IntegerField()
    heure = models.CharField(max_length=10)
    nombre_oeufs = models.IntegerField(default=0)
    nombre_poussins = models.IntegerField(default=0)
    observations = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Observation du {self.jour}/{self.mois} (Fiche {self.fiche.num_fiche})"


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
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Causes d'échec Fiche {self.fiche.num_fiche}"


class Validation(models.Model):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE, related_name="validations")
    reviewer = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'reviewer'})
    date_validation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Validation {self.observation.fiche.num_fiche} par {self.reviewer.nom}"


class HistoriqueModification(models.Model):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE, related_name="modifications")
    champ_modifie = models.CharField(max_length=100)
    ancienne_valeur = models.TextField()
    nouvelle_valeur = models.TextField()
    date_modification = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Modification {self.champ_modifie} ({self.date_modification})"