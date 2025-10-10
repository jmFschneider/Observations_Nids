"""URLs de l'application taxonomy."""

from django.urls import path

from taxonomy import views

app_name = 'taxonomy'

urlpatterns = [
    # Liste et détail
    path('especes/', views.liste_especes, name='liste_especes'),
    path('especes/<int:espece_id>/', views.detail_espece, name='detail_espece'),
    # CRUD
    path('especes/creer/', views.creer_espece, name='creer_espece'),
    path('especes/<int:espece_id>/modifier/', views.modifier_espece, name='modifier_espece'),
    path('especes/<int:espece_id>/supprimer/', views.supprimer_espece, name='supprimer_espece'),
    # Import
    path('importer/', views.importer_especes, name='importer_especes'),
]
