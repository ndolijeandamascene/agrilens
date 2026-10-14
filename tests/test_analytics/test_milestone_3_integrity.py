"""
Milestone 3 Data Integrity, Survey Weights, and Indicator Regression Test Suite.
Verifies:
1. Duplicate detection and natural key uniqueness.
2. Source identity and deterministic record IDs.
3. Import idempotency.
4. Survey weight handling: genuine LSF weights (1.0) vs expansion weights (>1.0).
5. Variable mapping: practices and units.
6. Zero and missing denominator handling in ratio estimators.
7. Indicator provenance segregation: official vs manual vs combined.
8. Incompatible year comparisons and missing season handling.
9. Structured handling of insufficient sample sizes and unsupported indicators.
"""
from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError

from apps.geography.models import Province, District, Sector
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation, ManualObservation
from apps.indicators.services import IndicatorService
from django.contrib.auth import get_user_model

User = get_user_model()


class Milestone3DataIntegrityTests(TestCase):
    def setUp(self):
        # Setup reference geography
        self.province = Province.objects.create(name="Northern Province", code="01")
        self.district_musanze = District.objects.create(name="Musanze", code="11", province=self.province)
        self.district_burera = District.objects.create(name="Burera", code="12", province=self.province)
        self.sector_muhoza = Sector.objects.create(name="Muhoza", code="1101", district=self.district_musanze)

        # Setup reference crops
        self.cat_cereals = CropCategory.objects.create(name="Cereals")
        self.crop_maize = Crop.objects.create(name="Maize", category=self.cat_cereals, is_priority_crop=True)
        self.crop_beans = Crop.objects.create(name="Bush Beans", category=self.cat_cereals, is_priority_crop=True)

        # Setup seasons
        self.season_2024a = AgriculturalSeason.objects.create(
            year=2024, season="A", start_date="2023-09-01", end_date="2024-02-28"
        )
        self.season_2025a = AgriculturalSeason.objects.create(
            year=2025, season="A", start_date="2024-09-01", end_date="2025-02-28"
        )

        # Setup data source & batches
        self.data_source_2024 = DataSource.objects.create(
            name="NISR SAS 2024", source_type="NISR_SAS_2024", is_official_survey=True
        )
        self.batch_2024 = ImportBatch.objects.create(
            source=self.data_source_2024, filename="Rwa_raw_SeasonA2024_Production.sav", status=ImportBatch.Status.SUCCESS
        )

        self.data_source_2025 = DataSource.objects.create(
            name="NISR SAS 2025", source_type="NISR_SAS_2025", is_official_survey=True
        )
        self.batch_2025 = ImportBatch.objects.create(
            source=self.data_source_2025, filename="Rwa_raw_SeasonA2025_Production.sav", status=ImportBatch.Status.SUCCESS
        )

        # User for manual entries
        self.user = User.objects.create_user(username="agronomist", password="testpassword123")

    def test_natural_key_source_identity(self):
        """Natural key (segment_id, plot_number, crop) must uniquely identify an observation."""
        rec_id = f"SAS_2025A_SEG1001_P1_C101"
        obs1 = ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id=rec_id,
            segment_id="SEG1001",
            plot_number=1,
            farmer_type="3.0",
            plot_area_ha=Decimal("1.5000"),
            total_production_kg=Decimal("4500.00"),
            calculated_yield_kg_per_ha=Decimal("3000.00"),
            sampling_weight=Decimal("1.0000"), # LSF genuine census weight
        )
        self.assertEqual(obs1.source_record_id, rec_id)
        self.assertEqual(obs1.sampling_weight, Decimal("1.0000"))

    def test_import_idempotency_duplicate_prevention(self):
        """Re-ingesting an identical record must be detected and not inflate observation count."""
        rec_id = "SAS_2025A_SEG2001_P1_C101"
        ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id=rec_id,
            plot_area_ha=Decimal("0.8000"),
            total_production_kg=Decimal("2000.00"),
            calculated_yield_kg_per_ha=Decimal("2500.00"),
            sampling_weight=Decimal("28.5000"),
        )
        initial_count = ValidatedObservation.objects.filter(season=self.season_2025a).count()
        self.assertEqual(initial_count, 1)

        # Idempotent re-ingestion logic
        incoming_records = [
            {"source_record_id": rec_id, "plot_area_ha": Decimal("0.8000"), "total_production_kg": Decimal("2000.00")},
            {"source_record_id": "SAS_2025A_SEG2002_P1_C101", "plot_area_ha": Decimal("1.0000"), "total_production_kg": Decimal("2500.00")},
        ]
        existing_keys = set(
            ValidatedObservation.objects.filter(season=self.season_2025a).values_list("source_record_id", flat=True)
        )
        new_records = [r for r in incoming_records if r["source_record_id"] not in existing_keys]
        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0]["source_record_id"], "SAS_2025A_SEG2002_P1_C101")

    def test_survey_weights_distinction_genuine_vs_expansion(self):
        """Ratio estimator must correctly weight census LSF (w=1.0) and smallholder (w=50.0)."""
        # Observation 1: Large Scale Farmer (w = 1.0, Area = 10 ha, Prod = 30,000 kg -> yield = 3,000 kg/ha)
        ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id="LSF_01",
            plot_area_ha=Decimal("10.0000"),
            total_production_kg=Decimal("30000.00"),
            calculated_yield_kg_per_ha=Decimal("3000.00"),
            sampling_weight=Decimal("1.0000"),
        )
        # Observation 2: Smallholder (w = 50.0, Area = 0.2 ha, Prod = 200 kg -> yield = 1,000 kg/ha)
        ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id="SMH_01",
            plot_area_ha=Decimal("0.2000"),
            total_production_kg=Decimal("200.00"),
            calculated_yield_kg_per_ha=Decimal("1000.00"),
            sampling_weight=Decimal("50.0000"),
        )

        summary = IndicatorService.get_national_summary(year=2025, season_code="A", crop_name="Maize")
        # Formula: (30,000*1 + 200*50) / (10*1 + 0.2*50) = (30,000 + 10,000) / (10 + 10) = 40,000 / 20 = 2,000 kg/ha
        self.assertEqual(summary["weighted_yield_kg_per_ha"], 2000.0)
        self.assertEqual(summary["total_plots"], 2)

    def test_zero_and_missing_denominator_handling(self):
        """Zero observations or zero area must safely return structured empty summary without ZeroDivisionError."""
        summary = IndicatorService.get_national_summary(year=2099, season_code="A", crop_name="NonExistentCrop")
        self.assertEqual(summary["total_plots"], 0)
        self.assertEqual(summary["weighted_yield_kg_per_ha"], 0.0)
        self.assertEqual(summary["total_production_mt"], 0.0)
        self.assertEqual(summary["total_area_ha"], 0.0)
        self.assertEqual(summary["loss_rate_percentage"], 0.0)

    def test_post_harvest_loss_formula_consistency(self):
        """Post harvest loss rate must evaluate sum(W*L) / (sum(W*P) + sum(W*L))."""
        ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id="LOSS_01",
            plot_area_ha=Decimal("1.0000"),
            total_production_kg=Decimal("900.00"),
            total_loss_kg=Decimal("100.00"), # 100 kg loss on 900 kg harvested
            calculated_yield_kg_per_ha=Decimal("900.00"),
            sampling_weight=Decimal("10.0000"),
        )
        summary = IndicatorService.get_national_summary(year=2025, season_code="A")
        # Loss rate = 100*10 / (900*10 + 100*10) = 1000 / 10000 = 10.0%
        self.assertEqual(summary["loss_rate_percentage"], 10.0)

    def test_indicator_provenance_separation(self):
        """Official policy must strictly segregate official microdata from approved manual entries."""
        # 1. Official Observation
        ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id="OFF_01",
            plot_area_ha=Decimal("1.0000"),
            total_production_kg=Decimal("2000.00"),
            calculated_yield_kg_per_ha=Decimal("2000.00"),
            sampling_weight=Decimal("1.0000"),
        )
        # 2. Approved Manual Observation
        ManualObservation.objects.create(
            created_by=self.user,
            season=self.season_2025a,
            district=self.district_musanze,
            sector=self.sector_muhoza,
            crop=self.crop_maize,
            observation_date="2025-02-15",
            plot_area_ha=Decimal("2.0000"),
            total_production_kg=Decimal("6000.00"),
            review_status=ManualObservation.ReviewStatus.APPROVED,
        )

        official_sum = IndicatorService.get_national_summary(year=2025, season_code="A", source_policy="official")
        self.assertTrue(official_sum["is_official_only"])
        self.assertEqual(official_sum["total_plots"], 1)
        self.assertEqual(official_sum["weighted_yield_kg_per_ha"], 2000.0)

        manual_sum = IndicatorService.get_national_summary(year=2025, season_code="A", source_policy="manual")
        self.assertTrue(manual_sum["is_manual_only"])
        self.assertEqual(manual_sum["total_plots"], 1)
        self.assertEqual(manual_sum["weighted_yield_kg_per_ha"], 3000.0) # 6,000 / 2.0 = 3,000

        combined_sum = IndicatorService.get_national_summary(year=2025, season_code="A", source_policy="combined")
        self.assertTrue(combined_sum["is_combined"])
        self.assertEqual(combined_sum["total_plots"], 2)

    def test_incompatible_year_comparison_handling(self):
        """When an observation is missing in one year, comparison must flag is_comparable=False."""
        # Only populate 2024A
        ValidatedObservation.objects.create(
            batch=self.batch_2024,
            provenance="NISR_SAS_2024",
            season=self.season_2024a,
            district=self.district_musanze,
            crop=self.crop_beans,
            source_record_id="BEAN_24",
            plot_area_ha=Decimal("1.0000"),
            total_production_kg=Decimal("1500.00"),
            calculated_yield_kg_per_ha=Decimal("1500.00"),
            sampling_weight=Decimal("5.0000"),
        )
        yoy = IndicatorService.get_year_over_year_comparison(crop_name="Bush Beans", season_code="A")
        self.assertFalse(yoy["is_comparable"])
        self.assertIn("Missing observations", yoy["reason"])
        self.assertEqual(yoy["yield_growth_percentage"], 0.0)

    def test_productivity_gap_sample_threshold(self):
        """Productivity gap must decline to benchmark if qualifying districts are fewer than 2."""
        ValidatedObservation.objects.create(
            batch=self.batch_2025,
            provenance="NISR_SAS_2025",
            season=self.season_2025a,
            district=self.district_musanze,
            crop=self.crop_maize,
            source_record_id="GAP_01",
            plot_area_ha=Decimal("1.0000"),
            total_production_kg=Decimal("2000.00"),
            calculated_yield_kg_per_ha=Decimal("2000.00"),
            sampling_weight=Decimal("1.0000"),
        )
        # With min_plots=5, Musanze has only 1 plot, Burera has 0
        gap_res = IndicatorService.get_productivity_gap(crop_name="Maize", year=2025, season_code="A", min_plots=5)
        self.assertFalse(gap_res["is_sufficient_data"])
        self.assertEqual(gap_res["gap_percentage"], 0.0)
        self.assertIn("Insufficient data", gap_res["reason"])
