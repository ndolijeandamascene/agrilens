"""
AgriLens Enterprise Dashboard & Decision Engine Views.
Sovereign Agricultural Decision Support & Market Intelligence Platform for Rwanda.
"""
from django.shortcuts import render
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Sector
from apps.data_management.models import ValidatedObservation, ImportBatch, ManualObservation
from apps.indicators.services import IndicatorService

VALID_YEARS = [2024, 2025]
VALID_SEASONS = ['A', 'B', 'C']
VALID_SOURCES = ['official', 'manual', 'combined']


from django.core.cache import cache


def public_home(request):
    """
    Public-facing commercial enterprise landing page for AgriLens.
    Showcases Sovereign GovTech context, national overview metrics,
    commercial stakeholder solutions, interactive Yield Gap simulator, interactive Rwanda map,
    and official NISR data lineage principles.
    Cached for sub-5ms response times.
    """
    cache_key = 'agrilens_public_home_context_v1'
    context = cache.get(cache_key)

    if context is None:
        summary = IndicatorService.get_national_summary(year=2025, season_code='A', source_policy='official')
        priority_crops = list(Crop.objects.filter(is_priority_crop=True).order_by('name'))

        context = {
            'page_title': 'AgriLens Enterprise • National Agricultural Intelligence & Decision Engine | Rwanda',
            'is_public_page': True,
            'summary': summary,
            'districts_count': 30,
            'sectors_count': 416,
            'priority_crops_count': len(priority_crops),
            'priority_crops': priority_crops,
            'verified_observations_count': ValidatedObservation.objects.count(),
        }
        cache.set(cache_key, context, timeout=900)

    return render(request, 'home.html', context)


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

    summary = IndicatorService.get_national_summary(
        year=year_filter, season_code=season_filter, crop_name=crop_filter, source_policy=source_filter
    )
    recent_observations = ValidatedObservation.objects.select_related(
        'district', 'crop', 'season'
    ).order_by('-id')[:10]

    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')

    context = {
        'page_title': 'National Agricultural Analytics & Indicator Hub',
        'is_public_page': False,
        'selected_year': year_filter,
        'selected_season': season_filter,
        'selected_crop': crop_filter or 'All Priority Crops',
        'selected_source': source_filter,
        'summary': summary,
        'districts_count': District.objects.count(),
        'sectors_count': Sector.objects.count(),
        'priority_crops_count': priority_crops.count(),
        'priority_crops': priority_crops,
        'total_observations_count': ValidatedObservation.objects.count(),
        'manual_records_count': ManualObservation.objects.filter(review_status=ManualObservation.ReviewStatus.APPROVED).count(),
        'recent_observations': recent_observations,
        'import_batches_count': ImportBatch.objects.count(),
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
        'market_data_available': False,
        'market_note': "Market price monitoring data is currently unavailable for the selected period. National and district agricultural intelligence reflects seasonal production survey microdata.",
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
        'market_data_available': False,
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


