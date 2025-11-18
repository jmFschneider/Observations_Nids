import django_filters
from django.db.models import Q
from django import forms
from django_filters.widgets import RangeWidget

from accounts.models import Utilisateur
from taxonomy.models import Espece

from .models import EtatCorrection, FicheObservation


class FicheObservationFilter(django_filters.FilterSet):
    date_creation = django_filters.DateFromToRangeFilter(
        field_name='date_creation',
        label="Date de création",  # Label is kept for accessibility, but will be hidden
        widget=RangeWidget(attrs={'type': 'date', 'class': 'form-control'}),
    )
    observateur = django_filters.ModelChoiceFilter(
        queryset=Utilisateur.objects.all().order_by('first_name', 'last_name'),
        field_name='observateur',
        to_field_name='pk',
        label="Observateur",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    espece = django_filters.ModelChoiceFilter(
        queryset=Espece.objects.all().order_by('nom'),
        field_name='espece',
        to_field_name='pk',
        label="Espèce",
        empty_label="Toutes",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    commune = django_filters.CharFilter(
        method='filter_by_commune',
        label="Commune",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Commune'}
        ),
    )
    statut_correction = django_filters.ChoiceFilter(
        field_name='etat_correction__statut',
        choices=EtatCorrection.STATUTS_CHOICES,
        label="Statut de correction",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide labels for all fields as they are implied by the column headers
        for _field_name, field in self.form.fields.items():
            field.label = ""

    def filter_by_commune(self, queryset, name, value):
        return queryset.filter(
            Q(localisation__commune__icontains=value)
            | Q(localisation__commune_saisie__icontains=value)
        )

    class Meta:
        model = FicheObservation
        fields = [
            'date_creation',
            'observateur',
            'espece',
            'commune',  # Use the custom commune filter
        ]
