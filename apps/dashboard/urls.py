from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.public_home, name='home'),
    path('', views.public_home, name='public_home'),
    path('dashboard/', views.dashboard_overview, name='overview'),

    # Public Agricultural Reports & Bulletins (Milestone 4 Design)
    path('reports/', views.public_reports, name='reports'),
    path('reports/<slug:slug>/pdf/', views.public_report_pdf, name='report_pdf'),
    path('reports/<slug:slug>/detail/', views.public_report_detail_api, name='report_detail_api'),
    path('reports/admin/generate-all/', views.admin_generate_all_reports_view, name='admin_generate_all_reports'),

    # Official Intelligence Reports & Bulletins (Milestone 4 Module)
    path('dashboard/reports/national/', views.reports_national, name='reports_national'),
    path('dashboard/reports/national/export/csv/', views.reports_national_export_csv, name='reports_national_export_csv'),
    path('dashboard/reports/national/export/excel/', views.reports_national_export_excel, name='reports_national_export_excel'),
    path('dashboard/reports/district/', views.reports_district, name='reports_district'),
    path('dashboard/reports/district/<int:district_id>/', views.reports_district, name='reports_district_detail'),
    path('dashboard/reports/district/export/csv/', views.reports_district_export_csv, name='reports_district_export_csv_default'),
    path('dashboard/reports/district/<int:district_id>/export/csv/', views.reports_district_export_csv, name='reports_district_export_csv'),
    path('dashboard/reports/district/export/excel/', views.reports_district_export_excel, name='reports_district_export_excel_default'),
    path('dashboard/reports/district/<int:district_id>/export/excel/', views.reports_district_export_excel, name='reports_district_export_excel'),
]

