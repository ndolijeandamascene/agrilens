from django.urls import path
from . import views

app_name = 'markets'

urlpatterns = [
    # 1. Public Commodity Markets Surveillance Board
    path('', views.market_list, name='market_list'),

    # 2. Staff Internal Commodity Prices Management Suite
    path('internal/', views.internal_dashboard, name='internal_dashboard'),
    path('internal/records/', views.internal_records, name='internal_records'),
    path('internal/records/create/', views.internal_record_create, name='internal_record_create'),
    path('internal/records/<int:pk>/edit/', views.internal_record_edit, name='internal_record_edit'),
    path('internal/records/<int:pk>/delete/', views.internal_record_delete, name='internal_record_delete'),
    path('internal/records/import/', views.internal_records_import, name='internal_records_import'),
    path('internal/markets/', views.internal_markets, name='internal_markets'),
    path('internal/markets/<int:pk>/edit/', views.internal_market_edit, name='internal_market_edit'),
    path('internal/markets/<int:pk>/delete/', views.internal_market_delete, name='internal_market_delete'),
    path('internal/commodities/', views.internal_commodities, name='internal_commodities'),
    path('internal/commodities/<int:pk>/edit/', views.internal_commodity_edit, name='internal_commodity_edit'),
    path('internal/commodities/<int:pk>/delete/', views.internal_commodity_delete, name='internal_commodity_delete'),
    path('internal/collection/', views.internal_collection, name='internal_collection'),
    path('internal/approvals/', views.internal_approvals, name='internal_approvals'),
    path('internal/approvals/<int:pk>/action/', views.internal_approval_action, name='internal_approval_action'),
    path('internal/analytics/', views.internal_analytics, name='internal_analytics'),
    path('internal/reports/', views.internal_reports, name='internal_reports'),
    path('internal/publications/', views.internal_publications, name='internal_publications'),
    path('internal/audit/', views.internal_audit_log, name='internal_audit_log'),
]
