from django.urls import path
from . import views

app_name = 'decision_support'

urlpatterns = [
    path('', views.decision_hub, name='hub'),
    path('recommendations/', views.recommendation_list, name='recommendation_list'),
    path('recommendations/<int:pk>/', views.recommendation_detail, name='recommendation_detail'),
    path('recommendations/<int:pk>/transition/', views.recommendation_transition, name='recommendation_transition'),
    path('recommendations/<int:pk>/actions/create/', views.action_plan_create, name='action_plan_create'),
    path('actions/<int:pk>/update/', views.action_plan_update, name='action_plan_update'),
    path('impact/', views.impact_dashboard, name='impact_dashboard'),
    path('generate/', views.generate_recommendations_action, name='generate'),
    path('export/csv/', views.recommendation_export_csv, name='recommendation_export_csv'),
    path('export/excel/', views.recommendation_export_excel, name='recommendation_export_excel'),
]
