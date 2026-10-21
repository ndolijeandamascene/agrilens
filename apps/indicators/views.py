"""
AgriLens Indicators & Productivity Views.
Provides dynamic analytics pages and JSON endpoints powered by PostgreSQL ValidatedObservation microdata.
Strict parameter validation protects against invalid requests and ensures statistical reproducibility.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Province, Sector
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
    Track 1: Agricultural Productivity Intelligence & Yield Gap Analysis Dashboard.
    Implements complete decision chain: Detect -> Investigate -> Prioritize -> Plan -> Monitor.
    Adheres to official 7-section blueprint with empirical microdata from NISR and MINAGRI.
    """
    year, season_code, source_policy, crop_filter = _validate_common_params(request)

    selected_province = request.GET.get('province', '').strip()
    selected_district = request.GET.get('district', '').strip()
    selected_sector = request.GET.get('sector', '').strip()
    benchmark_type = request.GET.get('benchmark', 'top_district').strip()
    if benchmark_type not in ('top_district', 'p90', 'national', 'attainable_target'):
        benchmark_type = 'top_district'

    # Geographic models for filters
    provinces = Province.objects.all().order_by('name')
    districts = District.objects.select_related('province').all().order_by('name')
    if selected_province and selected_province.lower() not in ('all', 'all provinces'):
        districts = districts.filter(province__name__iexact=selected_province)

    sectors = Sector.objects.none()
    target_district_id = None
    if selected_district and selected_district.lower() not in ('all', 'all districts'):
        target_dist = District.objects.filter(name__iexact=selected_district).first()
        if target_dist:
            target_district_id = target_dist.id
            sectors = Sector.objects.filter(district=target_dist).order_by('name')

    summary = IndicatorService.get_national_summary(
        season_code=season_code, year=year, crop_name=crop_filter, source_policy=source_policy
    )

    # 1. Base rankings across all districts (for choropleth map & benchmark determination)
    all_30_rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year, season_code=season_code, source_policy=source_policy
    )

    # 2. Scoped rankings (filtered if province/district filter applied)
    scoped_rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year, season_code=season_code, source_policy=source_policy,
        province_name=selected_province if selected_province else None,
        district_name=selected_district if selected_district else None
    )

    # 3. Yield Gap calculation using selected benchmark & target district
    gap = IndicatorService.get_productivity_gap(
        crop_name=crop_filter, year=year, season_code=season_code, min_plots=1,
        source_policy=source_policy, rankings=all_30_rankings,
        benchmark_type=benchmark_type, target_district_id=target_district_id
    )

    # Reference benchmark yield (t/ha)
    b_yield_tha = gap.get('reference_yield_tha', 0.0) if gap.get('is_sufficient_data') else 0.0

    # 4. Enrich every district with gap calculations, opportunity, and drivers
    enriched_rankings = []
    prioritized_locations = []
    for r in scoped_rankings:
        y_tha = r.get('yield_tha', 0.0)
        area_ha = float(r.get('area_ha') or 0.0)
        abs_gap = max(0.0, round(b_yield_tha - y_tha, 2)) if b_yield_tha > 0 else 0.0
        rel_gap = round(((b_yield_tha - y_tha) / b_yield_tha) * 100.0, 1) if b_yield_tha > 0 else 0.0
        opp_tonnes = max(0.0, round(abs_gap * area_ha, 1))

        # Priority tier assessment
        if rel_gap >= 40.0 and area_ha >= 500:
            tier = 'CRITICAL'
            tier_class = 'critical'
        elif rel_gap >= 25.0:
            tier = 'HIGH'
            tier_class = 'high'
        elif rel_gap > 5.0:
            tier = 'MODERATE'
            tier_class = 'moderate'
        else:
            tier = 'FRONTIER'
            tier_class = 'frontier'

        drivers = IndicatorService.evaluate_yield_gap_drivers(r)
        primary_constraint = next(
            (d['constraint'] for d in drivers if d['status'] == 'EVIDENCED_CONSTRAINT'),
            'Insufficient evidence to identify the driver'
        )

        d_record = {
            **r,
            'reference_yield_tha': b_yield_tha,
            'absolute_gap_tha': abs_gap,
            'relative_gap_percentage': rel_gap,
            'opportunity_tonnes': opp_tonnes,
            'priority_tier': tier,
            'priority_class': tier_class,
            'primary_constraint': primary_constraint,
            'drivers': drivers,
        }
        enriched_rankings.append(d_record)
        if tier in ('CRITICAL', 'HIGH', 'MODERATE'):
            prioritized_locations.append(d_record)

    prioritized_locations.sort(key=lambda x: (x['relative_gap_percentage'], x['opportunity_tonnes']), reverse=True)

    # Multi-year YoY comparison
    yoy = IndicatorService.get_year_over_year_comparison(
        crop_name=crop_filter, season_code=season_code, source_policy=source_policy
    )

    # Crop Comparison Chart Data (top 6 priority crops)
    top_crops_list = ['Maize', 'Beans', 'Irish Potato', 'Rice', 'Wheat', 'Cassava']
    crop_comparison = []
    for c_name in top_crops_list:
        c_nat = IndicatorService.get_national_summary(season_code=season_code, year=year, crop_name=c_name, source_policy=source_policy)
        c_ranks = IndicatorService.get_district_rankings(crop_name=c_name, year=year, season_code=season_code, source_policy=source_policy)
        obs_t = round(c_nat.get('weighted_yield_kg_per_ha', 0.0) / 1000.0, 2)
        bench_t = c_ranks[0].get('yield_tha', 0.0) if c_ranks else {
            'Maize': 4.0, 'Beans': 2.0, 'Irish Potato': 25.0, 'Rice': 6.0, 'Wheat': 3.5, 'Cassava': 18.0
        }.get(c_name, 3.0)
        gap_t = max(0.0, round(bench_t - obs_t, 2))
        gap_pct = round((gap_t / bench_t) * 100.0, 1) if bench_t > 0 else 0.0
        crop_comparison.append({
            'crop': c_name,
            'observed_tha': obs_t,
            'benchmark_tha': bench_t,
            'gap_tha': gap_t,
            'gap_pct': gap_pct,
        })

    # Seasonal Trend Chart Data
    seasonal_trends = []
    trend_points = [
        (2024, 'A', '2024A'),
        (2024, 'B', '2024B'),
        (2025, 'A', '2025A'),
        (2025, 'B', '2025B'),
    ]
    for ty, ts, tlabel in trend_points:
        t_gap = IndicatorService.get_productivity_gap(crop_name=crop_filter, year=ty, season_code=ts, source_policy=source_policy)
        seasonal_trends.append({
            'label': tlabel,
            'year': ty,
            'season': ts,
            'observed_tha': t_gap.get('observed_yield_tha', 0.0),
            'benchmark_tha': t_gap.get('reference_yield_tha', 0.0),
            'gap_tha': t_gap.get('absolute_gap_tha', 0.0),
            'gap_pct': abs(t_gap.get('gap_percentage', 0.0)),
        })

    all_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    if not all_crops.exists():
        all_crops = Crop.objects.all()[:15]

    context = {
        'page_title': 'Yield Gap Intelligence & Agricultural Productivity Analytics',
        'is_public_page': False,
        'selected_year': year,
        'selected_season': season_code,
        'selected_crop': crop_filter,
        'selected_source': source_policy,
        'selected_province': selected_province,
        'selected_district': selected_district,
        'selected_sector': selected_sector,
        'benchmark_type': benchmark_type,
        'provinces': provinces,
        'districts': districts,
        'sectors': sectors,
        'summary': summary,
        'rankings': enriched_rankings[:10],
        'all_rankings': enriched_rankings,
        'all_30_rankings': all_30_rankings,
        'prioritized_locations': prioritized_locations,
        'gap': gap,
        'yoy': yoy,
        'crop_comparison': crop_comparison,
        'seasonal_trends': seasonal_trends,
        'priority_crops': all_crops,
    }
    return render(request, 'indicators/productivity_intelligence.html', context)


@cache_page(60 * 30)
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


@cache_page(60 * 30)
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


@cache_page(60 * 30)
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

