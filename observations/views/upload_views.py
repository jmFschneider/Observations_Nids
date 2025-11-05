from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from ..forms import ImageSourceForm
from ..models import ImageSource


@login_required
def upload_image_source(request):
    if request.method == 'POST':
        form = ImageSourceForm(request.POST, request.FILES)
        if form.is_valid():
            image_source = form.save(commit=False)
            image_source.observateur = request.user
            image_source.save()
            messages.success(
                request,
                "Votre fiche image a été téléversée avec succès et est en attente de transcription.",
            )
            return redirect('observations:upload_success')
        else:
            messages.error(
                request, "Une erreur est survenue lors du téléversement de votre fiche image."
            )
    else:
        form = ImageSourceForm()
    return render(request, 'observations/upload_image_source.html', {'form': form})


@login_required
def upload_success(request):
    return render(request, 'observations/upload_success.html')


@login_required
def mes_images_sources(request):
    """Liste les images téléversées par l'utilisateur connecté"""
    images = (
        ImageSource.objects.filter(observateur=request.user)
        .select_related('fiche_observation', 'fiche_observation__espece')
        .order_by('-date_televersement')
    )

    # Statistiques
    total_images = images.count()
    images_transcrites = images.filter(est_transcrite=True).count()
    images_en_attente = images.filter(est_transcrite=False).count()

    # Pagination
    paginator = Paginator(images, 12)  # 12 images par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'images': page_obj,
        'total_images': total_images,
        'images_transcrites': images_transcrites,
        'images_en_attente': images_en_attente,
    }
    return render(request, 'observations/mes_images_sources.html', context)
