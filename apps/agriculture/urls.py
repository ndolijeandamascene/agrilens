from django.urls import path
from . import views

app_name = 'agriculture'

urlpatterns = [
    path('', views.crop_list, name='crop_list'),
    path('<int:pk>/', views.crop_detail, name='crop_detail'),
]

