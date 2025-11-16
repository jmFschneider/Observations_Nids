from django import forms
from django.utils import timezone

from geo.models import Localisation
from geo.services.geocodeur import geocoder_commune_unifiee
from observations.models import (
    CausesEchec,
    FicheObservation,
    ImageSource,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)


class FicheObservationForm(forms.ModelForm):
    class Meta:
        model = FicheObservation
        fields = ["observateur", "espece", "annee", "numero_personnel", "chemin_image"]
        widgets = {
            "observateur": forms.HiddenInput(),  # Changer pour HiddenInput
            "espece": forms.Select(
                attrs={
                    'class': 'form-control espece-select',
                    'data-live-search': 'true',
                    'data-search-delay': '800',  # Délai de 800ms entre les frappes
                }
            ),
            "numero_personnel": forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-sm',
                    'placeholder': 'N°',
                    'min': 1,
                    'style': 'width: 80px;',
                }
            ),
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
            'commune': forms.TextInput(
                attrs={
                    'class': 'form-field',
                    'id': 'id_commune',
                    'placeholder': 'Commune',
                    'autocomplete': 'off',
                }
            ),
            'lieu_dit': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Lieu-dit'}),
            'departement': forms.TextInput(
                attrs={
                    'class': 'form-field',
                    'id': 'id_departement',
                    'placeholder': 'Département',
                    'readonly': 'readonly',
                }
            ),
            'coordonnees': forms.TextInput(
                attrs={'class': 'form-field', 'placeholder': 'Coordonnées'}
            ),
            'latitude': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Latitude'}),
            'longitude': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Longitude'}),
            'altitude': forms.TextInput(attrs={'class': 'form-field', 'placeholder': 'Altitude'}),
            'paysage': forms.Textarea(
                attrs={
                    'class': 'section-content',
                    'rows': 2,
                    'placeholder': 'Description du paysage',
                }
            ),
            'alentours': forms.Textarea(
                attrs={
                    'class': 'section-content',
                    'rows': 2,
                    'placeholder': 'Description des alentours',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.coordonnees:
            self.fields['coordonnees'].initial = '0,0'

    def save(self, commit=True):
        """
        Surcharge pour gérer automatiquement commune_saisie et commune
        selon qu'il s'agit d'une ancienne commune ou non
        """

        instance = super().save(commit=False)

        # Si une commune est renseignée, vérifier s'il s'agit d'une ancienne commune
        if instance.commune:
            resultat = geocoder_commune_unifiee(instance.commune)
            if resultat:
                # Enregistrer le nom saisi par l'utilisateur
                instance.commune_saisie = instance.commune

                # Si c'est une ancienne commune fusionnée, normaliser vers la commune actuelle
                if resultat['est_fusionnee']:
                    instance.commune = resultat['commune_actuelle']
                # Sinon, on garde tel quel (commune actuelle)

        if commit:
            instance.save()
        return instance


class ObservationForm(forms.ModelForm):
    # Déclarer explicitement le champ date_observation avec SplitDateTimeField
    date_observation = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            date_attrs={'type': 'date', 'class': 'clear-on-focus date-input'},
            time_attrs={'type': 'time', 'class': 'clear-on-focus time-input'},
            date_format='%Y-%m-%d',
            time_format='%H:%M',
        ),
        input_date_formats=['%Y-%m-%d'],
        input_time_formats=['%H:%M', '%H:%M:%S'],
        required=True,
    )

    class Meta:
        model = Observation
        fields = [
            'date_observation',
            'heure_connue',
            'nombre_oeufs',
            'nombre_poussins',
            'observations',
        ]
        widgets = {
            'heure_connue': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'id': 'id_heure_connue'}
            ),
            'nombre_oeufs': forms.NumberInput(
                attrs={'class': 'clear-on-focus', 'placeholder': 'Nombre d\'œufs'}
            ),
            'nombre_poussins': forms.NumberInput(
                attrs={'class': 'clear-on-focus', 'placeholder': 'Nombre de poussins'}
            ),
            'observations': forms.Textarea(
                attrs={
                    'class': 'section-content clear-on-focus',
                    'rows': 1,
                    'placeholder': 'Observation',
                    'style': 'min-height: 30px; width: 250px; max-width: 100%; resize: vertical;',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure date_observation is properly formatted for the split date/time inputs
        if self.instance.pk and self.instance.date_observation:
            # Convert the stored UTC time to the local timezone
            local_dt = timezone.localtime(self.instance.date_observation)
            # SplitDateTimeField expects a datetime object, Django will handle the split
            self.initial['date_observation'] = local_dt

    def clean(self):
        """
        Validate and process form data.
        If heure_connue is False, set time to 00:00:00.
        """
        cleaned_data = super().clean()
        date_observation = cleaned_data.get('date_observation')
        heure_connue = cleaned_data.get('heure_connue', True)

        if not date_observation:
            raise forms.ValidationError({'date_observation': "Ce champ est obligatoire."})

        # Si l'heure n'est pas connue, on la met à 00:00:00
        if not heure_connue:
            cleaned_data['date_observation'] = date_observation.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        return cleaned_data


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
            'nombre_oeufs_pondus': forms.NumberInput(
                attrs={'min': 0, 'placeholder': 'Non observé'}
            ),
            'nombre_oeufs_eclos': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Non observé'}),
            'nombre_oeufs_non_eclos': forms.NumberInput(
                attrs={'min': 0, 'placeholder': 'Non observé'}
            ),
            'nombre_poussins': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Non observé'}),
        }

    def clean_nombre_oeufs_pondus(self):
        value = self.cleaned_data.get('nombre_oeufs_pondus')
        return None if value == '' or value is None else value

    def clean_nombre_oeufs_eclos(self):
        value = self.cleaned_data.get('nombre_oeufs_eclos')
        return None if value == '' or value is None else value

    def clean_nombre_oeufs_non_eclos(self):
        value = self.cleaned_data.get('nombre_oeufs_non_eclos')
        return None if value == '' or value is None else value

    def clean_nombre_poussins(self):
        value = self.cleaned_data.get('nombre_poussins')
        return None if value == '' or value is None else value


# utilisation de la form Django personnalisé avec mon css
class NidForm(forms.ModelForm):
    class Meta:
        model = Nid
        fields = [
            'nid_prec_t_meme_couple',
            'fiche_precedente',
            'hauteur_nid',
            'hauteur_couvert',
            'details_nid',
        ]
        widgets = {
            'nid_prec_t_meme_couple': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fiche_precedente': forms.NumberInput(
                attrs={
                    'class': 'form-field',
                    'placeholder': 'N° fiche précédente',
                    'min': 1,
                    'style': 'width: 120px;',
                }
            ),
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
            'description': forms.Textarea(
                attrs={'placeholder': 'Description des causes d\'échec', 'rows': 2}
            ),
        }


class RemarqueForm(forms.ModelForm):
    class Meta:
        model = Remarque
        fields = ['remarque']  # fiche sera assignée automatiquement, date_remarque est exclu
        widgets = {
            'remarque': forms.Textarea(
                attrs={
                    'placeholder': 'Entrez une remarque',
                    'rows': 2,
                    'style': 'width: 100%; resize: vertical;',
                }
            ),
        }


# Formset pour gérer plusieurs remarques
RemarqueFormSet = forms.inlineformset_factory(
    FicheObservation,
    Remarque,
    form=RemarqueForm,
    extra=1,  # Une ligne vide pour ajouter une nouvelle remarque
    can_delete=True,  # Permet de supprimer des remarques
    min_num=0,  # Aucune remarque minimum requise
    validate_min=True,
)


class ImageSourceForm(forms.ModelForm):
    class Meta:
        model = ImageSource
        fields = ['image']  # Only allow uploading the image file


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
