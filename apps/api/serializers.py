"""
DRF Serializers for AgriLens API endpoints.
Provides structured, safe serialization without exposing sensitive or unnecessary internal fields.
"""
from rest_framework import serializers
from apps.geography.models import Province, District
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.markets.models import CommodityPrice, MarketLocation


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name', 'code']


class DistrictSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source='province.name', read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'code', 'province', 'province_name']


class CropSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Crop
        fields = ['id', 'name', 'kinyarwanda_name', 'scientific_name', 'is_priority_crop', 'category', 'category_name']


class CommodityPriceSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    market_name = serializers.CharField(source='market.name', read_only=True)
    district_name = serializers.CharField(source='market.district.name', read_only=True)

    class Meta:
        model = CommodityPrice
        fields = [
            'id', 'crop', 'crop_name', 'market', 'market_name',
            'district_name', 'price_per_kg_rwf', 'wholesale_price_rwf', 'date_recorded'
        ]

