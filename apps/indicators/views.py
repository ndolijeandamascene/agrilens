"""
AgriLens Indicators & Productivity Views.
Provides dynamic analytics pages and JSON endpoints powered by PostgreSQL ValidatedObservation microdata.
Strict parameter validation protects against invalid requests and ensures statistical reproducibility.
"""
from django.shortcuts import render
from django.http import JsonResponse
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Province
from .services import IndicatorService

VALID_YEARS = [2024, 2025]
VALID_SEASONS = ['A', 'B', 'C']
VALID_SOURCES = ['official', 'manual', 'combined']


def _validate_common_params(request):
    """Safely extracts and validates query parameters with robust fallbacks."""
    # Year validation
    raw_year = request.GET.get('year', '2025')
    try:
        year = int(raw_year)
        if year not in VALID_YEARS:
            year = 2025
    except (ValueError, TypeError):
        year = 2025

    # Season validation
    season = request.GET.get('season', 'A').strip().upper()
    if season not in VALID_SEASONS:
        season = 'A'

    # Source policy validation
    source = request.GET.get('source', 'official').strip().lower()
    if source == 'all':
        source = 'combined'
    elif source not in VALID_SOURCES:
        source = 'official'

    # Crop validation
    crop = request.GET.get('crop', 'Maize').strip()
    if not crop:
        crop = 'Maize'

    return year, season, source, crop


def productivity_intelligence_view(request):
    """
    Track 1: Agricultural Productivity Intelligence Dashboard.
    Provides deep-dive comparisons, yield gap analytics, and multi-year trends.
    """
    year, season_code, source_policy, crop_filter = _validate_common_params(request)

    summary = IndicatorService.get_national_summary(
        season_code=season_code, year=year, crop_name=crop_filter, source_policy=source_policy
    )
    rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year, season_code=season_code, source_policy=source_policy
    )
    gap = IndicatorService.get_productivity_gap(
        crop_name=crop_filter, year=year, season_code=season_code, min_plots=5, source_policy=source_policy, rankings=rankings
    )
    yoy = IndicatorService.get_year_over_year_comparison(
        crop_name=crop_filter, season_code=season_code, source_policy=source_policy
    )

    all_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    if not all_crops.exists():
        all_crops = Crop.objects.all()[:15]

    context = {
        'page_title': 'Agricultural Productivity Intelligence & Yield Gap Analysis',
        'is_public_page': False,
        'selected_year': year,
        'selected_season': season_code,
        'selected_crop': crop_filter,
        'selected_source': source_policy,
        'summary': summary,
        'rankings': rankings[:10], # Top 10 districts
        'all_rankings': rankings,
        'gap': gap,
        'yoy': yoy,
        'priority_crops': all_crops,
    }
    return render(request, 'indicators/productivity_intelligence.html', context)


def api_national_summary(request):
    """
    REST endpoint returning national summary KPIs.
    """
    year, season, source, crop = _validate_common_params(request)
    # Check if crop parameter was explicitly provided
    crop_name = request.GET.get('crop') if 'crop' in request.GET else None

    data = IndicatorService.get_national_summary(
        season_code=season, year=year, crop_name=crop_name, source_policy=source
    )
    return JsonResponse({'status': 'success', 'data': data})


def api_district_rankings(request):
    """
    REST endpoint returning district rankings for Leaflet maps or charts.
    """
    year, season, source, crop = _validate_common_params(request)
    min_plots = 1
    raw_min = request.GET.get('min_plots')
    if raw_min and raw_min.isdigit():
        min_plots = max(1, int(raw_min))

    # If crop was not explicitly provided or is 'all', aggregate across all crops
    crop_param = request.GET.get('crop')
    crop_filter = crop if (crop_param and crop_param.strip().lower() not in ('', 'all', 'all priority crops')) else None

    rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year, season_code=season, min_plots=min_plots, source_policy=source
    )
    return JsonResponse({
        'status': 'success',
        'count': len(rankings),
        'filters': {'crop': crop_filter or 'All', 'year': year, 'season': season, 'source': source, 'min_plots': min_plots},
        'data': rankings
    })


def api_productivity_gap(request):
    """
    REST endpoint returning crop yield gap benchmark vs lagging with strict sample policy.
    """
    year, season, source, crop = _validate_common_params(request)
    min_plots = 5
    raw_min = request.GET.get('min_plots')
    if raw_min and raw_min.isdigit():
        min_plots = max(1, int(raw_min))

    gap = IndicatorService.get_productivity_gap(
        crop_name=crop, year=year, season_code=season, min_plots=min_plots, source_policy=source
    )
    return JsonResponse({'status': 'success', 'data': gap})

