from django.urls import path

from . import views

app_name = 'geo'

urlpatterns = [
    path('geocoder/', views.geocoder_commune_manuelle, name='geocoder_commune'),
    path('rechercher-communes/', views.rechercher_communes, name='rechercher_communes'),
]
