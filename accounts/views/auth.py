import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from accounts.forms import UtilisateurChangeForm, UtilisateurCreationForm
from accounts.models import Utilisateur
from observations.models import FicheObservation

logger = logging.getLogger(__name__)


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'administrateur'


def est_superuser(user):
    """Vérifie si l'utilisateur est un superuser"""
    return user.is_superuser


class ListeUtilisateursView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Utilisateur
    template_name = 'accounts/liste_utilisateurs.html'
    context_object_name = 'utilisateurs'
    paginate_by = 20

    def test_func(self):
        return est_admin(self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        recherche = self.request.GET.get('recherche', '')
        role = self.request.GET.get('role', 'tous')

        if recherche:
            queryset = queryset.filter(
                Q(username__icontains=recherche)
                | Q(first_name__icontains=recherche)
                | Q(last_name__icontains=recherche)
                | Q(email__icontains=recherche)
            )

        if role != 'tous':
            queryset = queryset.filter(role=role)

        return queryset.order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recherche'] = self.request.GET.get('recherche', '')
        context['role'] = self.request.GET.get('role', 'tous')
        context['valide'] = self.request.GET.get('valide', 'tous')
        return context


@login_required
@user_passes_test(est_admin)
def creer_utilisateur(request):
    """Vue pour créer un nouvel utilisateur"""
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            messages.success(
                request, f"L'utilisateur {utilisateur.username} a été créé avec succès"
            )
            return redirect('accounts:liste_utilisateurs')
    else:
        form = UtilisateurCreationForm()

    return render(request, 'accounts/creer_utilisateur.html', {'form': form})


@login_required
@user_passes_test(est_admin)
def modifier_utilisateur(request, user_id):
    """Vue pour modifier un utilisateur existant"""
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        form = UtilisateurChangeForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"L'utilisateur {utilisateur.username} a été modifié avec succès"
            )
            return redirect('accounts:liste_utilisateurs')
    else:
        form = UtilisateurChangeForm(instance=utilisateur)

    return render(
        request,
        'accounts/modifier_utilisateur.html',
        {'form': form, 'utilisateur': utilisateur},
    )


@login_required
@user_passes_test(est_admin)
def desactiver_utilisateur(request, user_id):
    """Vue pour désactiver un utilisateur"""
    if request.method == 'POST':
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        utilisateur.is_active = False
        utilisateur.save()
        messages.success(request, f"L'utilisateur {utilisateur.username} a été désactivé")

    return redirect('accounts:liste_utilisateurs')


@login_required
@user_passes_test(est_admin)
def activer_utilisateur(request, user_id):
    """Vue pour activer un utilisateur"""
    if request.method == 'POST':
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        utilisateur.is_active = True
        utilisateur.save()
        messages.success(request, f"L'utilisateur {utilisateur.username} a été activé")

    return redirect('accounts:liste_utilisateurs')


@login_required
@user_passes_test(est_admin)
def detail_utilisateur(request, user_id):
    """Vue pour afficher les détails d'un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    fiches = list(FicheObservation.objects.filter(observateur=utilisateur).order_by('-num_fiche'))
    observations_count = len(fiches)

    context = {
        'utilisateur': utilisateur,
        'observations_count': observations_count,
        'fiches': fiches,
    }

    # Si c'est une requête AJAX, renvoyer uniquement le contenu du détail
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'accounts/user_detail_partial.html', context)

    return render(request, 'accounts/user_detail.html', context)


@login_required
def mon_profil(request):
    """Vue pour afficher le profil de l'utilisateur connecté"""
    utilisateur = request.user
    fiches = list(FicheObservation.objects.filter(observateur=utilisateur).order_by('-num_fiche'))
    observations_count = len(fiches)

    context = {
        'utilisateur': utilisateur,
        'observations_count': observations_count,
        'fiches': fiches,
    }

    return render(request, 'accounts/mon_profil.html', context)


def inscription_publique(request):
    """Vue pour l'inscription publique des utilisateurs (sans authentification requise)"""
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            # Créer l'utilisateur mais le marquer comme non validé
            utilisateur = form.save(commit=False)
            utilisateur.est_valide = False  # Nécessite approbation par un admin
            utilisateur.role = 'observateur'  # Rôle par défaut
            utilisateur.save()
            logger.info(
                f"Nouvelle demande d'inscription reçue : {utilisateur.username} ({utilisateur.email})"
            )

            messages.success(
                request,
                "Votre demande d'inscription a été enregistrée. Un administrateur devra l'approuver avant que vous puissiez vous connecter.",
            )
            return redirect('login')
    else:
        form = UtilisateurCreationForm()

    return render(request, 'accounts/inscription_publique.html', {'form': form})


@user_passes_test(est_superuser)
def promouvoir_administrateur(request):
    """Vue pour promouvoir un utilisateur au rôle d'administrateur (réservée aux superusers)"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            utilisateur = get_object_or_404(Utilisateur, id=user_id)
            utilisateur.role = 'administrateur'
            utilisateur.save()
            messages.success(
                request,
                f"L'utilisateur {utilisateur.username} a été promu administrateur avec succès",
            )
            return redirect('accounts:liste_utilisateurs')

    # Récupérer tous les utilisateurs qui ne sont pas déjà administrateurs
    utilisateurs = Utilisateur.objects.exclude(role='administrateur')

    return render(request, 'accounts/promouvoir_admin.html', {'utilisateurs': utilisateurs})


@login_required
@user_passes_test(est_admin)
def valider_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    utilisateur.est_valide = True
    utilisateur.save()
    messages.success(request, f"L'utilisateur {utilisateur.username} a été validé.")
    return redirect('accounts:liste_utilisateurs')
