"""
AgriLens Agricultural Insights Web URL Configuration.
"""
from django.urls import path
from apps.insights import views

app_name = 'insights'

urlpatterns = [
    # Public Agricultural Insights & Data Stories
    path('', views.public_insights_list, name='public_list'),
    path('<int:pk>/', views.public_insight_detail, name='public_detail'),

    # Internal Analyst Management & Review Interface
    path('manage/', views.internal_dashboard, name='internal_dashboard'),
    path('manage/all/', views.internal_list, name='internal_list'),
    path('manage/review/', views.internal_review_queue, name='internal_review_queue'),
    path('manage/<int:pk>/', views.internal_detail, name='internal_detail'),
    path('manage/<int:pk>/approve/', views.internal_approve, name='internal_approve'),
    path('manage/<int:pk>/reject/', views.internal_reject, name='internal_reject'),
    path('manage/<int:pk>/publish/', views.internal_publish, name='internal_publish'),
    path('manage/<int:pk>/unpublish/', views.internal_unpublish, name='internal_unpublish'),
    path('manage/generate/', views.internal_generate, name='internal_generate'),
]
