"""
Read-only inspection of database records for Milestone 2 audit.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.geography.models import Province, District, Sector
from apps.agriculture.models import Crop, CropCategory, AgriculturalSeason
from apps.accounts.models import User
from apps.data_management.models import DataSource, ImportBatch, StagingSASProduction, ValidatedObservation, ManualObservation, DataQualityIssue
from django.db.models import Count

print("=== GEOGRAPHY ===")
print("Provinces:", Province.objects.count())
print("Districts:", District.objects.count())
print("Sectors:", Sector.objects.count())

print("\n=== AGRICULTURE ===")
print("CropCategories:", CropCategory.objects.count())
print("Crops (total):", Crop.objects.count())
print("Priority Crops:", Crop.objects.filter(is_priority_crop=True).count())
print("Seasons:", AgriculturalSeason.objects.count())

print("\n=== USERS ===")
print("Users:", User.objects.count())
for u in User.objects.all()[:10]:
    print(f"  User: {u.username}, Role: {u.role}")

print("\n=== DATA MANAGEMENT ===")
print("DataSources:", DataSource.objects.count())
for ds in DataSource.objects.all():
    print(f"  Source: {ds.source_type} ({ds.name})")

print("ImportBatches:", ImportBatch.objects.count())
for b in ImportBatch.objects.all():
    print(f"  Batch #{b.id}: {b.filename}, Status: {b.status}, Rows: {b.total_rows}, Accepted: {b.rows_accepted}, Rejected: {b.rows_rejected}, Checksum: {b.file_checksum[:12]}...")

print("StagingSASProduction:", StagingSASProduction.objects.count())
print("ValidatedObservation (total):", ValidatedObservation.objects.count())
for p in ValidatedObservation.objects.values('provenance', 'season__year', 'season__season').annotate(cnt=Count('id')):
    print(f"  Provenance: {p['provenance']}, Season: {p['season__year']}{p['season__season']}, Count: {p['cnt']}")

print("ManualObservation:", ManualObservation.objects.count())
for m in ManualObservation.objects.values('review_status').annotate(cnt=Count('id')):
    print(f"  Status: {m['review_status']}, Count: {m['cnt']}")

print("DataQualityIssue:", DataQualityIssue.objects.count())
for q in DataQualityIssue.objects.values('severity').annotate(cnt=Count('id')):
    print(f"  Severity: {q['severity']}, Count: {q['cnt']}")
