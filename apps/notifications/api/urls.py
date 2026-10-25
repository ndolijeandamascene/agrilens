"""
API URL routes for notifications.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.notifications.api.views import (
    NotificationViewSet,
    NotificationPreferenceAPIView,
    SystemAnnouncementViewSet,
)

router = DefaultRouter()
router.register(r'announcements', SystemAnnouncementViewSet, basename='announcement')
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('preferences/', NotificationPreferenceAPIView.as_view(), name='api_preferences'),
    path('', include(router.urls)),
]
