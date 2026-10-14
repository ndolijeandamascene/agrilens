from django.urls import path
from . import views

app_name = 'data_management'

urlpatterns = [
    path('', views.data_hub_dashboard, name='hub'),
    path('manual/', views.manual_entry_list, name='manual_entry_list'),
    path('manual/new/', views.manual_entry_create, name='manual_entry_create'),
    path('manual/<int:pk>/', views.manual_entry_detail, name='manual_entry_detail'),
    path('manual/<int:pk>/edit/', views.manual_entry_edit, name='manual_entry_edit'),
    path('manual/<int:pk>/review/', views.manual_entry_review, name='manual_entry_review'),
    
    # Dynamic Data Source Registration
    path('sources/new/', views.data_source_create, name='data_source_create'),
    
    # Dependent Dropdown APIs
    path('api/provinces/<int:province_id>/districts/', views.api_districts_by_province, name='api_districts'),
    path('api/districts/<int:district_id>/sectors/', views.api_sectors_by_district, name='api_sectors'),
]
