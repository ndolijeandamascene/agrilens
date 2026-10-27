from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.assistant_view, name='assistant_home'),
    path('api/query/', views.AssistantQueryAPIView.as_view(), name='assistant_api_query'),
    path('query/', views.AssistantQueryAPIView.as_view(), name='assistant_api_query_alt'),
    path('api/status/', views.AssistantStatusAPIView.as_view(), name='assistant_api_status'),
    path('status/', views.AssistantStatusAPIView.as_view(), name='assistant_api_status_alt'),
    path('api/download/', views.AssistantDownloadAPIView.as_view(), name='assistant_api_download'),
    path('download/', views.AssistantDownloadAPIView.as_view(), name='assistant_api_download_alt'),
]
