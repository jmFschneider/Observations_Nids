"""
Vues pour les statistiques de l'application Observations de Nids.

Ce module contient les vues pour afficher les différents tableaux de bord
statistiques réservés aux administrateurs et correcteurs.
"""

import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from accounts.models import Utilisateur
from observations.models import FicheObservation
from observations.stats import StatsGeographie, StatsTaxonomie, get_stats_tableau_bord


class StatsAccessMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux statistiques aux admins et correcteurs.
    """

    def test_func(self):
        """
        Vérifie que l'utilisateur est admin ou correcteur.
        """
        return self.request.user.is_authenticated and (
            self.request.user.role in ['administrateur', 'correcteur']
        )

    def handle_no_permission(self):
        """
        Redirige vers une page d'accès refusé si l'utilisateur n'a pas la permission.
        """
        return render(self.request, 'access_restricted.html', status=403)


class StatsDashboardView(LoginRequiredMixin, StatsAccessMixin, TemplateView):
    """
    Vue du tableau de bord principal des statistiques (Le Cockpit).

    Affiche les statistiques globales de volume et de performance.
    Accessible uniquement aux administrateurs et correcteurs.
    """

    template_name = 'observations/stats/dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Ajoute les statistiques globales au contexte.
        """
        context = super().get_context_data(**kwargs)

        # Récupérer toutes les stats du tableau de bord
        stats = get_stats_tableau_bord()

        # Ajouter au contexte
        context['stats_volume'] = stats['volume']
        context['stats_performance'] = stats['performance']

        # Titre de la page
        context['page_title'] = 'Tableau de Bord Statistiques'

        return context


class StatsCorrecteursView(LoginRequiredMixin, StatsAccessMixin, TemplateView):
    """
    Vue détaillée des statistiques des correcteurs.

    Affiche la charge de travail, le classement et les performances des correcteurs.
    Accessible uniquement aux administrateurs et correcteurs.
    """

    template_name = 'observations/stats/correcteurs.html'

    def get_context_data(self, **kwargs):
        """
        Ajoute les statistiques détaillées des correcteurs au contexte.
        """
        context = super().get_context_data(**kwargs)

        # Top correcteurs par nombre de validations
        top_correcteurs = (
            Utilisateur.objects.filter(validations__isnull=False)
            .annotate(nb_validations=Count('validations'))
            .order_by('-nb_validations')[:10]
        )

        # Correcteurs avec fiches en cours
        correcteurs_charges = (
            Utilisateur.objects.filter(fiches_en_correction__isnull=False)
            .annotate(nb_en_cours=Count('fiches_en_correction'))
            .order_by('-nb_en_cours')[:10]
        )

        # Correcteurs actifs
        correcteurs_actifs = Utilisateur.objects.filter(
            Q(role='correcteur') | Q(role='administrateur'), est_valide=True
        ).count()

        context['top_correcteurs'] = top_correcteurs
        context['correcteurs_charges'] = correcteurs_charges
        context['correcteurs_actifs'] = correcteurs_actifs
        context['page_title'] = 'Statistiques des Correcteurs'

        return context


class StatsGeographieView(LoginRequiredMixin, StatsAccessMixin, TemplateView):
    """
    Vue de la page de statistiques géographiques.

    Affiche une carte Leaflet avec des cercles proportionnels par commune,
    un graphique des top 10 communes, et des KPIs géographiques.
    Les données sont chargées dynamiquement via l'endpoint AJAX stats_geo_data.
    Accessible uniquement aux administrateurs et correcteurs.
    """

    template_name = 'observations/stats/geographie.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['annees_disponibles'] = StatsGeographie.get_annees_disponibles()
        context['especes_disponibles'] = StatsGeographie.get_especes_disponibles()
        context['page_title'] = 'Statistiques Géographiques'
        return context


class StatsTaxonomieView(LoginRequiredMixin, StatsAccessMixin, TemplateView):
    """
    Vue de la page de statistiques taxonomiques.

    Blocs :
    - Couverture + Top espèces (Chart.js barres horizontales)
    - Répartition par famille (Chart.js donut)
    - Espèces sans aucune fiche (tableau)
    - Évolution annuelle : nb espèces + taux de succès (double axe)
    - Carte maille géographique par espèce (Leaflet, données AJAX)
    """

    template_name = 'observations/stats/taxonomie.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        couverture = StatsTaxonomie.get_couverture()
        top_especes = StatsTaxonomie.get_top_especes(20)
        familles = StatsTaxonomie.get_repartition_familles()
        especes_sans_fiche = StatsTaxonomie.get_especes_sans_fiche()
        evolution = StatsTaxonomie.get_evolution_annuelle()

        context['couverture'] = couverture
        context['chart_especes_labels'] = json.dumps([e['espece__nom'] for e in top_especes])
        context['chart_especes_data'] = json.dumps([e['nb_fiches'] for e in top_especes])
        context['chart_familles_labels'] = json.dumps(
            [f['espece__famille__nom'] or 'Non classée' for f in familles]
        )
        context['chart_familles_data'] = json.dumps([f['nb_fiches'] for f in familles])
        context['especes_sans_fiche'] = especes_sans_fiche
        context['nb_especes_sans_fiche'] = len(especes_sans_fiche)
        context['chart_evolution_annees'] = json.dumps([e['annee'] for e in evolution])
        context['chart_evolution_especes'] = json.dumps([e['nb_especes'] for e in evolution])
        context['chart_evolution_succes'] = json.dumps([e['taux_succes'] for e in evolution])
        context['annees_disponibles'] = StatsGeographie.get_annees_disponibles()
        context['page_title'] = 'Statistiques Taxonomiques'
        return context


def stats_taxo_maille_data(request):
    """
    Endpoint AJAX retournant les données de la grille géographique par espèce.

    Paramètres GET :
        taille  (float) : taille de maille en degrés (0.1, 0.25, 0.5, 1.0)
        annee   (int, optionnel) : filtre sur l'année

    Retourne :
        JsonResponse avec 'mailles' (liste) et 'kpis' (max_especes, nb_mailles).
    """
    if not request.user.is_authenticated or request.user.role not in [
        'administrateur',
        'correcteur',
    ]:
        return JsonResponse({'error': 'Accès refusé'}, status=403)

    taille_str = request.GET.get('taille', '0.5')
    annee = request.GET.get('annee') or None

    try:
        taille = float(taille_str)
        if taille not in (0.1, 0.25, 0.5, 1.0):
            taille = 0.5
    except ValueError:
        taille = 0.5

    mailles = StatsTaxonomie.get_donnees_maille(taille=taille, annee=annee)
    max_especes = mailles[0]['nb_especes'] if mailles else 0

    return JsonResponse(
        {
            'mailles': mailles,
            'kpis': {
                'nb_mailles': len(mailles),
                'max_especes': max_especes,
            },
        }
    )


def stats_geo_data(request):
    """
    Endpoint AJAX retournant les données géographiques filtrées en JSON.

    Paramètres GET :
        annee_debut (int, optionnel) : première année à inclure
        annee_fin   (int, optionnel) : dernière année à inclure
        espece_id   (int, optionnel) : identifiant de l'espèce à isoler

    Retourne :
        JsonResponse avec les clés 'communes' et 'kpis'.
    """
    if not request.user.is_authenticated or request.user.role not in [
        'administrateur',
        'correcteur',
    ]:
        return JsonResponse({'error': 'Accès refusé'}, status=403)

    annee_debut = request.GET.get('annee_debut') or None
    annee_fin = request.GET.get('annee_fin') or None
    espece_id = request.GET.get('espece_id') or None

    donnees = StatsGeographie.get_donnees_geo(
        annee_debut=annee_debut,
        annee_fin=annee_fin,
        espece_id=espece_id,
    )

    # Les valeurs Decimal (lat/lon issues de Avg) ne sont pas sérialisables
    # directement en JSON — on les convertit en float
    communes_serializables = [
        {
            'commune': c['commune'],
            'departement': c['departement'],
            'lat': float(c['lat']),
            'lon': float(c['lon']),
            'nb_fiches': c['nb_fiches'],
        }
        for c in donnees['communes']
    ]

    return JsonResponse(
        {
            'communes': communes_serializables,
            'kpis': donnees['kpis'],
        }
    )


def stats_geo_fiches(request):
    """
    Endpoint AJAX retournant la liste des fiches d'une commune donnée.

    Paramètres GET :
        commune     (str) : nom de la commune
        departement (str) : code ou nom du département
        annee_debut (int, optionnel)
        annee_fin   (int, optionnel)
        espece_id   (int, optionnel)

    Retourne :
        JsonResponse avec les clés 'commune', 'departement', 'total', 'fiches'.
    """
    if not request.user.is_authenticated or request.user.role not in [
        'administrateur',
        'correcteur',
    ]:
        return JsonResponse({'error': 'Accès refusé'}, status=403)

    commune = request.GET.get('commune', '').strip()
    departement = request.GET.get('departement', '').strip()

    if not commune or not departement:
        return JsonResponse({'error': 'Paramètres commune et departement requis'}, status=400)

    annee_debut = request.GET.get('annee_debut') or None
    annee_fin = request.GET.get('annee_fin') or None
    espece_id = request.GET.get('espece_id') or None

    qs = FicheObservation.objects.filter(
        localisation__commune=commune,
        localisation__departement=departement,
    )

    if annee_debut:
        qs = qs.filter(annee__gte=int(annee_debut))
    if annee_fin:
        qs = qs.filter(annee__lte=int(annee_fin))
    if espece_id:
        qs = qs.filter(espece_id=int(espece_id))

    badge_par_statut = {
        'nouveau': 'bg-info',
        'en_edition': 'bg-info',
        'en_cours': 'bg-warning text-dark',
        'valide': 'bg-success',
    }

    fiches = []
    for fiche in qs.select_related('espece', 'etat_correction').order_by(
        '-annee', '-date_creation'
    ):
        statut_code = getattr(fiche.etat_correction, 'statut', 'nouveau')
        fiches.append(
            {
                'num': fiche.num_fiche,
                'espece': fiche.espece.nom,
                'annee': fiche.annee,
                'statut': fiche.etat_correction.get_statut_display(),
                'badge': badge_par_statut.get(statut_code, 'bg-secondary'),
                'url': reverse(
                    'observations:fiche_observation', kwargs={'fiche_id': fiche.num_fiche}
                ),
            }
        )

    return JsonResponse(
        {
            'commune': commune,
            'departement': departement,
            'total': len(fiches),
            'fiches': fiches,
        }
    )
