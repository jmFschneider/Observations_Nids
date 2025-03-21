from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from Observations.models import (Utilisateur,
                                 FicheObservation,
                                 Espece,
                                 Localisation,
                                 ResumeObservation,
                                 Nid,
                                 CausesEchec,
                                 Observation,
                                 Remarque)


class FicheObservationForm(forms.ModelForm):
    espece = forms.ModelChoiceField(queryset=Espece.objects.get_queryset(), empty_label="Sélectionnez une espèce",
                                    label="Espèce observée")
    annee = forms.IntegerField(initial=datetime.now().year, disabled=True, label="Année d'observation")

    class Meta:
        model = FicheObservation
        fields = ["espece", "annee", "chemin_image"]
        widgets = {
            "num_fiche": forms.TextInput(attrs={"readonly": True}),  # Rendre le champ num_fiche non modifiable
        }


class LocalisationForm(forms.ModelForm):
    class Meta:
        model = Localisation
        fields = ['commune', 'lieu_dit', 'departement', 'coordonnees',
                  'latitude', 'longitude', 'altitude', 'paysage', 'alentours']  # Définissez les champs pertinents


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations']
        widgets = {
            'date_observation': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class ResumeObservationForm(forms.ModelForm):
    class Meta:
        model = ResumeObservation
        fields = [
            'premier_oeuf_pondu_jour',
            'premier_oeuf_pondu_mois',
            'premier_poussin_eclos_jour',
            'premier_poussin_eclos_mois',
            'premier_poussin_volant_jour',
            'premier_poussin_volant_mois',
            'nombre_oeufs_pondus',
            'nombre_oeufs_eclos',
            'nombre_oeufs_non_eclos',
            'nombre_poussins',
        ]
        widgets = {
            'premier_oeuf_pondu_jour': forms.NumberInput(attrs={'placeholder': 'Jour', 'min': 1, 'max': 31}),
            'premier_oeuf_pondu_mois': forms.NumberInput(attrs={'placeholder': 'Mois', 'min': 1, 'max': 12}),
            'premier_poussin_eclos_jour': forms.NumberInput(attrs={'placeholder': 'Jour', 'min': 1, 'max': 31}),
            'premier_poussin_eclos_mois': forms.NumberInput(attrs={'placeholder': 'Mois', 'min': 1, 'max': 12}),
            'premier_poussin_volant_jour': forms.NumberInput(attrs={'placeholder': 'Jour', 'min': 1, 'max': 31}),
            'premier_poussin_volant_mois': forms.NumberInput(attrs={'placeholder': 'Mois', 'min': 1, 'max': 12}),
            'nombre_oeufs_pondus': forms.NumberInput(attrs={'min': 0}),
            'nombre_oeufs_eclos': forms.NumberInput(attrs={'min': 0}),
            'nombre_oeufs_non_eclos': forms.NumberInput(attrs={'min': 0}),
            'nombre_poussins': forms.NumberInput(attrs={'min': 0}),
        }


class NidForm(forms.ModelForm):
    class Meta:
        model = Nid
        fields = [
            'nid_prec_t_meme_couple',
            'hauteur_nid',
            'hauteur_couvert',
            'details_nid',
        ]
        widgets = {
            'nid_prec_t_meme_couple': forms.CheckboxInput(),
            'hauteur_nid': forms.NumberInput(attrs={'placeholder': 'hauteur_nid', 'min': 0}),
            'hauteur_couvert': forms.NumberInput(attrs={'placeholder': 'hauteur_couvert', 'min': 0}),
            'details_nid': forms.Textarea(attrs={'placeholder': 'details_nid'}),
        }


class CausesEchecForm(forms.ModelForm):
    class Meta:
        model = CausesEchec
        fields = [
            'description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'description'}),
        }


class RemarqueForm(forms.ModelForm):
    class Meta:
        model = Remarque
        fields = ['fiche', 'remarque']  # date_remarque est exclu
        widgets = {
            'remarque': forms.TextInput(attrs={'placeholder': 'Entrez une remarque'}),
        }


class UtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email']  # Correction ici


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2']
