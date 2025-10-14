"""
Vues d'administration pour la gestion des espèces d'oiseaux.

Réservé aux administrateurs uniquement.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from taxonomy.models import Espece, Famille, Ordre


def is_admin(user):
    """Vérifie que l'utilisateur est administrateur."""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def liste_especes(request):
    """Liste paginée des espèces avec recherche et filtres."""
    # Récupérer les paramètres de recherche et filtrage
    search_query = request.GET.get('q', '')
    famille_filter = request.GET.get('famille', '')
    ordre_filter = request.GET.get('ordre', '')
    statut_filter = request.GET.get('statut', '')

    # Requête de base
    especes = Espece.objects.select_related('famille', 'famille__ordre').all()

    # Appliquer la recherche
    if search_query:
        especes = especes.filter(
            Q(nom__icontains=search_query)
            | Q(nom_scientifique__icontains=search_query)
            | Q(nom_anglais__icontains=search_query)
        )

    # Appliquer les filtres
    if famille_filter:
        especes = especes.filter(famille_id=famille_filter)
    if ordre_filter:
        especes = especes.filter(famille__ordre_id=ordre_filter)
    if statut_filter:
        especes = especes.filter(statut=statut_filter)

    # Pagination
    paginator = Paginator(especes.order_by('nom'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques
    stats = {
        'total': Espece.objects.count(),
        'ordres': Ordre.objects.count(),
        'familles': Famille.objects.count(),
    }

    # Listes pour les filtres
    familles = Famille.objects.select_related('ordre').order_by('nom')
    ordres = Ordre.objects.order_by('nom')
    statuts = Espece.objects.values_list('statut', flat=True).distinct().order_by('statut')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'famille_filter': famille_filter,
        'ordre_filter': ordre_filter,
        'statut_filter': statut_filter,
        'stats': stats,
        'familles': familles,
        'ordres': ordres,
        'statuts': statuts,
    }

    return render(request, 'taxonomy/liste_especes.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def detail_espece(request, espece_id):
    """Affichage détaillé d'une espèce."""
    espece = get_object_or_404(
        Espece.objects.select_related('famille', 'famille__ordre'), pk=espece_id
    )

    # Compter les fiches utilisant cette espèce
    nombre_fiches = espece.observations.count()

    context = {
        'espece': espece,
        'nombre_fiches': nombre_fiches,
    }

    return render(request, 'taxonomy/detail_espece.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def creer_espece(request):
    """Création d'une nouvelle espèce."""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom', '').strip()
        nom_scientifique = request.POST.get('nom_scientifique', '').strip()
        nom_anglais = request.POST.get('nom_anglais', '').strip()
        famille_id = request.POST.get('famille')
        statut = request.POST.get('statut', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()
        lien_oiseau_net = request.POST.get('lien_oiseau_net', '').strip()

        # Validation
        if not nom or not nom_scientifique:
            messages.error(request, "Le nom français et le nom scientifique sont obligatoires.")
        else:
            try:
                # Vérifier si l'espèce existe déjà
                if Espece.objects.filter(nom=nom).exists():
                    messages.error(request, f"Une espèce avec le nom '{nom}' existe déjà.")
                elif Espece.objects.filter(nom_scientifique=nom_scientifique).exists():
                    messages.error(
                        request,
                        f"Une espèce avec le nom scientifique '{nom_scientifique}' existe déjà.",
                    )
                else:
                    # Créer l'espèce
                    famille = Famille.objects.get(pk=famille_id) if famille_id else None
                    espece = Espece.objects.create(
                        nom=nom,
                        nom_scientifique=nom_scientifique,
                        nom_anglais=nom_anglais,
                        famille=famille,
                        statut=statut,
                        commentaire=commentaire,
                        lien_oiseau_net=lien_oiseau_net,
                        valide_par_admin=True,
                    )
                    messages.success(request, f"L'espèce '{espece.nom}' a été créée avec succès.")
                    return redirect('taxonomy:detail_espece', espece_id=espece.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {e}")

    # Listes pour le formulaire
    familles = Famille.objects.select_related('ordre').order_by('nom')
    ordres = Ordre.objects.order_by('nom')

    context = {
        'familles': familles,
        'ordres': ordres,
    }

    return render(request, 'taxonomy/creer_espece.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def modifier_espece(request, espece_id):
    """Modification d'une espèce existante."""
    espece = get_object_or_404(Espece, pk=espece_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom', '').strip()
        nom_scientifique = request.POST.get('nom_scientifique', '').strip()
        nom_anglais = request.POST.get('nom_anglais', '').strip()
        famille_id = request.POST.get('famille')
        statut = request.POST.get('statut', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()
        lien_oiseau_net = request.POST.get('lien_oiseau_net', '').strip()

        # Validation
        if not nom or not nom_scientifique:
            messages.error(request, "Le nom français et le nom scientifique sont obligatoires.")
        else:
            try:
                # Vérifier les doublons (sauf l'espèce actuelle)
                if Espece.objects.filter(nom=nom).exclude(pk=espece_id).exists():
                    messages.error(request, f"Une espèce avec le nom '{nom}' existe déjà.")
                elif (
                    Espece.objects.filter(nom_scientifique=nom_scientifique)
                    .exclude(pk=espece_id)
                    .exists()
                ):
                    messages.error(
                        request,
                        f"Une espèce avec le nom scientifique '{nom_scientifique}' existe déjà.",
                    )
                else:
                    # Mettre à jour l'espèce
                    espece.nom = nom
                    espece.nom_scientifique = nom_scientifique
                    espece.nom_anglais = nom_anglais
                    espece.famille = Famille.objects.get(pk=famille_id) if famille_id else None
                    espece.statut = statut
                    espece.commentaire = commentaire
                    espece.lien_oiseau_net = lien_oiseau_net
                    espece.save()

                    messages.success(
                        request, f"L'espèce '{espece.nom}' a été modifiée avec succès."
                    )
                    return redirect('taxonomy:detail_espece', espece_id=espece.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la modification : {e}")

    # Listes pour le formulaire
    familles = Famille.objects.select_related('ordre').order_by('nom')
    ordres = Ordre.objects.order_by('nom')

    context = {
        'espece': espece,
        'familles': familles,
        'ordres': ordres,
    }

    return render(request, 'taxonomy/modifier_espece.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def supprimer_espece(request, espece_id):
    """Suppression d'une espèce."""
    espece = get_object_or_404(Espece, pk=espece_id)

    # Vérifier si l'espèce est utilisée dans des fiches
    nombre_fiches = espece.observations.count()

    if request.method == 'POST':
        if nombre_fiches > 0:
            messages.error(
                request,
                f"Impossible de supprimer '{espece.nom}' : "
                f"cette espèce est utilisée dans {nombre_fiches} fiche(s) d'observation.",
            )
            return redirect('taxonomy:detail_espece', espece_id=espece.id)

        try:
            nom_espece = espece.nom
            espece.delete()
            messages.success(request, f"L'espèce '{nom_espece}' a été supprimée avec succès.")
            return redirect('taxonomy:liste_especes')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {e}")
            return redirect('taxonomy:detail_espece', espece_id=espece.id)

    context = {
        'espece': espece,
        'nombre_fiches': nombre_fiches,
    }

    return render(request, 'taxonomy/supprimer_espece.html', context)


@login_required
@user_passes_test(is_admin, login_url='/auth/login/')
def importer_especes(request):
    """
    Page de gestion des imports (LOF et TaxRef).
    Affiche les instructions et statistiques.
    """
    # Statistiques actuelles
    stats = {
        'total_especes': Espece.objects.count(),
        'total_familles': Famille.objects.count(),
        'total_ordres': Ordre.objects.count(),
        'especes_lof': Espece.objects.filter(commentaire__icontains='Import LOF').count(),
        'especes_taxref': Espece.objects.filter(commentaire__icontains='Import TaxRef').count(),
        'especes_manuelles': Espece.objects.filter(valide_par_admin=False).count(),
    }

    # Dernières espèces importées
    dernieres_especes = Espece.objects.select_related('famille', 'famille__ordre').order_by('-id')[
        :10
    ]

    context = {
        'stats': stats,
        'dernieres_especes': dernieres_especes,
    }

    return render(request, 'taxonomy/importer_especes.html', context)
