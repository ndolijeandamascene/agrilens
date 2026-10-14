from django.urls import path
from . import views

app_name = 'markets'

urlpatterns = [
    path('', views.market_list, name='market_list'),
]

