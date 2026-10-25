from django.urls import path
from . import views

app_name = 'agriculture'

urlpatterns = [
    path('', views.crop_list, name='crop_list'),
    path('<int:pk>/', views.crop_detail, name='crop_detail'),
    
    # Crops CRUD
    path('crops/create/', views.crop_create, name='crop_create'),
    path('<int:pk>/edit/', views.crop_edit, name='crop_edit'),
    path('<int:pk>/delete/', views.crop_delete, name='crop_delete'),
    
    # Categories CRUD
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
