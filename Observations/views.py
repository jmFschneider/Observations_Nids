# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Utilisateur, Observation, FicheObservation
from .forms import UtilisateurForm
import logging
from django.http import HttpResponse
logger = logging.getLogger('Observations')

def home(request):
    logger.info("Accueil visité")
    if request.user.is_authenticated:
        logger.debug(f"Utilisateur connecté : {request.user.username}")
    else:
        logger.debug("Visite anonyme")

    users_count = Utilisateur.objects.count()
    observations_count = Observation.objects.count()
    return render(request, 'home.html', {
        'users_count': users_count,
        'observations_count': observations_count
    })

def user_list(request):
    users = Utilisateur.objects.all()
    return render(request, 'user_list.html', {'users': users})

def user_detail(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    observations_count = FicheObservation.objects.filter(observateur=user).count()
    fiches = FicheObservation.objects.filter(observateur=user).order_by('-num_fiche')

    return render(request, 'user_detail.html', {
        'user': user,
        'observations_count': observations_count,
        'fiches': fiches
    })


def user_create(request):
    if request.method == "POST":
        form = UtilisateurForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')  # Redirige vers la liste après l'ajout
    else:
        form = UtilisateurForm()

    return render(request, 'user_create.html', {'form': form})