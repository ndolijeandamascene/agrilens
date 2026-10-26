"""
AgriLens Official Ingestion Management Command: NISR Agriculture Household Survey (AHS) 2024.
Extracts, harmonizes, and calculates survey-weighted structural indicators for all 30 districts:
- Extension advisory reach & Twigire Muhinzi/Mworozi membership (Section 6)
- Financial inclusion, agricultural credit, and SACCO/Bank shares (Credits)
- Land tenure security (formal title deeds), parcel count, and area (Section 2)
- Sustainable environmental risk mitigation measures (Section 8)
- Cattle milk & livestock production (Section 11)
"""
import os
import hashlib
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd
import pyreadstat

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.geography.models import District
from apps.surveys.models import DistrictSocioeconomicProfile
from apps.data_management.models import DataSource, ImportBatch
from apps.accounts.permissions import AuditService
from apps.accounts.models import AuditLog


class Command(BaseCommand):
    help = "Ingest official NISR Agriculture Household Survey (AHS) 2024 microdata across all 30 districts"

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='Datasets/Agriculture Household Survey (AHS) 2024',
            help='Relative or absolute path to AHS 2024 directory'
        )
        parser.add_argument('--dry-run', action='store_true', default=False, help='Preview aggregation without saving to database')
        parser.add_argument('--force', action='store_true', default=False, help='Force re-ingest even if previously loaded')

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        if not data_dir.is_absolute():
            data_dir = Path.cwd() / data_dir

        if not data_dir.exists():
            self.stderr.write(self.style.ERROR(f"AHS directory not found: {data_dir}"))
            return

        dry_run = options['dry_run']
        force = options['force']

        mode_str = "DRY-RUN (Preview Mode)" if dry_run else "LIVE INGESTION"
        self.stdout.write(self.style.NOTICE(
            f"Starting Ingestion Pipeline [{mode_str}] for NISR AHS 2024\n"
            f"Directory: {data_dir}\n"
        ))

        # Check required files
        req_files = {
            'sec0': 'AHS2024_Section0.dta',
            'sec6': 'AHS2024_Section6_EXTENSION SERVICES AND AGRICULTURAL PROGRAMMES.dta',
            'cred': 'AHS2024_Credits.dta',
            'sec2': 'AHS2024_Section2_LAND TENURE.dta',
            'sec8': 'AHS2024_Section8_SUSTAINABLE AGRICULTURE.dta',
            'milk': 'AHS2024_Section11_1_CATTLE MILK PRODUCTION AND USE.dta',
        }

        for key, fname in req_files.items():
            fpath = data_dir / fname
            if not fpath.exists():
                self.stderr.write(self.style.ERROR(f"Missing required file: {fname}"))
                return

        # 1. Resolve Data Source
        data_source, _ = DataSource.objects.get_or_create(
            source_type='NISR_AHS_2024',
            defaults={
                'name': 'NISR Agriculture Household Survey 2024',
                'description': 'Official AHS structural and socioeconomic survey microdata for Rwanda (14 modules)',
                'is_official_survey': True,
                'data_kind': DataSource.DataKind.SURVEY,
                'year': 2024,
                'organization': 'NISR',
            }
        )

        # 2. Checksum of Master File
        hasher = hashlib.sha256()
        with open(data_dir / req_files['sec0'], 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()

        if not dry_run and not force:
            prior = ImportBatch.objects.filter(file_checksum=file_hash, status=ImportBatch.Status.SUCCESS).first()
            if prior:
                self.stdout.write(self.style.WARNING(
                    f"AHS 2024 microdata was already successfully imported in Batch #{prior.id} on {prior.completed_at}. "
                    f"Pass --force to overwrite or --dry-run to preview."
                ))
                return

        # 3. Read Microdata Modules
        self.stdout.write("Loading AHS 2024 survey microdata into memory...")
        df_sec0, _ = pyreadstat.read_dta(str(data_dir / req_files['sec0']), encoding='latin1')
        df_sec6, _ = pyreadstat.read_dta(str(data_dir / req_files['sec6']), encoding='latin1')
        df_cred, _ = pyreadstat.read_dta(str(data_dir / req_files['cred']), encoding='latin1')
        df_sec2, _ = pyreadstat.read_dta(str(data_dir / req_files['sec2']), encoding='latin1')
        df_sec8, _ = pyreadstat.read_dta(str(data_dir / req_files['sec8']), encoding='latin1')
        df_milk, _ = pyreadstat.read_dta(str(data_dir / req_files['milk']), encoding='latin1')

        total_households = len(df_sec0)
        total_plots = len(df_sec2)
        self.stdout.write(f"Loaded: {total_households:,} households and {total_plots:,} farm plots.")

        # 4. Household-Level Feature Aggregation
        self.stdout.write("Harmonizing household modules...")

        # Extension: s6q2 (any non-empty) or s6q5 (1 = Twigire Muhinzi)
        ext_hh = df_sec6.groupby('hhid').agg(
            has_ext=('s6q2', lambda x: 1 if any(pd.notnull(v) and str(v).strip() != '' for v in x) else 0),
            twigire=('s6q5', lambda x: 1 if any(v == 1 for v in x) else 0)
        ).reset_index()

        # Credits: s10aq1 == 1, s10q6 == 4 (SACCO), s10q6 == 2 (Commercial Bank)
        cred_hh = df_cred.groupby('hhid').agg(
            has_loan=('s10aq1', lambda x: 1 if any(v == 1 for v in x) else 0),
            sacco_loan=('s10q6', lambda x: 1 if any(v == 4 for v in x) else 0),
            bank_loan=('s10q6', lambda x: 1 if any(v == 2 for v in x) else 0)
        ).reset_index()

        # Land Tenure: s2q7 == 1 (formal land title), s2q2 (area sqm), count of plots
        land_hh = df_sec2.groupby('hhid').agg(
            plot_count=('s2q1', 'count'),
            titled_plots=('s2q7', lambda x: sum(1 for v in x if v == 1)),
            total_area_sqm=('s2q2', lambda x: sum(v for v in x if pd.notnull(v) and v > 0))
        ).reset_index()

        # Sustainable Agriculture: s8q2 == 1
        sust_hh = df_sec8.groupby('hhid').agg(
            has_sust=('s8q2', lambda x: 1 if any(v == 1 for v in x) else 0)
        ).reset_index()

        # Milk: s10q1_0 == 1
        milk_hh = df_milk.groupby('hhid').agg(
            has_milk=('s10q1_0', lambda x: 1 if any(v == 1 for v in x) else 0)
        ).reset_index()

        # Merge onto master households
        merged = df_sec0.merge(ext_hh, on='hhid', how='left')
        merged = merged.merge(cred_hh, on='hhid', how='left')
        merged = merged.merge(land_hh, on='hhid', how='left')
        merged = merged.merge(sust_hh, on='hhid', how='left')
        merged = merged.merge(milk_hh, on='hhid', how='left')
        merged = merged.fillna(0)

        # 5. Preload District Lookups
        district_lookup = {}
        for dist in District.objects.all():
            district_lookup[str(dist.code)] = dist
            district_lookup[int(dist.code) if dist.code.isdigit() else -1] = dist
            district_lookup[dist.name.lower()] = dist

        profiles_to_save = []
        summary_rows = []

        self.stdout.write("Calculating weighted indicators per district...")
        for dist_code_val, grp in merged.groupby('district'):
            dist_int = int(dist_code_val)
            dist_obj = district_lookup.get(dist_int) or district_lookup.get(str(dist_int))
            if not dist_obj:
                self.stderr.write(self.style.WARNING(f"District code {dist_int} not found in database."))
                continue

            w = grp['weight'].values
            tot_w = float(np.sum(w)) if np.sum(w) > 0 else float(len(grp))

            ext_pct = (float(np.sum(grp['has_ext'] * w)) / tot_w) * 100.0
            twigire_pct = (float(np.sum(grp['twigire'] * w)) / tot_w) * 100.0
            loan_pct = (float(np.sum(grp['has_loan'] * w)) / tot_w) * 100.0
            sacco_pct = (float(np.sum(grp['sacco_loan'] * w)) / tot_w) * 100.0
            bank_pct = (float(np.sum(grp['bank_loan'] * w)) / tot_w) * 100.0
            sust_pct = (float(np.sum(grp['has_sust'] * w)) / tot_w) * 100.0
            milk_pct = (float(np.sum(grp['has_milk'] * w)) / tot_w) * 100.0

            tot_plots = int(grp['plot_count'].sum())
            tot_titled = int(grp['titled_plots'].sum())
            title_pct = (tot_titled / tot_plots * 100.0) if tot_plots > 0 else 0.0
            avg_plots = float(grp['plot_count'].mean())
            avg_sqm = (float(grp['total_area_sqm'].sum()) / tot_plots) if tot_plots > 0 else 0.0

            profile = DistrictSocioeconomicProfile(
                district=dist_obj,
                survey_year=2024,
                provenance='NISR_AHS_2024',
                sample_households_count=len(grp),
                total_plots_surveyed=tot_plots,
                extension_advisory_reach_pct=Decimal(str(round(ext_pct, 2))),
                twigire_muhinzi_membership_pct=Decimal(str(round(twigire_pct, 2))),
                credit_access_pct=Decimal(str(round(loan_pct, 2))),
                sacco_credit_share_pct=Decimal(str(round(sacco_pct, 2))),
                bank_credit_share_pct=Decimal(str(round(bank_pct, 2))),
                formal_land_title_pct=Decimal(str(round(title_pct, 2))),
                avg_plots_per_household=Decimal(str(round(avg_plots, 2))),
                avg_plot_area_sqm=Decimal(str(round(avg_sqm, 2))),
                sustainable_practices_pct=Decimal(str(round(sust_pct, 2))),
                dairy_producing_households_pct=Decimal(str(round(milk_pct, 2))),
            )
            profiles_to_save.append(profile)
            summary_rows.append((dist_obj.name, len(grp), ext_pct, twigire_pct, loan_pct, title_pct, avg_plots, milk_pct))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n=======================================================\n"
                f"DRY-RUN AHS 2024 PREVIEW COMPLETED\n"
                f"=======================================================\n"
                f"Districts Computed: {len(profiles_to_save)} of 30\n"
                f"Households Sample:  {total_households:,}\n"
                f"Parcels Sample:     {total_plots:,}\n"
                f"Writes to DB:       NONE (Dry-run mode)\n"
                f"=======================================================\n"
            ))
            return

        # 6. Save in transaction
        batch = ImportBatch.objects.create(
            source=data_source,
            filename='AHS 2024 (Harmonized 6 Modules)',
            file_checksum=file_hash,
            total_rows=total_households,
            status=ImportBatch.Status.PROCESSING,
        )

        with transaction.atomic():
            # Delete existing records for 2024 if force re-importing
            DistrictSocioeconomicProfile.objects.filter(survey_year=2024).delete()
            DistrictSocioeconomicProfile.objects.bulk_create(profiles_to_save)

        batch.rows_accepted = len(profiles_to_save)
        batch.rows_rejected = 0
        batch.completed_at = timezone.now()
        batch.status = ImportBatch.Status.SUCCESS
        batch.summary_notes = (
            f"Successfully computed and stored AHS 2024 socioeconomic profiles across all {len(profiles_to_save)} districts. "
            f"Harmonized {total_households:,} households and {total_plots:,} farm parcels."
        )
        batch.save()

        AuditService.log(
            action=AuditLog.Action.DATA_IMPORTED,
            target=batch,
            details={
                'source': 'NISR_AHS_2024',
                'districts': len(profiles_to_save),
                'households': total_households,
                'parcels': total_plots,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n=======================================================\n"
            f"NISR AHS 2024 INGESTION COMPLETED SUCCESSFULLY\n"
            f"=======================================================\n"
            f"Batch ID:            #{batch.id}\n"
            f"Districts Stored:    {len(profiles_to_save)} of 30 districts\n"
            f"Households Surveyed: {total_households:,}\n"
            f"Parcels Analyzed:    {total_plots:,}\n"
            f"Batch Status:        {batch.get_status_display()}\n"
            f"=======================================================\n"
        ))
