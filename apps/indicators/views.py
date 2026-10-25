"""
AgriLens Indicators & Productivity Views.
Provides dynamic analytics pages and JSON endpoints powered by PostgreSQL ValidatedObservation microdata.
Strict parameter validation protects against invalid requests and ensures statistical reproducibility.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.db.models import Avg, Sum, Count
import json
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Province, Sector
from apps.data_management.models import ValidatedObservation, ManualObservation, DataQualityIssue
from apps.markets.models import CommodityPrice
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

    # Reference benchmark yield (t/ha) - explicit None if insufficient data
    b_yield_tha = gap.get('reference_yield_tha') if gap.get('is_sufficient_data') else None

    # 4. Enrich every district with gap calculations, opportunity, and drivers
    enriched_rankings = []
    prioritized_locations = []
    for r in scoped_rankings:
        y_tha = r.get('yield_tha')
        area_ha = float(r.get('area_ha') or 0.0) if r.get('area_ha') is not None else None

        if b_yield_tha is not None and b_yield_tha > 0 and y_tha is not None:
            abs_gap = max(0.0, round(b_yield_tha - y_tha, 2))
            rel_gap = round(((b_yield_tha - y_tha) / b_yield_tha) * 100.0, 1)
            opp_tonnes = max(0.0, round(abs_gap * (area_ha or 0.0), 1)) if area_ha is not None else None

            # Priority tier assessment
            if rel_gap >= 40.0 and (area_ha or 0.0) >= 500:
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
        else:
            abs_gap = None
            rel_gap = None
            opp_tonnes = None
            tier = 'UNAVAILABLE'
            tier_class = 'unavailable'

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

    prioritized_locations.sort(
        key=lambda x: (x['relative_gap_percentage'] or 0.0, x['opportunity_tonnes'] or 0.0),
        reverse=True
    )

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
        has_obs = (c_nat.get('total_plots') or 0) > 0 and c_nat.get('weighted_yield_kg_per_ha') is not None
        obs_t = round(c_nat.get('weighted_yield_kg_per_ha') / 1000.0, 2) if has_obs else None
        bench_t = c_ranks[0].get('yield_tha') if (c_ranks and c_ranks[0].get('yield_tha') is not None) else None
        if bench_t is not None and obs_t is not None and bench_t > 0:
            gap_t = max(0.0, round(bench_t - obs_t, 2))
            gap_pct = round((gap_t / bench_t) * 100.0, 1)
        else:
            gap_t = None
            gap_pct = None

        crop_comparison.append({
            'crop': c_name,
            'observed_tha': obs_t,
            'benchmark_tha': bench_t,
            'gap_tha': gap_t,
            'gap_pct': gap_pct,
            'has_data': has_obs and (bench_t is not None),
        })

    # Seasonal Trend Chart Data from actual database seasons with observations
    seasonal_trends = []
    db_seasons = AgriculturalSeason.objects.filter(observations__isnull=False).distinct().order_by('year', 'season')
    trend_points = [(s.year, s.season, f"{s.year}{s.season}") for s in db_seasons]
    for ty, ts, tlabel in trend_points:
        t_gap = IndicatorService.get_productivity_gap(crop_name=crop_filter, year=ty, season_code=ts, source_policy=source_policy)
        is_suff = t_gap.get('is_sufficient_data', False)
        gap_pct_val = abs(t_gap.get('relative_gap_percentage') or t_gap.get('gap_percentage') or 0.0) if is_suff else None
        seasonal_trends.append({
            'label': f"SAS {ty}{ts}",
            'year': ty,
            'season': ts,
            'observed_tha': t_gap.get('observed_yield_tha') if is_suff else None,
            'benchmark_tha': t_gap.get('reference_yield_tha') if is_suff else None,
            'gap_tha': t_gap.get('absolute_gap_tha') if is_suff else None,
            'gap_pct': gap_pct_val,
            'is_sufficient_data': is_suff,
        })

    # Dynamic provincial aggregation from actual rankings
    prov_aggs = {}
    for r in all_30_rankings:
        p_name = r.get('province_name') or 'Other'
        if p_name not in prov_aggs:
            prov_aggs[p_name] = {'prod_t': 0.0, 'area_ha': 0.0, 'yields': []}
        y = r.get('yield_tha')
        a = float(r.get('area_ha') or 0.0)
        p = float(r.get('production_tonnes') or 0.0)
        if y is not None and y > 0:
            prov_aggs[p_name]['yields'].append(y)
            prov_aggs[p_name]['prod_t'] += p
            prov_aggs[p_name]['area_ha'] += a

    known_provinces = ['Northern', 'Eastern', 'Southern', 'Western', 'Kigali']
    prov_labels = []
    prov_actual = []
    prov_potential = []
    for p in known_provinces:
        matched_key = next((k for k in prov_aggs if p.lower() in k.lower() or k.lower() in p.lower()), None)
        if matched_key and prov_aggs[matched_key]['area_ha'] > 0:
            act_y = round(prov_aggs[matched_key]['prod_t'] / prov_aggs[matched_key]['area_ha'], 2)
            pot_y = max(prov_aggs[matched_key]['yields']) if prov_aggs[matched_key]['yields'] else (b_yield_tha or act_y)
        elif matched_key and prov_aggs[matched_key]['yields']:
            act_y = round(sum(prov_aggs[matched_key]['yields']) / len(prov_aggs[matched_key]['yields']), 2)
            pot_y = max(prov_aggs[matched_key]['yields'])
        else:
            act_y = None
            pot_y = None
        prov_labels.append(p)
        prov_actual.append(act_y)
        prov_potential.append(pot_y)

    provincial_chart_data = {
        'labels': prov_labels,
        'actual': prov_actual,
        'potential': prov_potential,
        'has_data': any(a is not None for a in prov_actual)
    }

    # Dynamic commodity market price time-series
    c_prices = CommodityPrice.objects.filter(status=CommodityPrice.Status.PUBLISHED)
    if crop_filter and crop_filter.lower() not in ('all', 'all priority crops'):
        c_prices = c_prices.filter(crop__name__iexact=crop_filter)

    market_dates = list(c_prices.dates('date_recorded', 'month', order='ASC'))[-6:]
    market_labels = [d.strftime('%b %Y') for d in market_dates]
    top_markets = list(c_prices.values('market__name').annotate(cnt=Count('id')).order_by('-cnt')[:2])
    market_datasets = []
    palette = ['#10B981', '#2563EB']
    for idx, tm in enumerate(top_markets):
        m_name = tm['market__name']
        m_data = []
        for dt in market_dates:
            avg_p = c_prices.filter(market__name=m_name, date_recorded__year=dt.year, date_recorded__month=dt.month).aggregate(avg=Avg('price_per_kg_rwf'))['avg']
            m_data.append(round(float(avg_p), 1) if avg_p is not None else None)
        market_datasets.append({
            'label': m_name,
            'data': m_data,
            'borderColor': palette[idx % len(palette)],
            'pointBackgroundColor': palette[idx % len(palette)],
        })

    market_price_chart_data = {
        'labels': market_labels,
        'datasets': market_datasets,
        'has_data': len(market_datasets) > 0 and len(market_labels) > 0
    }

    # Dynamic post-harvest loss causes from database
    loss_causes_qs = ManualObservation.objects.filter(
        loss_quantity_kg__gt=0,
        primary_loss_cause__isnull=False
    ).exclude(
        primary_loss_cause=''
    ).values('primary_loss_cause').annotate(
        total_loss=Sum('loss_quantity_kg')
    ).order_by('-total_loss')

    total_loss_all = sum(float(l['total_loss'] or 0.0) for l in loss_causes_qs)
    postharvest_labels = []
    postharvest_pcts = []
    postharvest_breakdown = []
    loss_colors = ['#059669', '#2563EB', '#F59E0B', '#0284C7', '#8B5CF6', '#EC4899', '#64748B']
    if total_loss_all > 0:
        for idx, row in enumerate(loss_causes_qs):
            cause_code = row['primary_loss_cause']
            cause_label = dict(ManualObservation.LossCause.choices).get(cause_code, cause_code)
            pct = round((float(row['total_loss']) / total_loss_all) * 100.0, 1)
            color = loss_colors[idx % len(loss_colors)]
            postharvest_labels.append(cause_label)
            postharvest_pcts.append(pct)
            postharvest_breakdown.append({'label': cause_label, 'pct': pct, 'color': color})

    postharvest_chart_data = {
        'labels': postharvest_labels,
        'data': postharvest_pcts,
        'breakdown': postharvest_breakdown,
        'has_data': len(postharvest_pcts) > 0
    }

    all_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    if not all_crops.exists():
        all_crops = Crop.objects.all()[:15]

    # Data Quality percentage from validated records and issues
    total_valid = ValidatedObservation.objects.count()
    qa_issues_count = DataQualityIssue.objects.count()
    if total_valid > 0:
        data_quality_pct = round((total_valid / (total_valid + qa_issues_count)) * 100.0, 1)
    else:
        data_quality_pct = None

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
        'seasonal_trends_json': json.dumps(seasonal_trends),
        'provincial_chart_data': provincial_chart_data,
        'provincial_chart_json': json.dumps(provincial_chart_data),
        'market_price_chart_data': market_price_chart_data,
        'market_price_chart_json': json.dumps(market_price_chart_data),
        'postharvest_chart_data': postharvest_chart_data,
        'postharvest_chart_json': json.dumps(postharvest_chart_data),
        'priority_crops': all_crops,
        'data_quality_pct': data_quality_pct,
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

