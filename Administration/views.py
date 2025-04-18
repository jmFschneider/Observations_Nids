# Administration/views.py
import logging

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Utilisateur
from .forms import UtilisateurCreationForm, UtilisateurChangeForm

logger = logging.getLogger(__name__)


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'administrateur'


@login_required
@user_passes_test(est_admin)
def liste_utilisateurs(request):
    """Vue pour afficher la liste des utilisateurs"""
    # Filtre de recherche
    recherche = request.GET.get('recherche', '')
    role = request.GET.get('role', 'tous')

    utilisateurs = Utilisateur.objects.all()

    # Appliquer les filtres
    if recherche:
        utilisateurs = utilisateurs.filter(
        Q(username__icontains=recherche) |
        Q(first_name__icontains=recherche) |
        Q(last_name__icontains=recherche) |
        Q(email__icontains=recherche)
        )

    if role != 'tous':
        utilisateurs = utilisateurs.filter(role=role)

    # Pagination
    paginator = Paginator(utilisateurs.order_by('username'), 20)
    page = request.GET.get('page', 1)
    utilisateurs_page = paginator.get_page(page)

    context = {
        'utilisateurs': utilisateurs_page,
        'recherche': recherche,
        'role': role,
    }

    return render(request, 'administration/liste_utilisateurs.html', context)


@login_required
@user_passes_test(est_admin)
def creer_utilisateur(request):
    """Vue pour créer un nouvel utilisateur"""
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            messages.success(request, f"L'utilisateur {utilisateur.username} a été créé avec succès")
            return redirect('liste_utilisateurs')
    else:
        form = UtilisateurCreationForm()

    return render(request, 'administration/creer_utilisateur.html', {'form': form})


@login_required
@user_passes_test(est_admin)
def modifier_utilisateur(request, user_id):
    """Vue pour modifier un utilisateur existant"""
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        form = UtilisateurChangeForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'utilisateur {utilisateur.username} a été modifié avec succès")
            return redirect('liste_utilisateurs')
    else:
        form = UtilisateurChangeForm(instance=utilisateur)

    return render(request, 'administration/modifier_utilisateur.html', {'form': form, 'utilisateur': utilisateur})


@login_required
@user_passes_test(est_admin)
def desactiver_utilisateur(request, user_id):
    """Vue pour désactiver un utilisateur"""
    if request.method == 'POST':
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        utilisateur.is_active = False
        utilisateur.save()
        messages.success(request, f"L'utilisateur {utilisateur.username} a été désactivé")

    return redirect('liste_utilisateurs')


@login_required
@user_passes_test(est_admin)
def activer_utilisateur(request, user_id):
    """Vue pour activer un utilisateur"""
    if request.method == 'POST':
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        utilisateur.is_active = True
        utilisateur.save()
        messages.success(request, f"L'utilisateur {utilisateur.username} a été activé")

    return redirect('liste_utilisateurs')