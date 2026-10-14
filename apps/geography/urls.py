from django.urls import path
from . import views

app_name = 'geography'

urlpatterns = [
    path('', views.district_list, name='district_list'),
    path('<int:pk>/', views.district_detail, name='district_detail'),
]

