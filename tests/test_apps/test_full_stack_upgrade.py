"""
Automated Integration and Regression Tests for AgriLens Full-Stack Upgrade.
Validates:
  1. 3-way Source Selection Policy (official vs manual vs combined).
  2. Strict Minimum-Sample Policy for Productivity Gap Benchmarks.
  3. Query Parameter Validation & Error Handling.
  4. Authentication & Role-Based Authorization Enforcement.
  5. Module views (agriculture, geography, markets, surveys, farmers, inputs).
  6. API endpoints & DRF Serializers.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import CropCategory, Crop, AgriculturalSeason
from apps.markets.models import MarketLocation, CommodityPrice
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation, ManualObservation
from apps.indicators.services import IndicatorService


class FullStackUpgradeTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin & Role Users
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True
        )
        self.analyst_user = User.objects.create_user(
            username='analyst_test',
            password='Password123!',
            role=User.Role.ANALYST
        )
        self.extension_user = User.objects.create_user(
            username='extension_test',
            password='Password123!',
            role=User.Role.EXTENSION_OFFICER
        )

        # Geography
        self.province = Province.objects.create(name='Northern Province', code='NORTH')
        self.district_musanze = District.objects.create(name='Musanze', code='MUS', province=self.province)
        self.district_burera = District.objects.create(name='Burera', code='BUR', province=self.province)
        self.sector = Sector.objects.create(name='Muhoza', code='MUH01', district=self.district_musanze)

        # Agriculture
        self.category = CropCategory.objects.create(name='Cereals')
        self.crop_maize = Crop.objects.create(name='Maize', category=self.category, is_priority_crop=True)
        self.season_2025a = AgriculturalSeason.objects.create(
            year=2025, season='A',
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

        # Official DataSource & Batch
        self.source_nisr = DataSource.objects.create(
            name='NISR SAS 2025',
            source_type=DataSource.SourceType.NISR_SAS_2025,
            is_official_survey=True
        )
        self.batch = ImportBatch.objects.create(
            source=self.source_nisr,
            filename='sas_2025_a.sav',
            status=ImportBatch.Status.SUCCESS
        )

        # Seed Official ValidatedObservation (Musanze: 4,000 kg/ha, weight=1.0)
        self.official_obs = ValidatedObservation.objects.create(
            batch=self.batch,
            provenance='NISR_SAS_2025',
            season=self.season_2025a,
            district=self.district_musanze,
            sector=self.sector,
            crop=self.crop_maize,
            source_record_id='OFF_001',
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('4000.0'),
            calculated_yield_kg_per_ha=Decimal('4000.0'),
            sampling_weight=Decimal('1.0'),
            is_irrigated=True,
            is_improved_seed=True,
            uses_inorganic_fertilizer=True
        )

        # Seed Approved ManualObservation (Burera: 2,500 kg/ha)
        self.manual_obs = ManualObservation.objects.create(
            created_by=self.extension_user,
            season=self.season_2025a,
            district=self.district_burera,
            sector=self.sector,
            crop=self.crop_maize,
            observation_date=timezone.now().date(),
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('2500.0'),
            calculated_yield_kg_per_ha=Decimal('2500.0'),
            review_status=ManualObservation.ReviewStatus.APPROVED,
            is_irrigated=False,
            is_improved_seed=False,
            uses_inorganic_fertilizer=False
        )

    # --------------------------------------------------------------------------
    # 1. 3-Way Source Selection Policy Tests
    # --------------------------------------------------------------------------
    def test_official_source_policy_excludes_manual_data(self):
        """Official source policy must only aggregate NISR verified records."""
        summary = IndicatorService.get_national_summary(
            year=2025, season_code='A', crop_name='Maize', source_policy='official'
        )
        self.assertEqual(summary['source_policy'], 'official')
        self.assertTrue(summary['is_official_only'])
        self.assertEqual(summary['total_plots'], 1)
        self.assertEqual(summary['weighted_yield_kg_per_ha'], 4000.0)
        self.assertEqual(summary['official_plots_count'], 1)
        self.assertEqual(summary['manual_plots_count'], 0)

    def test_manual_source_policy_only_aggregates_approved_manual_entries(self):
        """Manual source policy must aggregate approved manual records without survey weights."""
        summary = IndicatorService.get_national_summary(
            year=2025, season_code='A', crop_name='Maize', source_policy='manual'
        )
        self.assertEqual(summary['source_policy'], 'manual')
        self.assertTrue(summary['is_manual_only'])
        self.assertEqual(summary['total_plots'], 1)
        self.assertEqual(summary['weighted_yield_kg_per_ha'], 2500.0)
        self.assertEqual(summary['manual_plots_count'], 1)
        self.assertEqual(summary['official_plots_count'], 0)

    def test_combined_source_policy_clearly_labels_dual_sources(self):
        """Combined source policy must include both official and approved manual records with explicit counts."""
        summary = IndicatorService.get_national_summary(
            year=2025, season_code='A', crop_name='Maize', source_policy='combined'
        )
        self.assertEqual(summary['source_policy'], 'combined')
        self.assertTrue(summary['is_combined'])
        self.assertEqual(summary['total_plots'], 2)
        # Combined yield: (4000 + 2500) / (1.0 + 1.0) = 3250.0 kg/ha
        self.assertEqual(summary['weighted_yield_kg_per_ha'], 3250.0)
        self.assertEqual(summary['official_plots_count'], 1)
        self.assertEqual(summary['manual_plots_count'], 1)

    # --------------------------------------------------------------------------
    # 2. Strict Minimum-Sample Policy Tests
    # --------------------------------------------------------------------------
    def test_productivity_gap_enforces_strict_sample_size_without_silent_downgrade(self):
        """When min_plots=5 is requested and districts have fewer plots, return structured insufficient data."""
        gap = IndicatorService.get_productivity_gap(
            crop_name='Maize', year=2025, season_code='A', min_plots=5, source_policy='official'
        )
        self.assertFalse(gap['is_sufficient_data'])
        self.assertIsNone(gap['benchmark'])
        self.assertIsNone(gap['lagging'])
        self.assertIn("Insufficient data", gap['reason'])
        self.assertIn("min_plots_threshold", gap)
        self.assertEqual(gap['min_plots_threshold'], 5)

    # --------------------------------------------------------------------------
    # 3. View Parameter Validation & Error Handling Tests
    # --------------------------------------------------------------------------
    def test_dashboard_view_handles_invalid_query_params_safely(self):
        """Malformed year, season, or source query parameters must not cause HTTP 500."""
        response = self.client.get('/dashboard/', {
            'year': 'invalid_year',
            'season': 'INVALID_SEASON',
            'source': 'malicious_source_inject',
            'crop': 'NonExistentCrop<script>'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_year'], 2025)
        self.assertEqual(response.context['selected_season'], 'A')
        self.assertEqual(response.context['selected_source'], 'official')

    def test_indicators_view_handles_invalid_query_params_safely(self):
        """Productivity intelligence page must safely sanitize inputs."""
        response = self.client.get(reverse('indicators:productivity'), {
            'year': '-999',
            'season': 'XYZ',
            'source': 'unknown_source'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_year'], 2025)
        self.assertEqual(response.context['selected_season'], 'A')
        self.assertEqual(response.context['selected_source'], 'official')

    # --------------------------------------------------------------------------
    # 4. Authentication & Authorization (RBAC) Tests
    # --------------------------------------------------------------------------
    def test_unauthenticated_user_cannot_create_manual_entry(self):
        """Unauthenticated POST to manual entry creation must redirect to login."""
        response = self.client.post(reverse('data_management:manual_entry_create'), {
            'crop': self.crop_maize.id,
            'district': self.district_musanze.id,
            'sector': self.sector.id,
            'season': self.season_2025a.id,
            'plot_area_ha': '1.5',
            'total_production_kg': '3000'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_unauthenticated_user_cannot_review_or_approve_manual_entry(self):
        """Unauthenticated user cannot approve submissions."""
        entry = ManualObservation.objects.create(
            created_by=self.extension_user,
            season=self.season_2025a,
            district=self.district_musanze,
            sector=self.sector,
            crop=self.crop_maize,
            observation_date=timezone.now().date(),
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('2000.0'),
            review_status=ManualObservation.ReviewStatus.SUBMITTED
        )

        response = self.client.post(reverse('data_management:manual_entry_review', kwargs={'pk': entry.pk}), {
            'decision': 'approve',
            'review_comments': 'Malicious attempt'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        # Record must remain SUBMITTED, not approved
        entry.refresh_from_db()
        self.assertEqual(entry.review_status, ManualObservation.ReviewStatus.SUBMITTED)

    def test_unauthorized_role_cannot_review_manual_entry(self):
        """Extension officer cannot approve submissions (requires ANALYST/ADMIN/POLICY_MAKER)."""
        entry = ManualObservation.objects.create(
            created_by=self.extension_user,
            season=self.season_2025a,
            district=self.district_musanze,
            sector=self.sector,
            crop=self.crop_maize,
            observation_date=timezone.now().date(),
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('2000.0'),
            review_status=ManualObservation.ReviewStatus.SUBMITTED
        )

        self.client.login(username='extension_test', password='Password123!')
        response = self.client.post(reverse('data_management:manual_entry_review', kwargs={'pk': entry.pk}), {
            'decision': 'approve',
            'review_comments': 'Unauthorized approval'
        })
        entry.refresh_from_db()
        self.assertEqual(entry.review_status, ManualObservation.ReviewStatus.SUBMITTED)

    def test_authorized_analyst_can_approve_manual_entry(self):
        """Agricultural Analyst can approve submitted observations."""
        entry = ManualObservation.objects.create(
            created_by=self.extension_user,
            season=self.season_2025a,
            district=self.district_musanze,
            sector=self.sector,
            crop=self.crop_maize,
            observation_date=timezone.now().date(),
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('2000.0'),
            review_status=ManualObservation.ReviewStatus.SUBMITTED
        )

        self.client.login(username='analyst_test', password='Password123!')
        response = self.client.post(reverse('data_management:manual_entry_review', kwargs={'pk': entry.pk}), {
            'decision': 'approve',
            'review_comments': 'QA verified against cooperative weight receipts.'
        })
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.review_status, ManualObservation.ReviewStatus.APPROVED)
        self.assertEqual(entry.reviewed_by, self.analyst_user)

    # --------------------------------------------------------------------------
    # 5. Upgraded Module Views Tests
    # --------------------------------------------------------------------------
    def test_agriculture_module_views(self):
        """Crop catalog list and detail views render correctly."""
        resp_list = self.client.get(reverse('agriculture:crop_list'))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, 'Maize')

        resp_detail = self.client.get(reverse('agriculture:crop_detail', kwargs={'pk': self.crop_maize.pk}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, 'Maize')

    def test_geography_module_views(self):
        """District list and detail views render correctly."""
        resp_list = self.client.get(reverse('geography:district_list'))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, 'Musanze')

        resp_detail = self.client.get(reverse('geography:district_detail', kwargs={'pk': self.district_musanze.pk}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, 'Muhoza')

    def test_markets_module_views(self):
        """Market price monitoring page renders with explanatory empty/filled state."""
        market = MarketLocation.objects.create(name='Musanze Modern Market', district=self.district_musanze, is_major_hub=True)
        CommodityPrice.objects.create(
            market=market, crop=self.crop_maize,
            price_per_kg_rwf=Decimal('460.0'), date_recorded=timezone.now().date()
        )
        resp = self.client.get(reverse('markets:market_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Musanze Modern Market')
        self.assertContains(resp, '460.0')

    def test_surveys_farmers_inputs_modules(self):
        """Surveys, farmers, and inputs catalog pages resolve with status 200."""
        self.assertEqual(self.client.get(reverse('surveys:survey_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('farmers:farmer_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('inputs:input_list')).status_code, 200)

    # --------------------------------------------------------------------------
    # 6. API Endpoints Tests
    # --------------------------------------------------------------------------
    def test_indicators_json_apis(self):
        """Indicators REST endpoints return structured JSON."""
        resp_sum = self.client.get(reverse('indicators:api_summary'), {'year': 2025, 'season': 'A'})
        self.assertEqual(resp_sum.status_code, 200)
        data_sum = resp_sum.json()
        self.assertEqual(data_sum['status'], 'success')
        self.assertEqual(data_sum['data']['weighted_yield_kg_per_ha'], 4000.0)

        resp_dist = self.client.get(reverse('indicators:api_districts'), {'year': 2025, 'season': 'A', 'crop': 'Maize'})
        self.assertEqual(resp_dist.status_code, 200)
        data_dist = resp_dist.json()
        self.assertEqual(data_dist['status'], 'success')
        self.assertEqual(len(data_dist['data']), 1)
        self.assertEqual(data_dist['data'][0]['district_name'], 'Musanze')

    def test_drf_viewsets_serialization(self):
        """DRF viewsets return valid structured JSON without exposing unauthorized fields."""
        resp = self.client.get('/api/districts/')
        self.assertEqual(resp.status_code, 200)
        results = resp.json().get('results', resp.json())
        self.assertTrue(len(results) >= 2)
        first = results[0]
        self.assertIn('name', first)
        self.assertIn('province_name', first)
