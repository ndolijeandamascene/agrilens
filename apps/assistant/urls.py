from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.assistant_view, name='assistant_home'),
    path('api/query/', views.AssistantQueryAPIView.as_view(), name='assistant_api_query'),
    path('query/', views.AssistantQueryAPIView.as_view(), name='assistant_api_query_alt'),
]
