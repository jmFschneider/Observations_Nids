from django.urls import path
from . import views
from .views import fiche_observation_view

urlpatterns = [
    path('', views.home, name='home'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/add/', views.user_create, name='user_create'),
    path('fiche/<int:fiche_id>/', fiche_observation_view, name='fiche_observation'),
]