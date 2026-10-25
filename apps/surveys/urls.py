from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_list, name='survey_list'),
    path('campaigns/create/', views.survey_campaign_create, name='survey_campaign_create'),
    path('campaigns/<int:pk>/edit/', views.survey_campaign_edit, name='survey_campaign_edit'),
    path('campaigns/<int:pk>/delete/', views.survey_campaign_delete, name='survey_campaign_delete'),
]
