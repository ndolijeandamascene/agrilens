from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'provinces', views.ProvinceViewSet, basename='province')
router.register(r'districts', views.DistrictViewSet, basename='district')
router.register(r'crops', views.CropViewSet, basename='crop')
router.register(r'prices', views.CommodityPriceViewSet, basename='price')

urlpatterns = [
    path('', include(router.urls)),
]
