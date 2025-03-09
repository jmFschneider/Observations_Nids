# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Utilisateur, Observation, FicheObservation, Nid
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
    fiches = list(FicheObservation.objects.filter(observateur=user).order_by('-num_fiche'))
    observations_count = len(fiches)  # Pas besoin d'une requête supplémentaire

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

def fiche_observation_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    localisation = fiche.localisation  # Récupérer la localisation liée

    # Vérifie si un résumé existe, sinon passe None
    resume = fiche.resume if hasattr(fiche, 'resume') else None

    # Vérifie si un nid existe, sinon passe None
    nid = fiche.nid if hasattr(fiche, 'nid') else None

    # Vérifie si un objet CausesEchec existe, sinon passe None
    causes_echec = fiche.causes_echec if hasattr(fiche, 'causes_echec') else None

    context = {
        'fiche': fiche,
        'localisation': localisation,
        'resume' : resume,
        'nid' : nid,
        'causes_echec': causes_echec,  # Ajout explicite de l'objet CausesEchec dans le contexte
    }
    return render(request, 'fiche_observation.html', context)

def nid_detail_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    nid = fiche.nid  # Accès direct via la relation OneToOne

    context = {
        'fiche': fiche,
        'nid': nid,
    }
    return render(request, 'observations/fiche_observation/nid_detail.html', context)

def resume_observation_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)
    resume = fiche.resume  # Accès direct via OneToOneField

    context = {
        'fiche': fiche,
        'resume': resume,
    }
    return render(request, 'observations/fiche_observation/resume_observation.html', context)


def causes_echec_view(request, fiche_id):
    fiche = get_object_or_404(FicheObservation, pk=fiche_id)

    # Vérifie si un objet CausesEchec existe, sinon passe None
    causes_echec = fiche.causes_echec if hasattr(fiche, 'causes_echec') else None

    context = {
        'fiche': fiche,
        'causes_echec': causes_echec,  # Ajout explicite de l'objet CausesEchec dans le contexte
    }
    return render(request, 'observations/fiche_observation/causes_echec.html', context)
