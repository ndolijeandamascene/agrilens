"""
AgriLens Agricultural Insights Web Views.
Supports both public evidence-based agricultural data stories (/insights/)
and internal analyst management/review workflows (/insights/manage/).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import Http404

from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import District, Province
from apps.insights.models import AgriculturalInsight
from apps.insights.services.engine import AgriculturalInsightEngine
from apps.insights.services.rules import resolve_comparison_period
from apps.insights.services.workflow import InsightWorkflowService


# ==============================================================================
# PUBLIC AGRICULTURAL INSIGHTS & DATA STORIES
# ==============================================================================

def public_insights_list(request):
    """
    Public showcase of approved & published agricultural insights.
    Accessible to all citizens, researchers, and policy makers without authentication.
    """
    qs = AgriculturalInsight.objects.published().select_related(
        'crop', 'district', 'province', 'current_season', 'comparison_season'
    )

    # Active filters
    category = request.GET.get('category', '').strip()
    crop_id = request.GET.get('crop', '').strip()
    province_id = request.GET.get('province', '').strip()
    district_id = request.GET.get('district', '').strip()
    season_id = request.GET.get('season', '').strip()
    search = request.GET.get('search', '').strip()

    if category:
        qs = qs.filter(category=category)
    if crop_id:
        qs = qs.filter(crop_id=crop_id)
    if province_id:
        qs = qs.filter(province_id=province_id)
    if district_id:
        qs = qs.filter(district_id=district_id)
    if season_id:
        qs = qs.filter(current_season_id=season_id)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(headline__icontains=search) |
            Q(summary__icontains=search) |
            Q(crop__name__icontains=search) |
            Q(district__name__icontains=search)
        )

    qs = qs.order_by('-is_featured', '-published_at', '-created_at')

    # Featured insight (top priority or marked featured)
    featured_insight = None
    if not category and not crop_id and not district_id and not search:
        featured_insight = qs.filter(is_featured=True).first()
        if not featured_insight:
            featured_insight = qs.first()

    # If featured insight exists, exclude it from the primary paginated list to avoid repetition
    if featured_insight:
        qs = qs.exclude(id=featured_insight.id)

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter dropdown context
    crops = Crop.objects.filter(is_priority_crop=True)
    provinces = Province.objects.all()
    districts = District.objects.select_related('province').all()
    seasons = AgriculturalSeason.objects.all().order_by('-year', '-season')

    # Counts by category for filter pills
    category_counts = {}
    for cat_key, cat_label in AgriculturalInsight.Category.choices:
        cnt = AgriculturalInsight.objects.published().filter(category=cat_key).count()
        category_counts[cat_key] = cnt

    total_published = AgriculturalInsight.objects.published().count()

    context = {
        'page_obj': page_obj,
        'featured_insight': featured_insight,
        'crops': crops,
        'provinces': provinces,
        'districts': districts,
        'seasons': seasons,
        'categories': AgriculturalInsight.Category.choices,
        'category_counts': category_counts,
        'total_published': total_published,
        'selected_category': category,
        'selected_crop': crop_id,
        'selected_province': province_id,
        'selected_district': district_id,
        'selected_season': season_id,
        'search_query': search,
    }
    return render(request, 'insights/public_list.html', context)


def public_insight_detail(request, pk):
    """
    Public single insight data story detail page.
    Displays narrative, metrics, data quality disclosure, and investigation points.
    """
    # Strict public protection: only published insights accessible unless authenticated reviewer
    insight = get_object_or_404(
        AgriculturalInsight.objects.select_related(
            'crop', 'district', 'province', 'current_season', 'comparison_season'
        ),
        pk=pk
    )

    if insight.status != AgriculturalInsight.Status.PUBLISHED:
        if not (request.user.is_authenticated and InsightWorkflowService.can_review(request.user)):
            raise Http404("This agricultural insight has not yet been published.")

    # Related insights in same category or crop
    related_insights = AgriculturalInsight.objects.published().filter(
        Q(category=insight.category) | Q(crop=insight.crop)
    ).exclude(id=insight.id).select_related('crop', 'district')[:4]

    context = {
        'insight': insight,
        'related_insights': related_insights,
    }
    return render(request, 'insights/public_detail.html', context)


# ==============================================================================
# INTERNAL INSIGHTS MANAGEMENT & WORKFLOW
# ==============================================================================

@login_required
def internal_dashboard(request):
    """Internal insights command center with metrics and category distributions."""
    if not InsightWorkflowService.can_review(request.user):
        raise PermissionDenied("You do not have permission to access the Agricultural Insights Management Portal.")

    total_count = AgriculturalInsight.objects.count()
    generated_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.GENERATED).count()
    under_review_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.UNDER_REVIEW).count()
    approved_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.APPROVED).count()
    published_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.PUBLISHED).count()
    rejected_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.REJECTED).count()

    # Category breakdown
    cat_breakdown = []
    for code, label in AgriculturalInsight.Category.choices:
        cnt = AgriculturalInsight.objects.filter(category=code).count()
        pub_cnt = AgriculturalInsight.objects.filter(category=code, status=AgriculturalInsight.Status.PUBLISHED).count()
        cat_breakdown.append({
            'code': code,
            'label': label,
            'total': cnt,
            'published': pub_cnt,
        })

    # Paginated insights for recently discovered / catalog table
    insights_qs = AgriculturalInsight.objects.select_related(
        'crop', 'district', 'current_season'
    ).order_by('-is_featured', '-created_at')

    paginator = Paginator(insights_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    seasons = AgriculturalSeason.objects.all().order_by('-year', '-season')

    context = {
        'total_count': total_count,
        'generated_count': generated_count,
        'under_review_count': under_review_count,
        'approved_count': approved_count,
        'published_count': published_count,
        'rejected_count': rejected_count,
        'cat_breakdown': cat_breakdown,
        'page_obj': page_obj,
        'recent_insights': page_obj,
        'seasons': seasons,
    }
    return render(request, 'insights/internal/dashboard.html', context)


@login_required
def internal_list(request):
    """Full searchable and filterable catalog of all insights across all lifecycle states."""
    if not InsightWorkflowService.can_review(request.user):
        raise PermissionDenied("Access denied.")

    qs = AgriculturalInsight.objects.select_related(
        'crop', 'district', 'province', 'current_season', 'comparison_season', 'created_by', 'reviewed_by'
    )

    status_filter = request.GET.get('status', '').strip()
    category_filter = request.GET.get('category', '').strip()
    crop_id = request.GET.get('crop', '').strip()
    district_id = request.GET.get('district', '').strip()
    season_id = request.GET.get('season', '').strip()
    search = request.GET.get('search', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if category_filter:
        qs = qs.filter(category=category_filter)
    if crop_id:
        qs = qs.filter(crop_id=crop_id)
    if district_id:
        qs = qs.filter(district_id=district_id)
    if season_id:
        qs = qs.filter(current_season_id=season_id)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(headline__icontains=search) |
            Q(crop__name__icontains=search) |
            Q(district__name__icontains=search)
        )

    # Repository KPI metrics
    total_in_db = AgriculturalInsight.objects.count()
    published_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.PUBLISHED).count()
    pending_count = AgriculturalInsight.objects.filter(
        status__in=[AgriculturalInsight.Status.GENERATED, AgriculturalInsight.Status.UNDER_REVIEW]
    ).count()
    approved_count = AgriculturalInsight.objects.filter(status=AgriculturalInsight.Status.APPROVED).count()

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    has_active_filters = bool(status_filter or category_filter or crop_id or district_id or season_id or search)

    context = {
        'page_obj': page_obj,
        'crops': Crop.objects.filter(is_priority_crop=True),
        'districts': District.objects.all(),
        'seasons': AgriculturalSeason.objects.all().order_by('-year', '-season'),
        'statuses': AgriculturalInsight.Status.choices,
        'categories': AgriculturalInsight.Category.choices,
        'selected_status': status_filter,
        'selected_category': category_filter,
        'selected_crop': crop_id,
        'selected_district': district_id,
        'selected_season': season_id,
        'search_query': search,
        'total_in_db': total_in_db,
        'published_count': published_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'has_active_filters': has_active_filters,
    }
    return render(request, 'insights/internal/list.html', context)


@login_required
def internal_review_queue(request):
    """Dedicated queue for insights requiring analyst or supervisor review & approval."""
    if not InsightWorkflowService.can_review(request.user):
        raise PermissionDenied("Access denied.")

    qs = AgriculturalInsight.objects.review_queue().select_related(
        'crop', 'district', 'province', 'current_season', 'created_by'
    )

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'pending_count': qs.count(),
    }
    return render(request, 'insights/internal/review_queue.html', context)


@login_required
def internal_detail(request, pk):
    """Detailed internal inspection view showing calculation evidence, review log, and action triggers."""
    if not InsightWorkflowService.can_review(request.user):
        raise PermissionDenied("Access denied.")

    insight = get_object_or_404(
        AgriculturalInsight.objects.select_related(
            'crop', 'district', 'province', 'current_season', 'comparison_season', 'created_by', 'reviewed_by'
        ),
        pk=pk
    )

    can_approve = False
    if request.user.is_superuser or request.user.is_system_admin:
        can_approve = True
    elif insight.created_by != request.user and InsightWorkflowService.can_review(request.user):
        can_approve = True

    context = {
        'insight': insight,
        'can_approve': can_approve,
        'can_publish': InsightWorkflowService.can_publish(request.user),
    }
    return render(request, 'insights/internal/detail.html', context)


@login_required
def internal_approve(request, pk):
    """Approve action endpoint."""
    if request.method != 'POST':
        return redirect('insights:internal_detail', pk=pk)

    insight = get_object_or_404(AgriculturalInsight, pk=pk)
    comments = request.POST.get('comments', '').strip()

    try:
        InsightWorkflowService.approve(insight, request.user, comments=comments, request=request)
        messages.success(request, f"Insight '{insight.title}' approved successfully.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Failed to approve insight: {e}")

    return redirect('insights:internal_detail', pk=pk)


@login_required
def internal_reject(request, pk):
    """Reject action endpoint."""
    if request.method != 'POST':
        return redirect('insights:internal_detail', pk=pk)

    insight = get_object_or_404(AgriculturalInsight, pk=pk)
    comments = request.POST.get('comments', '').strip()

    if not comments:
        messages.error(request, "A reason comment is required when rejecting an insight.")
        return redirect('insights:internal_detail', pk=pk)

    try:
        InsightWorkflowService.reject(insight, request.user, comments=comments, request=request)
        messages.warning(request, f"Insight '{insight.title}' has been rejected.")
    except Exception as e:
        messages.error(request, f"Failed to reject insight: {e}")

    return redirect('insights:internal_detail', pk=pk)


@login_required
def internal_publish(request, pk):
    """Publish action endpoint."""
    if request.method != 'POST':
        return redirect('insights:internal_detail', pk=pk)

    insight = get_object_or_404(AgriculturalInsight, pk=pk)
    try:
        InsightWorkflowService.publish(insight, request.user, request=request)
        messages.success(request, f"Insight '{insight.title}' is now live on the public portal.")
    except Exception as e:
        messages.error(request, f"Failed to publish insight: {e}")

    return redirect('insights:internal_detail', pk=pk)


@login_required
def internal_unpublish(request, pk):
    """Unpublish action endpoint."""
    if request.method != 'POST':
        return redirect('insights:internal_detail', pk=pk)

    insight = get_object_or_404(AgriculturalInsight, pk=pk)
    comments = request.POST.get('comments', '').strip()
    try:
        InsightWorkflowService.unpublish(insight, request.user, comments=comments, request=request)
        messages.info(request, f"Insight '{insight.title}' unpublished and returned to review queue.")
    except Exception as e:
        messages.error(request, f"Failed to unpublish: {e}")

    return redirect('insights:internal_detail', pk=pk)


@login_required
def internal_generate(request):
    """Triggers the discovery engine via internal web dashboard."""
    if request.method != 'POST':
        return redirect('insights:internal_dashboard')

    if not InsightWorkflowService.can_review(request.user):
        raise PermissionDenied("Access denied.")

    season_id = request.POST.get('season_id')
    auto_pub = request.POST.get('auto_publish') == 'on'

    season = get_object_or_404(AgriculturalSeason, pk=season_id)
    comp_season = resolve_comparison_period(season)

    engine = AgriculturalInsightEngine(current_season=season, comparison_season=comp_season, user=request.user)
    generated = engine.generate_all(auto_publish=auto_pub)

    messages.success(
        request,
        f"Discovery engine completed: {len(generated)} insights generated/updated for {season}. "
        f"{'Published live to public portal.' if auto_pub else 'Queued for analyst review.'}"
    )
    return redirect('insights:internal_dashboard')
