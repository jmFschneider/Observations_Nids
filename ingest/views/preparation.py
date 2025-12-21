"""
Vues pour la préparation des images (fusion recto/verso, prétraitements).
"""

import json

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ingest.models import PreparationImage


@login_required
@require_http_methods(["GET", "POST"])
def preparer_images_view(request):
    """
    Interface de préparation des images pour OCR.

    GET : Affiche l'interface de préparation
    POST : Reçoit les images fusionnées et crée les enregistrements PreparationImage
    """
    if request.method == "GET":
        # Afficher l'interface
        return render(
            request,
            'ingest/preparer_images.html',
            {
                'titre': 'Préparation des images pour OCR',
            },
        )

    # POST : Traiter l'upload d'une image fusionnée
    try:
        # Récupérer les données du formulaire
        fichier_recto = request.POST.get('fichier_recto')
        fichier_verso = request.POST.get('fichier_verso', '')
        operations = request.POST.get('operations', '{}')
        notes = request.POST.get('notes', '')

        # Récupérer le fichier uploadé
        if 'fichier_fusionne' not in request.FILES:
            return JsonResponse(
                {'success': False, 'error': 'Aucun fichier fusionné fourni'}, status=400
            )

        fichier_fusionne = request.FILES['fichier_fusionne']

        # Créer l'enregistrement PreparationImage
        operations_dict = json.loads(operations) if operations else {}

        preparation = PreparationImage.objects.create(
            fichier_brut_recto=fichier_recto,
            fichier_brut_verso=fichier_verso,
            operations_effectuees=operations_dict,
            notes=notes,
            operateur=request.user,
        )

        # Sauvegarder le fichier fusionné
        preparation.fichier_fusionne.save(
            fichier_fusionne.name, ContentFile(fichier_fusionne.read()), save=True
        )

        return JsonResponse(
            {
                'success': True,
                'preparation_id': preparation.id,
                'message': f'Image préparée avec succès (ID: {preparation.id})',
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Format JSON invalide pour les opérations'}, status=400
        )

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def liste_preparations_view(request):
    """
    Liste des préparations d'images effectuées.
    """
    preparations = PreparationImage.objects.select_related('operateur').order_by(
        '-date_preparation'
    )

    return render(
        request,
        'ingest/liste_preparations.html',
        {
            'preparations': preparations,
            'titre': 'Liste des préparations d\'images',
        },
    )
