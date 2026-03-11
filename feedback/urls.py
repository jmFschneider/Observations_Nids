from django.urls import path

from . import views

app_name = 'feedback'

urlpatterns = [
    path('submit/', views.submit_feedback, name='submit'),
    path('list/', views.feedback_list, name='list'),
    path('detail/<int:feedback_id>/', views.feedback_detail, name='detail'),
    path('triage/', views.feedback_triage, name='triage'),
    path('update/<int:feedback_id>/', views.update_feedback, name='update'),
    path('problemes-techniques/', views.technical_problems, name='technical_problems'),
    path('ocr/', views.ocr_problems, name='ocr_problems'),
]
