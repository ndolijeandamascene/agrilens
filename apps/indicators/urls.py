from django.urls import path
from . import views

app_name = 'indicators'

urlpatterns = [
    path('productivity/', views.productivity_intelligence_view, name='productivity'),
    path('api/summary/', views.api_national_summary, name='api_summary'),
    path('api/districts/', views.api_district_rankings, name='api_districts'),
    path('api/productivity-gap/', views.api_productivity_gap, name='api_gap'),
]
