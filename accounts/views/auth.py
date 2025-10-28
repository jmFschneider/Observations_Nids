import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import ListView

from accounts.forms import (
    MotDePasseOublieForm,
    NouveauMotDePasseForm,
    UtilisateurChangeForm,
    UtilisateurCreationForm,
)
from accounts.models import Notification, Utilisateur
from accounts.utils.email_service import EmailService
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
        valide = self.request.GET.get('valide', 'tous')
        actif = self.request.GET.get('actif', 'tous')

        if recherche:
            queryset = queryset.filter(
                Q(username__icontains=recherche)
                | Q(first_name__icontains=recherche)
                | Q(last_name__icontains=recherche)
                | Q(email__icontains=recherche)
            )

        if role != 'tous':
            queryset = queryset.filter(role=role)

        if valide == 'oui':
            queryset = queryset.filter(est_valide=True)
        elif valide == 'non':
            queryset = queryset.filter(est_valide=False)

        if actif == 'oui':
            queryset = queryset.filter(is_active=True)
        elif actif == 'non':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('-date_joined')  # Les plus récents en premier

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recherche'] = self.request.GET.get('recherche', '')
        context['role'] = self.request.GET.get('role', 'tous')
        context['valide'] = self.request.GET.get('valide', 'tous')
        context['actif'] = self.request.GET.get('actif', 'tous')
        # Ajouter le nombre de demandes en attente
        context['demandes_en_attente'] = Utilisateur.objects.filter(est_valide=False).count()
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
    """Vue pour désactiver un utilisateur (soft delete)"""
    if request.method == 'POST':
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        utilisateur.is_active = False
        utilisateur.save()
        logger.info(
            f"Utilisateur {utilisateur.username} supprimé (soft delete) par {request.user.username}"
        )
        messages.success(
            request,
            f"L'utilisateur {utilisateur.username} a été supprimé. "
            f"Il ne peut plus se connecter mais ses données sont conservées. "
            f"Vous pouvez le réactiver à tout moment.",
        )

    return redirect('accounts:liste_utilisateurs')


@login_required
@user_passes_test(est_admin)
def activer_utilisateur(request, user_id):
    """Vue pour réactiver un utilisateur précédemment désactivé"""
    if request.method == 'POST':
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        utilisateur.is_active = True
        utilisateur.save()
        logger.info(f"Utilisateur {utilisateur.username} réactivé par {request.user.username}")
        messages.success(
            request,
            f"L'utilisateur {utilisateur.username} a été réactivé. "
            f"Il peut à nouveau se connecter à l'application.",
        )

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
            utilisateur.is_active = False  # Compte inactif jusqu'à validation
            utilisateur.save()
            logger.info(
                f"Nouvelle demande d'inscription reçue : {utilisateur.username} ({utilisateur.email})"
            )

            # Créer des notifications pour tous les administrateurs
            administrateurs = Utilisateur.objects.filter(role='administrateur', is_active=True)
            for admin in administrateurs:
                Notification.objects.create(
                    destinataire=admin,
                    type_notification='demande_compte',
                    titre=f"Nouvelle demande de compte : {utilisateur.username}",
                    message=f"{utilisateur.first_name} {utilisateur.last_name} ({utilisateur.email}) a demandé un compte.",
                    lien=f"/accounts/utilisateurs/{utilisateur.id}/detail/",
                    utilisateur_concerne=utilisateur,
                )

            # Envoyer un email à l'administrateur principal
            EmailService.envoyer_email_nouvelle_demande_compte(utilisateur)

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
    utilisateur.is_active = True  # Activer le compte
    utilisateur.save()

    # Créer une notification pour l'utilisateur
    Notification.objects.create(
        destinataire=utilisateur,
        type_notification='compte_valide',
        titre="Votre compte a été validé",
        message="Votre demande de compte a été approuvée. Vous pouvez maintenant vous connecter.",
        lien="/login/",
    )

    # Envoyer un email à l'utilisateur
    EmailService.envoyer_email_compte_valide(utilisateur)

    # Marquer les notifications des admins comme lues
    Notification.objects.filter(
        type_notification='demande_compte', utilisateur_concerne=utilisateur, est_lue=False
    ).update(est_lue=True)

    messages.success(
        request,
        f"L'utilisateur {utilisateur.username} a été validé et notifié par email.",
    )
    logger.info(f"Compte validé pour {utilisateur.username} par {request.user.username}")

    return redirect('accounts:liste_utilisateurs')


def mot_de_passe_oublie(request):
    """
    Vue pour demander une réinitialisation de mot de passe.
    L'utilisateur saisit son email et reçoit un lien de réinitialisation.
    """
    if request.method == 'POST':
        form = MotDePasseOublieForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Récupérer tous les utilisateurs actifs avec cet email
            utilisateurs = Utilisateur.objects.filter(email=email, is_active=True)

            if utilisateurs.exists():
                # Envoyer un email à chaque utilisateur trouvé
                for utilisateur in utilisateurs:
                    # Générer le token et l'UID
                    token = default_token_generator.make_token(utilisateur)
                    uid = urlsafe_base64_encode(force_bytes(utilisateur.pk))

                    # Envoyer l'email avec le lien de réinitialisation
                    EmailService.envoyer_email_reinitialisation_mdp(utilisateur, uid, token)

                logger.info(
                    f"Email de réinitialisation envoyé à {email} ({utilisateurs.count()} compte(s))"
                )
            else:
                # Ne pas révéler si l'email existe ou non (sécurité)
                logger.warning(f"Tentative de réinitialisation pour email inexistant : {email}")

            # Message identique que l'email existe ou non (sécurité)
            messages.success(
                request,
                "Un email contenant les instructions de réinitialisation a été envoyé à votre adresse.",
            )
            return redirect('login')
    else:
        form = MotDePasseOublieForm()

    return render(request, 'accounts/mot_de_passe_oublie.html', {'form': form})


def reinitialiser_mot_de_passe(request, uidb64, token):
    """
    Vue pour réinitialiser le mot de passe avec un token valide.
    L'utilisateur saisit son nouveau mot de passe.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        utilisateur = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        utilisateur = None

    # Vérifier que l'utilisateur et le token sont valides
    if utilisateur is not None and default_token_generator.check_token(utilisateur, token):
        if request.method == 'POST':
            form = NouveauMotDePasseForm(request.POST)
            if form.is_valid():
                # Enregistrer le nouveau mot de passe
                nouveau_mdp = form.cleaned_data['password1']
                utilisateur.password = make_password(nouveau_mdp)
                utilisateur.save()

                logger.info(f"Mot de passe réinitialisé pour {utilisateur.username}")
                messages.success(
                    request,
                    "Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.",
                )
                return redirect('login')
        else:
            form = NouveauMotDePasseForm()

        return render(
            request,
            'accounts/reinitialiser_mot_de_passe.html',
            {'form': form, 'validlink': True},
        )
    else:
        logger.warning("Tentative de réinitialisation avec lien invalide ou expiré")
        return render(
            request,
            'accounts/reinitialiser_mot_de_passe.html',
            {'validlink': False},
        )
