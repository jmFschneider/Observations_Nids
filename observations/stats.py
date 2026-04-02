"""
Module de calcul des statistiques pour l'application Observations de Nids.

Ce module fournit des fonctions pour calculer diverses statistiques sur les fiches
d'observation, les utilisateurs et l'activité de l'application.
"""

import json
from collections import defaultdict
from datetime import timedelta
from math import floor

from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Q, fields
from django.db.models.functions import Cast
from django.utils import timezone

from audit.models import HistoriqueModification
from geo.models import Localisation
from observations.models import FicheObservation, Observation
from taxonomy.models import Espece


class StatsVolume:
    """
    Classe pour calculer les statistiques de volume de l'application.

    Ces statistiques donnent une vue d'ensemble de la base de données et
    permettent de mesurer la croissance globale.
    """

    @staticmethod
    def get_total_fiches():
        """
        Retourne le nombre total de fiches d'observation.

        Returns:
            int: Nombre total de fiches
        """
        return FicheObservation.objects.count()

    @staticmethod
    def get_fiches_par_statut():
        """
        Retourne la répartition des fiches par statut.

        Returns:
            dict: Dictionnaire avec les clés:
                - nouvelles: nombre de fiches nouvelles
                - en_edition: nombre de fiches en cours d'édition
                - en_attente_correction: nombre de fiches en attente de correcteur
                - en_correction: nombre de fiches en cours de correction (avec correcteur)
                - validees: nombre de fiches validées
                - stats_brutes: queryset avec la répartition complète
        """
        stats_brutes = FicheObservation.objects.values('etat_correction__statut').annotate(
            count=Count('num_fiche')
        )

        # Compteurs détaillés
        nouvelles = FicheObservation.objects.filter(etat_correction__statut='nouveau').count()

        en_edition = FicheObservation.objects.filter(etat_correction__statut='en_edition').count()

        # En attente : statut 'en_cours' mais pas de correcteur assigné
        en_attente_correction = FicheObservation.objects.filter(
            etat_correction__statut='en_cours', etat_correction__en_correction_par__isnull=True
        ).count()

        # En correction : correcteur assigné et pas encore validée
        en_correction = (
            FicheObservation.objects.filter(etat_correction__en_correction_par__isnull=False)
            .exclude(etat_correction__statut='valide')
            .count()
        )

        validees = FicheObservation.objects.filter(etat_correction__statut='valide').count()

        return {
            'nouvelles': nouvelles,
            'en_edition': en_edition,
            'en_attente_correction': en_attente_correction,
            'en_correction': en_correction,
            'validees': validees,
            'stats_brutes': list(stats_brutes),
        }

    @staticmethod
    def get_fiches_recentes(jours=30):
        """
        Retourne le nombre de fiches créées dans les X derniers jours.

        Args:
            jours (int): Nombre de jours à considérer (par défaut: 30)

        Returns:
            int: Nombre de fiches créées récemment
        """
        il_y_a_x_jours = timezone.now() - timedelta(days=jours)
        return FicheObservation.objects.filter(date_creation__gte=il_y_a_x_jours).count()

    @staticmethod
    def get_total_observations():
        """
        Retourne le nombre total d'observations terrain.

        Mesure la richesse des données collectées (plusieurs observations par fiche).

        Returns:
            int: Nombre total d'observations terrain
        """
        return Observation.objects.count()

    @staticmethod
    def get_completion_moyenne():
        """
        Retourne le taux de completion moyen des fiches.

        Indicateur de qualité des données saisies.

        Returns:
            float: Pourcentage moyen de completion (0-100) ou None si aucune fiche
        """
        result = FicheObservation.objects.aggregate(
            avg_completion=Avg('etat_correction__pourcentage_completion')
        )
        return result['avg_completion']

    @staticmethod
    def get_stats_volume_completes():
        """
        Retourne toutes les statistiques de volume en un seul appel.

        Returns:
            dict: Dictionnaire contenant toutes les statistiques de volume
        """
        fiches_statut = StatsVolume.get_fiches_par_statut()

        return {
            'total_fiches': StatsVolume.get_total_fiches(),
            'fiches_nouvelles': fiches_statut['nouvelles'],
            'fiches_en_edition': fiches_statut['en_edition'],
            'fiches_en_attente_correction': fiches_statut['en_attente_correction'],
            'fiches_en_correction': fiches_statut['en_correction'],
            'fiches_validees': fiches_statut['validees'],
            'fiches_recentes_30j': StatsVolume.get_fiches_recentes(30),
            'total_observations': StatsVolume.get_total_observations(),
            'completion_moyenne': StatsVolume.get_completion_moyenne(),
        }


class StatsPerformance:
    """
    Classe pour calculer les statistiques de performance de l'application.

    Ces statistiques mesurent l'efficacité du processus de correction/validation
    et la progression globale du projet.
    """

    @staticmethod
    def get_temps_moyen_validation():
        """
        Retourne le temps moyen de validation d'une fiche (de la création à la validation).

        Returns:
            dict: Dictionnaire avec:
                - duree_moyenne: objet timedelta ou None
                - jours: nombre de jours (float) ou None
        """
        duree_validation_moyenne = (
            FicheObservation.objects.filter(
                etat_correction__statut='valide', etat_correction__date_validation__isnull=False
            )
            .annotate(
                duree=ExpressionWrapper(
                    F('etat_correction__date_validation') - F('date_creation'),
                    output_field=fields.DurationField(),
                )
            )
            .aggregate(avg_duree=Avg('duree'))['avg_duree']
        )

        # Convertir en jours si disponible
        jours = None
        if duree_validation_moyenne:
            jours = duree_validation_moyenne.total_seconds() / 86400

        return {
            'duree_moyenne': duree_validation_moyenne,
            'jours': jours,
        }

    @staticmethod
    def get_taux_validation():
        """
        Retourne le taux de validation (pourcentage de fiches validées).

        Returns:
            dict: Dictionnaire avec:
                - total: nombre total de fiches
                - validees: nombre de fiches validées
                - taux: pourcentage (0-100)
        """
        total = FicheObservation.objects.count()
        validees = FicheObservation.objects.filter(etat_correction__statut='valide').count()
        taux = (validees / total * 100) if total > 0 else 0

        return {
            'total': total,
            'validees': validees,
            'taux': round(taux, 2),
        }

    @staticmethod
    def get_validations_mois_courant():
        """
        Retourne le nombre de fiches validées durant le mois en cours.

        Returns:
            int: Nombre de validations ce mois
        """
        debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return FicheObservation.objects.filter(
            etat_correction__date_validation__gte=debut_mois
        ).count()

    @staticmethod
    def get_activite_corrections(jours=30):
        """
        Retourne le nombre de modifications effectuées dans les X derniers jours.

        Mesure l'intensité du travail de correction.

        Args:
            jours (int): Nombre de jours à considérer (par défaut: 30)

        Returns:
            int: Nombre de modifications récentes
        """
        il_y_a_x_jours = timezone.now() - timedelta(days=jours)
        return HistoriqueModification.objects.filter(date_modification__gte=il_y_a_x_jours).count()

    @staticmethod
    def get_stats_performance_completes():
        """
        Retourne toutes les statistiques de performance en un seul appel.

        Returns:
            dict: Dictionnaire contenant toutes les statistiques de performance
        """
        temps_validation = StatsPerformance.get_temps_moyen_validation()
        taux_validation = StatsPerformance.get_taux_validation()

        return {
            'temps_moyen_validation_jours': temps_validation['jours'],
            'temps_moyen_validation_duree': temps_validation['duree_moyenne'],
            'taux_validation_pourcent': taux_validation['taux'],
            'total_fiches': taux_validation['total'],
            'fiches_validees': taux_validation['validees'],
            'validations_mois_courant': StatsPerformance.get_validations_mois_courant(),
            'modifications_30j': StatsPerformance.get_activite_corrections(30),
        }


class StatsGeographie:
    """
    Classe pour calculer les statistiques géographiques des fiches d'observation.

    Fournit les données pour la carte Leaflet et les KPIs géographiques,
    avec filtrage optionnel par plage d'années et par espèce.
    """

    @staticmethod
    def get_annees_disponibles():
        """Retourne la liste triée des années ayant au moins une fiche."""
        return list(
            FicheObservation.objects.values_list('annee', flat=True).distinct().order_by('annee')
        )

    @staticmethod
    def get_especes_disponibles():
        """Retourne les espèces ayant au moins une fiche, triées par nom."""
        return list(
            Espece.objects.filter(observations__isnull=False)
            .distinct()
            .order_by('nom')
            .values('id', 'nom')
        )

    @staticmethod
    def get_donnees_geo(annee_debut=None, annee_fin=None, espece_id=None):
        """
        Retourne les données géographiques filtrées pour la carte et les KPIs.

        Args:
            annee_debut (int|None): Première année à inclure.
            annee_fin (int|None): Dernière année à inclure.
            espece_id (int|None): Filtre sur une espèce spécifique.

        Returns:
            dict: {
                'communes': [{'commune', 'departement', 'lat', 'lon', 'nb_fiches'}, ...],
                'kpis': {'nb_fiches', 'nb_communes', 'nb_departements', 'nb_non_geocodees'}
            }
        """
        qs = FicheObservation.objects.all()

        if annee_debut:
            qs = qs.filter(annee__gte=int(annee_debut))
        if annee_fin:
            qs = qs.filter(annee__lte=int(annee_fin))
        if espece_id:
            qs = qs.filter(espece_id=int(espece_id))

        total_fiches = qs.count()

        # Localisations liées aux fiches filtrées
        locs = Localisation.objects.filter(fiche__in=qs)

        # Fiches sans coordonnées exploitables (lat/lon = '0.0' ou commune vide)
        nb_non_geocodees = locs.filter(
            Q(latitude='0.0') | Q(longitude='0.0') | Q(commune='')
        ).count()

        # Communes géolocalisées : on groupe par commune+département,
        # on moyenne les coordonnées pour avoir un point représentatif
        communes_qs = (
            locs.exclude(latitude='0.0')
            .exclude(longitude='0.0')
            .exclude(commune='')
            .annotate(
                lat_float=Cast('latitude', FloatField()),
                lon_float=Cast('longitude', FloatField()),
            )
            .values('commune', 'departement')
            .annotate(
                nb_fiches=Count('fiche'),
                lat=Avg('lat_float'),
                lon=Avg('lon_float'),
            )
            .order_by('-nb_fiches')
        )

        communes_list = list(communes_qs)
        nb_communes = len(communes_list)

        nb_departements = (
            locs.exclude(departement='00')
            .exclude(departement='')
            .values('departement')
            .distinct()
            .count()
        )

        return {
            'communes': communes_list,
            'kpis': {
                'nb_fiches': total_fiches,
                'nb_communes': nb_communes,
                'nb_departements': nb_departements,
                'nb_non_geocodees': nb_non_geocodees,
            },
        }


class StatsTaxonomie:
    """
    Statistiques taxonomiques : couverture des espèces, répartition par famille,
    évolution annuelle et maille géographique par espèce.
    """

    @staticmethod
    def get_couverture():
        """Retourne nb espèces observées, nb au référentiel et taux de couverture."""
        nb_referentiel = Espece.objects.count()
        nb_observees = FicheObservation.objects.values('espece').distinct().count()
        taux = round(nb_observees / nb_referentiel * 100, 1) if nb_referentiel > 0 else 0
        return {
            'nb_referentiel': nb_referentiel,
            'nb_observees': nb_observees,
            'taux': taux,
        }

    @staticmethod
    def get_top_especes(limit=20):
        """Retourne les N espèces avec le plus de fiches."""
        return list(
            FicheObservation.objects.values('espece__nom', 'espece__code_gonm')
            .annotate(nb_fiches=Count('num_fiche'))
            .order_by('-nb_fiches')[:limit]
        )

    @staticmethod
    def get_repartition_familles():
        """Retourne la répartition du nombre de fiches par famille taxonomique."""
        return list(
            FicheObservation.objects.values('espece__famille__nom')
            .annotate(nb_fiches=Count('num_fiche'))
            .order_by('-nb_fiches')
        )

    @staticmethod
    def get_especes_sans_fiche():
        """Retourne les espèces du référentiel sans aucune fiche d'observation."""
        return list(
            Espece.objects.annotate(nb_fiches=Count('observations'))
            .filter(nb_fiches=0)
            .order_by('nom')
            .values('nom', 'nom_scientifique', 'code_gonm', 'famille__nom')
        )

    @staticmethod
    def get_evolution_annuelle():
        """
        Retourne par année : nombre d'espèces distinctes et taux de succès de nidification.
        Taux de succès = fiches avec au moins 1 poussin volant / total fiches de l'année.
        """
        par_annee = {
            row['annee']: {'total': row['total'], 'nb_especes': row['nb_especes']}
            for row in FicheObservation.objects.values('annee').annotate(
                total=Count('num_fiche'),
                nb_especes=Count('espece', distinct=True),
            )
        }
        succes_par_annee = dict(
            FicheObservation.objects.filter(resume__nombre_poussins_vol_t__gt=0)
            .values('annee')
            .annotate(nb=Count('num_fiche'))
            .values_list('annee', 'nb')
        )
        result = []
        for annee in sorted(par_annee):
            total = par_annee[annee]['total']
            succes = succes_par_annee.get(annee, 0)
            taux_succes = round(succes / total * 100, 1) if total > 0 else 0
            result.append(
                {
                    'annee': annee,
                    'nb_especes': par_annee[annee]['nb_especes'],
                    'taux_succes': taux_succes,
                }
            )
        return result

    @staticmethod
    def get_donnees_maille(taille=0.5, annee=None):
        """
        Regroupe les fiches dans une grille de mailles carrées (en degrés).
        Retourne pour chaque maille non vide le nombre d'espèces distinctes.

        Args:
            taille (float): Côté de la maille en degrés (ex: 0.25, 0.5, 1.0).
            annee (int|None): Filtre optionnel sur l'année.
        """
        qs = (
            Localisation.objects.exclude(latitude='0.0')
            .exclude(longitude='0.0')
            .exclude(commune='')
            .annotate(
                lat_f=Cast('latitude', FloatField()),
                lon_f=Cast('longitude', FloatField()),
            )
        )
        if annee:
            qs = qs.filter(fiche__annee=int(annee))

        cells = defaultdict(set)
        for loc in qs.values('lat_f', 'lon_f', 'fiche__espece_id'):
            if loc['lat_f'] and loc['lon_f']:
                cell_lat = floor(loc['lat_f'] / taille) * taille
                cell_lon = floor(loc['lon_f'] / taille) * taille
                cells[(cell_lat, cell_lon)].add(loc['fiche__espece_id'])

        result = [
            {'lat': k[0], 'lon': k[1], 'nb_especes': len(v), 'taille': taille}
            for k, v in cells.items()
        ]
        result.sort(key=lambda x: -x['nb_especes'])
        return result


def get_stats_tableau_bord():
    """
    Fonction de commodité qui retourne toutes les statistiques de volume et de performance.

    Utile pour alimenter un tableau de bord admin/superviseur.

    Returns:
        dict: Dictionnaire avec deux clés 'volume' et 'performance'
    """
    return {
        'volume': StatsVolume.get_stats_volume_completes(),
        'performance': StatsPerformance.get_stats_performance_completes(),
    }


def get_stats_page_statistiques():
    """
    Prépare les données statistiques pour la page de statistiques publique.

    Retourne un dictionnaire contenant diverses statistiques sur les fiches d'observation,
    formaté pour le template observations/statistiques.html.

    Returns:
        dict: Dictionnaire contenant toutes les statistiques pour la page
    """
    # Total de fiches
    total_fiches = FicheObservation.objects.count()

    # Fiches en cours de saisie (statut 'nouveau' ou 'en_edition')
    fiches_en_cour_saisie = FicheObservation.objects.filter(
        Q(etat_correction__statut='nouveau') | Q(etat_correction__statut='en_edition')
    ).count()

    # Fiches en attente de correction (statut 'en_cours' et non assignées)
    fiches_en_attente_correction = FicheObservation.objects.filter(
        etat_correction__statut='en_cours', etat_correction__en_correction_par__isnull=True
    ).count()

    # Fiches en cours de correction (assignées à un correcteur et non validées)
    fiches_en_cours_correction = (
        FicheObservation.objects.filter(etat_correction__en_correction_par__isnull=False)
        .exclude(etat_correction__statut='valide')
        .count()
    )

    # Fiches validées (statut 'valide')
    fiches_valides = FicheObservation.objects.filter(etat_correction__statut='valide').count()

    # Nombre d'espèces distinctes observées
    nb_especes = FicheObservation.objects.values('espece').distinct().count()

    # Nombre d'observateurs distincts
    nb_observateurs = FicheObservation.objects.values('observateur').distinct().count()

    # Top 4 espèces les plus fréquentes
    top_especes = (
        FicheObservation.objects.values('espece__nom')
        .annotate(count=Count('espece'))
        .order_by('-count')[:4]
    )

    # Fiches par année pour graphique
    fiches_par_annee_qs = (
        FicheObservation.objects.values('annee')
        .annotate(count=Count('num_fiche'))
        .order_by('annee')
    )
    fiches_par_annee = list(fiches_par_annee_qs)
    chart_labels = json.dumps([item['annee'] for item in fiches_par_annee])
    chart_data = json.dumps([item['count'] for item in fiches_par_annee])

    return {
        'total_fiches': total_fiches,
        'fiches_en_cour_saisie': fiches_en_cour_saisie,
        'fiches_en_attente_correction': fiches_en_attente_correction,
        'fiches_en_cours_correction': fiches_en_cours_correction,
        'fiches_valides': fiches_valides,
        'nb_especes': nb_especes,
        'nb_observateurs': nb_observateurs,
        'top_especes': top_especes,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
