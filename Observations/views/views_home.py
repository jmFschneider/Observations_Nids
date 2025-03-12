# views_home.py
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from Observations.models import Utilisateur, Observation, FicheObservation
from Observations.forms import UtilisateurForm, InscriptionForm
import logging
logger = logging.getLogger('Observations')

def home(request):
    logger.info("Accueil visité")

    # 🔹 Redirection vers `access_restricted.html` si l'utilisateur n'est pas connecté
    if not request.user.is_authenticated:
        logger.debug("Visite anonyme - Redirection vers access_restricted.html")
        return render(request, 'access_restricted.html')

    # 🔹 Renommage pour éviter la confusion avec le modèle `Utilisateur`
    user = request.user  # L'utilisateur Django connecté

    users_count = Utilisateur.objects.count()
    observations_count = Observation.objects.count()

    return render(request, 'home.html', {
        'user': user,  # Renommé pour éviter la confusion avec le modèle
        'users_count': users_count,
        'observations_count': observations_count
    })


def default_view(request):
    return render(request, 'access_restricted.html')

def user_list(request):
    users = Utilisateur.objects.all()
    return render(request, 'user_list.html', {'users': users})

def user_detail(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    fiches = list(FicheObservation.objects.filter(observateur=user).order_by('-num_fiche'))
    observations_count = len(fiches)  # Pas besoin d'une requête supplémentaire

    return render(request, 'user_detail.html', {
        'user': user,
        'observations_count': observations_count,
        'fiches': fiches
    })


def inscription(request):
    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Connexion automatique après inscription
            return redirect('home')  # Redirige vers l'accueil
    else:
        form = InscriptionForm()

    return render(request, 'user_inscription.html', {'form': form})