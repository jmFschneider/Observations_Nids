"""
Module de calcul des statistiques pour l'application Observations de Nids.

Ce module fournit des fonctions pour calculer diverses statistiques sur les fiches
d'observation, les utilisateurs et l'activité de l'application.
"""

from datetime import timedelta

from django.db.models import Avg, Count, ExpressionWrapper, F, Q
from django.db.models import fields
from django.utils import timezone

from audit.models import HistoriqueModification
from observations.models import FicheObservation, Observation


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
                - en_correction: nombre de fiches en cours de correction
                - validees: nombre de fiches validées
                - stats_brutes: queryset avec la répartition complète
        """
        stats_brutes = FicheObservation.objects.values(
            'etat_correction__statut'
        ).annotate(
            count=Count('num_fiche')
        )
        
        # Compteurs détaillés
        nouvelles = FicheObservation.objects.filter(
            etat_correction__statut='nouveau'
        ).count()
        
        en_edition = FicheObservation.objects.filter(
            etat_correction__statut='en_edition'
        ).count()
        
        en_correction = FicheObservation.objects.filter(
            etat_correction__statut='en_cours'
        ).count()
        
        validees = FicheObservation.objects.filter(
            etat_correction__statut='valide'
        ).count()
        
        return {
            'nouvelles': nouvelles,
            'en_edition': en_edition,
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
        return FicheObservation.objects.filter(
            date_creation__gte=il_y_a_x_jours
        ).count()
    
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
        duree_validation_moyenne = FicheObservation.objects.filter(
            etat_correction__statut='valide',
            etat_correction__date_validation__isnull=False
        ).annotate(
            duree=ExpressionWrapper(
                F('etat_correction__date_validation') - F('date_creation'),
                output_field=fields.DurationField()
            )
        ).aggregate(
            avg_duree=Avg('duree')
        )['avg_duree']
        
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
        validees = FicheObservation.objects.filter(
            etat_correction__statut='valide'
        ).count()
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
        debut_mois = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
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
        return HistoriqueModification.objects.filter(
            date_modification__gte=il_y_a_x_jours
        ).count()
    
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
