from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_list, name='survey_list'),
]

