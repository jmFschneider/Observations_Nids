
from django.db import models


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
    nom = models.CharField(max_length=100, unique=True)
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
