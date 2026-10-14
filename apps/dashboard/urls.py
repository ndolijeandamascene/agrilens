from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.public_home, name='home'),
    path('', views.public_home, name='public_home'),
    path('dashboard/', views.dashboard_overview, name='overview'),

    # Official Intelligence Reports & Bulletins (Milestone 4 Module)
    path('dashboard/reports/national/', views.reports_national, name='reports_national'),
    path('dashboard/reports/district/', views.reports_district, name='reports_district'),
    path('dashboard/reports/district/<int:district_id>/', views.reports_district, name='reports_district_detail'),
]

