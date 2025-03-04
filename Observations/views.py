# views.py
from django.shortcuts import render, get_object_or_404
from .models import Utilisateur, Observation

def home(request):
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
    observations_count = Observation.objects.filter(user_id=user.id).count()
    last_observation = Observation.objects.filter(user_id=user.id).order_by('-observation_date').first()
    return render(request, 'user_detail.html', {
        'user': user,
        'observations_count': observations_count,
        'last_observation': last_observation
    })