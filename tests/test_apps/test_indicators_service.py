"""
Unit tests for AgriLens Statistical Indicators, Weighted Estimators, and Productivity Gap.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase

from apps.geography.models import Province, District
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation
from apps.indicators.services import IndicatorService


class IndicatorServiceUnitTests(TestCase):
    def setUp(self):
        # Province & Districts
        self.prov = Province.objects.create(name='Northern Province', code='01')
        self.dist1 = District.objects.create(name='Musanze', code='13', province=self.prov)
        self.dist2 = District.objects.create(name='Burera', code='14', province=self.prov)

        # Seasons
        self.season2024a = AgriculturalSeason.objects.create(
            year=2024, season='A',
            start_date=date(2023, 9, 1), end_date=date(2024, 2, 28)
        )
        self.season2025a = AgriculturalSeason.objects.create(
            year=2025, season='A',
            start_date=date(2024, 9, 1), end_date=date(2025, 2, 28)
        )

        # Crop
        cat = CropCategory.objects.create(name='Cereals')
        self.crop_maize = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)

        # Data sources & batches
        self.ds2024 = DataSource.objects.create(name='SAS 2024', source_type='NISR_SAS_2024', is_official_survey=True)
        self.batch2024 = ImportBatch.objects.create(source=self.ds2024, filename='sas24.sav')

        self.ds2025 = DataSource.objects.create(name='SAS 2025', source_type='NISR_SAS_2025', is_official_survey=True)
        self.batch2025 = ImportBatch.objects.create(source=self.ds2025, filename='sas25.sav')

    def test_weighted_yield_calculation(self):
        """
        Verify that weighted yield is calculated properly:
        Plot 1: Area = 1.0 ha, Prod = 3,000 kg, Weight = 2.0 -> Weighted Area = 2.0, Weighted Prod = 6,000
        Plot 2: Area = 2.0 ha, Prod = 4,000 kg, Weight = 1.0 -> Weighted Area = 2.0, Weighted Prod = 4,000
        Sum Weighted Prod = 10,000 kg. Sum Weighted Area = 4.0 ha.
        Expected Weighted Yield = 10,000 / 4.0 = 2,500.0 kg/ha
        """
        ValidatedObservation.objects.create(
            batch=self.batch2025, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist1, crop=self.crop_maize, source_record_id='REC1',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('3000.0'),
            calculated_yield_kg_per_ha=Decimal('3000.0'), sampling_weight=Decimal('2.0'),
            is_improved_seed=True, uses_inorganic_fertilizer=True
        )
        ValidatedObservation.objects.create(
            batch=self.batch2025, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist1, crop=self.crop_maize, source_record_id='REC2',
            plot_area_ha=Decimal('2.0'), total_production_kg=Decimal('4000.0'),
            calculated_yield_kg_per_ha=Decimal('2000.0'), sampling_weight=Decimal('1.0'),
            is_improved_seed=False, uses_inorganic_fertilizer=False
        )

        summary = IndicatorService.get_national_summary(year=2025, season_code='A')
        self.assertEqual(summary['total_plots'], 2)
        self.assertEqual(summary['weighted_yield_kg_per_ha'], 2500.00)
        self.assertEqual(summary['adoption_rates']['improved_seed'], 50.0)
        self.assertEqual(summary['adoption_rates']['inorganic_fertilizer'], 50.0)

    def test_empty_dataset_zero_division_guard(self):
        """Empty season should safely return zero metrics without ZeroDivisionError."""
        summary = IndicatorService.get_national_summary(year=2030, season_code='C')
        self.assertEqual(summary['total_plots'], 0)
        self.assertEqual(summary['weighted_yield_kg_per_ha'], 0.0)
        self.assertEqual(summary['total_production_mt'], 0.0)

    def test_productivity_gap_benchmarking(self):
        """District ranking and productivity gap computation."""
        # Musanze (High yield: 4,000 kg/ha)
        ValidatedObservation.objects.create(
            batch=self.batch2025, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist1, crop=self.crop_maize, source_record_id='P1',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('4000.0'),
            calculated_yield_kg_per_ha=Decimal('4000.0'), sampling_weight=Decimal('1.0'),
            is_irrigated=True
        )
        # Burera (Lower yield: 2,000 kg/ha)
        ValidatedObservation.objects.create(
            batch=self.batch2025, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist2, crop=self.crop_maize, source_record_id='P2',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('2000.0'),
            calculated_yield_kg_per_ha=Decimal('2000.0'), sampling_weight=Decimal('1.0'),
            is_irrigated=False
        )

        gap = IndicatorService.get_productivity_gap(crop_name='Maize', year=2025, season_code='A')
        self.assertIsNotNone(gap)
        self.assertEqual(gap['benchmark']['district_name'], 'Musanze')
        self.assertEqual(gap['lagging']['district_name'], 'Burera')
        self.assertEqual(gap['gap_percentage'], -50.0) # (2000 - 4000) / 4000 = -50%
        self.assertEqual(gap['yield_difference_kg_per_ha'], 2000.0)

    def test_yoy_comparison_filters_by_crop(self):
        """YoY comparison must calculate growth specifically for the requested crop."""
        cat_legume = CropCategory.objects.create(name='Legumes')
        crop_beans = Crop.objects.create(name='Bush Beans', category=cat_legume)

        # 2024 Maize: yield = 2,000 kg/ha
        ValidatedObservation.objects.create(
            batch=self.batch2024, provenance='NISR_SAS_2024', season=self.season2024a,
            district=self.dist1, crop=self.crop_maize, source_record_id='Y24_M',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('2000.0'),
            calculated_yield_kg_per_ha=Decimal('2000.0'), sampling_weight=Decimal('1.0')
        )
        # 2024 Beans: yield = 5,000 kg/ha (should NOT affect Maize YoY!)
        ValidatedObservation.objects.create(
            batch=self.batch2024, provenance='NISR_SAS_2024', season=self.season2024a,
            district=self.dist1, crop=crop_beans, source_record_id='Y24_B',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('5000.0'),
            calculated_yield_kg_per_ha=Decimal('5000.0'), sampling_weight=Decimal('1.0')
        )

        # 2025 Maize: yield = 2,500 kg/ha -> Growth = +25%
        ValidatedObservation.objects.create(
            batch=self.batch2025, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist1, crop=self.crop_maize, source_record_id='Y25_M',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('2500.0'),
            calculated_yield_kg_per_ha=Decimal('2500.0'), sampling_weight=Decimal('1.0')
        )

        yoy_maize = IndicatorService.get_year_over_year_comparison(crop_name='Maize', season_code='A')
        self.assertEqual(yoy_maize['year_2024']['weighted_yield_kg_per_ha'], 2000.0)
        self.assertEqual(yoy_maize['year_2025']['weighted_yield_kg_per_ha'], 2500.0)
        self.assertEqual(yoy_maize['yield_growth_percentage'], 25.0)

    def test_district_rankings_min_plots_threshold(self):
        """Districts with fewer than min_plots should be filtered out."""
        # Musanze has 1 plot
        ValidatedObservation.objects.create(
            batch=self.batch2025, provenance='NISR_SAS_2025', season=self.season2025a,
            district=self.dist1, crop=self.crop_maize, source_record_id='TH1',
            plot_area_ha=Decimal('1.0'), total_production_kg=Decimal('4000.0'),
            calculated_yield_kg_per_ha=Decimal('4000.0'), sampling_weight=Decimal('1.0')
        )

        rankings_all = IndicatorService.get_district_rankings(crop_name='Maize', year=2025, season_code='A', min_plots=1)
        self.assertEqual(len(rankings_all), 1)

        rankings_min5 = IndicatorService.get_district_rankings(crop_name='Maize', year=2025, season_code='A', min_plots=5)
        self.assertEqual(len(rankings_min5), 0) # Musanze excluded because it has < 5 plots

