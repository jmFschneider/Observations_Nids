# observations/views/api_observateurs.py
"""
API pour la gestion des observateurs : recherche similaire, autocomplétion et fusion.
Utilisé pour corriger les noms d'observateurs mal transcrits par l'OCR.
"""

import json
import logging
import os
from difflib import SequenceMatcher

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import CharField, Count, Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Utilisateur
from audit.models import HistoriqueModification
from observations.models import FicheObservation

logger = logging.getLogger('observations')

SEUIL_SIMILARITE_DEFAUT = 0.8


def calculer_similarite(nom1: str, nom2: str) -> float:
    """
    Calcule le score de similarité entre deux noms (fuzzy matching).
    Utilise difflib.SequenceMatcher comme dans importation_service.py.

    Args:
        nom1: Premier nom à comparer
        nom2: Second nom à comparer

    Returns:
        Score de similarité entre 0.0 et 1.0
    """
    if not nom1 or not nom2:
        return 0.0
    return SequenceMatcher(None, nom1.lower().strip(), nom2.lower().strip()).ratio()


def verifier_permission_fusion(user) -> bool:
    """
    Vérifie si l'utilisateur peut effectuer une fusion d'observateurs.
    Seuls les reviewers et administrateurs ont cette permission.
    """
    return user.role in ['reviewer', 'administrateur']


def obtenir_nom_complet(utilisateur: Utilisateur) -> str:
    """Retourne le nom complet formaté d'un utilisateur."""
    return f"{utilisateur.first_name} {utilisateur.last_name}".strip() or utilisateur.username


@login_required
@require_GET
def rechercher_observateurs_similaires(request):
    """
    API pour rechercher des observateurs similaires à un observateur donné.
    Utilisé pour la détection automatique et les suggestions.

    GET params:
        - observateur_id (int, requis): ID de l'observateur de référence
        - seuil (float, optionnel): Seuil de similarité (défaut: 0.8)

    Returns:
        JSON avec observateur_actuel et liste de suggestions triées par similarité
    """
    # Vérifier requête AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requête AJAX uniquement'}, status=400)

    # Récupérer paramètres
    observateur_id = request.GET.get('observateur_id')
    try:
        seuil = float(request.GET.get('seuil', SEUIL_SIMILARITE_DEFAUT))
    except (ValueError, TypeError):
        seuil = SEUIL_SIMILARITE_DEFAUT

    if not observateur_id:
        return JsonResponse(
            {'success': False, 'message': 'Paramètre observateur_id requis'}, status=400
        )

    # Récupérer l'observateur de référence
    try:
        observateur_ref = Utilisateur.objects.annotate(nombre_fiches=Count('fiches')).get(
            pk=observateur_id
        )
    except Utilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Observateur non trouvé'}, status=404)

    nom_ref = obtenir_nom_complet(observateur_ref)

    # Chercher les observateurs similaires
    # On exclut l'observateur de référence et on ne garde que les actifs/validés
    autres_observateurs = (
        Utilisateur.objects.filter(is_active=True, est_valide=True)
        .exclude(pk=observateur_id)
        .annotate(nombre_fiches=Count('fiches'))
    )

    suggestions = []
    for obs in autres_observateurs:
        nom_obs = obtenir_nom_complet(obs)
        score = calculer_similarite(nom_ref, nom_obs)

        if score >= seuil:
            suggestions.append(
                {
                    'id': obs.id,
                    'nom_complet': nom_obs,
                    'est_transcription': obs.est_transcription,
                    'score_similarite': round(score, 2),
                    'nombre_fiches': obs.nombre_fiches,
                }
            )

    # Trier par score décroissant
    suggestions.sort(key=lambda x: x['score_similarite'], reverse=True)

    return JsonResponse(
        {
            'success': True,
            'observateur_actuel': {
                'id': observateur_ref.id,
                'nom_complet': nom_ref,
                'est_transcription': observateur_ref.est_transcription,
                'nombre_fiches': observateur_ref.nombre_fiches,
            },
            'suggestions': suggestions[:10],  # Limiter à 10 suggestions
        }
    )


@login_required
@require_GET
def rechercher_observateurs(request):
    """
    API pour rechercher des observateurs par nom (autocomplétion).
    Utilisé pour la recherche manuelle dans la modale.

    GET params:
        - q (str, requis): Terme de recherche (min 2 caractères)
        - reference_id (int, optionnel): ID observateur pour calcul similarité
        - limit (int, optionnel): Nombre max de résultats (défaut: 20)

    Returns:
        JSON avec liste d'observateurs correspondants
    """
    # Vérifier requête AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requête AJAX uniquement'}, status=400)

    query = request.GET.get('q', '').strip()
    reference_id = request.GET.get('reference_id')
    try:
        limit = int(request.GET.get('limit', 20))
    except (ValueError, TypeError):
        limit = 20

    if len(query) < 2:
        return JsonResponse({'observateurs': []})

    # Récupérer le nom de référence pour calcul de similarité
    nom_reference = None
    obs_ref = None
    if reference_id:
        try:
            obs_ref = Utilisateur.objects.get(pk=reference_id)
            nom_reference = obtenir_nom_complet(obs_ref)
        except Utilisateur.DoesNotExist:
            pass

    # Base queryset avec noms concaténés pour couvrir les variantes OCR :
    #   nom_fn  : "A. TYPLOT"  (prénom + nom)
    #   nom_nf  : "TYPLOT A."  (nom + prénom)
    #   nom_colle : "TYPLOTA." (nom + prénom sans espace, comme les fusions OCR)
    base_qs = Utilisateur.objects.filter(is_active=True, est_valide=True).annotate(
        nom_fn=Concat('first_name', Value(' '), 'last_name', output_field=CharField()),
        nom_nf=Concat('last_name', Value(' '), 'first_name', output_field=CharField()),
        nom_colle=Concat('last_name', 'first_name', output_field=CharField()),
    )

    # Exclure l'observateur de référence uniquement s'il est une transcription OCR
    # (pas un compte validé — on veut pouvoir le retrouver dans la recherche)
    if reference_id and obs_ref and obs_ref.est_transcription:
        base_qs = base_qs.exclude(pk=reference_id)

    startswith_filter = (
        Q(first_name__istartswith=query)
        | Q(last_name__istartswith=query)
        | Q(nom_fn__istartswith=query)
        | Q(nom_nf__istartswith=query)
        | Q(nom_colle__istartswith=query)
    )

    contains_filter = (
        Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(nom_fn__icontains=query)
        | Q(nom_nf__icontains=query)
        | Q(nom_colle__icontains=query)
    )

    observateurs_startswith = base_qs.filter(startswith_filter).annotate(
        nombre_fiches=Count('fiches', distinct=True)
    )

    observateurs_contains = (
        base_qs.filter(contains_filter)
        .exclude(startswith_filter)
        .annotate(nombre_fiches=Count('fiches', distinct=True))
    )

    # Combiner les résultats (dédoublonnage par id)
    resultats = []
    seen_ids: set[int] = set()

    for obs in list(observateurs_startswith) + list(observateurs_contains):
        if len(resultats) >= limit:
            break
        if obs.id in seen_ids:
            continue
        seen_ids.add(obs.id)

        nom_complet = obtenir_nom_complet(obs)
        score = calculer_similarite(nom_reference, nom_complet) if nom_reference else None

        resultats.append(
            {
                'id': obs.id,
                'nom_complet': nom_complet,
                'est_transcription': obs.est_transcription,
                'score_similarite': round(score, 2) if score else None,
                'nombre_fiches': obs.nombre_fiches,
            }
        )

    return JsonResponse({'observateurs': resultats})


@login_required
@require_POST
def fusionner_observateurs(request):  # noqa: PLR0911
    """
    API pour fusionner les fiches d'un observateur vers un autre.
    Traçage complet dans l'historique des modifications.

    POST params:
        - ancien_observateur_id (int, requis): ID de l'observateur source
        - nouvel_observateur_id (int, requis): ID de l'observateur cible
        - fiche_id (int, optionnel): ID de la fiche courante (si fusion unique)
        - fusionner_toutes (str): 'true' pour fusionner toutes les fiches

    Returns:
        JSON avec statut de la fusion
    """
    # Vérifier requête AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requête AJAX uniquement'}, status=400)

    # Vérifier les permissions
    if not verifier_permission_fusion(request.user):
        return JsonResponse(
            {
                'success': False,
                'error': 'permission_denied',
                'message': 'Seuls les reviewers et administrateurs peuvent fusionner des observateurs',
            },
            status=403,
        )

    # Récupérer les paramètres
    ancien_id = request.POST.get('ancien_observateur_id')
    nouveau_id = request.POST.get('nouvel_observateur_id')
    fiche_id = request.POST.get('fiche_id')
    fusionner_toutes = request.POST.get('fusionner_toutes') == 'true'

    # Validation des paramètres
    if not ancien_id or not nouveau_id:
        return JsonResponse(
            {
                'success': False,
                'error': 'missing_params',
                'message': 'Paramètres ancien_observateur_id et nouvel_observateur_id requis',
            },
            status=400,
        )

    if ancien_id == nouveau_id:
        return JsonResponse(
            {
                'success': False,
                'error': 'same_observer',
                'message': 'Les deux observateurs sont identiques',
            },
            status=400,
        )

    # Récupérer les observateurs
    try:
        ancien_obs = Utilisateur.objects.get(pk=ancien_id)
        nouveau_obs = Utilisateur.objects.get(pk=nouveau_id)
    except Utilisateur.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'observer_not_found', 'message': 'Observateur non trouvé'},
            status=404,
        )

    # Déterminer les fiches à transférer
    if fusionner_toutes:
        fiches_a_transferer = FicheObservation.objects.filter(observateur=ancien_obs)
    elif fiche_id:
        fiches_a_transferer = FicheObservation.objects.filter(pk=fiche_id, observateur=ancien_obs)
        if not fiches_a_transferer.exists():
            return JsonResponse(
                {
                    'success': False,
                    'error': 'fiche_not_found',
                    'message': 'Fiche non trouvée ou n\'appartient pas à cet observateur',
                },
                status=404,
            )
    else:
        return JsonResponse(
            {
                'success': False,
                'error': 'no_fiches_specified',
                'message': 'Aucune fiche spécifiée pour le transfert',
            },
            status=400,
        )

    nombre_fiches = fiches_a_transferer.count()
    if nombre_fiches == 0:
        return JsonResponse(
            {'success': False, 'error': 'no_fiches', 'message': 'Aucune fiche à transférer'},
            status=400,
        )

    # Effectuer la fusion dans une transaction
    try:
        with transaction.atomic():
            ancien_nom = obtenir_nom_complet(ancien_obs)
            nouveau_nom = obtenir_nom_complet(nouveau_obs)

            for fiche in fiches_a_transferer:
                # Enregistrer dans l'historique AVANT modification
                HistoriqueModification.objects.create(
                    fiche=fiche,
                    champ_modifie='observateur',
                    ancienne_valeur=f"{ancien_nom} (ID:{ancien_obs.id})",
                    nouvelle_valeur=f"{nouveau_nom} (ID:{nouveau_obs.id})",
                    categorie='fiche',
                    modifie_par=request.user,
                )

                # Modifier l'observateur
                fiche.observateur = nouveau_obs
                fiche.save(update_fields=['observateur'])

            # Gérer l'ancien observateur si plus aucune fiche ne lui est rattachée
            ancien_obs_supprime = False
            ancien_obs_desactive = False

            fiches_restantes = FicheObservation.objects.filter(observateur=ancien_obs).count()

            if fiches_restantes == 0:
                # Déterminer si l'observateur peut être supprimé :
                # - Créé par OCR (est_transcription=True)
                # - OU créé via la modale de correction (@observateur.local)
                est_supprimable = ancien_obs.est_transcription or ancien_obs.email.endswith(
                    '@observateur.local'
                )

                if est_supprimable:
                    # Observateur temporaire → SUPPRIMER
                    ancien_obs_id = ancien_obs.id
                    raison = (
                        "transcription OCR"
                        if ancien_obs.est_transcription
                        else "correction temporaire"
                    )
                    ancien_obs.delete()
                    ancien_obs_supprime = True
                    logger.info(
                        f"Observateur {ancien_obs_id} ({ancien_nom}) SUPPRIMÉ "
                        f"après transfert de toutes ses fiches ({raison})"
                    )
                else:
                    # Observateur réel → DÉSACTIVER (peut être réutilisé)
                    ancien_obs.is_active = False
                    ancien_obs.save(update_fields=['is_active'])
                    ancien_obs_desactive = True
                    logger.info(
                        f"Observateur {ancien_obs.id} ({ancien_nom}) désactivé "
                        f"après transfert de toutes ses fiches"
                    )

            logger.info(
                f"Fusion réussie: {nombre_fiches} fiche(s) de {ancien_nom} vers {nouveau_nom} "
                f"par {request.user.username}"
            )

            return JsonResponse(
                {
                    'success': True,
                    'message': f'{nombre_fiches} fiche(s) transférée(s) de {ancien_nom} vers {nouveau_nom}',
                    'fiches_transferees': nombre_fiches,
                    'ancien_observateur_supprime': ancien_obs_supprime,
                    'ancien_observateur_desactive': ancien_obs_desactive,
                }
            )

    except Exception as e:
        logger.exception(f"Erreur lors de la fusion d'observateurs: {e}")
        return JsonResponse(
            {
                'success': False,
                'error': 'fusion_error',
                'message': f'Erreur lors de la fusion: {str(e)}',
            },
            status=500,
        )


@login_required
@require_GET
def obtenir_nom_ocr_json(request):  # noqa: PLR0911
    """
    API pour lire le nom d'observateur transcrit depuis le fichier JSON source.
    Extrait informations_generales.observateur du fichier JSON.

    GET params:
        - fiche_id (int, requis): ID de la fiche pour récupérer le chemin JSON

    Returns:
        JSON avec nom_ocr (ou null si non disponible)
    """
    # Vérifier requête AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requête AJAX uniquement'}, status=400)

    fiche_id = request.GET.get('fiche_id')
    if not fiche_id:
        return JsonResponse({'success': False, 'message': 'Paramètre fiche_id requis'}, status=400)

    # Récupérer la fiche
    try:
        fiche = FicheObservation.objects.get(pk=fiche_id)
    except FicheObservation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Fiche non trouvée'}, status=404)

    # Vérifier si la fiche a un chemin JSON
    if not fiche.chemin_json:
        return JsonResponse(
            {
                'success': True,
                'nom_ocr': None,
                'message': 'Aucun fichier JSON associé à cette fiche',
            }
        )

    # Construire le chemin absolu vers le fichier JSON
    chemin_json_absolu = os.path.join(settings.MEDIA_ROOT, fiche.chemin_json)

    # Vérifier que le fichier existe
    if not os.path.exists(chemin_json_absolu):
        return JsonResponse(
            {
                'success': True,
                'nom_ocr': None,
                'message': f'Fichier JSON non trouvé: {fiche.chemin_json}',
            }
        )

    # Lire et parser le fichier JSON
    try:
        with open(chemin_json_absolu, encoding='utf-8') as f:
            data = json.load(f)

        # Extraire le nom de l'observateur
        nom_ocr = None
        if 'informations_generales' in data:
            nom_ocr = data['informations_generales'].get('observateur')

        return JsonResponse(
            {
                'success': True,
                'nom_ocr': nom_ocr,
                'chemin_json': fiche.chemin_json,
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing JSON {chemin_json_absolu}: {e}")
        return JsonResponse(
            {
                'success': False,
                'error': 'json_parse_error',
                'message': f'Erreur de lecture du fichier JSON: {str(e)}',
            },
            status=500,
        )
    except Exception as e:
        logger.exception(f"Erreur lecture JSON: {e}")
        return JsonResponse(
            {'success': False, 'error': 'read_error', 'message': f'Erreur: {str(e)}'}, status=500
        )


@login_required
@require_POST
def creer_observateur(request):
    """
    API pour créer un nouvel observateur à partir d'un nom saisi manuellement.
    Crée un utilisateur avec est_transcription=False et est_valide=True.

    POST params:
        - nom (str, requis): Nom complet (format "Prénom Nom" ou "Nom")

    Returns:
        JSON avec l'observateur créé
    """
    # Vérifier requête AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requête AJAX uniquement'}, status=400)

    # Vérifier les permissions (reviewer ou admin)
    if not verifier_permission_fusion(request.user):
        return JsonResponse(
            {
                'success': False,
                'error': 'permission_denied',
                'message': 'Seuls les reviewers et administrateurs peuvent créer des observateurs',
            },
            status=403,
        )

    nom_complet = request.POST.get('nom', '').strip()
    if not nom_complet or len(nom_complet) < 2:
        return JsonResponse(
            {
                'success': False,
                'error': 'invalid_name',
                'message': 'Le nom doit contenir au moins 2 caractères',
            },
            status=400,
        )

    # Parser le nom (format "Prénom Nom" ou juste "Nom")
    parties = nom_complet.split(maxsplit=1)
    if len(parties) == 1:
        # Juste un nom
        prenom = ''
        nom = parties[0]
    else:
        # Prénom et Nom
        prenom = parties[0]
        nom = parties[1]

    # Générer un username unique basé sur le nom
    base_username = f"{prenom.lower()}.{nom.lower()}".replace(' ', '_')
    base_username = ''.join(c for c in base_username if c.isalnum() or c in '._')
    if not base_username:
        base_username = 'observateur'

    username = base_username
    counter = 1
    while Utilisateur.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    # Créer l'observateur
    try:
        with transaction.atomic():
            observateur = Utilisateur.objects.create(
                username=username,
                email=f"{username}@observateur.local",
                first_name=prenom,
                last_name=nom,
                est_transcription=False,  # Créé manuellement, pas par OCR
                est_valide=True,
                is_active=True,
                role='observateur',
            )

            logger.info(
                f"Nouvel observateur créé: {nom_complet} (ID:{observateur.id}) "
                f"par {request.user.username}"
            )

            return JsonResponse(
                {
                    'success': True,
                    'observateur': {
                        'id': observateur.id,
                        'nom_complet': f"{prenom} {nom}".strip(),
                        'est_transcription': False,
                        'nombre_fiches': 0,
                    },
                    'message': f'Observateur "{nom_complet}" créé avec succès',
                }
            )

    except Exception as e:
        logger.exception(f"Erreur création observateur: {e}")
        return JsonResponse(
            {
                'success': False,
                'error': 'creation_error',
                'message': f'Erreur lors de la création: {str(e)}',
            },
            status=500,
        )
