"""
AgriLens Official Commodity Markets & Price Surveillance Views.
Monitors weekly wholesale and retail commodity prices across major commercial hubs.
Governs the 5-stage workflow: Collect -> Validate -> Review -> Approve -> Publish.
"""
import csv
import io
import json
from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Max, Min, Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.conf import settings

from apps.markets.models import (
    MarketLocation,
    MarketCommodity,
    CommodityPrice,
    PriceCollectionAssignment,
    PricePublicNotice,
    PriceAuditLog,
)
from apps.agriculture.models import Crop
from apps.geography.models import District, Province
from apps.markets.forms import (
    CommodityPriceForm,
    CommodityPriceCorrectionForm,
    PriceCSVImportForm,
    MarketLocationForm,
    MarketCommodityForm,
    PricePublicNoticeForm,
)


def is_market_staff(user):
    """Checks if the user has staff or market surveillance officer privileges."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return (
        getattr(user, 'is_staff', False) or
        getattr(user, 'is_superuser', False) or
        (hasattr(user, 'groups') and user.groups.filter(name__icontains='officer').exists())
    )


# ==============================================================================
# Cache for Rwanda District SVG Polygons
_RWANDA_DISTRICT_SVGS = None

def get_rwanda_district_svgs():
    """Project Rwanda district GeoJSON into responsive, crisp SVG path coordinates."""
    global _RWANDA_DISTRICT_SVGS
    if _RWANDA_DISTRICT_SVGS is not None:
        return _RWANDA_DISTRICT_SVGS
    import json
    from pathlib import Path
    geojson_path = Path(settings.BASE_DIR) / 'static' / 'data' / 'rwanda_districts.geojson'
    if not geojson_path.exists():
        return []
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []

    min_x, max_x = 28.8618, 30.900
    min_y, max_y = -2.840, -1.047
    width, height = 540, 460
    pad = 18

    def project(lon, lat):
        px = pad + (lon - min_x) / (max_x - min_x) * (width - 2 * pad)
        py = pad + (max_y - lat) / (max_y - min_y) * (height - 2 * pad)
        return round(px, 1), round(py, 1)

    label_map = {
        'Musanze': 'Ruhengeri',
        'Gicumbi': 'Byumba',
        'Karongi': 'Kibuye',
        'Muhanga': 'Gitarama',
        'Nyarugenge': 'Kigali',
        'Kayonza': 'Kayonza',
        'Rusizi': 'Cyangugu',
        'Nyamagabe': 'Gikongoro',
        'Huye': 'Butare',
    }

    result = []
    for feat in data.get('features', []):
        name = feat['properties'].get('shapeName', '')
        geom = feat['geometry']
        poly_list = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
        d_chunks = []
        all_pts = []
        for poly in poly_list:
            for ring in poly:
                pts = [project(p[0], p[1]) for p in ring]
                all_pts.extend(pts)
                if pts:
                    d_chunks.append('M ' + ' L '.join(f'{x},{y}' for x, y in pts) + ' Z')
        cx = round(sum(p[0] for p in all_pts) / len(all_pts), 1) if all_pts else 0
        cy = round(sum(p[1] for p in all_pts) / len(all_pts), 1) if all_pts else 0
        result.append({
            'name': name,
            'label': label_map.get(name, ''),
            'path': ' '.join(d_chunks),
            'cx': cx,
            'cy': cy,
        })
    _RWANDA_DISTRICT_SVGS = result
    return result


# ==============================================================================
# Rwanda 30-District Market Surveillance Intelligence Constants & Dynamic Engine
# ==============================================================================

RWANDA_30_DISTRICTS = [
    'Bugesera', 'Burera', 'Gakenke', 'Gasabo', 'Gatsibo', 'Gicumbi', 'Gisagara', 'Huye',
    'Kamonyi', 'Karongi', 'Kayonza', 'Kicukiro', 'Kirehe', 'Muhanga', 'Musanze', 'Ngoma',
    'Ngororero', 'Nyabihu', 'Nyagatare', 'Nyamagabe', 'Nyamasheke', 'Nyanza', 'Nyarugenge',
    'Nyaruguru', 'Rubavu', 'Ruhango', 'Rulindo', 'Rusizi', 'Rutsiro', 'Rwamagana'
]

def get_crop_surveillance_data(crop, published_prices_qs):
    """
    Computes authentic 30-district market pricing and dynamic choropleth tiers
    for a given commodity strictly from published database records.
    """
    crop_name = crop.name if crop else 'Maize'
    crop_prices = published_prices_qs.filter(crop=crop) if crop else published_prices_qs.none()
    db_avg = crop_prices.aggregate(avg=Avg('price_per_kg_rwf'))['avg']
    national_avg = round(float(db_avg)) if db_avg is not None else None

    # District averages from actual database records
    district_records = crop_prices.values('market__district__name').annotate(avg_price=Avg('price_per_kg_rwf'))
    db_district_map = {
        d['market__district__name']: round(float(d['avg_price']))
        for d in district_records if d['market__district__name']
    }

    # 30-district pricing (None for districts without published quotes)
    district_prices = {}
    for d_name in RWANDA_30_DISTRICTS:
        district_prices[d_name] = db_district_map.get(d_name, None)

    # Dynamic Choropleth Tiers:
    valid_prices = sorted([p for p in district_prices.values() if p is not None])
    if valid_prices:
        p_min, p_max = valid_prices[0], valid_prices[-1]
        span = p_max - p_min
        if span <= 15:
            step = max(round(p_max * 0.03 / 5) * 5, 5)
            t4 = p_min
            t3 = p_min + step
            t2 = p_min + 2 * step
            t1 = p_min + 3 * step
        else:
            step = span / 5
            t4 = round((p_min + step) / 5) * 5
            t3 = round((p_min + 2 * step) / 5) * 5
            t2 = round((p_min + 3 * step) / 5) * 5
            t1 = round((p_min + 4 * step) / 5) * 5

        if t1 <= t2: t1 = t2 + 5
        if t2 <= t3: t2 = t3 + 5
        if t3 <= t4: t3 = t4 + 5

        legend_tiers = [t1, t2, t3, t4]
    else:
        legend_tiers = [500, 400, 300, 200]

    # Dynamic trend curve based on distinct collection dates
    date_points = list(
        crop_prices.values('date_recorded')
        .annotate(avg_price=Avg('price_per_kg_rwf'))
        .order_by('date_recorded')
    )

    if len(date_points) >= 2:
        is_insufficient = False
        earliest_p = float(date_points[0]['avg_price'])
        latest_p = float(date_points[-1]['avg_price'])
        trend_pct = round(((latest_p - earliest_p) / earliest_p) * 100, 1) if earliest_p > 0 else 0.0
        trend_points = [round(float(dp['avg_price'])) for dp in date_points]
        chart_min = round(min(trend_points) * 0.98 / 5) * 5
        chart_max = round(max(trend_points) * 1.02 / 5) * 5
        chart_step = max(round((chart_max - chart_min) / 3 / 5) * 5, 5)
        chart_ticks = [chart_min, chart_min + chart_step, chart_min + 2 * chart_step, chart_min + 3 * chart_step]

        num_pts = len(trend_points)
        x_coords = [int(55 + i * (390 / max(num_pts - 1, 1))) for i in range(num_pts)]
        y_coords = []
        y_span = max(chart_ticks[-1] - chart_ticks[0], 1)
        for p in trend_points:
            y = 140 - ((p - chart_ticks[0]) / y_span) * 120
            y_coords.append(round(y, 1))
        svg_pts = list(zip(x_coords, y_coords, trend_points))
    else:
        is_insufficient = True
        trend_pct = None
        trend_points = []
        chart_ticks = []
        x_coords = []
        y_coords = []
        svg_pts = []

    return {
        'crop_name': crop_name,
        'national_avg': national_avg,
        'district_prices': district_prices,
        'legend_tiers': legend_tiers,
        'trend_pct': trend_pct,
        'is_insufficient_time_series': is_insufficient,
        'trend_points': trend_points,
        'chart_ticks': chart_ticks,
        'x_coords': x_coords,
        'y_coords': y_coords,
        'svg_pts': svg_pts,
    }


def market_list(request):
    """
    Public Commodity Market Prices Page.
    Strictly displays approved and published prices to the public.
    Matches the official Rwanda Agricultural Intelligence reference design:
    - Hero banner: 'Know the market. Make better decisions.'
    - 4 Top KPI Cards: Maize average, Markets monitored, Commodities tracked, Last update
    - Filter bar: Search, Commodity, Province, Market type, Date range, Apply filters
    - Rwanda District Choropleth Map with Price Levels (Low, Medium, High)
    - Trend Line Chart & Key insights
    - Latest verified market prices table with image/icon support & pagination
    """
    query = request.GET.get('q', '').strip()
    crop_filter = request.GET.get('commodity', request.GET.get('crop', '')).strip()
    province_filter = request.GET.get('province', '').strip()
    market_type_filter = request.GET.get('market_type', '').strip()
    date_range = request.GET.get('date_range', '7d').strip()

    # Base Query: Strictly published records
    public_prices = CommodityPrice.objects.filter(
        status=CommodityPrice.Status.PUBLISHED
    ).select_related('market__district__province', 'crop').order_by('-date_recorded', '-id')

    # 1. Search Query
    if query:
        public_prices = public_prices.filter(
            Q(crop__name__icontains=query) |
            Q(market__name__icontains=query) |
            Q(market__district__name__icontains=query) |
            Q(market__province__name__icontains=query)
        )

    # 2. Commodity Filter
    if crop_filter and crop_filter != 'all':
        if crop_filter.isdigit():
            public_prices = public_prices.filter(crop_id=int(crop_filter))
        else:
            public_prices = public_prices.filter(crop__name__iexact=crop_filter)

    # 3. Province Filter
    if province_filter and province_filter != 'all':
        if province_filter.isdigit():
            public_prices = public_prices.filter(market__district__province_id=int(province_filter))
        else:
            public_prices = public_prices.filter(market__district__province__name__icontains=province_filter)

    # 4. Market Type Filter
    if market_type_filter and market_type_filter != 'all':
        public_prices = public_prices.filter(market__market_type=market_type_filter)

    # 5. Date Range Filter
    today = timezone.now().date()
    if date_range == 'today':
        public_prices = public_prices.filter(date_recorded=today)
    elif date_range == '7d':
        public_prices = public_prices.filter(date_recorded__gte=today - timedelta(days=7))
    elif date_range == '30d':
        public_prices = public_prices.filter(date_recorded__gte=today - timedelta(days=30))
    elif date_range == '90d':
        public_prices = public_prices.filter(date_recorded__gte=today - timedelta(days=90))

    # Determine Pinned / Selected District
    selected_district = request.GET.get('district', '').strip()
    if not selected_district and query:
        matching_dist = [d for d in RWANDA_30_DISTRICTS if d.lower() == query.lower()]
        if matching_dist:
            selected_district = matching_dist[0]
    if not selected_district:
        selected_district = 'Nyanza'

    # Filter table by district if user selected a district
    if request.GET.get('district'):
        public_prices = public_prices.filter(market__district__name__iexact=selected_district)

    # Pagination: 5 rows per page as per reference design
    paginator = Paginator(public_prices, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Dynamic collection timestamps and weekly changes from database
    for idx, item in enumerate(page_obj):
        # Format time
        if item.time_recorded:
            item.formatted_time = item.time_recorded.strftime('%I:%M %p')
        else:
            item.formatted_time = "—"

        item.formatted_date = item.date_recorded.strftime('%d %b %Y')

        # Compute weekly change from previous quote for the same commodity and market
        prev_quote = CommodityPrice.objects.filter(
            status=CommodityPrice.Status.PUBLISHED,
            crop=item.crop,
            market=item.market,
            date_recorded__lt=item.date_recorded
        ).order_by('-date_recorded', '-id').first()

        if prev_quote and prev_quote.price_per_kg_rwf and prev_quote.price_per_kg_rwf > 0:
            pct_diff = float((item.price_per_kg_rwf - prev_quote.price_per_kg_rwf) / prev_quote.price_per_kg_rwf) * 100
            item.is_positive_change = (pct_diff >= 0)
            item.change_display = f"+{pct_diff:.1f}%" if pct_diff >= 0 else f"{pct_diff:.1f}%"
        else:
            item.is_positive_change = None
            item.change_display = "—"

    # Determine Active Commodity for Live Surveillance & Map
    active_crop = None
    if crop_filter and crop_filter != 'all':
        if crop_filter.isdigit():
            active_crop = Crop.objects.filter(id=int(crop_filter)).first()
        else:
            active_crop = Crop.objects.filter(name__iexact=crop_filter).first()

    if not active_crop:
        # Default to Maize
        active_crop = Crop.objects.filter(name__iexact='Maize').first() or Crop.objects.first()

    # Pre-fetch published prices for calculation
    published_prices_qs = CommodityPrice.objects.filter(status=CommodityPrice.Status.PUBLISHED)

    # Compute comprehensive dynamic surveillance dataset for active commodity
    active_crop_data = get_crop_surveillance_data(active_crop, published_prices_qs)

    # Priority Crops list for filter dropdown
    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    if not priority_crops.exists():
        priority_crops = Crop.objects.all()[:12]

    # Precompute dataset for all priority crops for instant client-side switching
    all_crops_district_data = {}
    for c in priority_crops:
        all_crops_district_data[c.name] = get_crop_surveillance_data(c, published_prices_qs)

    # Top KPI Metrics (Dynamic to active commodity)
    kpi_commodity_name = active_crop_data['crop_name']
    kpi_commodity_avg = active_crop_data['national_avg']
    kpi_commodity_trend = active_crop_data['trend_pct']

    # KPI 2: Markets Monitored
    kpi_markets_monitored = MarketLocation.objects.filter(is_active=True).count()

    # KPI 3: Commodities Tracked
    kpi_commodities_tracked = Crop.objects.filter(market_prices__status=CommodityPrice.Status.PUBLISHED).distinct().count()

    # KPI 4: Last Price Update
    latest_published = CommodityPrice.objects.filter(
        status=CommodityPrice.Status.PUBLISHED
    ).order_by('-date_recorded', '-time_recorded', '-id').first()

    if latest_published:
        kpi_last_updated_date = latest_published.date_recorded.strftime('%d %b %Y')
        kpi_last_update_time = latest_published.time_recorded.strftime('%I:%M %p') if latest_published.time_recorded else "—"
    else:
        kpi_last_updated_date = "—"
        kpi_last_update_time = "—"

    provinces_list = Province.objects.all().order_by('name')
    market_types_list = [
        ('retail', 'Retail Consumer Market'),
        ('wholesale', 'Wholesale Trade Hub'),
        ('border', 'Cross-Border Trading Post'),
        ('assembly', 'Rural Assembly Market'),
    ]
    date_ranges_list = [
        ('7d', 'Last 7 days'),
        ('today', 'Today'),
        ('30d', 'Last 30 days'),
        ('90d', 'Last 90 days'),
        ('all', 'All time'),
    ]

    context = {
        'page_title': f'AgriLens Market Prices - {kpi_commodity_name} Surveillance',
        'page_obj': page_obj,
        'kpi_commodity_name': kpi_commodity_name,
        'kpi_commodity_avg': kpi_commodity_avg,
        'kpi_commodity_trend': kpi_commodity_trend,
        'kpi_maize_avg': kpi_commodity_avg, # backwards compatibility
        'kpi_maize_trend': kpi_commodity_trend,
        'kpi_markets_monitored': kpi_markets_monitored,
        'kpi_commodities_tracked': kpi_commodities_tracked,
        'kpi_last_update_time': kpi_last_update_time,
        'kpi_last_updated_date': kpi_last_updated_date,
        'selected_q': query,
        'selected_crop': crop_filter,
        'selected_district': selected_district,
        'selected_province': province_filter,
        'selected_market_type': market_type_filter,
        'selected_date_range': date_range,
        'priority_crops': priority_crops,
        'provinces_list': provinces_list,
        'market_types_list': market_types_list,
        'date_ranges_list': date_ranges_list,
        'trend_crop': active_crop,
        'district_price_json': json.dumps(active_crop_data['district_prices']),
        'legend_tiers': active_crop_data['legend_tiers'],
        'legend_tiers_json': json.dumps(active_crop_data['legend_tiers']),
        'all_crops_json': json.dumps({
            k: {
                'avg': v['national_avg'],
                'tiers': v['legend_tiers'],
                'districts': v['district_prices']
            } for k, v in all_crops_district_data.items()
        }),
        'trend_chart_data': active_crop_data,
        'total_published_count': public_prices.count(),
        'is_staff_user': is_market_staff(getattr(request, 'user', None)),
    }
    return render(request, 'markets/market_list.html', context)


# ==============================================================================
# 2. INTERNAL COMMODITY PRICES MANAGEMENT SUITE (STAFF ONLY)
# ==============================================================================

@login_required
@user_passes_test(is_market_staff)
def internal_dashboard(request):
    """
    Internal Price Dashboard.
    Provides operational KPIs: Total Published, Pending Approval, Needs Correction,
    Active Markets, Today's Collected, and Recent Surveillance Submissions.
    """
    today = timezone.now().date()
    
    # Operational KPIs
    total_published = CommodityPrice.objects.filter(status=CommodityPrice.Status.PUBLISHED).count()
    pending_approvals = CommodityPrice.objects.filter(status__in=[CommodityPrice.Status.SUBMITTED, CommodityPrice.Status.UNDER_REVIEW]).count()
    needs_correction = CommodityPrice.objects.filter(status=CommodityPrice.Status.NEEDS_CORRECTION).count()
    active_markets_count = MarketLocation.objects.filter(is_active=True).count()
    today_collected = CommodityPrice.objects.filter(date_recorded=today).count()

    # Workflow state distribution
    workflow_counts = {
        'draft': CommodityPrice.objects.filter(status=CommodityPrice.Status.DRAFT).count(),
        'submitted': CommodityPrice.objects.filter(status=CommodityPrice.Status.SUBMITTED).count(),
        'under_review': CommodityPrice.objects.filter(status=CommodityPrice.Status.UNDER_REVIEW).count(),
        'needs_correction': needs_correction,
        'approved': CommodityPrice.objects.filter(status=CommodityPrice.Status.APPROVED).count(),
        'published': total_published,
        'rejected': CommodityPrice.objects.filter(status=CommodityPrice.Status.REJECTED).count(),
    }

    # Recent Submissions requiring action or monitoring
    recent_records = CommodityPrice.objects.select_related('market__district', 'crop', 'collected_by').order_by('-updated_at', '-id')[:10]

    # Active validation alerts
    flagged_records = CommodityPrice.objects.exclude(validation_flags=[]).select_related('market', 'crop')[:5]

    context = {
        'active_subnav': 'dashboard',
        'total_published': total_published,
        'pending_approvals': pending_approvals,
        'needs_correction': needs_correction,
        'active_markets_count': active_markets_count,
        'today_collected': today_collected,
        'workflow_counts': workflow_counts,
        'recent_records': recent_records,
        'flagged_records': flagged_records,
    }
    return render(request, 'markets/internal/dashboard.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_records(request):
    """
    Price Records Registry.
    Full tabular access with status badges, search, filter, and bulk actions.
    """
    status_filter = request.GET.get('status', '').strip()
    crop_filter = request.GET.get('crop', '').strip()
    market_filter = request.GET.get('market', '').strip()
    search_q = request.GET.get('q', '').strip()

    records = CommodityPrice.objects.select_related('market__district', 'crop', 'collected_by', 'approved_by').order_by('-date_recorded', '-id')

    if status_filter:
        records = records.filter(status=status_filter)
    if crop_filter:
        records = records.filter(crop__name__iexact=crop_filter)
    if market_filter and market_filter.isdigit():
        records = records.filter(market_id=int(market_filter))
    if search_q:
        records = records.filter(
            Q(crop__name__icontains=search_q) |
            Q(market__name__icontains=search_q) |
            Q(market__district__name__icontains=search_q)
        )

    paginator = Paginator(records, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'active_subnav': 'records',
        'page_obj': page_obj,
        'status_choices': CommodityPrice.Status.choices,
        'selected_status': status_filter,
        'selected_crop': crop_filter,
        'selected_market': market_filter,
        'selected_q': search_q,
        'crops': Crop.objects.filter(is_priority_crop=True).order_by('name'),
        'markets': MarketLocation.objects.filter(is_active=True).order_by('name'),
    }
    return render(request, 'markets/internal/records.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_record_create(request):
    """
    Add new price observation manually.
    Enforces workflow logic:
    Collectors cannot directly publish their own unverified prices.
    Only Staff/Superusers can publish directly; collectors submit for review.
    """
    if request.method == 'POST':
        form = CommodityPriceForm(request.POST)
        action_intent = request.POST.get('action_intent', 'submit')

        if form.is_valid():
            price_record = form.save(commit=False)
            price_record.collected_by = request.user

            # Automated sanity validation against catalog bounds
            comm_catalog = MarketCommodity.objects.filter(crop=price_record.crop).first()
            flags = []
            if comm_catalog:
                if price_record.price_per_kg_rwf < comm_catalog.min_expected_price:
                    flags.append('price_below_expected_bound')
                elif price_record.price_per_kg_rwf > comm_catalog.max_expected_price:
                    flags.append('price_above_expected_bound')
            price_record.validation_flags = flags

            # Role & Intent handling
            if action_intent == 'draft':
                price_record.status = CommodityPrice.Status.DRAFT
                msg = "Price record saved as draft."
            elif action_intent == 'publish' and (request.user.is_superuser or request.user.is_staff):
                price_record.status = CommodityPrice.Status.PUBLISHED
                price_record.approved_by = request.user
                price_record.approved_at = timezone.now()
                price_record.published_at = timezone.now()
                msg = "Price record approved and published live."
            else:
                # Default workflow submission for review
                price_record.status = CommodityPrice.Status.SUBMITTED
                msg = "Price record submitted for review & validation."

            price_record.save()

            # Immutable audit trail
            PriceAuditLog.objects.create(
                price_record=price_record,
                actor=request.user,
                action='created',
                reason=f"Recorded via internal data entry form ({price_record.get_status_display()})",
                details={
                    'price': float(price_record.price_per_kg_rwf),
                    'market': price_record.market.name,
                    'crop': price_record.crop.name,
                    'flags': flags
                }
            )

            messages.success(request, msg)
            return redirect('markets:internal_records')
    else:
        form = CommodityPriceForm()

    context = {
        'active_subnav': 'records',
        'form': form,
        'page_title': 'Record New Commodity Price Observation',
    }
    return render(request, 'markets/internal/record_form.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_record_edit(request, pk):
    """
    Correct or edit an existing price record.
    Preserves audit lineage without silent overwrites.
    """
    record = get_object_or_404(CommodityPrice, pk=pk)
    old_price = record.price_per_kg_rwf

    if request.method == 'POST':
        form = CommodityPriceCorrectionForm(request.POST, instance=record)
        if form.is_valid():
            updated_record = form.save(commit=False)
            correction_reason = form.cleaned_data['correction_reason']

            if old_price != updated_record.price_per_kg_rwf:
                updated_record.original_price = old_price
                updated_record.correction_reason = correction_reason
                
                # If record was in 'needs_correction', move back to submitted
                if updated_record.status == CommodityPrice.Status.NEEDS_CORRECTION:
                    updated_record.status = CommodityPrice.Status.SUBMITTED

            updated_record.save()

            # Record in audit log
            PriceAuditLog.objects.create(
                price_record=updated_record,
                actor=request.user,
                action='corrected',
                reason=correction_reason,
                details={
                    'previous_price': float(old_price),
                    'new_price': float(updated_record.price_per_kg_rwf),
                }
            )

            messages.success(request, f"Price record #{record.id} updated with audit justification.")
            return redirect('markets:internal_records')
    else:
        form = CommodityPriceCorrectionForm(instance=record)

    context = {
        'active_subnav': 'records',
        'form': form,
        'record': record,
        'page_title': f'Audit Correction: Record #{record.id} ({record.crop.name})',
    }
    return render(request, 'markets/internal/record_form.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_record_delete(request, pk):
    """Delete a commodity price observation and record an audit log."""
    record = get_object_or_404(CommodityPrice, pk=pk)
    if request.method == 'POST':
        PriceAuditLog.objects.create(
            actor=request.user,
            action='deleted',
            reason=f"Deleted price record #{record.id} for {record.crop.name} in {record.market.name}",
            details={'record_id': record.id, 'price': float(record.price_per_kg_rwf), 'market': record.market.name, 'crop': record.crop.name}
        )
        record.delete()
        messages.success(request, f"Price record #{pk} deleted.")
    return redirect('markets:internal_records')


@login_required
@user_passes_test(is_market_staff)
def internal_records_import(request):
    """
    Bulk import market surveillance prices from CSV.
    Parses and verifies rows, creates records in 'submitted' status.
    """
    if request.method == 'POST':
        form = PriceCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            selected_hub = form.cleaned_data.get('market_hub')
            
            try:
                decoded_file = csv_file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                imported_count = 0
                error_count = 0

                for row in reader:
                    # Resolve market
                    market_name = row.get('market') or (selected_hub.name if selected_hub else None)
                    market = MarketLocation.objects.filter(name__icontains=market_name).first() if market_name else selected_hub
                    
                    # Resolve crop
                    crop_name = row.get('crop') or row.get('commodity')
                    crop = Crop.objects.filter(name__icontains=crop_name).first() if crop_name else None

                    # Retail price
                    retail_raw = row.get('retail_price') or row.get('price')
                    
                    if not market or not crop or not retail_raw:
                        error_count += 1
                        continue

                    try:
                        retail_val = Decimal(str(retail_raw).strip())
                    except Exception:
                        error_count += 1
                        continue

                    wholesale_raw = row.get('wholesale_price')
                    wholesale_val = Decimal(str(wholesale_raw).strip()) if wholesale_raw else None

                    date_val = row.get('date') or timezone.now().date()

                    price_record = CommodityPrice.objects.create(
                        market=market,
                        crop=crop,
                        price_per_kg_rwf=retail_val,
                        wholesale_price_rwf=wholesale_val,
                        date_recorded=date_val,
                        status=CommodityPrice.Status.SUBMITTED,
                        source_type='partner',
                        source_document=csv_file.name,
                        collected_by=request.user,
                    )
                    imported_count += 1

                # Audit log for import batch
                PriceAuditLog.objects.create(
                    actor=request.user,
                    action='batch_import',
                    reason=f"Imported {imported_count} prices from {csv_file.name}",
                    details={'success': imported_count, 'errors': error_count}
                )

                messages.success(request, f"Successfully imported {imported_count} price observations ({error_count} skipped).")
                return redirect('markets:internal_records')
            except Exception as e:
                messages.error(request, f"Failed to process CSV file: {str(e)}")
    else:
        form = PriceCSVImportForm()

    context = {
        'active_subnav': 'records',
        'form': form,
    }
    return render(request, 'markets/internal/import.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_markets(request):
    """Markets & Locations catalog across Rwanda's 30 districts."""
    if request.method == 'POST':
        form = MarketLocationForm(request.POST)
        if form.is_valid():
            market = form.save()
            messages.success(request, f"Market hub '{market.name}' registered successfully.")
            return redirect('markets:internal_markets')
    else:
        form = MarketLocationForm()

    markets = MarketLocation.objects.select_related('district__province').annotate(
        record_count=Count('prices')
    ).order_by('district__province__name', 'name')

    context = {
        'active_subnav': 'markets',
        'markets': markets,
        'form': form,
    }
    return render(request, 'markets/internal/markets.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_commodities(request):
    """Commodities definition catalog and expected sanity boundaries."""
    if request.method == 'POST':
        form = MarketCommodityForm(request.POST)
        if form.is_valid():
            comm = form.save()
            messages.success(request, f"Commodity catalog item '{comm.name}' updated.")
            return redirect('markets:internal_commodities')
    else:
        form = MarketCommodityForm()

    commodities = MarketCommodity.objects.select_related('crop').all().order_by('category', 'name')

    context = {
        'active_subnav': 'commodities',
        'commodities': commodities,
        'form': form,
    }
    return render(request, 'markets/internal/commodities.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_market_edit(request, pk):
    """Edit market location details."""
    market = get_object_or_404(MarketLocation, pk=pk)
    if request.method == 'POST':
        form = MarketLocationForm(request.POST, instance=market)
        if form.is_valid():
            form.save()
            messages.success(request, f"Market hub '{market.name}' updated successfully.")
            return redirect('markets:internal_markets')
    else:
        form = MarketLocationForm(instance=market)

    return render(request, 'markets/internal/market_form.html', {
        'active_subnav': 'markets',
        'form': form,
        'market': market,
        'page_title': f"Edit Market: {market.name}",
    })


@login_required
@user_passes_test(is_market_staff)
def internal_market_delete(request, pk):
    """Delete market location if no prices recorded."""
    market = get_object_or_404(MarketLocation, pk=pk)
    if request.method == 'POST':
        price_count = market.prices.count()
        if price_count > 0:
            messages.warning(request, f"Cannot delete '{market.name}' because {price_count} price observations are recorded for this hub.")
        else:
            name = market.name
            market.delete()
            messages.success(request, f"Market hub '{name}' has been deleted.")
    return redirect('markets:internal_markets')


@login_required
@user_passes_test(is_market_staff)
def internal_commodity_edit(request, pk):
    """Edit commodity bounds and properties."""
    comm = get_object_or_404(MarketCommodity, pk=pk)
    if request.method == 'POST':
        form = MarketCommodityForm(request.POST, instance=comm)
        if form.is_valid():
            form.save()
            messages.success(request, f"Commodity item '{comm.name}' updated.")
            return redirect('markets:internal_commodities')
    else:
        form = MarketCommodityForm(instance=comm)

    return render(request, 'markets/internal/commodity_form.html', {
        'active_subnav': 'commodities',
        'form': form,
        'commodity': comm,
        'page_title': f"Edit Commodity Bounds: {comm.name}",
    })


@login_required
@user_passes_test(is_market_staff)
def internal_commodity_delete(request, pk):
    """Delete a commodity bounds item."""
    comm = get_object_or_404(MarketCommodity, pk=pk)
    if request.method == 'POST':
        name = comm.name
        comm.delete()
        messages.success(request, f"Commodity bounds catalog item '{name}' deleted.")
    return redirect('markets:internal_commodities')


@login_required
@user_passes_test(is_market_staff)
def internal_collection(request):
    """
    Data Collection view for field officers.
    Shows assigned markets, quick entry form, and today's logs.
    """
    assignments = PriceCollectionAssignment.objects.filter(
        officer=request.user, is_active=True
    ).select_related('market', 'crop') if not request.user.is_superuser else PriceCollectionAssignment.objects.filter(is_active=True).select_related('officer', 'market')

    today_logs = CommodityPrice.objects.filter(
        collected_by=request.user,
        date_recorded=timezone.now().date()
    ).select_related('market', 'crop').order_by('-id')

    context = {
        'active_subnav': 'collection',
        'assignments': assignments,
        'today_logs': today_logs,
        'quick_form': CommodityPriceForm(),
    }
    return render(request, 'markets/internal/collection.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_approvals(request):
    """
    Validation & Approval queue.
    Reviewers accept, reject, or return records for correction.
    Checks units, dates, market, commodity, duplicates, and price outliers.
    """
    queue_records = CommodityPrice.objects.filter(
        status__in=[
            CommodityPrice.Status.SUBMITTED,
            CommodityPrice.Status.UNDER_REVIEW,
            CommodityPrice.Status.NEEDS_CORRECTION,
            CommodityPrice.Status.APPROVED,
        ]
    ).select_related('market__district', 'crop', 'collected_by').order_by('-date_recorded', '-id')

    context = {
        'active_subnav': 'approvals',
        'queue_records': queue_records,
        'pending_count': queue_records.count(),
    }
    return render(request, 'markets/internal/approvals.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_approval_action(request, pk):
    """
    Workflow transition endpoint for single record:
    Actions: 'approve', 'publish', 'return_for_correction', 'reject'.
    """
    record = get_object_or_404(CommodityPrice, pk=pk)
    action = request.POST.get('action')
    reason = request.POST.get('reason', '').strip()

    # Rule: Collector cannot approve/publish their own price records
    if record.collected_by == request.user and not request.user.is_superuser:
        messages.error(request, "Governance Rule: You cannot approve or publish price records that you collected yourself.")
        return redirect('markets:internal_approvals')

    if action == 'approve':
        record.status = CommodityPrice.Status.APPROVED
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()
        msg = f"Record #{record.id} marked as Approved."

    elif action == 'publish':
        record.status = CommodityPrice.Status.PUBLISHED
        if not record.approved_by:
            record.approved_by = request.user
            record.approved_at = timezone.now()
        record.published_at = timezone.now()
        record.save()
        msg = f"Record #{record.id} Published live to public portal."

    elif action == 'return_for_correction':
        if not reason:
            messages.error(request, "Correction feedback reason is required when returning a record.")
            return redirect('markets:internal_approvals')
        record.status = CommodityPrice.Status.NEEDS_CORRECTION
        record.review_comments = reason
        record.correction_reason = reason
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.save()
        msg = f"Record #{record.id} returned to collector for correction."

    elif action == 'reject':
        record.status = CommodityPrice.Status.REJECTED
        record.review_comments = reason or "Rejected during supervisory review."
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.save()
        msg = f"Record #{record.id} marked as Rejected."

    else:
        messages.error(request, "Invalid workflow action specified.")
        return redirect('markets:internal_approvals')

    # Audit Trail Entry
    PriceAuditLog.objects.create(
        price_record=record,
        actor=request.user,
        action=f"workflow_{action}",
        reason=reason or f"Transitioned to {record.get_status_display()}",
        details={
            'price': float(record.price_per_kg_rwf),
            'status': record.status,
            'crop': record.crop.name,
            'market': record.market.name,
        }
    )

    messages.success(request, msg)
    return redirect('markets:internal_approvals')


@login_required
@user_passes_test(is_market_staff)
def internal_analytics(request):
    """
    Price Analytics & Disparities.
    Examines price spreads between production assembly markets vs Kigali consumption hubs.
    """
    # District price disparities
    disparities_raw = CommodityPrice.objects.filter(
        status=CommodityPrice.Status.PUBLISHED
    ).values('crop__name').annotate(
        avg_price=Avg('price_per_kg_rwf'),
        min_price=Min('price_per_kg_rwf'),
        max_price=Max('price_per_kg_rwf'),
        quote_count=Count('id')
    ).order_by('-quote_count')

    disparities = []
    for d in disparities_raw:
        min_p = d.get('min_price')
        max_p = d.get('max_price')
        spread = round(float(max_p - min_p), 1) if (max_p is not None and min_p is not None) else None
        disparities.append({
            **d,
            'spread': spread
        })

    # Market Hub Rankings
    market_averages = CommodityPrice.objects.filter(
        status=CommodityPrice.Status.PUBLISHED
    ).values('market__name', 'market__district__name').annotate(
        avg_retail=Avg('price_per_kg_rwf'),
        total_quotes=Count('id')
    ).order_by('-avg_retail')[:10]

    context = {
        'active_subnav': 'analytics',
        'disparities': disparities,
        'market_averages': market_averages,
    }
    return render(request, 'markets/internal/analytics.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_reports(request):
    """
    Reports & Exports.
    Provides CSV download of the authoritative surveillance records and print bulletins.
    """
    export_format = request.GET.get('export')
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="agrilens_commodity_prices_{timezone.now().date()}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Record ID', 'Date', 'Market Hub', 'District', 'Province',
            'Crop', 'Retail Price (RWF/kg)', 'Wholesale Price (RWF/kg)',
            'Status', 'Collected By', 'Approved By'
        ])

        prices = CommodityPrice.objects.select_related(
            'market__district__province', 'crop', 'collected_by', 'approved_by'
        ).all().order_by('-date_recorded')

        for p in prices:
            writer.writerow([
                p.id,
                p.date_recorded,
                p.market.name,
                p.market.district.name,
                p.market.province.name if p.market.province else '',
                p.crop.name,
                p.price_per_kg_rwf,
                p.wholesale_price_rwf or '',
                p.get_status_display(),
                p.collected_by.username if p.collected_by else '',
                p.approved_by.username if p.approved_by else '',
            ])
        return response

    context = {
        'active_subnav': 'reports',
        'total_records': CommodityPrice.objects.count(),
        'published_records': CommodityPrice.objects.filter(status=CommodityPrice.Status.PUBLISHED).count(),
    }
    return render(request, 'markets/internal/reports.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_publications(request):
    """
    Publications & Public Notices.
    Manage public bulletins and price notifications displayed on public portal.
    """
    if request.method == 'POST':
        form = PricePublicNoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, f"Price notice '{notice.title}' published.")
            return redirect('markets:internal_publications')
    else:
        form = PricePublicNoticeForm()

    notices = PricePublicNotice.objects.all().order_by('-effective_date', '-id')

    context = {
        'active_subnav': 'publications',
        'notices': notices,
        'form': form,
    }
    return render(request, 'markets/internal/publications.html', context)


@login_required
@user_passes_test(is_market_staff)
def internal_audit_log(request):
    """
    Audit Log Trail.
    Immutable surveillance history of every creation, correction, approval, and publication.
    """
    action_filter = request.GET.get('action', '').strip()
    logs = PriceAuditLog.objects.select_related('actor', 'price_record__crop', 'price_record__market').all().order_by('-timestamp')

    if action_filter:
        logs = logs.filter(action__icontains=action_filter)

    paginator = Paginator(logs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'active_subnav': 'audit',
        'page_obj': page_obj,
        'selected_action': action_filter,
    }
    return render(request, 'markets/internal/audit_log.html', context)
