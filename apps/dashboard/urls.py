from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.public_home, name='home'),
    path('dashboard/', views.dashboard_overview, name='overview'),
]
