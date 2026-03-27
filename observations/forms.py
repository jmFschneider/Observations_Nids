from django import forms
from django.utils import timezone

from accounts.models import Utilisateur
from geo.models import Localisation
from geo.services.geocodeur import geocoder_commune_unifiee
from observations.models import (
    CausesEchec,
    FicheObservation,
    ImageSource,
    Nid,
    NoteCorrection,
    Observation,
    Remarque,
    ResumeObservation,
)


class FicheObservationForm(forms.ModelForm):
    # Définir explicitement le champ observateur comme ModelChoiceField pour le rendre modifiable
    observateur = forms.ModelChoiceField(
        queryset=Utilisateur.objects.all(),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),
        required=True,
        label="Observateur",
    )

    class Meta:
        model = FicheObservation
        fields = ["observateur", "espece", "annee", "numero_personnel", "chemin_image"]
        widgets = {
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

        # Stocker l'utilisateur pour l'utiliser comme fallback dans save()
        self.user = user

        # Configurer le queryset des observateurs (utilisateurs actifs et validés)
        observateur_queryset = Utilisateur.objects.filter(is_active=True, est_valide=True)
        if self.instance.pk and self.instance.observateur:
            observateur_queryset = observateur_queryset | Utilisateur.objects.filter(
                pk=self.instance.observateur.pk
            )
        if user and user.pk:
            observateur_queryset = observateur_queryset | Utilisateur.objects.filter(pk=user.pk)
        self.fields["observateur"].queryset = observateur_queryset.order_by(
            'first_name', 'last_name'
        )

        # Définir la valeur initiale si c'est une nouvelle instance
        if user and (not self.instance.pk or not self.instance.observateur):  # Nouvelle instance
            self.fields["observateur"].initial = user

    def save(self, commit=True):
        """Sauvegarder avec la valeur du formulaire pour l'observateur."""
        instance = super().save(commit=False)

        # Utiliser la valeur du formulaire si fournie, sinon utiliser l'utilisateur courant comme fallback
        if not instance.observateur and self.user:
            instance.observateur = self.user

        if commit:
            instance.save()

        return instance


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

    # Surcharger les champs nombre_oeufs et nombre_poussins pour accepter "5?" et "?"
    nombre_oeufs = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'type': 'text',
                'class': 'clear-on-focus nombre-avec-incertitude',
                'placeholder': 'Nombre d\'œufs (ex: 5, 5? ou ?)',
                'inputmode': 'numeric',
                'autocomplete': 'off',
            }
        ),
    )

    nombre_poussins = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'type': 'text',
                'class': 'clear-on-focus nombre-avec-incertitude',
                'placeholder': 'Nombre de poussins (ex: 3, 3? ou ?)',
                'inputmode': 'numeric',
                'autocomplete': 'off',
            }
        ),
    )

    class Meta:
        model = Observation
        fields = [
            'date_observation',
            'heure_connue',
            'nombre_oeufs',
            'nombre_oeufs_incertain',
            'nombre_poussins',
            'nombre_poussins_incertain',
            'observations',
        ]
        widgets = {
            'heure_connue': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'id': 'id_heure_connue'}
            ),
            'nombre_oeufs_incertain': forms.HiddenInput(),
            'nombre_poussins_incertain': forms.HiddenInput(),
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

        # Restaurer le "?" pour les champs avec incertitude
        if self.instance.pk:
            if self.instance.nombre_oeufs_incertain:
                if self.instance.nombre_oeufs is None:
                    self.initial['nombre_oeufs'] = '?'
                else:
                    self.initial['nombre_oeufs'] = f"{self.instance.nombre_oeufs}?"

            if self.instance.nombre_poussins_incertain:
                if self.instance.nombre_poussins is None:
                    self.initial['nombre_poussins'] = '?'
                else:
                    self.initial['nombre_poussins'] = f"{self.instance.nombre_poussins}?"

    def clean_nombre_oeufs(self):
        """Valide et nettoie le champ nombre_oeufs (accepte '5', '5?' ou '?')"""
        value = self.cleaned_data.get('nombre_oeufs', '').strip()

        if not value:
            return None
        if value == '?':
            return None

        # Vérifier le pattern valide
        if not value.replace('?', '').isdigit():
            raise forms.ValidationError(
                "Saisie invalide. Utilisez uniquement des chiffres, éventuellement suivis de '?' (ex: 5 ou 5?)"
            )

        # Extraire le nombre
        nombre_str = value.rstrip('?')
        if not nombre_str:
            raise forms.ValidationError("Veuillez saisir un nombre (ex: 5 ou 5?)")

        try:
            return int(nombre_str)
        except ValueError as err:
            raise forms.ValidationError(
                "Valeur invalide. Utilisez un nombre entier (ex: 5 ou 5?)"
            ) from err

    def clean_nombre_poussins(self):
        """Valide et nettoie le champ nombre_poussins (accepte '3', '3?' ou '?')"""
        value = self.cleaned_data.get('nombre_poussins', '').strip()

        if not value:
            return None
        if value == '?':
            return None

        # Vérifier le pattern valide
        if not value.replace('?', '').isdigit():
            raise forms.ValidationError(
                "Saisie invalide. Utilisez uniquement des chiffres, éventuellement suivis de '?' (ex: 3 ou 3?)"
            )

        # Extraire le nombre
        nombre_str = value.rstrip('?')
        if not nombre_str:
            raise forms.ValidationError("Veuillez saisir un nombre (ex: 3 ou 3?)")

        try:
            return int(nombre_str)
        except ValueError as err:
            raise forms.ValidationError(
                "Valeur invalide. Utilisez un nombre entier (ex: 3 ou 3?)"
            ) from err

    def clean(self):
        """
        Validate and process form data.
        If heure_connue is False, set time to 00:00:00.
        Parse incertitude flags from input values.
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

        # Gérer les flags d'incertitude à partir des valeurs brutes
        # (car le JS met à jour le champ caché ET ajoute le "?")
        # Utiliser add_prefix pour récupérer la bonne valeur dans un formset
        nombre_oeufs_raw = self.data.get(self.add_prefix('nombre_oeufs'), '').strip()
        if nombre_oeufs_raw and nombre_oeufs_raw.endswith('?'):
            cleaned_data['nombre_oeufs_incertain'] = True
        # Si le champ hidden a bien transmis la valeur, on la garde
        # Sinon on met à False par défaut
        elif 'nombre_oeufs_incertain' not in cleaned_data:
            cleaned_data['nombre_oeufs_incertain'] = False

        nombre_poussins_raw = self.data.get(self.add_prefix('nombre_poussins'), '').strip()
        if nombre_poussins_raw and nombre_poussins_raw.endswith('?'):
            cleaned_data['nombre_poussins_incertain'] = True
        elif 'nombre_poussins_incertain' not in cleaned_data:
            cleaned_data['nombre_poussins_incertain'] = False

        return cleaned_data

    def save(self, commit=True):
        """
        Surcharge pour s'assurer que les flags d'incertitude sont bien sauvegardés
        """
        instance = super().save(commit=False)

        # Forcer l'assignation des flags d'incertitude depuis cleaned_data
        if hasattr(self, 'cleaned_data'):
            instance.nombre_oeufs_incertain = self.cleaned_data.get('nombre_oeufs_incertain', False)
            instance.nombre_poussins_incertain = self.cleaned_data.get(
                'nombre_poussins_incertain', False
            )

        if commit:
            instance.save()

        return instance


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
            'nombre_poussins_1_2',
            'nombre_poussins_3_4',
            'nombre_poussins_vol_t',
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
            'nombre_poussins_1_2': forms.NumberInput(
                attrs={'min': 0, 'placeholder': 'Non observé'}
            ),
            'nombre_poussins_3_4': forms.NumberInput(
                attrs={'min': 0, 'placeholder': 'Non observé'}
            ),
            'nombre_poussins_vol_t': forms.NumberInput(
                attrs={'min': 0, 'placeholder': 'Non observé'}
            ),
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

    def clean_nombre_poussins_1_2(self):
        value = self.cleaned_data.get('nombre_poussins_1_2')
        return None if value == '' or value is None else value

    def clean_nombre_poussins_3_4(self):
        value = self.cleaned_data.get('nombre_poussins_3_4')
        return None if value == '' or value is None else value

    def clean_nombre_poussins_vol_t(self):
        value = self.cleaned_data.get('nombre_poussins_vol_t')
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
                attrs={'class': 'form-field', 'placeholder': 'Hauteur du nid (cm)', 'min': 0}
            ),
            'hauteur_couvert': forms.NumberInput(
                attrs={'class': 'form-field', 'placeholder': 'Hauteur du couvert (cm)', 'min': 0}
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


class NoteCorrectionForm(forms.ModelForm):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Saisir une note relative à la correction',
                'rows': 3,
                'required': False,
            }
        ),
    )

    class Meta:
        model = NoteCorrection
        fields = ['note']


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
