"""
AgriLens Agricultural Insights REST API URL Configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.insights.api_views import AgriculturalInsightViewSet

router = DefaultRouter()
router.register(r'insights', AgriculturalInsightViewSet, basename='insight-api')

urlpatterns = [
    path('', include(router.urls)),
]
