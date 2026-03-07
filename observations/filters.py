import unicodedata
from datetime import datetime

import django_filters
from django import forms
from django.db.models import Q

from taxonomy.models import Espece

from .models import EtatCorrection, FicheObservation


def _sans_accents(s: str) -> str:
    """Normalise une chaîne pour comparaison insensible aux accents."""
    if not s:
        return ""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


class FicheObservationFilter(django_filters.FilterSet):
    num_fiche = django_filters.CharFilter(
        method='filter_by_id_or_range',
        label="N° Fiche",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID ou 10-20'}),
    )
    date_creation = django_filters.CharFilter(
        method='filter_by_date_smart',
        label="Date de création",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'JJ/MM/AAAA ou -'}),
    )
    observateur = django_filters.CharFilter(
        method='filter_by_observateur',
        label="Observateur",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom...'}),
    )
    espece = django_filters.CharFilter(
        method='filter_by_espece',
        label="Espèce",
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nom français ou scientifique...',
            }
        ),
    )
    commune = django_filters.CharFilter(
        method='filter_by_commune',
        label="Commune",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Commune'}),
    )
    # Création d'une liste de choix personnalisée incluant l'option "En attente de correction"
    STATUTS_CHOICES_CUSTOM = list(EtatCorrection.STATUTS_CHOICES) + [
        ('en_attente_correction', 'En attente de correction'),
    ]
    # Tri par libellé (ordre alphabétique)
    STATUTS_CHOICES_CUSTOM.sort(key=lambda x: x[1])

    statut_correction = django_filters.ChoiceFilter(
        method='filter_statut',
        choices=STATUTS_CHOICES_CUSTOM,
        label="Statut de correction",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    correcteur = django_filters.CharFilter(
        method='filter_by_correcteur',
        label="Correcteur",
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nom du correcteur...',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide labels for all fields as they are implied by the column headers
        for _field_name, field in self.form.fields.items():
            field.label = ""

    def filter_by_id_or_range(self, queryset, name, value):
        """
        Filtre intelligent pour l'ID :
        - Si "16" -> num_fiche=16
        - Si "10-20" -> 10 <= num_fiche <= 20
        """
        if not value:
            return queryset

        value = value.strip()
        if '-' in value:
            try:
                min_val, max_val = value.split('-', 1)
                return queryset.filter(num_fiche__range=(min_val.strip(), max_val.strip()))
            except ValueError:
                pass  # Format incorrect, on ignore ou on tente le match exact

        # Tentative de match exact
        try:
            return queryset.filter(num_fiche=value)
        except ValueError:
            return queryset

    def filter_by_date_smart(self, queryset, name, value):
        """
        Filtre intelligent pour la date :
        - DD/MM/YYYY : Date exacte
        - YYYY : Année entière
        - D1-D2 : Intervalle
        """
        if not value:
            return queryset

        value = value.strip()

        # Fonction utilitaire pour parser une date
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
            except ValueError:
                return None

        # Cas 1: Intervalle (séparateur '-')
        if '-' in value:
            parts = value.split('-', 1)
            start_date = parse_date(parts[0])
            end_date = parse_date(parts[1])

            if start_date and end_date:
                # Inclusif : fin de journée pour la date de fin
                return queryset.filter(
                    date_creation__date__gte=start_date, date_creation__date__lte=end_date
                )

        # Cas 2: Année seule (YYYY)
        if len(value) == 4 and value.isdigit():
            return queryset.filter(date_creation__year=value)

        # Cas 3: Date exacte (DD/MM/YYYY)
        date_obj = parse_date(value)
        if date_obj:
            return queryset.filter(date_creation__date=date_obj)

        # Si aucun format ne correspond, on ignore ou on cherche en tant que chaîne (peu utile pour une date)
        return queryset

    def filter_by_espece(self, queryset, name, value):
        """
        Filtre par nom d'espèce (français ou scientifique), insensible aux accents.
        Ex. "ecureuil" trouve "Écureuil roux".
        """
        if not value or not value.strip():
            return queryset
        search_norm = _sans_accents(value.strip()).lower()
        matching_ids = [
            e.pk
            for e in Espece.objects.only("pk", "nom", "nom_scientifique").iterator(chunk_size=200)
            if search_norm in _sans_accents(e.nom or "").lower()
            or search_norm in _sans_accents(e.nom_scientifique or "").lower()
        ]
        if not matching_ids:
            return queryset.none()
        return queryset.filter(espece_id__in=matching_ids)

    def filter_by_observateur(self, queryset, name, value):
        return queryset.filter(
            Q(observateur__first_name__icontains=value) | Q(observateur__last_name__icontains=value)
        )

    def filter_by_commune(self, queryset, name, value):
        return queryset.filter(
            Q(localisation__commune__icontains=value)
            | Q(localisation__commune_saisie__icontains=value)
        )

    def filter_statut(self, queryset, name, value):
        """
        Filtre personnalisé pour les statuts.
        Gère le cas spécial 'en_attente_correction'.
        """
        if value == 'en_attente_correction':
            # Fiches en cours de correction MAIS sans correcteur assigné
            return queryset.filter(
                etat_correction__statut='en_cours', etat_correction__en_correction_par__isnull=True
            )
        else:
            # Filtrage standard sur le champ statut
            return queryset.filter(etat_correction__statut=value)

    def filter_by_correcteur(self, queryset, name, value):
        """
        Filtre par nom du correcteur (en cours de correction ou ayant validé).
        Recherche sur prénom et nom, insensible à la casse.
        """
        if not value or not value.strip():
            return queryset
        term = value.strip()
        return queryset.filter(
            Q(etat_correction__en_correction_par__first_name__icontains=term)
            | Q(etat_correction__en_correction_par__last_name__icontains=term)
            | Q(etat_correction__validee_par__first_name__icontains=term)
            | Q(etat_correction__validee_par__last_name__icontains=term)
        )

    class Meta:
        model = FicheObservation
        fields = [
            'num_fiche',
            'date_creation',
            'observateur',
            'espece',
            'commune',  # Use the custom commune filter
        ]
