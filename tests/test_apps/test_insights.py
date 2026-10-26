"""
Automated Pytest Suite for AgriLens Agricultural Insights & Data Stories.
Tests calculation rules, quality policies, discovery engine, maker-checker workflow,
idempotency, DRF APIs, and public view segregation.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.exceptions import PermissionDenied, ValidationError

from apps.agriculture.models import Crop, AgriculturalSeason
from apps.geography.models import Province, District
from apps.data_management.models import ValidatedObservation
from apps.insights.models import AgriculturalInsight
from apps.insights.services.rules import (
    calculate_percentage_change,
    calculate_absolute_change,
    resolve_comparison_period,
    determine_direction,
)
from apps.insights.services.quality import evaluate_data_quality, QualityPolicy
from apps.insights.services.engine import AgriculturalInsightEngine
from apps.insights.services.workflow import InsightWorkflowService
from apps.accounts.models import User


# ==============================================================================
# 1. CALCULATION AND MATHEMATICAL RULES TESTS
# ==============================================================================

@pytest.mark.django_db
def test_calculate_percentage_change_positive():
    pct, note = calculate_percentage_change(120.0, 100.0)
    assert pct == Decimal('20.00')
    assert note is None


@pytest.mark.django_db
def test_calculate_percentage_change_negative():
    pct, note = calculate_percentage_change(75.0, 100.0)
    assert pct == Decimal('-25.00')
    assert note is None


@pytest.mark.django_db
def test_calculate_percentage_change_zero_baseline():
    pct, note = calculate_percentage_change(100.0, 0.0)
    assert pct is None
    assert "Baseline value is zero" in note


@pytest.mark.django_db
def test_calculate_percentage_change_missing_values():
    pct1, note1 = calculate_percentage_change(None, 100.0)
    assert pct1 is None
    assert "Missing" in note1

    pct2, note2 = calculate_percentage_change(100.0, None)
    assert pct2 is None
    assert "Missing" in note2


@pytest.mark.django_db
def test_calculate_percentage_change_genuine_zero():
    pct, note = calculate_percentage_change(0.0, 50.0)
    assert pct == Decimal('-100.00')
    assert note is None


@pytest.mark.django_db
def test_calculate_absolute_change():
    diff = calculate_absolute_change(1450.5, 1200.0)
    assert diff == Decimal('250.50')

    diff_neg = calculate_absolute_change(900.0, 1000.0)
    assert diff_neg == Decimal('-100.00')

    diff_none = calculate_absolute_change(None, 1000.0)
    assert diff_none is None


@pytest.mark.django_db
def test_determine_direction():
    assert determine_direction(Decimal('12.5')) == 'increase'
    assert determine_direction(Decimal('-8.3')) == 'decrease'
    assert determine_direction(Decimal('0.4')) == 'stable'
    assert determine_direction(None) == 'stable'


@pytest.mark.django_db
def test_resolve_comparison_period():
    s24a = AgriculturalSeason.objects.filter(year=2024, season='A').first()
    s25a = AgriculturalSeason.objects.filter(year=2025, season='A').first()
    if s24a and s25a:
        resolved = resolve_comparison_period(s25a)
        assert resolved == s24a


# ==============================================================================
# 2. DATA QUALITY AND ADEQUACY TESTS
# ==============================================================================

def test_evaluate_data_quality_sufficient():
    # District sample n=20 >= 15
    status, notes, eligible = evaluate_data_quality(sample_size_current=20, sample_size_comparison=18, is_national=False)
    assert status == AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA
    assert eligible is True


def test_evaluate_data_quality_limited():
    # District sample n=8 (between 5 and 14)
    status, notes, eligible = evaluate_data_quality(sample_size_current=8, is_national=False)
    assert status == AgriculturalInsight.DataQualityStatus.LIMITED_DATA
    assert eligible is True
    assert "indicative" in notes


def test_evaluate_data_quality_insufficient():
    # District sample n=3 (< 5)
    status, notes, eligible = evaluate_data_quality(sample_size_current=3, is_national=False)
    assert status == AgriculturalInsight.DataQualityStatus.INSUFFICIENT_DATA
    assert eligible is False


def test_evaluate_data_quality_outlier_yield():
    # Yield exceeds 60,000 kg/ha threshold
    status, notes, eligible = evaluate_data_quality(sample_size_current=25, yield_val=75000.0)
    assert status == AgriculturalInsight.DataQualityStatus.UNDER_REVIEW
    assert eligible is False
    assert "exceeds typical agronomic plausibility" in notes


def get_or_create_test_season(year=2025, season_code='A'):
    season, _ = AgriculturalSeason.objects.get_or_create(
        year=year,
        season=season_code,
        defaults={
            'start_date': '2024-09-01',
            'end_date': '2025-02-28',
        }
    )
    return season


# ==============================================================================
# 3. WORKFLOW AND SEPARATION OF DUTIES TESTS
# ==============================================================================

@pytest.mark.django_db
def test_maker_checker_separation_of_duties():
    creator = User.objects.create_user(username='analyst1', role=User.Role.ANALYST)
    supervisor = User.objects.create_user(username='manager1', role=User.Role.NISR_DATA_MANAGER)
    season = get_or_create_test_season(2025, 'A')

    insight = AgriculturalInsight.objects.create(
        title="Test Maize Yield Uplift",
        summary="Test summary narrative",
        category=AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
        current_season=season,
        fingerprint="test-fp-1",
        created_by=creator,
        status=AgriculturalInsight.Status.GENERATED
    )

    # 1. Creator cannot approve their own insight
    with pytest.raises(PermissionDenied) as exc:
        InsightWorkflowService.approve(insight, actor=creator)
    assert "Separation-of-duties violation" in str(exc.value)

    # 2. Another authorized reviewer CAN approve
    InsightWorkflowService.approve(insight, actor=supervisor, comments="Verified against SAS table 4")
    insight.refresh_from_db()
    assert insight.status == AgriculturalInsight.Status.APPROVED
    assert insight.reviewed_by == supervisor

    # 3. Publish approved insight
    InsightWorkflowService.publish(insight, actor=supervisor)
    insight.refresh_from_db()
    assert insight.status == AgriculturalInsight.Status.PUBLISHED
    assert insight.published_at is not None

    # 4. Unpublish insight
    InsightWorkflowService.unpublish(insight, actor=supervisor, comments="Withdrawn for recalculation")
    insight.refresh_from_db()
    assert insight.status == AgriculturalInsight.Status.UNDER_REVIEW


@pytest.mark.django_db
def test_rejection_requires_comment():
    supervisor = User.objects.create_user(username='manager2', role=User.Role.NISR_DATA_MANAGER)
    season = get_or_create_test_season()
    insight = AgriculturalInsight.objects.create(
        title="Test Anomaly",
        summary="Test",
        category=AgriculturalInsight.Category.DATA_QUALITY,
        current_season=season,
        fingerprint="test-fp-2",
        status=AgriculturalInsight.Status.GENERATED
    )

    # Reject without comment fails
    with pytest.raises(ValidationError):
        InsightWorkflowService.reject(insight, actor=supervisor, comments="")

    # Reject with comment succeeds
    InsightWorkflowService.reject(insight, actor=supervisor, comments="Inconclusive survey coverage")
    insight.refresh_from_db()
    assert insight.status == AgriculturalInsight.Status.REJECTED


# ==============================================================================
# 4. IDEMPOTENCY AND DISCOVERY ENGINE TESTS
# ==============================================================================

@pytest.mark.django_db
def test_engine_idempotency_and_no_duplicates():
    season_2025a = get_or_create_test_season(2025, 'A')
    season_2024a = get_or_create_test_season(2024, 'A')

    engine = AgriculturalInsightEngine(current_season=season_2025a, comparison_season=season_2024a)

    # Run 1
    insights_run1 = engine.generate_productivity_insights(min_pct=10.0)
    count_1 = AgriculturalInsight.objects.count()

    # Run 2 (Repeated generation with exact same data)
    insights_run2 = engine.generate_productivity_insights(min_pct=10.0)
    count_2 = AgriculturalInsight.objects.count()

    # Must be 100% idempotent: count does NOT increase
    assert count_1 == count_2
    assert len(insights_run1) == len(insights_run2)


# ==============================================================================
# 5. PUBLIC WEB VIEW SEGREGATION TESTS
# ==============================================================================

@pytest.mark.django_db
def test_public_view_only_shows_published_insights(client):
    season = get_or_create_test_season()

    # Create one published and one under-review insight
    pub_insight = AgriculturalInsight.objects.create(
        title="Published Data Story 101",
        summary="Public story content",
        category=AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
        current_season=season,
        fingerprint="test-fp-pub",
        status=AgriculturalInsight.Status.PUBLISHED
    )
    draft_insight = AgriculturalInsight.objects.create(
        title="Internal Draft Finding 102",
        summary="Confidential draft content",
        category=AgriculturalInsight.Category.PRODUCTIVITY_CHANGE,
        current_season=season,
        fingerprint="test-fp-draft",
        status=AgriculturalInsight.Status.GENERATED
    )

    # Anonymous public listing request
    resp = client.get(reverse('insights:public_list'))
    assert resp.status_code == 200
    content = resp.content.decode('utf-8')
    assert "Published Data Story 101" in content
    assert "Internal Draft Finding 102" not in content

    # Anonymous detail request for published insight
    detail_resp = client.get(reverse('insights:public_detail', kwargs={'pk': pub_insight.id}))
    assert detail_resp.status_code == 200

    # Anonymous detail request for draft insight returns 404
    draft_resp = client.get(reverse('insights:public_detail', kwargs={'pk': draft_insight.id}))
    assert draft_resp.status_code == 404


# ==============================================================================
# 6. REST API ENDPOINTS AND STATISTICS TESTS
# ==============================================================================

@pytest.mark.django_db
def test_insights_api_statistics_and_listing():
    api_client = APIClient()
    season = get_or_create_test_season()

    AgriculturalInsight.objects.create(
        title="API Test Insight 1",
        summary="Summary 1",
        category=AgriculturalInsight.Category.DISTRICT_PERFORMANCE,
        current_season=season,
        fingerprint="test-fp-api1",
        status=AgriculturalInsight.Status.PUBLISHED
    )

    # Public anonymous API call to listing
    list_resp = api_client.get('/api/v1/insights/')
    assert list_resp.status_code == 200
    assert len(list_resp.data['results']) >= 1

    # Public anonymous API call to stats
    stats_resp = api_client.get('/api/v1/insights/statistics/')
    assert stats_resp.status_code == 200
    assert 'total_insights' in stats_resp.data
    assert 'by_category' in stats_resp.data
