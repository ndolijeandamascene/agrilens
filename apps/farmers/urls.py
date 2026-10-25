from django.urls import path
from . import views

app_name = 'farmers'

urlpatterns = [
    path('', views.farmer_list, name='farmer_list'),
    
    # Cooperatives CRUD
    path('cooperatives/create/', views.cooperative_create, name='cooperative_create'),
    path('cooperatives/<int:pk>/edit/', views.cooperative_edit, name='cooperative_edit'),
    path('cooperatives/<int:pk>/delete/', views.cooperative_delete, name='cooperative_delete'),
    
    # Farmers CRUD
    path('create/', views.farmer_create, name='farmer_create'),
    path('<int:pk>/edit/', views.farmer_edit, name='farmer_edit'),
    path('<int:pk>/delete/', views.farmer_delete, name='farmer_delete'),
]
