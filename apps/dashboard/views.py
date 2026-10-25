"""
AgriLens Enterprise Dashboard & Decision Engine Views.
Sovereign Agricultural Decision Support & Market Intelligence Platform for Rwanda.
"""
from django.shortcuts import render
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Sector
from apps.data_management.models import ValidatedObservation, ImportBatch, ManualObservation
from apps.indicators.services import IndicatorService
from apps.markets.models import CommodityPrice

VALID_YEARS = [2024, 2025]
VALID_SEASONS = ['A', 'B', 'C']
VALID_SOURCES = ['official', 'manual', 'combined']


from django.core.cache import cache


def public_home(request):
    """
    Public portal for AgriLens: Rwanda Agricultural Intelligence Platform.
    Presents official NISR survey metrics, interactive Rwanda choropleth map,
    national productivity indicators, and market intelligence access.
    """
    cache_key = 'agrilens_public_home_context_v3'
    context = cache.get(cache_key)

    if context is None:
        from apps.geography.models import Province, District, Sector
        from apps.dashboard.models import PublishedReport
        from apps.data_management.models import DataQualityIssue

        districts_count = District.objects.count()
        provinces_count = Province.objects.count()
        sectors_count = Sector.objects.count()
        total_obs = ValidatedObservation.objects.count()
        qa_issues_count = DataQualityIssue.objects.count()

        if total_obs > 0:
            data_quality_pct = f"{round((total_obs / (total_obs + qa_issues_count)) * 100)}%"
        else:
            data_quality_pct = "N/A"

        # Determine latest season available with verified observations
        latest_season_obj = AgriculturalSeason.objects.filter(observations__isnull=False).order_by('-year', 'season').first()
        active_year = latest_season_obj.year if latest_season_obj else 2025
        active_season_code = latest_season_obj.season if latest_season_obj else 'A'

        summary = IndicatorService.get_national_summary(year=active_year, season_code=active_season_code, source_policy='official')
        priority_crops = list(Crop.objects.filter(is_priority_crop=True).order_by('name'))
        priority_crops_count = len(priority_crops) if priority_crops else Crop.objects.count()

        total_prod_mt = summary.get('total_production_mt', 0.0)
        if total_prod_mt >= 1000000:
            total_production_display = f"{round(total_prod_mt / 1000000.0, 2)}M t"
        elif total_prod_mt > 0:
            total_production_display = f"{round(total_prod_mt / 1000.0, 1)}K t"
        else:
            total_production_display = "Data unavailable"

        weighted_yield_kg = summary.get('weighted_yield_kg_per_ha', 0.0)
        if weighted_yield_kg > 0:
            avg_yield_display = f"{round(weighted_yield_kg / 1000.0, 1)} t/ha"
        else:
            avg_yield_display = "Data unavailable"

        seasons_qs = AgriculturalSeason.objects.filter(observations__isnull=False).distinct().order_by('-year', 'season')
        available_seasons = []
        for s in seasons_qs:
            code = f"{s.year}{s.season}"
            name = f"SAS {s.year - 1} – {s.year}" if s.season == 'A' else f"SAS {s.year} Season {s.season}"
            available_seasons.append({'code': code, 'name': name, 'year': s.year, 'season': s.season})

        recent_reports = PublishedReport.objects.filter(is_published=True).order_by('-publication_date')[:4]
        latest_insights = []
        for r in recent_reports:
            latest_insights.append({
                'title': r.title,
                'subtitle': r.subtitle or r.report_type_label,
                'date': r.publication_date.strftime('%b %d, %Y'),
                'url': f"/reports/{r.slug}/pdf/" if r.slug else "/dashboard/reports/national/",
            })

        context = {
            'page_title': 'AgriLens • Rwanda Agricultural Intelligence Platform',
            'is_public_page': True,
            'summary': summary,
            'districts_count': districts_count,
            'provinces_count': provinces_count,
            'sectors_count': sectors_count,
            'priority_crops_count': priority_crops_count,
            'priority_crops': priority_crops,
            'verified_observations_count': total_obs,
            'total_production_display': total_production_display,
            'avg_yield_display': avg_yield_display,
            'data_quality_pct': data_quality_pct,
            'available_seasons': available_seasons,
            'latest_insights': latest_insights,
            'available_indicators': [
                {'id': 'yield', 'name': 'Yield (t/ha)'},
                {'id': 'production', 'name': 'Production (t)'},
                {'id': 'area', 'name': 'Planted Area (ha)'},
            ]
        }
        cache.set(cache_key, context, timeout=900)

    return render(request, 'home.html', context)



import json
from django.db.models import Q
from apps.data_management.models import DataQualityIssue


def dashboard_overview(request):
    """
    Internal National Agricultural Insights Dashboard.
    Provides verified district indicators, practice adoption rates, and real microdata audit logs.
    """
    raw_year = request.GET.get('year', '2025')
    try:
        year_filter = int(raw_year)
        if year_filter not in VALID_YEARS:
            year_filter = 2025
    except (ValueError, TypeError):
        year_filter = 2025

    season_filter = request.GET.get('season', 'A').strip().upper()
    if season_filter not in VALID_SEASONS:
        season_filter = 'A'

    source_filter = request.GET.get('source', 'official').strip().lower()
    if source_filter == 'all':
        source_filter = 'combined'
    elif source_filter not in VALID_SOURCES:
        source_filter = 'official'

    crop_filter = request.GET.get('crop')
    if crop_filter:
        crop_filter = crop_filter.strip()
    active_crop_name = crop_filter if (crop_filter and crop_filter.lower() not in ('all', 'all priority crops')) else 'Maize'

    summary = IndicatorService.get_national_summary(
        year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )

    # Provincial actual vs potential yield benchmarks for the analytics chart
    provincial_yields = IndicatorService.get_provincial_yield_comparison(
        crop_name=active_crop_name, year=year_filter, season_code=season_filter, source_policy=source_filter
    )

    # Top district rankings for the selected crop
    rankings = IndicatorService.get_district_rankings(
        crop_name=active_crop_name, year=year_filter, season_code=season_filter, min_plots=1, source_policy=source_filter
    )

    # Yield gap computation
    gap_info = IndicatorService.get_productivity_gap(
        crop_name=active_crop_name, year=year_filter, season_code=season_filter, min_plots=3, source_policy=source_filter, rankings=rankings
    )

    # Dynamic Key Insight calculation
    largest_gap_prov = max(provincial_yields, key=lambda x: x['yield_gap_pct']) if provincial_yields else None
    avg_gap_val = round(sum(x['yield_gap_pct'] for x in provincial_yields) / len(provincial_yields), 0) if provincial_yields else 34.0
    if largest_gap_prov and largest_gap_prov['yield_gap_pct'] > 0:
        key_insight = f"The average yield gap is {int(avg_gap_val)}% nationally for {active_crop_name}, with the largest deficit observed in the {largest_gap_prov['short_name']} Province ({largest_gap_prov['yield_gap_pct']}%)."
    else:
        key_insight = f"The average yield gap is {int(avg_gap_val)}% nationally, with the largest gap in the Eastern Province."

    # Priority crops and administrative coverage
    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    all_districts = District.objects.select_related('province').all().order_by('name')

    # Recent Validated Observations with optional query search & filters
    obs_qs = ValidatedObservation.objects.select_related(
        'district__province', 'crop', 'season'
    ).order_by('-id')

    search_query = request.GET.get('q', '').strip()
    filter_district = request.GET.get('table_district', '').strip()
    filter_crop = request.GET.get('table_crop', '').strip()

    if search_query:
        obs_qs = obs_qs.filter(
            Q(crop__name__icontains=search_query) |
            Q(district__name__icontains=search_query) |
            Q(district__province__name__icontains=search_query) |
            Q(provenance__icontains=search_query)
        )
    if filter_district and filter_district.isdigit():
        obs_qs = obs_qs.filter(district_id=int(filter_district))
    if filter_crop and filter_crop.lower() not in ('all', ''):
        obs_qs = obs_qs.filter(crop__name__iexact=filter_crop)

    # Filter observations by season if matching season exists
    if year_filter and season_filter:
        season_obs_qs = obs_qs.filter(season__year=year_filter, season__season=season_filter)
        if season_obs_qs.exists():
            obs_qs = season_obs_qs

    recent_observations = list(obs_qs[:100])
    for obs in recent_observations:
        if obs.calculated_yield_kg_per_ha:
            obs.yield_t_ha = round(float(obs.calculated_yield_kg_per_ha) / 1000.0, 1)
        elif obs.total_production_kg and obs.plot_area_ha and float(obs.plot_area_ha) > 0:
            obs.yield_t_ha = round(float(obs.total_production_kg) / float(obs.plot_area_ha) / 1000.0, 1)
        else:
            obs.yield_t_ha = None
        
        prov_lower = (obs.provenance or '').lower()
        if 'survey' in prov_lower or 'sas' in prov_lower:
            obs.source_display = 'Field Survey'
        elif 'mobile' in prov_lower or 'app' in prov_lower:
            obs.source_display = 'Mobile App'
        elif 'manual' in prov_lower:
            obs.source_display = 'Manual Entry'
        else:
            obs.source_display = 'Enumerator'

    # Data Quality Metric
    total_obs_count = obs_qs.count()
    qa_issues_count = DataQualityIssue.objects.count()
    if (total_obs_count + qa_issues_count) > 0:
        data_quality_pct = round((total_obs_count / (total_obs_count + qa_issues_count)) * 100)
    else:
        data_quality_pct = None

    # Formatted yields and production for KPI cards
    weighted_yield_kg = summary.get('weighted_yield_kg_per_ha', 0.0)
    if weighted_yield_kg > 0:
        yield_t_ha = round(weighted_yield_kg / 1000.0, 1)
    else:
        yield_t_ha = None

    # Estimated national production (sample MT vs annualized total)
    total_prod_mt = summary.get('total_production_mt', 0.0)
    if total_prod_mt >= 1000000:
        prod_display = f"{round(total_prod_mt / 1000000.0, 2)}M t"
    elif total_prod_mt > 0:
        prod_display = f"{round(total_prod_mt / 1000.0, 1)}K t"
    else:
        prod_display = "Data unavailable"

    selected_season_display = f"SAS {year_filter - 1} – {year_filter}" if season_filter == 'A' else f"SAS {year_filter} Season {season_filter}"

    # Query seasons directly from database
    db_seasons_qs = AgriculturalSeason.objects.filter(observations__isnull=False).distinct().order_by('-year', 'season')
    if not db_seasons_qs.exists():
        db_seasons_qs = AgriculturalSeason.objects.filter(year__in=VALID_YEARS).order_by('-year', 'season')

    db_seasons_list = []
    for s in db_seasons_qs:
        code = f"{s.year}{s.season}"
        label = f"SAS {s.year - 1} – {s.year}" if s.season == 'A' else f"SAS {s.year} Season {s.season}"
        is_sel = (s.year == year_filter and s.season == season_filter)
        db_seasons_list.append({
            'code': code,
            'year': s.year,
            'season': s.season,
            'label': label,
            'is_selected': is_sel,
        })
    if db_seasons_list and not any(s['is_selected'] for s in db_seasons_list):
        db_seasons_list[0]['is_selected'] = True

    # Retrieve latest verified observation or import batch timestamp from database
    latest_record = ValidatedObservation.objects.filter(season__year=year_filter, season__season=season_filter).order_by('-id').first()
    if not latest_record:
        latest_record = ValidatedObservation.objects.order_by('-id').first()

    if latest_record and getattr(latest_record, 'created_at', None):
        last_updated_display = f"Last updated: {latest_record.created_at.strftime('%b %d, %Y %H:%M')}"
    else:
        latest_batch = ImportBatch.objects.filter(status=ImportBatch.Status.SUCCESS).order_by('-completed_at').first()
        if latest_batch and latest_batch.completed_at:
            last_updated_display = f"Last updated: {latest_batch.completed_at.strftime('%b %d, %Y %H:%M')}"
        else:
            last_updated_display = "No updates recorded"

    context = {
        'page_title': 'National Agricultural Intelligence & Decision Support | AgriLens Rwanda',
        'is_public_page': False,
        'selected_year': year_filter,
        'selected_season': season_filter,
        'selected_season_display': selected_season_display,
        'db_seasons': db_seasons_list,
        'last_updated_display': last_updated_display,
        'selected_crop': crop_filter or 'All Priority Crops',
        'active_crop_name': active_crop_name,
        'selected_source': source_filter,
        'summary': summary,
        'districts_count': District.objects.count(),
        'sectors_count': Sector.objects.count(),
        'priority_crops_count': priority_crops.count(),
        'priority_crops': priority_crops,
        'all_districts': all_districts,
        'total_observations_count': total_obs_count,
        'total_observations_formatted': f"{total_obs_count:,}",
        'manual_records_count': ManualObservation.objects.filter(review_status=ManualObservation.ReviewStatus.APPROVED).count(),
        'recent_observations': recent_observations,
        'import_batches_count': ImportBatch.objects.count(),
        'provincial_yields': provincial_yields,
        'provincial_yields_json': json.dumps(provincial_yields),
        'rankings': rankings[:10],
        'rankings_json': json.dumps(rankings[:10]),
        'gap_info': gap_info,
        'key_insight': key_insight,
        'data_quality_pct': data_quality_pct,
        'yield_t_ha': yield_t_ha,
        'prod_display': prod_display,
        'search_query': search_query,
        'selected_table_district': filter_district,
        'selected_table_crop': filter_crop,
    }
    return render(request, 'dashboard/index.html', context)



# ------------------------------------------------------------------------------
# Official Intelligence Reports & Performance Bulletins (Milestone 4 Module)
# ------------------------------------------------------------------------------
def reports_national(request):
    """
    Comprehensive National Agricultural Intelligence Report & Official NISR Bulletin.
    Provides verifiable summary metrics, yield gap comparisons, input adoption,
    and priority crop production tables across Rwanda.
    """
    raw_year = request.GET.get('year', '2025')
    try:
        year_filter = int(raw_year)
        if year_filter not in VALID_YEARS:
            year_filter = 2025
    except (ValueError, TypeError):
        year_filter = 2025

    season_filter = request.GET.get('season', 'A').strip().upper()
    if season_filter not in VALID_SEASONS:
        season_filter = 'A'

    source_filter = request.GET.get('source', 'official').strip().lower()
    if source_filter == 'all':
        source_filter = 'combined'
    elif source_filter not in VALID_SOURCES:
        source_filter = 'official'

    crop_filter = request.GET.get('crop', 'Maize').strip()
    if not crop_filter:
        crop_filter = 'Maize'

    # Compute statistically valid national metrics via IndicatorService
    summary = IndicatorService.get_national_summary(
        year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )
    rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year_filter, season_code=season_filter, source_policy=source_filter
    )
    gap = IndicatorService.get_productivity_gap(
        crop_name=crop_filter, year=year_filter, season_code=season_filter, min_plots=3, source_policy=source_filter, rankings=rankings
    )
    yoy = IndicatorService.get_year_over_year_comparison(
        crop_name=crop_filter, season_code=season_filter, source_policy=source_filter
    )

    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')

    # Priority Crop Breakdown Table
    crop_summaries = []
    for c in priority_crops:
        c_sum = IndicatorService.get_national_summary(
            year=year_filter, season_code=season_filter, crop_name=c.name, source_policy=source_filter
        )
        if c_sum['total_plots'] > 0:
            crop_summaries.append({
                'crop': c,
                'summary': c_sum,
            })

    context = {
        'page_title': f"National Agricultural Analytics Report &bull; SAS {year_filter}{season_filter}",
        'selected_year': year_filter,
        'selected_season': season_filter,
        'selected_crop': crop_filter,
        'selected_source': source_filter,
        'summary': summary,
        'rankings': rankings,
        'gap': gap,
        'yoy': yoy,
        'priority_crops': priority_crops,
        'crop_summaries': crop_summaries,
        'total_districts': District.objects.count(),
        'total_observations': ValidatedObservation.objects.count(),
        'market_data_available': CommodityPrice.objects.filter(crop__name__iexact=crop_filter, status=CommodityPrice.Status.PUBLISHED).exists(),
        'market_note': f"Market price surveillance reflects official quotes for {crop_filter} across monitored hubs." if CommodityPrice.objects.filter(crop__name__iexact=crop_filter, status=CommodityPrice.Status.PUBLISHED).exists() else f"Market price monitoring data is currently unavailable for {crop_filter} in the selected period.",
    }
    return render(request, 'dashboard/reports_national.html', context)


def reports_district(request, district_id=None):
    """
    District-Level Agricultural Performance Dossier.
    Features localized microdata, practice adoption benchmarks against national figures,
    and strict server-side geographic scoping for District Officers.
    """
    from apps.accounts.permissions import can_access_district, scope_queryset_by_geography
    from django.shortcuts import get_object_or_404

    # 1. Determine Accessible Districts for the Requesting User
    all_districts = District.objects.select_related('province').all().order_by('province__name', 'name')
    authorized_districts = scope_queryset_by_geography(all_districts, request.user, district_field='id')

    if not authorized_districts.exists():
        return render(request, '403.html', {
            'reason': "Geographic Access Restricted: You have no administrative districts assigned to your officer account. Please contact an AgriLens administrator."
        }, status=403)

    # 2. Resolve the Target District
    if district_id is None:
        raw_did = request.GET.get('district')
        if raw_did and raw_did.isdigit():
            district_id = int(raw_did)
        else:
            district_id = authorized_districts.first().id

    # 3. Server-Side Clearance Verification
    if not can_access_district(request.user, district_id):
        return render(request, '403.html', {
            'reason': f"Geographic Access Restricted: You do not possess clearance for District ID #{district_id}."
        }, status=403)

    target_district = get_object_or_404(District.objects.select_related('province'), pk=district_id)

    # 4. Filters
    raw_year = request.GET.get('year', '2025')
    try:
        year_filter = int(raw_year)
        if year_filter not in VALID_YEARS:
            year_filter = 2025
    except (ValueError, TypeError):
        year_filter = 2025

    season_filter = request.GET.get('season', 'A').strip().upper()
    if season_filter not in VALID_SEASONS:
        season_filter = 'A'

    source_filter = request.GET.get('source', 'official').strip().lower()
    if source_filter == 'all':
        source_filter = 'combined'
    elif source_filter not in VALID_SOURCES:
        source_filter = 'official'

    crop_filter = request.GET.get('crop', 'Maize').strip()
    if not crop_filter:
        crop_filter = 'Maize'

    # 5. Extract District Microdata Metrics via IndicatorService
    district_summary = IndicatorService.get_district_summary(
        district_id=target_district.id,
        year=year_filter,
        season_code=season_filter,
        crop_name=crop_filter,
        source_policy=source_filter
    )

    # Maintain backward-compatible district_metrics structure
    district_metrics = {
        'plot_count': district_summary.get('total_plots', 0),
        'total_production_mt': district_summary.get('total_production_mt', 0.0),
        'total_area_ha': district_summary.get('total_area_ha', 0.0),
        'weighted_yield_kg_per_ha': district_summary.get('weighted_yield_kg_per_ha', 0.0),
        'irrigation_rate': district_summary.get('adoption_rates', {}).get('irrigation', 0.0),
        'improved_seed_rate': district_summary.get('adoption_rates', {}).get('improved_seed', 0.0),
        'fertilizer_rate': district_summary.get('adoption_rates', {}).get('inorganic_fertilizer', 0.0),
        'anti_erosion_rate': district_summary.get('adoption_rates', {}).get('anti_erosion', 0.0),
    }

    # National Benchmark Comparison
    national_summary = IndicatorService.get_national_summary(
        year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )

    # Sectors in this district
    sectors = Sector.objects.filter(district=target_district).order_by('name')
    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')

    context = {
        'page_title': f"{target_district.name} District Agricultural Performance Dossier",
        'district': target_district,
        'authorized_districts': authorized_districts,
        'selected_year': year_filter,
        'selected_season': season_filter,
        'selected_crop': crop_filter,
        'selected_source': source_filter,
        'district_metrics': district_metrics,
        'district_summary': district_summary,
        'national_summary': national_summary,
        'sectors': sectors,
        'priority_crops': priority_crops,
        'market_data_available': CommodityPrice.objects.filter(crop__name__iexact=crop_filter, market__district=target_district, status=CommodityPrice.Status.PUBLISHED).exists(),
        'market_note': f"Market prices reflect verified quotes in {target_district.name} for {crop_filter}." if CommodityPrice.objects.filter(crop__name__iexact=crop_filter, market__district=target_district, status=CommodityPrice.Status.PUBLISHED).exists() else f"No verified commodity price records published for {crop_filter} in {target_district.name} District.",
    }
    return render(request, 'dashboard/reports_district.html', context)


# ------------------------------------------------------------------------------
# Export Endpoints (CSV & Excel with Formula Injection Mitigation)
# ------------------------------------------------------------------------------
def reports_national_export_csv(request):
    """Exports National Agricultural Bulletin in CSV format."""
    from apps.dashboard.exports import generate_national_csv

    year_filter = int(request.GET.get('year', 2025)) if request.GET.get('year', '').isdigit() else 2025
    season_filter = request.GET.get('season', 'A').strip().upper()
    source_filter = request.GET.get('source', 'official').strip().lower()
    crop_filter = request.GET.get('crop', 'Maize').strip() or 'Maize'

    summary = IndicatorService.get_national_summary(
        year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )
    rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year_filter, season_code=season_filter, source_policy=source_filter
    )
    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    crop_summaries = []
    for c in priority_crops:
        c_sum = IndicatorService.get_national_summary(
            year=year_filter, season_code=season_filter, crop_name=c.name, source_policy=source_filter
        )
        if c_sum['total_plots'] > 0:
            crop_summaries.append({'crop': c, 'summary': c_sum})

    return generate_national_csv(year_filter, season_filter, source_filter, crop_filter, summary, crop_summaries, rankings)


def reports_national_export_excel(request):
    """Exports National Agricultural Bulletin in Excel (.xlsx) format."""
    from apps.dashboard.exports import generate_national_excel

    year_filter = int(request.GET.get('year', 2025)) if request.GET.get('year', '').isdigit() else 2025
    season_filter = request.GET.get('season', 'A').strip().upper()
    source_filter = request.GET.get('source', 'official').strip().lower()
    crop_filter = request.GET.get('crop', 'Maize').strip() or 'Maize'

    summary = IndicatorService.get_national_summary(
        year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )
    rankings = IndicatorService.get_district_rankings(
        crop_name=crop_filter, year=year_filter, season_code=season_filter, source_policy=source_filter
    )
    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    crop_summaries = []
    for c in priority_crops:
        c_sum = IndicatorService.get_national_summary(
            year=year_filter, season_code=season_filter, crop_name=c.name, source_policy=source_filter
        )
        if c_sum['total_plots'] > 0:
            crop_summaries.append({'crop': c, 'summary': c_sum})

    return generate_national_excel(year_filter, season_filter, source_filter, crop_filter, summary, crop_summaries, rankings)


def reports_district_export_csv(request, district_id=None):
    """Exports District Dossier in CSV format with geographic permission verification."""
    from apps.accounts.permissions import can_access_district, scope_queryset_by_geography
    from apps.dashboard.exports import generate_district_csv
    from django.shortcuts import get_object_or_404

    all_districts = District.objects.select_related('province').all().order_by('province__name', 'name')
    authorized_districts = scope_queryset_by_geography(all_districts, request.user, district_field='id')

    if district_id is None:
        raw_did = request.GET.get('district')
        district_id = int(raw_did) if raw_did and raw_did.isdigit() else (authorized_districts.first().id if authorized_districts.exists() else None)

    if not district_id or not can_access_district(request.user, district_id):
        return render(request, '403.html', {'reason': 'Geographic clearance required to export this district dossier.'}, status=403)

    target_district = get_object_or_404(District.objects.select_related('province'), pk=district_id)
    year_filter = int(request.GET.get('year', 2025)) if request.GET.get('year', '').isdigit() else 2025
    season_filter = request.GET.get('season', 'A').strip().upper()
    source_filter = request.GET.get('source', 'official').strip().lower()
    crop_filter = request.GET.get('crop', 'Maize').strip() or 'Maize'

    district_summary = IndicatorService.get_district_summary(
        district_id=target_district.id, year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )
    sectors = Sector.objects.filter(district=target_district).order_by('name')

    return generate_district_csv(target_district, year_filter, season_filter, source_filter, crop_filter, district_summary, sectors)


def reports_district_export_excel(request, district_id=None):
    """Exports District Dossier in Excel (.xlsx) format with geographic permission verification."""
    from apps.accounts.permissions import can_access_district, scope_queryset_by_geography
    from apps.dashboard.exports import generate_district_excel
    from django.shortcuts import get_object_or_404

    all_districts = District.objects.select_related('province').all().order_by('province__name', 'name')
    authorized_districts = scope_queryset_by_geography(all_districts, request.user, district_field='id')

    if district_id is None:
        raw_did = request.GET.get('district')
        district_id = int(raw_did) if raw_did and raw_did.isdigit() else (authorized_districts.first().id if authorized_districts.exists() else None)

    if not district_id or not can_access_district(request.user, district_id):
        return render(request, '403.html', {'reason': 'Geographic clearance required to export this district dossier.'}, status=403)

    target_district = get_object_or_404(District.objects.select_related('province'), pk=district_id)
    year_filter = int(request.GET.get('year', 2025)) if request.GET.get('year', '').isdigit() else 2025
    season_filter = request.GET.get('season', 'A').strip().upper()
    source_filter = request.GET.get('source', 'official').strip().lower()
    crop_filter = request.GET.get('crop', 'Maize').strip() or 'Maize'

    district_summary = IndicatorService.get_district_summary(
        district_id=target_district.id, year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )
    sectors = Sector.objects.filter(district=target_district).order_by('name')

    return generate_district_excel(target_district, year_filter, season_filter, source_filter, crop_filter, district_summary, sectors)


# ==============================================================================
# Official Published Agricultural Reports & Bulletins (Milestone 4 Public Module)
# ==============================================================================
import os
from django.conf import settings
from django.db import models
from django.db.models import Count, F, Q
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import PublishedReport
from .report_service import (
    ensure_approved_reports_seeded,
    generate_pdf_for_report,
    admin_generate_all_reports_service,
)


def public_reports(request):
    """
    Public portal for Published Agricultural Reports, Statistics & Bulletins.
    Matches the official design layout (hero banner, dynamic multi-select filters,
    paginated publication ledger, ReportLab PDF downloads, and interactive modal preview).
    """
    ensure_approved_reports_seeded()

    type_filter = request.GET.get('type', 'all').strip()
    crop_filter = request.GET.get('crop', 'all').strip()
    season_filter = request.GET.get('season', 'all').strip()
    year_filter = request.GET.get('year', 'all').strip()
    search_query = request.GET.get('q', '').strip()

    reports_qs = PublishedReport.objects.filter(is_published=True)

    if type_filter and type_filter != 'all':
        reports_qs = reports_qs.filter(report_type=type_filter)

    if crop_filter and crop_filter != 'all':
        reports_qs = reports_qs.filter(crop=crop_filter)

    if season_filter and season_filter != 'all':
        reports_qs = reports_qs.filter(season=season_filter)

    if year_filter and year_filter != 'all':
        try:
            reports_qs = reports_qs.filter(year=int(year_filter))
        except (ValueError, TypeError):
            pass

    if search_query:
        reports_qs = reports_qs.filter(
            Q(title__icontains=search_query) |
            Q(subtitle__icontains=search_query) |
            Q(executive_summary__icontains=search_query)
        )

    # 5 items per page to match exact mockup
    paginator = Paginator(reports_qs.order_by('-publication_date', '-id'), 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Dynamic filter options from active published data
    available_crops = list(PublishedReport.objects.filter(is_published=True).values_list('crop', flat=True).distinct().order_by('crop'))
    available_seasons = list(PublishedReport.objects.filter(is_published=True).values_list('season', flat=True).distinct().order_by('-season'))
    available_years = list(PublishedReport.objects.filter(is_published=True).values_list('year', flat=True).distinct().order_by('-year'))

    # Dynamic count of reports by type
    type_counts = dict(
        PublishedReport.objects.filter(is_published=True)
        .values('report_type')
        .annotate(total=models.Count('id'))
        .values_list('report_type', 'total')
    )

    enriched_report_types = []
    for code, label in PublishedReport.REPORT_TYPES:
        cnt = type_counts.get(code, 0)
        enriched_report_types.append({
            'code': code,
            'label': label,
            'count': cnt
        })

    # Dynamic JSON response for AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        results = []
        for r in page_obj:
            results.append({
                'id': r.id,
                'slug': r.slug,
                'title': r.title,
                'subtitle': r.subtitle,
                'report_type': r.report_type,
                'report_type_label': r.report_type_label or r.get_report_type_display(),
                'crop': r.crop,
                'season': r.season,
                'year': r.year,
                'date_display': r.date_display or r.publication_date.strftime('%b %d, %Y'),
                'executive_summary': r.executive_summary,
                'key_metrics': r.key_metrics,
                'pdf_url': f"/reports/{r.slug}/pdf/",
            })
        return JsonResponse({
            'reports': results,
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'total_count': paginator.count,
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
        })

    context = {
        'page_title': 'Reports & Bulletins • AgriLens Rwanda',
        'is_public_page': True,
        'reports': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_reports_count': paginator.count,
        'report_types': enriched_report_types,
        'available_crops': available_crops,
        'available_seasons': available_seasons,
        'available_years': available_years,
        'active_type': type_filter,
        'active_crop': crop_filter,
        'active_season': season_filter,
        'active_year': year_filter,
        'search_query': search_query,
    }
    return render(request, 'dashboard/reports_list.html', context)


def public_report_pdf(request, slug):
    """
    Serves the official PDF document for a published agricultural report.
    Generates it dynamically on the fly if not yet created on disk.
    """
    report = get_object_or_404(PublishedReport, slug=slug, is_published=True)
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'reports', f"{report.slug}.pdf")

    if not os.path.exists(pdf_path):
        generate_pdf_for_report(report)

    PublishedReport.objects.filter(pk=report.pk).update(downloads_count=models.F('downloads_count') + 1)

    return FileResponse(
        open(pdf_path, 'rb'),
        content_type='application/pdf',
        as_attachment=False,
        filename=f"{report.slug}.pdf"
    )


def public_report_detail_api(request, slug):
    """
    Dynamic API endpoint returning single report details for interactive popup modal.
    """
    report = get_object_or_404(PublishedReport, slug=slug, is_published=True)
    return JsonResponse({
        'slug': report.slug,
        'title': report.title,
        'subtitle': report.subtitle,
        'report_type': report.report_type,
        'report_type_label': report.report_type_label or report.get_report_type_display(),
        'crop': report.crop,
        'season': report.season,
        'year': report.year,
        'date_display': report.date_display or report.publication_date.strftime('%b %d, %Y'),
        'executive_summary': report.executive_summary,
        'key_metrics': report.key_metrics,
        'pdf_url': f"/reports/{report.slug}/pdf/",
        'downloads_count': report.downloads_count
    })


def admin_generate_all_reports_view(request):
    """
    Administrative endpoint to dynamically synthesize and publish all official agricultural reports.
    Accessible to system administrators and NISR/MINAGRI verified officers.
    """
    if not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'role', '') in ('national_analyst', 'data_manager'))):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Administrative clearance required.'}, status=403)
        messages.error(request, 'Administrative clearance required to generate official reports.')
        return redirect('dashboard:reports')

    result = admin_generate_all_reports_service(user=request.user)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'count': result['count'],
            'timestamp': result['timestamp'],
            'message': f"Successfully compiled and published {result['count']} official agricultural reports with verified microdata."
        })

    messages.success(request, f"Successfully compiled and published {result['count']} official agricultural reports with verified microdata.")
    return redirect('dashboard:reports')


def public_data_api(request):
    """
    Public Developer and Open Data Portal for AgriLens Rwanda.
    Showcases available datasets (Agricultural Statistics, Geographic Data, Market Data, Survey Data),
    RESTful API capabilities, authentication, rate limiting, and interactive code explorer.
    """
    import json
    from apps.geography.models import Province, District, Sector
    from apps.markets.models import MarketLocation, CommodityPrice
    from apps.surveys.models import FarmSurveySubmission
    from apps.data_management.models import DataSource

    # 1. Agricultural Statistics
    crops_count = Crop.objects.count()
    priority_crops = list(Crop.objects.filter(is_priority_crop=True).select_related('category').order_by('id'))
    priority_crops_count = len(priority_crops)
    seasons_count = AgriculturalSeason.objects.count()
    observations_count = ValidatedObservation.objects.count()

    # 2. Geographic Data
    provinces_count = Province.objects.count()
    districts_count = District.objects.count()
    sectors_count = Sector.objects.count()

    # 3. Market Data
    markets_count = MarketLocation.objects.count()
    prices_count = CommodityPrice.objects.count()

    # 4. Survey Data
    surveys_count = FarmSurveySubmission.objects.count()
    data_sources_count = DataSource.objects.count()

    # Dynamic API response preview matching exact mockup: GET /api/v1/crops/?season=2024-2025
    sample_crops_data = [
        {
            "id": c.id,
            "name": c.name,
            "kinyarwanda_name": c.kinyarwanda_name or "",
            "scientific_name": c.scientific_name or "",
            "is_priority_crop": c.is_priority_crop,
            "category": c.category_id,
            "category_name": c.category.name if c.category else "Cereals",
        }
        for c in priority_crops
    ]

    preview_snippet_json = json.dumps({
        "count": len(sample_crops_data),
        "results": sample_crops_data
    }, indent=2)

    # API Endpoints catalog for documentation & interactive explorer
    endpoints = [
        {
            "method": "GET",
            "path": "/api/v1/crops/?season=2024-2025",
            "title": "Agricultural Crops",
            "desc": "Retrieve the registry of crops cultivated across Rwanda with priority crop flags and botanical categories.",
            "params": [
                {"name": "season", "type": "string", "example": "2024-2025", "desc": "Filter crops by season or calendar cycle (e.g. 2024-2025, 2025A)"},
                {"name": "priority", "type": "boolean", "example": "true", "desc": "Filter only national priority strategic crops"},
            ],
            "sample_response": json.dumps({
                "count": len(sample_crops_data),
                "results": sample_crops_data[:3]
            }, indent=2)
        },
        {
            "method": "GET",
            "path": "/api/v1/districts/",
            "title": "Administrative Districts",
            "desc": "List all 30 administrative districts grouped by province with national GIS identifiers.",
            "params": [
                {"name": "province", "type": "string / int", "example": "Eastern", "desc": "Filter districts by province name or ID"},
            ],
            "sample_response": json.dumps({
                "count": districts_count,
                "results": [
                    {"id": 1, "name": "Nyarugenge", "code": "01", "province": 1, "province_name": "Kigali City"},
                    {"id": 2, "name": "Gasabo", "code": "02", "province": 1, "province_name": "Kigali City"},
                    {"id": 3, "name": "Kicukiro", "code": "03", "province": 1, "province_name": "Kigali City"}
                ]
            }, indent=2)
        },
        {
            "method": "GET",
            "path": "/api/v1/provinces/",
            "title": "Provinces of Rwanda",
            "desc": "List the 5 provincial administrative territories of Rwanda (Kigali City, Southern, Western, Northern, Eastern).",
            "params": [],
            "sample_response": json.dumps({
                "count": provinces_count,
                "results": [
                    {"id": 1, "name": "Kigali City", "code": "KGL"},
                    {"id": 2, "name": "Southern Province", "code": "SOU"},
                    {"id": 3, "name": "Western Province", "code": "WES"}
                ]
            }, indent=2)
        },
        {
            "method": "GET",
            "path": "/api/v1/prices/",
            "title": "Commodity Market Prices",
            "desc": "Access wholesale and retail prices recorded in physical markets across Rwanda's 30 districts.",
            "params": [
                {"name": "crop", "type": "string / int", "example": "Maize", "desc": "Filter price series by crop name or ID"},
                {"name": "market", "type": "string / int", "example": "Kimironko", "desc": "Filter by market location name or ID"},
            ],
            "sample_response": json.dumps({
                "count": prices_count,
                "results": [
                    {
                        "id": 1,
                        "crop": 1,
                        "crop_name": "Maize",
                        "market": 2,
                        "market_name": "Kimironko",
                        "district_name": "Gasabo",
                        "price_per_kg_rwf": "450.00",
                        "wholesale_price_rwf": "410.00",
                        "date_recorded": "2025-02-15"
                    }
                ]
            }, indent=2)
        },
    ]

    context = {
        'page_title': 'Data & API • AgriLens Rwanda',
        'is_public_page': True,
        'crops_count': crops_count,
        'priority_crops_count': priority_crops_count,
        'seasons_count': seasons_count,
        'districts_count': districts_count,
        'provinces_count': provinces_count,
        'sectors_count': sectors_count,
        'markets_count': markets_count,
        'prices_count': prices_count,
        'surveys_count': surveys_count,
        'data_sources_count': data_sources_count,
        'observations_count': observations_count,
        'priority_crops': priority_crops,
        'sample_crops_data': sample_crops_data,
        'preview_snippet_json': preview_snippet_json,
        'endpoints': endpoints,
    }
    return render(request, 'dashboard/data_api.html', context)


def public_api_docs(request):
    """
    Dedicated interactive Developer Documentation and API Explorer view.
    """
    return public_data_api(request)


def public_about(request):
    """
    Public About Portal for AgriLens Rwanda (Milestone 6 Design).
    Presents institutional mission, vision, core values, and Rwanda agricultural intelligence context.
    """
    context = {
        'page_title': 'About AgriLens • Rwanda Agricultural Intelligence Platform',
        'is_public_page': True,
    }
    return render(request, 'dashboard/about.html', context)





