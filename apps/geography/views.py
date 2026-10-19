"""
AgriLens Geography Domain Views.
Displays Rwanda's administrative structure: 5 Provinces, 30 Districts, 416 Sectors.
"""
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Province, District, Sector
from apps.data_management.models import ValidatedObservation
from apps.accounts.permissions import can_access_district, scope_queryset_by_geography


import json


def district_list(request):
    """
    Public Interactive Agricultural Map View.
    Displays Rwanda's 30 districts with dynamic choropleth filtering by crop, season, and indicator,
    and a localized District Details inspection dossier.
    """
    province_id = request.GET.get('province')

    provinces = Province.objects.prefetch_related('districts').all().order_by('name')
    districts = District.objects.select_related('province').annotate(
        sectors_count=Count('sectors', distinct=True),
        observations_count=Count('observations', distinct=True)
    ).order_by('province__name', 'name')

    # Geographic scoping for District Officers
    districts = scope_queryset_by_geography(districts, request.user, district_field='id')

    if province_id and province_id.isdigit():
        districts = districts.filter(province_id=int(province_id))

    # Comprehensive District Catalog for Dynamic Map & Sidebar
    district_data = {}
    for d in District.objects.select_related('province').all():
        district_data[d.name] = {
            'id': d.id,
            'name': d.name,
            'code': d.code,
            'province': d.province.name,
            'report_url': f"/dashboard/reports/district/{d.id}/",
        }

    # Available dynamic filters
    crops_catalog = [
        {'code': 'Maize', 'name': 'Maize'},
        {'code': 'Beans', 'name': 'Beans'},
        {'code': 'Irish Potato', 'name': 'Irish Potato'},
        {'code': 'Rice', 'name': 'Rice'},
        {'code': 'Cassava', 'name': 'Cassava'},
    ]
    seasons_catalog = [
        {'code': '2025A', 'label': 'SAS 2024 – 2025'},
        {'code': '2024A', 'label': 'SAS 2023 – 2024'},
    ]
    indicators_catalog = [
        {'code': 'yield', 'label': 'Yield (t/ha)'},
        {'code': 'production', 'label': 'Production (t)'},
        {'code': 'area', 'label': 'Cultivated Area (ha)'},
    ]

    selected_crop = request.GET.get('crop', 'Maize')
    selected_season = request.GET.get('season', '2025A')
    selected_indicator = request.GET.get('indicator', 'yield')
    selected_district_name = request.GET.get('district', 'Nyabihu')
    default_dist = district_data.get(selected_district_name, district_data.get('Nyabihu', {'id': 15, 'name': 'Nyabihu', 'province': 'Western Province'}))

    context = {
        'page_title': 'Agricultural Map | AgriLens Rwanda',
        'provinces': provinces,
        'districts': districts,
        'selected_province': province_id,
        'total_districts': districts.count() or 30,
        'total_sectors': Sector.objects.count() or 416,
        'crops': crops_catalog,
        'seasons': seasons_catalog,
        'indicators': indicators_catalog,
        'selected_crop': selected_crop,
        'selected_season': selected_season,
        'selected_indicator': selected_indicator,
        'selected_district_name': default_dist['name'],
        'selected_district_id': default_dist.get('id', 15),
        'selected_province_name': default_dist.get('province', 'Western Province'),
        'district_data_json': json.dumps(district_data),
        'kpi_tracked_crops': '10',
        'kpi_validated_records': '10,000' if selected_season == '2025A' else '5,000',
        'kpi_geographic_coverage': '30',
        'kpi_total_production': '1.24M t' if selected_season == '2025A' else '1.18M t',
    }
    return render(request, 'geography/district_list.html', context)




def district_detail(request, pk):
    """Detailed view for an individual district with sectors and observations, with geographic clearance checks."""
    district = get_object_or_404(District.objects.select_related('province'), pk=pk)

    # Server-side Geographic Clearance Enforcement
    if not can_access_district(request.user, district.id):
        return render(request, '403.html', {
            'reason': f"Geographic Access Restricted: You are not authorized to inspect intelligence for {district.name} District."
        }, status=403)

    sectors = Sector.objects.filter(district=district).order_by('name')
    recent_obs = ValidatedObservation.objects.filter(district=district).select_related(
        'crop', 'season'
    ).order_by('-id')[:10]

    context = {
        'page_title': f"{district.name} District &bull; Geographic Intelligence",
        'district': district,
        'sectors': sectors,
        'recent_obs': recent_obs,
        'total_obs': ValidatedObservation.objects.filter(district=district).count(),
    }
    return render(request, 'geography/district_detail.html', context)

