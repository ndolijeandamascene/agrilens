"""
AgriLens Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def health_check(request):
    """Health check endpoint for Docker / orchestration liveness probes."""
    return HttpResponse("OK", content_type="text/plain")

urlpatterns = [
    path('health/', health_check, name='health_check'),
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
    path('data-management/', include('apps.data_management.urls', namespace='data_management')),
    path('decision-support/', include('apps.decision_support.urls', namespace='decision_support')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('insights/', include('apps.insights.urls', namespace='insights')),
    path('assistant/', include('apps.assistant.urls', namespace='assistant')),
    path('api/', include('apps.api.urls', namespace='api')),
    path('api/v1/ml/', include('apps.ml.urls', namespace='ml')),
    path('api/v1/assistant/', include('apps.assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
