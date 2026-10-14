"""
API Viewsets and endpoints for external consumers and frontend visualizations.
"""
from rest_framework import viewsets
from apps.geography.models import Province, District
from apps.agriculture.models import Crop
from apps.markets.models import CommodityPrice
from apps.accounts.permissions import scope_queryset_by_geography
from .serializers import ProvinceSerializer, DistrictSerializer, CropSerializer, CommodityPriceSerializer


class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Province.objects.all().order_by('name')
    serializer_class = ProvinceSerializer


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DistrictSerializer

    def get_queryset(self):
        qs = District.objects.select_related('province').all().order_by('name')
        
        # Geographic scoping for District Officers
        if self.request.user.is_authenticated:
            qs = scope_queryset_by_geography(qs, self.request.user, district_field='id')

        province = self.request.query_params.get('province')
        if province:
            if province.isdigit():
                qs = qs.filter(province_id=int(province))
            else:
                qs = qs.filter(province__name__iexact=province)
        return qs


class CropViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CropSerializer

    def get_queryset(self):
        qs = Crop.objects.select_related('category').all().order_by('name')
        priority = self.request.query_params.get('priority')
        if priority is not None:
            is_prio = priority.lower() in ['true', '1', 'yes']
            qs = qs.filter(is_priority_crop=is_prio)
        return qs


class CommodityPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommodityPriceSerializer

    def get_queryset(self):
        qs = CommodityPrice.objects.select_related('market__district', 'crop').all().order_by('-date_recorded')

        # Geographic scoping for District Officers
        if self.request.user.is_authenticated:
            qs = scope_queryset_by_geography(qs, self.request.user, district_field='market__district')

        crop = self.request.query_params.get('crop')
        if crop:
            if crop.isdigit():
                qs = qs.filter(crop_id=int(crop))
            else:
                qs = qs.filter(crop__name__iexact=crop)

        market = self.request.query_params.get('market')
        if market:
            if market.isdigit():
                qs = qs.filter(market_id=int(market))
            else:
                qs = qs.filter(market__name__icontains=market)

        return qs

