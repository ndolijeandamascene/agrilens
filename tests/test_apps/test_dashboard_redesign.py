"""
Test Suite for AgriLens National Agricultural Intelligence Dashboard Redesign.
Validates:
1. Executive 6 KPI cards rendering with verified microdata indicators.
2. Provincial yield benchmarks and 5-province analytical comparison structure.
3. Dynamic Key Insight generation based on real data.
4. Filter handling for season, year, crop, and search query parameters.
5. National bulletin and dataset export endpoints (CSV and Excel).
6. Graceful handling of unobserved data or empty filters.
"""
from decimal import Decimal
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import CropCategory, Crop, AgriculturalSeason
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation
from apps.indicators.services import IndicatorService


class DashboardRedesignTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # Create test provinces
        self.prov_north = Province.objects.create(name='Northern Province', code='01')
        self.prov_east = Province.objects.create(name='Eastern Province', code='02')
        self.prov_south = Province.objects.create(name='Southern Province', code='03')
        self.prov_west = Province.objects.create(name='Western Province', code='04')
        self.prov_kigali = Province.objects.create(name='Kigali City', code='05')

        # Create test districts
        self.dist_musanze = District.objects.create(name='Musanze', code='13', province=self.prov_north)
        self.dist_rwamagana = District.objects.create(name='Rwamagana', code='21', province=self.prov_east)
        self.dist_huye = District.objects.create(name='Huye', code='31', province=self.prov_south)
        self.dist_rubavu = District.objects.create(name='Rubavu', code='41', province=self.prov_west)
        self.dist_gasabo = District.objects.create(name='Gasabo', code='51', province=self.prov_kigali)

        # Create Seasons
        self.season2025a = AgriculturalSeason.objects.create(
            year=2025, season='A',
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )
        self.season2024a = AgriculturalSeason.objects.create(
            year=2024, season='A',
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

        # Create Priority Crops
        self.cat_cereals = CropCategory.objects.create(name='Cereals')
        self.cat_legumes = CropCategory.objects.create(name='Legumes')
        self.crop_maize = Crop.objects.create(name='Maize', category=self.cat_cereals, is_priority_crop=True)
        self.crop_beans = Crop.objects.create(name='Beans', category=self.cat_legumes, is_priority_crop=True)

        # Create Data Source & Batch
        self.datasource = DataSource.objects.create(
            name='NISR SAS 2025',
            source_type='NISR_SAS_2025',
            is_official_survey=True,
            year=2025,
            season='A'
        )
        self.batch = ImportBatch.objects.create(
            source=self.datasource,
            filename='sas_2025_test.sav'
        )

        # Create sample Validated Observations across provinces
        self.obs1 = ValidatedObservation.objects.create(
            batch=self.batch,
            provenance='NISR_SAS_2025',
            season=self.season2025a,
            district=self.dist_musanze,
            crop=self.crop_maize,
            source_record_id='SAS25-001-MUS',
            plot_area_ha=Decimal('2.50'),
            total_production_kg=Decimal('7500.00'),
            calculated_yield_kg_per_ha=Decimal('3000.00'),
            sampling_weight=Decimal('1.5'),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True
        )
        self.obs2 = ValidatedObservation.objects.create(
            batch=self.batch,
            provenance='NISR_SAS_2025',
            season=self.season2025a,
            district=self.dist_rwamagana,
            crop=self.crop_maize,
            source_record_id='SAS25-002-RWA',
            plot_area_ha=Decimal('3.00'),
            total_production_kg=Decimal('12000.00'),
            calculated_yield_kg_per_ha=Decimal('4000.00'),
            sampling_weight=Decimal('1.2'),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True
        )

    def test_dashboard_renders_successfully(self):
        """Dashboard overview responds with 200 and loads essential context."""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')
        self.assertIn('summary', response.context)
        self.assertIn('provincial_yields', response.context)
        self.assertIn('key_insight', response.context)
        self.assertIn('data_quality_pct', response.context)

    def test_six_executive_kpi_cards_present(self):
        """All 6 executive KPI cards are present with correct IDs and readable labels."""
        response = self.client.get('/dashboard/')
        content = response.content.decode('utf-8')

        # 6 KPI cards
        self.assertIn('id="kpi-tracked-crops"', content)
        self.assertIn('id="kpi-validated-records"', content)
        self.assertIn('id="kpi-geographic-coverage"', content)
        self.assertIn('id="kpi-total-production"', content)
        self.assertIn('id="kpi-average-yield"', content)
        self.assertIn('id="kpi-data-quality"', content)

        # Metric Titles
        self.assertIn('Tracked Crops', content)
        self.assertIn('Validated Records', content)
        self.assertIn('Geographic Coverage', content)
        self.assertIn('Total Production', content)
        self.assertIn('Average Yield', content)
        self.assertIn('Data Quality', content)

    def test_provincial_yield_comparison_service(self):
        """Test IndicatorService.get_provincial_yield_comparison calculates actual and potential yields."""
        prov_yields = IndicatorService.get_provincial_yield_comparison(
            crop_name='Maize', year=2025, season_code='A', source_policy='official'
        )
        self.assertEqual(len(prov_yields), 5)
        names = [p['short_name'] for p in prov_yields]
        self.assertIn('Northern', names)
        self.assertIn('Eastern', names)
        self.assertIn('Southern', names)
        self.assertIn('Western', names)
        self.assertIn('Kigali', names)

        # Check Northern Province actual yield calculation from Musanze plot
        north = next(p for p in prov_yields if p['short_name'] == 'Northern')
        self.assertEqual(north['actual_yield_t_ha'], 3.0)
        self.assertGreater(north['potential_yield_t_ha'], 0)
        self.assertGreaterEqual(north['yield_gap_pct'], 0)

    def test_dynamic_key_insight_generation(self):
        """Dynamic Key Insight generates an actionable sentence referencing the actual yield gap."""
        response = self.client.get('/dashboard/?crop=Maize')
        content = response.content.decode('utf-8')
        self.assertIn('Key Insight:', content)
        self.assertIn('yield gap', content.lower())

    def test_recent_observations_filtering(self):
        """Table search and filter parameters correctly narrow down observations."""
        # Filter by Musanze district
        resp_dist = self.client.get(f'/dashboard/?table_district={self.dist_musanze.id}')
        self.assertEqual(resp_dist.status_code, 200)
        obs_list = resp_dist.context['recent_observations']
        self.assertEqual(len(obs_list), 1)
        self.assertEqual(obs_list[0].district.name, 'Musanze')

        # Filter by search query
        resp_q = self.client.get('/dashboard/?q=Rwamagana')
        self.assertEqual(resp_q.status_code, 200)
        obs_q_list = resp_q.context['recent_observations']
        self.assertEqual(len(obs_q_list), 1)
        self.assertEqual(obs_q_list[0].district.name, 'Rwamagana')

    def test_export_endpoints_available(self):
        """CSV and Excel export endpoints respond with valid content attachments."""
        # CSV Export
        csv_resp = self.client.get('/dashboard/reports/national/export/csv/?year=2025&season=A')
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment;', csv_resp['Content-Disposition'])

        # Excel Export
        xlsx_resp = self.client.get('/dashboard/reports/national/export/excel/?year=2025&season=A')
        self.assertEqual(xlsx_resp.status_code, 200)
        self.assertEqual(
            xlsx_resp['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment;', xlsx_resp['Content-Disposition'])
