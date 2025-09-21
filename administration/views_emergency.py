# administration/views_emergency.py
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .models import Utilisateur


def est_superuser(user):
    """Vérifie si l'utilisateur est un superuser"""
    return user.is_superuser


@user_passes_test(est_superuser)
def promouvoir_administrateur(request):
    """Vue pour promouvoir un utilisateur au rôle d'administrateur (réservée aux superusers)"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            utilisateur = get_object_or_404(Utilisateur, id=user_id)
            utilisateur.role = 'administrateur'
            utilisateur.save()
            messages.success(request, f"L'utilisateur {utilisateur.username} a été promu administrateur avec succès")
            return redirect('liste_utilisateurs')

    # Récupérer tous les utilisateurs qui ne sont pas déjà administrateurs
    utilisateurs = Utilisateur.objects.exclude(role='administrateur')

    return render(request, 'administration/promouvoir_admin.html', {'utilisateurs': utilisateurs})