"""
API Viewsets and endpoints for external consumers and frontend visualizations.
"""
from rest_framework import viewsets
from apps.geography.models import Province, District
from apps.agriculture.models import Crop
from apps.markets.models import CommodityPrice
from .serializers import ProvinceSerializer, DistrictSerializer, CropSerializer, CommodityPriceSerializer

class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer

class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer

class CropViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer

class CommodityPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommodityPrice.objects.all()
    serializer_class = CommodityPriceSerializer
