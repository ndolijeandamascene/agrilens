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

    from apps.agriculture.models import Crop, AgriculturalSeason
    from apps.indicators.services import IndicatorService

    # Available dynamic filters queried directly from database
    p_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    if not p_crops.exists():
        p_crops = Crop.objects.all().order_by('name')
    crops_catalog = [{'code': c.name, 'name': c.name} for c in p_crops]

    db_seasons = AgriculturalSeason.objects.filter(observations__isnull=False).distinct().order_by('-year', 'season')
    if not db_seasons.exists():
        db_seasons = AgriculturalSeason.objects.all().order_by('-year', 'season')
    seasons_catalog = [
        {
            'code': f"{s.year}{s.season}",
            'label': f"SAS {s.year - 1} – {s.year}" if s.season == 'A' else f"SAS {s.year} Season {s.season}"
        }
        for s in db_seasons
    ]

    indicators_catalog = [
        {'code': 'yield', 'label': 'Yield (t/ha)'},
        {'code': 'production', 'label': 'Production (t)'},
        {'code': 'area', 'label': 'Cultivated Area (ha)'},
    ]

    selected_crop = request.GET.get('crop', crops_catalog[0]['code'] if crops_catalog else 'Maize')
    selected_season = request.GET.get('season', seasons_catalog[0]['code'] if seasons_catalog else '2025A')
    selected_indicator = request.GET.get('indicator', 'yield')
    selected_district_name = request.GET.get('district')

    # Support direct global search terms passed from header search
    search_term = (request.GET.get('search') or request.GET.get('q') or '').strip()
    if search_term:
        matching_dist = District.objects.filter(name__iexact=search_term).first() or District.objects.filter(name__icontains=search_term).first()
        if matching_dist:
            selected_district_name = matching_dist.name

        matching_crop = Crop.objects.filter(name__iexact=search_term).first() or Crop.objects.filter(name__icontains=search_term).first()
        if matching_crop:
            selected_crop = matching_crop.name

        term_lower = search_term.lower()
        if 'yield' in term_lower or 'productiv' in term_lower:
            selected_indicator = 'yield'
        elif 'prod' in term_lower or 'harvest' in term_lower or 'volume' in term_lower:
            selected_indicator = 'production'
        elif 'area' in term_lower or 'hectare' in term_lower or 'ha' in term_lower:
            selected_indicator = 'area'

    default_dist = district_data.get(selected_district_name) if selected_district_name else next(iter(district_data.values()), None)

    # Dynamic KPI computation from IndicatorService
    try:
        filter_year = int(selected_season[:4])
        filter_season_code = selected_season[4:]
    except (ValueError, IndexError):
        filter_year = 2025
        filter_season_code = 'A'

    nat_summary = IndicatorService.get_national_summary(
        year=filter_year, season_code=filter_season_code, crop_name=selected_crop
    )
    obs_count = nat_summary.get('observation_count', 0)
    total_prod = nat_summary.get('total_production_mt', 0.0)
    if total_prod >= 1e6:
        prod_display = f"{round(total_prod / 1e6, 2)}M t"
    elif total_prod > 0:
        prod_display = f"{round(total_prod / 1e3, 1)}K t"
    else:
        prod_display = "Data unavailable"

    context = {
        'page_title': 'Agricultural Map | AgriLens Rwanda',
        'provinces': provinces,
        'districts': districts,
        'selected_province': province_id,
        'total_districts': districts.count(),
        'total_sectors': Sector.objects.count(),
        'crops': crops_catalog,
        'seasons': seasons_catalog,
        'indicators': indicators_catalog,
        'selected_crop': selected_crop,
        'selected_season': selected_season,
        'selected_indicator': selected_indicator,
        'selected_district_name': default_dist['name'] if default_dist else None,
        'selected_district_id': default_dist.get('id') if default_dist else None,
        'selected_province_name': default_dist.get('province') if default_dist else None,
        'district_data_json': json.dumps(district_data),
        'kpi_tracked_crops': str(p_crops.count()),
        'kpi_validated_records': f"{obs_count:,}" if obs_count else "0",
        'kpi_geographic_coverage': str(District.objects.count()),
        'kpi_total_production': prod_display,
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

