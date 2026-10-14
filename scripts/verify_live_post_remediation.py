import os, sys, django
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.data_management.models import ImportBatch, StagingSASProduction, ValidatedObservation
from apps.indicators.services import IndicatorService
from django.db import IntegrityError

print("=== POST-REMEDIATION LIVE DATABASE VERIFICATION ===\n")

# 1. Row counts
print("1. Table counts:")
print(f"   Total ImportBatch: {ImportBatch.objects.count()}")
print(f"   Total StagingSASProduction: {StagingSASProduction.objects.count()}")
print(f"   Total ValidatedObservation: {ValidatedObservation.objects.count()}")

print("\n2. Batches breakdown:")
for b in ImportBatch.objects.all().order_by('id'):
    stg_c = StagingSASProduction.objects.filter(batch=b).count()
    val_c = ValidatedObservation.objects.filter(batch=b).count()
    print(f"   Batch #{b.id} ({b.filename}): Staged={stg_c}, Validated={val_c}, Status={b.status}, Skipped={b.rows_skipped}")
    print(f"     Summary: {b.summary_notes[:75]}...")

# 3. Test uniqueness constraint enforcement
print("\n3. Testing PostgreSQL UniqueConstraint Enforcement:")
sample_obs = ValidatedObservation.objects.first()
try:
    ValidatedObservation.objects.create(
        batch=sample_obs.batch,
        provenance=sample_obs.provenance,
        season=sample_obs.season,
        district=sample_obs.district,
        crop=sample_obs.crop,
        source_record_id=sample_obs.source_record_id, # Exact duplicate
        plot_area_ha=sample_obs.plot_area_ha,
        total_production_kg=sample_obs.total_production_kg,
        calculated_yield_kg_per_ha=sample_obs.calculated_yield_kg_per_ha,
        sampling_weight=sample_obs.sampling_weight,
    )
    print("   ERROR: Duplicate insertion was NOT blocked!")
except IntegrityError as e:
    print("   SUCCESS: Duplicate insertion strictly blocked by PostgreSQL!")
    print(f"   IntegrityError: {str(e).strip()[:100]}...")

# 4. Agricultural indicators recalculation
print("\n4. Recalculating Agricultural Indicators:")
s24 = IndicatorService.get_national_summary(year=2024, season_code='A')
s25 = IndicatorService.get_national_summary(year=2025, season_code='A')
yoy_maize = IndicatorService.get_year_over_year_comparison(crop_name='Maize', season_code='A')

print("   2024A Summary:")
print(f"     Plots: {s24['total_plots']}")
print(f"     Total Prod (MT): {s24['total_production_mt']}")
print(f"     Total Area (ha): {s24['total_area_ha']}")
print(f"     Weighted Yield: {s24['weighted_yield_kg_per_ha']} kg/ha")
print(f"     Loss Rate: {s24['loss_rate_percentage']}%")
print(f"     Adoption: {s24['adoption_rates']}")
print(f"     Availability: {s24['practice_availability']}")

print("\n   2025A Summary (Clean Authoritative):")
print(f"     Plots: {s25['total_plots']}")
print(f"     Total Prod (MT): {s25['total_production_mt']}")
print(f"     Total Area (ha): {s25['total_area_ha']}")
print(f"     Weighted Yield: {s25['weighted_yield_kg_per_ha']} kg/ha")
print(f"     Loss Rate: {s25['loss_rate_percentage']}%")
print(f"     Adoption: {s25['adoption_rates']}")
print(f"     Availability: {s25['practice_availability']}")

print("\n   Maize Year-Over-Year:")
print(f"     2024 Yield: {yoy_maize['year_2024']['weighted_yield_kg_per_ha']} kg/ha")
print(f"     2025 Yield: {yoy_maize['year_2025']['weighted_yield_kg_per_ha']} kg/ha")
print(f"     Clean YOY Growth: {yoy_maize['yield_growth_percentage']}%")
