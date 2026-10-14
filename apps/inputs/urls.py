from django.urls import path
from . import views

app_name = 'inputs'

urlpatterns = [
    path('', views.input_list, name='input_list'),
]

