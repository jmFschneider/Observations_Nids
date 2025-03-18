from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from Observations.models import (Utilisateur,
                                 FicheObservation, Espece)

class TestForm(forms.ModelForm):
    espece = forms.ModelChoiceField(queryset=Espece.objects.get_queryset(), empty_label="Sélectionnez une espèce", label="Espèce observée")
    annee = forms.IntegerField(initial=datetime.now().year, disabled=True, label="Année d'observation")
    observateur = forms.CharField(max_length=100, disabled=True, label="Observateur")

    class Meta:
        model = FicheObservation
        fields = ["num_fiche", "espece", "annee", "observateur", "chemin_image"]
        widgets = {
            "num_fiche": forms.TextInput(attrs={"readonly": True}), # Rendre le champ num_fiche non modifiable
        }

"""
class TestForm(forms.ModelForm):
    class Meta:
        model = FicheObservation
        exclude = ["date_creation"]  # Exclure date_creation
        fields = [
            "num_fiche",
            "observateur",
            "espece",
            "annee",
            "chemin_image",
        ]
"""
class UtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email']  # Correction ici

class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2']

