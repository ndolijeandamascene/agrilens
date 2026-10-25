"""
URL routing for AgriLens Notification Center & Preferences.
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_center, name='notification_center'),
    path('mark-all-read/', views.notification_mark_all_read, name='mark_all_read'),
    path('<int:pk>/read/', views.notification_mark_read, name='mark_read'),
    path('<int:pk>/unread/', views.notification_mark_unread, name='mark_unread'),
    path('<int:pk>/dismiss/', views.notification_dismiss, name='dismiss'),
    path('preferences/', views.notification_preferences_view, name='preferences'),
    path('admin/', views.admin_announcements_view, name='admin_announcements'),
    path('admin/retry-email/<int:pk>/', views.admin_retry_email, name='admin_retry_email'),
    path('unread-count/', views.api_unread_count, name='unread_count'),
]
