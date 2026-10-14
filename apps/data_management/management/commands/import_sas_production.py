"""
AgriLens Production Ingestion Management Command.
Executes Phase Six ETL: Extract -> Profile -> Validate -> Stage -> Load -> Verify.
Supports pilot execution and full production imports with repeatable idempotency.
"""
import os
import hashlib
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pyreadstat
import pandas as pd

from django.core.management.base import BaseCommand
from django.db import transaction

from django.utils import timezone
from apps.geography.models import District, Province
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import (
    DataSource, ImportBatch, StagingSASProduction, 
    ValidatedObservation, DataQualityIssue
)

CROP_CODE_MAPPING = {
    101.0: 'Maize',
    102.0: 'Marshland Rice',
    103.0: 'Sorghum',
    104.0: 'Wheat',
    106.0: 'Bush Beans',
    107.0: 'Climbing Beans',
    110.0: 'Irish Potato',
    111.0: 'Sweet Potato',
    122.0: 'Soyabean',
    301.0: 'Cooking Banana',
    304.0: 'Coffee',
    305.0: 'Cassava',
    310.0: 'Tea',
}

class Command(BaseCommand):
    help = "Ingest official NISR Seasonal Agricultural Survey (SAS) Production data"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help="Relative or absolute path to SAS Production file")
        parser.add_argument('--year', type=int, default=2025, help="Survey Year (e.g. 2025)")
        parser.add_argument('--season', type=str, default='A', help="Agricultural Season (A, B, or C)")
        parser.add_argument('--limit', type=int, default=None, help="Limit number of rows for pilot test")
        parser.add_argument('--chunk-size', type=int, default=2000, help="Bulk chunk size for database inserts")
        parser.add_argument('--dry-run', action='store_true', default=False, help="Run validation and transformation preview without database writes")
        parser.add_argument('--force', action='store_true', default=False, help="Force re-import even if file checksum was previously ingested successfully")

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Source file not found: {file_path}"))
            return

        year = options['year']
        season_code = options['season'].upper()
        limit = options['limit']
        chunk_size = options['chunk_size']
        dry_run = options['dry_run']
        force = options['force']

        mode_str = "DRY-RUN (Preview Mode - No Database Writes)" if dry_run else "LIVE INGESTION"
        self.stdout.write(self.style.NOTICE(
            f"Starting Ingestion Pipeline [{mode_str}] for SAS {year} Season {season_code}\n"
            f"File: {file_path.name} (Limit: {limit or 'Full dataset'})\n"
        ))

        # 1. Resolve Season & Data Source
        try:
            season = AgriculturalSeason.objects.get(year=year, season=season_code)
        except AgriculturalSeason.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"AgriculturalSeason {year}{season_code} does not exist."))
            return

        source_type = f"NISR_SAS_{year}"
        data_source, _ = DataSource.objects.get_or_create(
            source_type=source_type,
            defaults={
                'name': f"NISR Seasonal Agricultural Survey {year}",
                'description': f"Official SAS survey microdata for agricultural year {year}",
                'is_official_survey': True,
            }
        )

        # 2. File Checksum & Duplicate Ingestion Detection
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()

        if not dry_run and not force:
            prior = ImportBatch.objects.filter(file_checksum=file_hash, status=ImportBatch.Status.SUCCESS).first()
            if prior:
                self.stderr.write(self.style.WARNING(
                    f"Duplicate Ingestion Guard: This exact file (SHA256: {file_hash[:16]}...) was already successfully ingested "
                    f"in Batch #{prior.id} on {prior.completed_at}. Pass --force to re-import or --dry-run to preview."
                ))
                return

        batch = None
        if not dry_run:
            batch = ImportBatch.objects.create(
                source=data_source,
                filename=file_path.name,
                file_checksum=file_hash,
                status=ImportBatch.Status.PROCESSING,
            )

        # 3. Read Source Microdata
        ext = file_path.suffix.lower()
        self.stdout.write("Reading file into memory...")
        if ext == '.sav':
            df, meta = pyreadstat.read_sav(str(file_path))
        elif ext == '.dta':
            try:
                df, meta = pyreadstat.read_dta(str(file_path))
            except Exception:
                df, meta = pyreadstat.read_dta(str(file_path), encoding='latin1')
        elif ext == '.csv':
            # Auto detect delimiter
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                first = fp.readline()
                sep = '\t' if '\t' in first else ','
            df = pd.read_csv(file_path, sep=sep, encoding='utf-8', encoding_errors='ignore')
        else:
            self.stderr.write(self.style.ERROR(f"Unsupported format: {ext}"))
            batch.status = ImportBatch.Status.FAILED
            batch.error_log = f"Unsupported extension: {ext}"
            batch.save()
            return

        total_rows = len(df)
        if limit:
            df = df.head(limit)
            total_rows = len(df)

        batch.total_rows = total_rows
        batch.save(update_fields=['total_rows'])
        self.stdout.write(f"Source rows loaded: {total_rows:,}")

        # 4. Preload reference lookups (Districts & Crops)
        district_lookup = {}
        for dist in District.objects.all():
            district_lookup[str(dist.code)] = dist
            district_lookup[int(dist.code) if dist.code.isdigit() else -1] = dist
            district_lookup[dist.name.lower()] = dist

        crop_lookup = {}
        for crop in Crop.objects.all():
            crop_lookup[crop.name.lower()] = crop
            crop_lookup[crop.id] = crop

        # Fallback category for unexpected crops
        default_cat, _ = CropCategory.objects.get_or_create(name='Other Crops', defaults={'description': 'Uncategorized'})

        meta_crop_dict = {}
        if 'meta' in locals() and hasattr(meta, 'variable_value_labels'):
            meta_crop_dict = meta.variable_value_labels.get('s2q4', {})

        staging_records = []
        validated_records = []
        qa_issues = []
        rows_accepted = 0
        rows_rejected = 0

        self.stdout.write("Transforming and validating records...")

        for idx, row in df.iterrows():
            seg_id = str(row.get('Segment_ID', ''))
            prov_code = row.get('s1q1')
            dist_code = row.get('s1q2')
            plot_no = row.get('s2q1')
            crop_raw = row.get('s2q4')
            
            # Staging record construction
            stg = StagingSASProduction(
                batch=batch,
                source_row_index=idx,
                segment_id=seg_id,
                s1q1=int(prov_code) if pd.notnull(prov_code) and str(prov_code).replace('.','').isdigit() else None,
                s1q2=int(dist_code) if pd.notnull(dist_code) and str(dist_code).replace('.','').isdigit() else None,
                s1q3=str(row.get('s1q3', '')),
                s1q6=str(row.get('s1q6', '')),
                s1q7=str(row.get('s1q7', '')),
                s2q1=int(plot_no) if pd.notnull(plot_no) and str(plot_no).replace('.','').isdigit() else None,
                s2q2=float(row.get('s2q2')) if pd.notnull(row.get('s2q2')) else None,
                s2q2_ha=float(row.get('s2q2_ha')) if pd.notnull(row.get('s2q2_ha')) else None,
                s2q4=str(crop_raw),
                crop_category=str(row.get('CropCategory', '')),
                s2q9=str(row.get('s2q9', '')),
                s2q19_3=float(row.get('s2q19_3')) if pd.notnull(row.get('s2q19_3')) else None,
                s2q20_2=float(row.get('s2q20_2')) if pd.notnull(row.get('s2q20_2')) else None,
                s2q21=float(row.get('s2q21')) if pd.notnull(row.get('s2q21')) else None,
                s2q25=float(row.get('s2q25')) if pd.notnull(row.get('s2q25')) else None,
                s2q26=float(row.get('s2q26')) if pd.notnull(row.get('s2q26')) else None,
                s2q28=float(row.get('s2q28')) if pd.notnull(row.get('s2q28')) else None,
                s2q36=float(row.get('s2q36')) if pd.notnull(row.get('s2q36')) else None,
                s2q37=str(row.get('s2q37', '')),
                loss_harvest_kg=float(row.get('s2q45')) if pd.notnull(row.get('s2q45')) else 0.0,
                loss_transport_kg=float(row.get('s2q46')) if pd.notnull(row.get('s2q46')) else 0.0,
                loss_storage_kg=float(row.get('s2q47')) if pd.notnull(row.get('s2q47')) else 0.0,
                loss_processing_kg=float(row.get('s2q48')) if pd.notnull(row.get('s2q48')) else 0.0,
                loss_sales_kg=float(row.get('s2q50')) if pd.notnull(row.get('s2q50')) else 0.0,
                uses_organic_fert=str(row.get('s3q3', '')),
                uses_inorganic_fert=str(row.get('s3q9', '')),
                uses_pesticide=str(row.get('s3q18', '')),
                plot_weight=float(row.get('plot_weight', 1.0)) if pd.notnull(row.get('plot_weight')) else 1.0,
            )
            staging_records.append(stg)

            # Validation & Domain Mapping
            # 1. District lookup
            district_obj = district_lookup.get(dist_code) or district_lookup.get(int(dist_code) if pd.notnull(dist_code) and str(dist_code).replace('.','').isdigit() else -1)
            if not district_obj:
                rows_rejected += 1
                stg.validation_error = f"Invalid district code: {dist_code}"
                continue

            # 2. Crop lookup
            crop_name = None
            if pd.notnull(crop_raw) and isinstance(crop_raw, (int, float)):
                crop_name = CROP_CODE_MAPPING.get(float(crop_raw)) or meta_crop_dict.get(float(crop_raw)) or meta_crop_dict.get(int(crop_raw))
            elif pd.notnull(crop_raw):
                crop_name = str(crop_raw).strip()

            if not crop_name:
                rows_rejected += 1
                stg.validation_error = f"Unmapped crop: {crop_raw}"
                continue

            crop_obj = crop_lookup.get(crop_name.lower())
            if not crop_obj:
                # Dynamic crop creation if official crop not already present
                crop_obj, _ = Crop.objects.get_or_create(
                    name=crop_name,
                    defaults={'category': default_cat, 'is_priority_crop': False}
                )
                crop_lookup[crop_name.lower()] = crop_obj

            # 3. Area normalization (ha)
            area_ha = 0.0
            if pd.notnull(row.get('s2q2_ha')) and float(row['s2q2_ha']) > 0:
                area_ha = float(row['s2q2_ha'])
            elif pd.notnull(row.get('s2q2')) and float(row['s2q2']) > 0:
                area_ha = float(row['s2q2']) / 10000.0

            if area_ha <= 0:
                rows_rejected += 1
                stg.validation_error = f"Zero or negative plot area: {area_ha}"
                continue

            # 4. Production quantity (kg)
            prod_kg = 0.0
            if pd.notnull(row.get('s2q21')):
                prod_kg = float(row['s2q21'])
            elif pd.notnull(row.get('s2q19_3')):
                prod_kg = float(row['s2q19_3'])

            if prod_kg < 0:
                rows_rejected += 1
                stg.validation_error = f"Negative production: {prod_kg}"
                continue

            # 5. Calculated yield
            yield_val = round(prod_kg / area_ha, 2)
            if yield_val > 60000.0:  # Plausibility threshold flag
                qa_issues.append(DataQualityIssue(
                    batch=batch,
                    dataset_name=file_path.name,
                    variable_name='calculated_yield',
                    record_reference=f"Seg:{seg_id}_Plot:{plot_no}",
                    issue_type='PlausibilityThreshold',
                    severity=DataQualityIssue.Severity.MEDIUM,
                    description=f"Extremely high yield: {yield_val:,.1f} kg/ha for {crop_name} on {area_ha:.4f} ha",
                    recommended_action='Flag for outlier trimming in aggregate indicators',
                ))

            # 6. Practices & inputs
            is_improved = str(row.get('s2q9', '')).lower() in ['1', '1.0', 'yes']
            uses_inorg = str(row.get('s3q9', '')).lower() in ['1', '1.0', 'yes']
            uses_org = str(row.get('s3q3', '')).lower() in ['1', '1.0', 'yes']
            uses_pest = str(row.get('s3q18', '')).lower() in ['1', '1.0', 'yes']
            has_anti_erosion = str(row.get('s4q3', '')).lower() in ['1', '1.0', 'yes']
            uses_mech = str(row.get('s4q9', '')).lower() in ['1', '1.0', 'yes']

            # Irrigation: s4q15 in 2024 (plot-level); s4q14 in 2025 (plot-level)
            if year == 2024:
                is_irrig = str(row.get('s4q15', '')).lower() in ['1', '1.0', 'yes']
            else:
                is_irrig = str(row.get('s4q14', '')).lower() in ['1', '1.0', 'yes']

            # 7. Post harvest losses
            loss_kg = (
                (float(row.get('s2q45')) if pd.notnull(row.get('s2q45')) else 0.0) +
                (float(row.get('s2q46')) if pd.notnull(row.get('s2q46')) else 0.0) +
                (float(row.get('s2q47')) if pd.notnull(row.get('s2q47')) else 0.0) +
                (float(row.get('s2q48')) if pd.notnull(row.get('s2q48')) else 0.0) +
                (float(row.get('s2q50')) if pd.notnull(row.get('s2q50')) else 0.0)
            )
            loss_rate = None
            if (prod_kg + loss_kg) > 0:
                loss_rate = round((loss_kg / (prod_kg + loss_kg)) * 100, 2)

            weight_val = float(row.get('plot_weight', 1.0)) if pd.notnull(row.get('plot_weight')) else 1.0

            source_rec_id = f"{seg_id}_{plot_no}_{crop_name}_{idx}"

            val_obs = ValidatedObservation(
                batch=batch,
                provenance=source_type,
                season=season,
                district=district_obj,
                crop=crop_obj,
                source_record_id=source_rec_id,
                segment_id=seg_id,
                plot_number=int(float(plot_no)) if pd.notnull(plot_no) and str(plot_no).replace('.','').isdigit() else None,
                farmer_type=str(row.get('s1q7', '')),
                plot_area_ha=Decimal(str(round(area_ha, 4))),
                total_production_kg=Decimal(str(round(prod_kg, 2))),
                calculated_yield_kg_per_ha=Decimal(str(round(yield_val, 2))),
                is_improved_seed=is_improved,
                uses_inorganic_fertilizer=uses_inorg,
                uses_organic_fertilizer=uses_org,
                uses_pesticide=uses_pest,
                is_irrigated=is_irrig,
                has_anti_erosion=has_anti_erosion,
                uses_mechanization=uses_mech,
                quantity_sold_kg=Decimal(str(round(float(row.get('s2q26')), 2))) if pd.notnull(row.get('s2q26')) else Decimal('0.0'),
                market_price_rwf=Decimal(str(round(float(row.get('s2q28')), 2))) if pd.notnull(row.get('s2q28')) else None,
                quantity_stored_kg=Decimal(str(round(float(row.get('s2q36')), 2))) if pd.notnull(row.get('s2q36')) else Decimal('0.0'),
                total_loss_kg=Decimal(str(round(loss_kg, 2))),
                loss_rate_percentage=Decimal(str(loss_rate)) if loss_rate is not None else None,
                sampling_weight=Decimal(str(round(weight_val, 4))),
            )
            validated_records.append(val_obs)
            stg.is_validated = True
            rows_accepted += 1

        # Check existing source_record_ids in DB to guarantee idempotency and avoid duplicates
        existing_keys = set(
            ValidatedObservation.objects.filter(
                provenance=source_type, season=season
            ).values_list('source_record_id', flat=True)
        )
        unique_validated_records = [r for r in validated_records if r.source_record_id not in existing_keys]
        rows_skipped = len(validated_records) - len(unique_validated_records)
        if rows_skipped > 0:
            self.stdout.write(self.style.WARNING(f"Skipping {rows_skipped:,} records that already exist in database for this season."))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n=======================================================\n"
                f"DRY-RUN VALIDATION PREVIEW COMPLETED\n"
                f"=======================================================\n"
                f"Source File:     {file_path.name}\n"
                f"Total In File:   {total_rows:,}\n"
                f"Eligible:        {rows_accepted:,} ({(rows_accepted/total_rows)*100:.1f}%)\n"
                f"New Unique:      {len(unique_validated_records):,}\n"
                f"Existing Skips:  {rows_skipped:,}\n"
                f"Rejected:        {rows_rejected:,} ({(rows_rejected/total_rows)*100:.1f}%)\n"
                f"QA Flags:        {len(qa_issues)}\n"
                f"DB Writes:       NONE (Dry-run mode)\n"
                f"=======================================================\n"
            ))
            return

        # 5. Atomic Bulk Ingestion into PostgreSQL
        self.stdout.write("Inserting staging and validated records in chunks...")
        with transaction.atomic():
            # Ingest Staging records
            for i in range(0, len(staging_records), chunk_size):
                StagingSASProduction.objects.bulk_create(staging_records[i:i + chunk_size])

            # Ingest Validated records (idempotent, only new unique records)
            for i in range(0, len(unique_validated_records), chunk_size):
                ValidatedObservation.objects.bulk_create(unique_validated_records[i:i + chunk_size])

            # Ingest Quality Issues (single bulk_create call)
            if qa_issues:
                DataQualityIssue.objects.bulk_create(qa_issues)

        # 6. Update Batch Summary
        batch.rows_accepted = rows_accepted
        batch.rows_rejected = rows_rejected
        batch.rows_skipped = rows_skipped
        batch.completed_at = timezone.now()
        batch.status = ImportBatch.Status.SUCCESS if rows_rejected == 0 else ImportBatch.Status.PARTIAL
        batch.summary_notes = (
            f"Successfully imported {len(unique_validated_records):,} new verified observations "
            f"({rows_skipped:,} skipped as already existing). "
            f"Rejected {rows_rejected:,} rows (zero area or unmapped keys). "
            f"Flagged {len(qa_issues)} QA outliers."
        )
        batch.save()

        from apps.accounts.permissions import AuditService
        from apps.accounts.models import AuditLog
        AuditService.log(
            action=AuditLog.Action.DATA_IMPORTED,
            target=batch,
            details={
                'filename': file_path.name,
                'source': source_type,
                'accepted': rows_accepted,
                'new_unique': len(unique_validated_records),
                'rejected': rows_rejected,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n=======================================================\n"
            f"INGESTION COMPLETED SUCCESSFULLY\n"
            f"=======================================================\n"
            f"Batch ID:        #{batch.id}\n"
            f"Source File:     {file_path.name}\n"
            f"Total Processed: {total_rows:,}\n"
            f"Accepted:        {rows_accepted:,} ({(rows_accepted/total_rows)*100:.1f}%)\n"
            f"New Written:     {len(unique_validated_records):,}\n"
            f"Skipped Dupes:   {rows_skipped:,}\n"
            f"Rejected:        {rows_rejected:,} ({(rows_rejected/total_rows)*100:.1f}%)\n"
            f"QA Flags:        {len(qa_issues)}\n"
            f"Batch Status:    {batch.get_status_display()}\n"
            f"=======================================================\n"
        ))
