"""
AgriLens Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('agriculture/', include('apps.agriculture.urls', namespace='agriculture')),
    path('geography/', include('apps.geography.urls', namespace='geography')),
    path('surveys/', include('apps.surveys.urls', namespace='surveys')),
    path('farmers/', include('apps.farmers.urls', namespace='farmers')),
    path('inputs/', include('apps.inputs.urls', namespace='inputs')),
    path('markets/', include('apps.markets.urls', namespace='markets')),
    path('indicators/', include('apps.indicators.urls', namespace='indicators')),
    path('api/', include('apps.api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
