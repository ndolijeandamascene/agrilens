from django.urls import path
from . import views
from . import views_internal_reports

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

    # Internal Report Center (Role-Protected Institutional Workspace)
    path('dashboard/reports/center/', views_internal_reports.report_center_overview, name='internal_report_center'),
    path('dashboard/reports/generate/', views_internal_reports.report_center_generate, name='internal_report_generate'),
    path('dashboard/reports/history/', views_internal_reports.report_center_history, name='internal_report_history'),
    path('dashboard/reports/generated/<int:report_id>/', views_internal_reports.report_center_detail, name='internal_report_detail'),
    path('dashboard/reports/generated/<int:report_id>/download/', views_internal_reports.report_center_download, name='internal_report_download'),
    path('dashboard/reports/generated/<int:report_id>/submit-review/', views_internal_reports.report_action_submit_review, name='internal_report_submit_review'),
    path('dashboard/reports/generated/<int:report_id>/approve/', views_internal_reports.report_action_approve, name='internal_report_approve'),
    path('dashboard/reports/generated/<int:report_id>/reject/', views_internal_reports.report_action_reject, name='internal_report_reject'),
    path('dashboard/reports/generated/<int:report_id>/publish/', views_internal_reports.report_action_publish, name='internal_report_publish'),
    path('dashboard/reports/generated/<int:report_id>/unpublish/', views_internal_reports.report_action_unpublish, name='internal_report_unpublish'),
    path('dashboard/reports/schedules/', views_internal_reports.report_center_schedules, name='internal_report_schedules'),
    path('dashboard/reports/schedules/create/', views_internal_reports.report_schedule_create, name='internal_report_schedule_create'),
    path('dashboard/reports/schedules/<int:schedule_id>/toggle/', views_internal_reports.report_schedule_toggle, name='internal_report_schedule_toggle'),
    path('dashboard/reports/schedules/<int:schedule_id>/run-now/', views_internal_reports.report_schedule_run_now, name='internal_report_schedule_run_now'),
    path('dashboard/reports/published/', views_internal_reports.report_center_published, name='internal_report_published'),
]

