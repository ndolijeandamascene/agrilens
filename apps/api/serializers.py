"""
DRF Serializers for AgriLens API endpoints.
"""
from rest_framework import serializers
from apps.geography.models import Province, District
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.markets.models import CommodityPrice

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'

class CommodityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommodityPrice
        fields = '__all__'
