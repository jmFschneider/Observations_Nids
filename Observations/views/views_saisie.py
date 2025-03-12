from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import datetime
from Observations.models import Espece, Observation, FicheObservation
from django.contrib import messages

@login_required  # Empêche les utilisateurs non connectés d'accéder à cette vue
def saisie_observation(request):
    especes_disponibles = Espece.objects.all()
#    numeros_disponibles = Observation.objects.all()
    annee_actuelle = datetime.now().year

    # Récupérer le dernier numéro de fiche utilisé et l'incrémenter
    dernier_fiche = FicheObservation.objects.order_by('-num_fiche').first()
    prochain_num_fiche = (dernier_fiche.num_fiche + 1) if dernier_fiche else 1

    fiche = {
        'num_fiche': prochain_num_fiche
    }

    # Récupérer le nom de l'utilisateur connecté
    utilisateur_nom = f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated else "Utilisateur anonyme"

    return render(request, 'saisie/saisie_observation.html', {
        'fiche': fiche,
        'especes_disponibles': especes_disponibles,
#        'numeros_disponibles': numeros_disponibles,
        'annee_actuelle': annee_actuelle,
        'utilisateur_nom': utilisateur_nom,  # Ajout de l'utilisateur dans le contexte
    })

def traiter_saisie_observation(request):
    if request.method == "POST":
        observateur = request.user  # L'utilisateur connecté
        espece_id = request.POST.get("espece")
        numero_id = request.POST.get("numero_observation")
        annee = datetime.now().year  # Année actuelle

        try:
            espece = Espece.objects.get(id=espece_id)
            numero_observation = Observation.objects.get(id=numero_id)

            # Créer une nouvelle observation
            nouvelle_observation = Observation.objects.create(
                observateur=observateur,
                espece=espece,
                annee=annee
            )

            messages.success(request, "Observation enregistrée avec succès !")
            return redirect('saisie_observation')  # Redirige vers le formulaire après succès

        except Espece.DoesNotExist or Observation.DoesNotExist:
            messages.error(request, "Erreur lors de l'enregistrement. Veuillez réessayer.")

    return redirect('saisie_observation')  # En cas d'erreur, on revient au formulaire
