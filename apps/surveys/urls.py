from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_list, name='survey_list'),
    
    # Survey Campaigns CRUD
    path('campaigns/create/', views.survey_campaign_create, name='survey_campaign_create'),
    path('campaigns/<int:pk>/edit/', views.survey_campaign_edit, name='survey_campaign_edit'),
    path('campaigns/<int:pk>/delete/', views.survey_campaign_delete, name='survey_campaign_delete'),
    
    # AHS District Socioeconomic Profiles CRUD
    path('socioeconomic/create/', views.socioeconomic_create, name='socioeconomic_create'),
    path('socioeconomic/<int:pk>/edit/', views.socioeconomic_edit, name='socioeconomic_edit'),
    path('socioeconomic/<int:pk>/delete/', views.socioeconomic_delete, name='socioeconomic_delete'),

    # Farm Survey Submissions CRUD
    path('submissions/create/', views.submission_create, name='submission_create'),
    path('submissions/<int:pk>/edit/', views.submission_edit, name='submission_edit'),
    path('submissions/<int:pk>/delete/', views.submission_delete, name='submission_delete'),
]
