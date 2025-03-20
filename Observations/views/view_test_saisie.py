from django.shortcuts import render, redirect
from Observations.forms import (
    FicheObservationForm,
    LocalisationForm,
    ResumeObservationForm,
    NidForm,
    CausesEchecForm, RemarqueForm,
)
from Observations.models import FicheObservation, Espece, Remarque
from datetime import datetime
from django.contrib.auth.decorators import login_required

#@login_required
def fiche_test_observation_view(request, fiche_id=None):
    if request.method == "POST":
        fiche_form = FicheObservationForm(request.POST, request.FILES)
        localisation_form = LocalisationForm(request.POST)
        resume_form = ResumeObservationForm(request.POST)
        nid_form = NidForm(request.POST)
        causes_echec_form = CausesEchecForm(request.POST)

        forms = [
            fiche_form,
            localisation_form,
            resume_form,
            nid_form,
            causes_echec_form,
        ]

        if all(form.is_valid() for form in forms):
            # Enregistrez FicheObservation en premier pour obtenir l'instance
            fiche = fiche_form.save(commit=False)
            fiche.observateur = request.user
            fiche.annee = datetime.now().year
            fiche.save()

            # Enregistrez les autres formulaires en utilisant une boucle
            for form in forms[1:]:  # Commencez à l'index 1 pour exclure fiche_form
                instance = form.save(commit=False)
                instance.fiche = fiche
                instance.save()


            # Récupérez l'instance de FicheObservation pour l'affichage
            fiche_instance = FicheObservation.objects.get(pk=fiche.pk)  # Utilisez fiche.pk pour obtenir l'ID

            # Réinitialisez les formulaires avec l'instance enregistrée
            fiche_form = FicheObservationForm(instance=fiche_instance)
            localisation_form = LocalisationForm(instance=fiche_instance.localisation)  # Exemple
            resume_form = ResumeObservationForm(instance=fiche_instance.resume)  # Exemple
            nid_form = NidForm(instance=fiche_instance.nid)  # Exemple
            causes_echec_form = CausesEchecForm(instance=fiche_instance.causesechec)  # Exemple

            remarques = Remarque.objects.filter(fiche=fiche_instance)  # Récupérer les remarques

            return render(request, "saisie_observation_test.html", {
                "fiche_form": fiche_form,
                "localisation_form": localisation_form,
                "resume_form": resume_form,
                "nid_form": nid_form,
                "causes_echec_form": causes_echec_form,
                "remarques": remarques,
            })

    else:
        if fiche_id:  #   Si un ID est fourni, on édite
            try:
                fiche_instance = FicheObservation.objects.get(pk=fiche_id)
                fiche_form = FicheObservationForm(instance=fiche_instance)
                localisation_form = LocalisationForm(instance=fiche_instance.localisation) # Exemple, adapter selon vos modèles
                resume_form = ResumeObservationForm(instance=fiche_instance.resume) # Exemple, adapter selon vos modèles
                nid_form = NidForm(instance=fiche_instance.nid) # Exemple, adapter selon vos modèles
                causes_echec_form = CausesEchecForm(instance=fiche_instance.causes_echec) # Exemple, adapter selon vos modèles

                remarques = Remarque.objects.filter(fiche_id=fiche_id)  #   Filtrer par l'ID
            except FicheObservation.DoesNotExist:
                #   Gérer le cas où la fiche n'existe pas
                return render(request, 'saisie/error_page.html', {'message': "Fiche non trouvée"})

        else:  #   Sinon, on crée
            fiche_form = FicheObservationForm()
            localisation_form = LocalisationForm()
            resume_form = ResumeObservationForm()
            nid_form = NidForm()
            causes_echec_form = CausesEchecForm()
            remarques = [] # liste remarques vide

        return render(request, 'saisie/saisie_observation_test.html', {
            'fiche_form': fiche_form,
            'localisation_form': localisation_form,
            'resume_form': resume_form,
            'nid_form': nid_form,
            'causes_echec_form': causes_echec_form,
            'remarques': remarques
        })

@login_required
def ajouter_remarque(request, fiche_id):
    fiche = FicheObservation.objects.get(pk=fiche_id)  # Récupérer l'instance de FicheObservation
    if request.method == 'POST':
        form = RemarqueForm(request.POST)
        if form.is_valid():
            remarque = form.save(commit=False)  # Créer l'objet Remarque sans l'enregistrer
            remarque.fiche = fiche  # Associer la remarque à la fiche
            remarque.save()  # Enregistrer l'objet Remarque
            return redirect('detail_fiche', fiche_id=fiche_id)  # Rediriger vers la vue de détail de la fiche
    else:
        form = RemarqueForm(initial={'fiche': fiche})  # Pré-remplir le champ fiche
    return render(request, 'saisie/ajouter_remarque.html', {'form': form})