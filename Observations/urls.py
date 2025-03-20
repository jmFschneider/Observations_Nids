from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path


from Observations.views.view_test_saisie import fiche_test_observation_view
from Observations.views.views_home import home, user_list, user_detail, inscription, default_view
from Observations.views.views_observation import (
    fiche_observation_view)

from Observations.views.views_saisie import saisie_observation, traiter_saisie_observation

urlpatterns = [
    path('', home, name='home'),
    path('default/', default_view, name='default'),

    path('inscription/', inscription, name='inscription'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('users/', user_list, name='user_list'),
    path('users/<int:user_id>/', user_detail, name='user_detail'),
    path('users/add/', inscription, name='user_create'),
    path('fiche/<int:fiche_id>/', fiche_observation_view, name='fiche_observation'),
    path('observations/nouvelle/', saisie_observation, name='saisie_observation'),
    path('observations/sauvegarde/', traiter_saisie_observation, name='traiter_saisie_observation'),
    path('observations/saisie/', fiche_test_observation_view, name='saisie_test'),
]
""" path(route, associate view, name='reverse')

  path('articles/<int:year>/<int:month>/', views.month_archive),
 A request to /articles/2005/03/ would match the third entry in the list. Django would call the function 
 views.month_archive(request, year=2005, month=3)
 
 path('articles/<int:year>/', views.year_archive, name='news-year-archive'),
 
 fichier html : 
 <a href="{% url 'news-year-archive' yearvar %}">{{ yearvar }} Archive</a>
  fichier views : 
  def redirect_to_year(request):
    # ...
    year = 2006
    # ...
    return HttpResponseRedirect(reverse('news-year-archive', args=(year,)))
 """
