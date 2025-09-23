# observations/forms.py
from django import forms

from observations.models import (
    CausesEchec,
    FicheObservation,
    Localisation,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)


class FicheObservationForm(forms.ModelForm):
    class Meta:
        model = FicheObservation
        fields = ["observateur", "espece", "annee", "chemin_image"]
        widgets = {
            "observateur": forms.HiddenInput(),  # Changer pour HiddenInput
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Définir l'observateur comme l'utilisateur actuel
            if not self.instance.pk:  # Nouvelle instance
                self.instance.observateur = user

            # Toujours définir la valeur initiale
            self.fields["observateur"].initial = user.id

            # Pour les non-admins/reviewers, désactiver mais garder la valeur
            if user.role not in ['administrateur', 'reviewer']:
                self.fields["observateur"].disabled = True


class LocalisationForm(forms.ModelForm):
    class Meta:
        model = Localisation
        fields = [
            'commune',
            'lieu_dit',
            'departement',
            'coordonnees',
            'latitude',
            'longitude',
            'altitude',
            'paysage',
            'alentours',
        ]
        widgets = {
            'commune': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Commune'}),
            'lieu_dit': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Lieu-dit'}),
            'departement': forms.TextInput(
                attrs={'class': 'form-field', 'placeholder': 'Département'}
            ),
            'coordonnees': forms.TextInput(
                attrs={'class': 'form-field', 'placeholder': 'Coordonnées'}
            ),
            'latitude': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Latitude'}),
            'longitude': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Longitude'}),
            'altitude': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Altitude'}),
            'paysage': forms.Textarea(attrs={'class': 'section-content', 'rows': 2}),
            'alentours': forms.Textarea(attrs={'class': 'section-content', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.coordonnees:
            self.fields['coordonnees'].initial = '0,0'


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['date_observation', 'nombre_oeufs', 'nombre_poussins', 'observations']
        widgets = {
            'date_observation': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'observations': forms.Textarea(
                attrs={
                    'class': 'section-content',
                    'rows': 1,
                    'placeholder': 'Observation',
                    'style': 'min-height: 30px; width: 250px; max-width: 100%; resize: vertical;',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure date_observation is properly formatted for the datetime-local input
        if self.instance.pk and self.instance.date_observation:
            # Format the existing date for the datetime-local input
            self.initial['date_observation'] = self.instance.date_observation.strftime(
                '%Y-%m-%dT%H:%M'
            )

    def clean_date_observation(self):
        """
        Ensure the date_observation field is properly processed.
        This method is called during form validation.
        """
        date_observation = self.cleaned_data.get('date_observation')
        if not date_observation:
            raise forms.ValidationError("Ce champ est obligatoire.")
        return date_observation


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
            'premier_oeuf_pondu_jour': forms.NumberInput(
                attrs={'placeholder': 'Jour', 'min': 1, 'max': 31}
            ),
            'premier_oeuf_pondu_mois': forms.NumberInput(
                attrs={'placeholder': 'Mois', 'min': 1, 'max': 12}
            ),
            'premier_poussin_eclos_jour': forms.NumberInput(
                attrs={'placeholder': 'Jour', 'min': 1, 'max': 31}
            ),
            'premier_poussin_eclos_mois': forms.NumberInput(
                attrs={'placeholder': 'Mois', 'min': 1, 'max': 12}
            ),
            'premier_poussin_volant_jour': forms.NumberInput(
                attrs={'placeholder': 'Jour', 'min': 1, 'max': 31}
            ),
            'premier_poussin_volant_mois': forms.NumberInput(
                attrs={'placeholder': 'Mois', 'min': 1, 'max': 12}
            ),
            'nombre_oeufs_pondus': forms.NumberInput(attrs={'min': 0}),
            'nombre_oeufs_eclos': forms.NumberInput(attrs={'min': 0}),
            'nombre_oeufs_non_eclos': forms.NumberInput(attrs={'min': 0}),
            'nombre_poussins': forms.NumberInput(attrs={'min': 0}),
        }


# utilisation de la form Django personnalisé avec mon css
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
            'nid_prec_t_meme_couple': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hauteur_nid': forms.NumberInput(
                attrs={'class': 'form-field', 'placeholder': 'hauteur_nid', 'min': 0}
            ),
            'hauteur_couvert': forms.NumberInput(
                attrs={'class': 'form-field', 'placeholder': 'hauteur_couvert', 'min': 0}
            ),
            'details_nid': forms.Textarea(
                attrs={'class': 'section-content', 'rows': 2, 'placeholder': 'Détails du nid'}
            ),
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


#
# class UtilisateurForm(forms.ModelForm):
#     class Meta:
#         model = Utilisateur
#         fields = ['first_name', 'last_name', 'email']  # Correction ici
#
#
# class InscriptionForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#
#     class Meta:
#         model = Utilisateur
#         fields = ['username', 'email', 'password1', 'password2']
