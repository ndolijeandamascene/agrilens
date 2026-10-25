from django.urls import path
from . import views

app_name = 'inputs'

urlpatterns = [
    path('', views.input_list, name='input_list'),
    
    # Inputs CRUD
    path('create/', views.input_create, name='input_create'),
    path('<int:pk>/edit/', views.input_edit, name='input_edit'),
    path('<int:pk>/delete/', views.input_delete, name='input_delete'),
    
    # Categories CRUD
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
