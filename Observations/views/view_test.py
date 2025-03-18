from django.shortcuts import render, redirect
from Observations.forms import TestForm  # Importez votre formulaire
from Observations.models import FicheObservation, Localisation, Espece  # Importez votre modèle
from datetime import datetime

def saisie_test(request):
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('saisie_test')
    else:
        # Créer le formulaire
        form = TestForm()
        # Ajouter le nom d'utilisateur, l'année courante et la liste des espèces au contexte
        context = {
            'form': form,
            'utilisateur_nom': 'Nom utilisateur', # Récupérez le nom de l'utilisateur réel ici
            'especes_disponibles': Espece.objects.all(),
            'annee_actuelle': datetime.now().year,
        }
    return render(request, 'saisie/saisie_test.html', context)