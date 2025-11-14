"""
Vues d'administration pour la gestion des communes françaises.

Réservé aux administrateurs uniquement.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from geo.models import CommuneFrance, AncienneCommune
from geo.utils.geocoding import get_geocodeur

logger = logging.getLogger(__name__)


def is_admin(user):
    """Vérifie que l'utilisateur est administrateur."""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def liste_communes(request):
    """Liste paginée des communes avec recherche et filtres."""
    # Récupérer les paramètres de recherche et filtrage
    search_query = request.GET.get('q', '')
    departement_filter = request.GET.get('departement', '')
    region_filter = request.GET.get('region', '')
    source_filter = request.GET.get('source', '')

    # Requête de base
    communes = CommuneFrance.objects.all()

    # Appliquer la recherche (nom + alias + anciennes communes)
    if search_query:
        # 1. Chercher si c'est une ancienne commune
        anciennes = AncienneCommune.objects.filter(nom__icontains=search_query)
        communes_actuelles_ids = list(anciennes.values_list('commune_actuelle_id', flat=True))

        # 2. Chercher dans les communes actuelles (nom, alias, codes) + communes liées aux anciennes
        communes = communes.filter(
            Q(nom__icontains=search_query)
            | Q(autres_noms__icontains=search_query)
            | Q(code_postal__icontains=search_query)
            | Q(code_insee__icontains=search_query)
            | Q(id__in=communes_actuelles_ids)  # Ajouter les communes actuelles liées aux anciennes communes trouvées
        )

    # Appliquer les filtres
    if departement_filter:
        communes = communes.filter(code_departement=departement_filter)
    if region_filter:
        communes = communes.filter(region__icontains=region_filter)
    if source_filter:
        communes = communes.filter(source_ajout=source_filter)

    # Précharger les anciennes communes pour éviter N+1 queries
    communes = communes.prefetch_related('anciennes_communes')

    # Pagination
    paginator = Paginator(communes.order_by('nom'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques
    stats = {
        'total': CommuneFrance.objects.count(),
        'source_api': CommuneFrance.objects.filter(source_ajout='api_geo').count(),
        'source_nominatim': CommuneFrance.objects.filter(source_ajout='nominatim').count(),
        'source_manuelle': CommuneFrance.objects.filter(source_ajout='manuel').count(),
        'avec_alias': CommuneFrance.objects.exclude(autres_noms='').count(),
        'communes_fusionnees': AncienneCommune.objects.count(),  # Anciennes communes dans table séparée
    }

    # Listes pour les filtres
    departements = (
        CommuneFrance.objects.values_list('code_departement', 'departement')
        .distinct()
        .order_by('code_departement')
    )
    regions = (
        CommuneFrance.objects.exclude(region='')
        .values_list('region', flat=True)
        .distinct()
        .order_by('region')
    )
    sources = CommuneFrance._meta.get_field('source_ajout').choices

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'departement_filter': departement_filter,
        'region_filter': region_filter,
        'source_filter': source_filter,
        'stats': stats,
        'departements': departements,
        'regions': regions,
        'sources': sources,
    }

    return render(request, 'geo/liste_communes.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def detail_commune(request, commune_id):
    """Affichage détaillé d'une commune."""
    commune = get_object_or_404(CommuneFrance, pk=commune_id)

    # Compter les fiches utilisant cette commune
    nombre_fiches = commune.nombre_observations()

    # Anciennes communes liées (si c'est une commune actuelle)
    anciennes_communes = commune.anciennes_communes.all()

    context = {
        'commune': commune,
        'nombre_fiches': nombre_fiches,
        'anciennes_communes': anciennes_communes,
    }

    return render(request, 'geo/detail_commune.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def creer_commune(request):
    """Création manuelle d'une nouvelle commune."""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom', '').strip()
        code_insee = request.POST.get('code_insee', '').strip()
        code_postal = request.POST.get('code_postal', '').strip()
        departement = request.POST.get('departement', '').strip()
        code_departement = request.POST.get('code_departement', '').strip()
        region = request.POST.get('region', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        altitude = request.POST.get('altitude', '').strip()
        autres_noms = request.POST.get('autres_noms', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()

        # Validation
        if not nom or not code_insee:
            messages.error(request, "Le nom et le code INSEE sont obligatoires.")
        elif not latitude or not longitude:
            messages.error(request, "Les coordonnées GPS (latitude, longitude) sont obligatoires.")
        else:
            try:
                # Vérifier si la commune existe déjà
                if CommuneFrance.objects.filter(code_insee=code_insee).exists():
                    messages.error(
                        request, f"Une commune avec le code INSEE '{code_insee}' existe déjà."
                    )
                else:
                    # Créer la commune
                    # Normaliser les virgules en points pour les nombres décimaux
                    commune = CommuneFrance.objects.create(
                        nom=nom,
                        code_insee=code_insee,
                        code_postal=code_postal or '00000',
                        departement=departement,
                        code_departement=code_departement,
                        region=region,
                        latitude=float(latitude.replace(',', '.')),
                        longitude=float(longitude.replace(',', '.')),
                        altitude=int(float(altitude.replace(',', '.'))) if altitude else None,
                        autres_noms=autres_noms,
                        commentaire=commentaire,
                        source_ajout='manuel',
                        ajoutee_par=request.user,
                    )
                    messages.success(
                        request, f"La commune '{commune.nom}' a été créée avec succès."
                    )
                    return redirect('geo:detail_commune', commune_id=commune.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {e}")

    context = {}

    return render(request, 'geo/creer_commune.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def modifier_commune(request, commune_id):
    """Modification d'une commune existante."""
    commune = get_object_or_404(CommuneFrance, pk=commune_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom', '').strip()
        code_insee = request.POST.get('code_insee', '').strip()
        code_postal = request.POST.get('code_postal', '').strip()
        departement = request.POST.get('departement', '').strip()
        code_departement = request.POST.get('code_departement', '').strip()
        region = request.POST.get('region', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        altitude = request.POST.get('altitude', '').strip()
        autres_noms = request.POST.get('autres_noms', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()

        # Validation
        if not nom or not code_insee:
            messages.error(request, "Le nom et le code INSEE sont obligatoires.")
        elif not latitude or not longitude:
            messages.error(request, "Les coordonnées GPS (latitude, longitude) sont obligatoires.")
        else:
            try:
                # Vérifier les doublons (sauf la commune actuelle)
                if (
                    CommuneFrance.objects.filter(code_insee=code_insee)
                    .exclude(pk=commune_id)
                    .exists()
                ):
                    messages.error(
                        request, f"Une autre commune avec le code INSEE '{code_insee}' existe déjà."
                    )
                else:
                    # Mettre à jour la commune
                    commune.nom = nom
                    commune.code_insee = code_insee
                    commune.code_postal = code_postal or '00000'
                    commune.departement = departement
                    commune.code_departement = code_departement
                    commune.region = region
                    # Normaliser les virgules en points pour les nombres décimaux
                    commune.latitude = float(latitude.replace(',', '.'))
                    commune.longitude = float(longitude.replace(',', '.'))
                    commune.altitude = int(float(altitude.replace(',', '.'))) if altitude else None
                    commune.autres_noms = autres_noms
                    commune.commentaire = commentaire

                    commune.save()

                    messages.success(
                        request, f"La commune '{commune.nom}' a été modifiée avec succès."
                    )
                    return redirect('geo:detail_commune', commune_id=commune.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la modification : {e}")

    context = {
        'commune': commune,
    }

    return render(request, 'geo/modifier_commune.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def supprimer_commune(request, commune_id):
    """Suppression d'une commune."""
    commune = get_object_or_404(CommuneFrance, pk=commune_id)

    # Vérifier si la commune est utilisée dans des fiches
    nombre_fiches = commune.nombre_observations()

    if request.method == 'POST':
        if nombre_fiches > 0:
            messages.error(
                request,
                f"Impossible de supprimer '{commune.nom}' : "
                f"cette commune est utilisée dans {nombre_fiches} fiche(s) d'observation.",
            )
            return redirect('geo:detail_commune', commune_id=commune.id)

        try:
            nom_commune = commune.nom
            commune.delete()
            messages.success(request, f"La commune '{nom_commune}' a été supprimée avec succès.")
            return redirect('geo:liste_communes')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {e}")
            return redirect('geo:detail_commune', commune_id=commune.id)

    context = {
        'commune': commune,
        'nombre_fiches': nombre_fiches,
    }

    return render(request, 'geo/supprimer_commune.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def rechercher_nominatim(request):
    """
    Page de recherche Nominatim pour ajouter une commune facilement.
    """
    result = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'rechercher':
            # Rechercher sur Nominatim
            nom = request.POST.get('nom', '').strip()
            departement = request.POST.get('departement', '').strip()

            if not nom:
                messages.error(request, "Le nom de la commune est obligatoire.")
            else:
                try:
                    geocodeur = get_geocodeur()
                    coords = geocodeur.geocoder_commune(nom, departement)

                    if coords:
                        result = coords
                        result['nom_recherche'] = nom
                        result['departement_recherche'] = departement

                        # Rechercher si la commune existe déjà dans la base
                        result['communes_existantes'] = CommuneFrance.objects.filter(
                            nom__icontains=nom
                        )

                        # Rechercher dans les anciennes communes
                        result['anciennes_communes_existantes'] = AncienneCommune.objects.filter(
                            nom__icontains=nom
                        ).select_related('commune_actuelle')
                    else:
                        error = f"Commune '{nom}' non trouvée sur Nominatim."
                except Exception as e:
                    error = f"Erreur lors de la recherche : {e}"
                    logger.error(error)

        elif action == 'ajouter':
            # Ajouter la commune trouvée
            nom = request.POST.get('nom_trouve', '').strip()
            code_insee = request.POST.get('code_insee', '').strip() or f"99{hash(nom) % 10000:05d}"
            latitude = request.POST.get('latitude', '').strip()
            longitude = request.POST.get('longitude', '').strip()
            altitude = request.POST.get('altitude', '').strip()
            adresse = request.POST.get('adresse', '').strip()
            source = request.POST.get('source', '').strip()

            try:
                # Vérifier si existe déjà
                if CommuneFrance.objects.filter(nom__iexact=nom).exists():
                    messages.warning(
                        request, f"La commune '{nom}' existe déjà dans la base de données."
                    )
                else:
                    # Extraire département depuis adresse si possible
                    # Format adresse: "Commune, Département, France"
                    parts = [p.strip() for p in adresse.split(',')]
                    departement = parts[1] if len(parts) > 1 else ''
                    code_dept = '99'  # Code par défaut

                    # Normaliser les virgules en points pour les nombres décimaux
                    commune = CommuneFrance.objects.create(
                        nom=nom,
                        code_insee=code_insee,
                        code_postal='00000',  # À renseigner manuellement ensuite
                        departement=departement,
                        code_departement=code_dept,
                        latitude=float(latitude.replace(',', '.')),
                        longitude=float(longitude.replace(',', '.')),
                        altitude=int(float(altitude.replace(',', '.'))) if altitude else None,
                        source_ajout='nominatim',
                        ajoutee_par=request.user,
                        commentaire=f"Ajouté via Nominatim - Adresse complète: {adresse}",
                    )
                    messages.success(
                        request,
                        f"Commune '{commune.nom}' ajoutée avec succès ! "
                        f"Pensez à compléter le code département et le code postal.",
                    )
                    return redirect('geo:modifier_commune', commune_id=commune.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de l'ajout : {e}")
                logger.error(f"Erreur ajout commune depuis Nominatim: {e}")

    context = {
        'result': result,
        'error': error,
    }

    return render(request, 'geo/rechercher_nominatim.html', context)
