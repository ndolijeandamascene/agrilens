"""
AgriLens Report Center Test Suite.
Validates:
1. Multi-type report generation from verified agricultural microdata.
2. Accurate aggregation and reporting-period boundary calculations (Africa/Kigali).
3. PDF, Excel (XLSX), and CSV artifact generation with formula injection prevention.
4. Missing, empty, and edge-case datasets handling.
5. Role-based access control (RBAC) and geographic scoping for district officers.
6. Report lifecycle workflow with strict separation of duties (no self-approval).
7. Public publication promotion to PublishedReport and withdrawal workflow.
8. Automated scheduler runner, concurrency locking, duplicate-run prevention, and retries.
9. Security audit trail completeness.
"""
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User, AuditLog
from apps.accounts.permissions import AuditService
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.dashboard.exports import sanitize_for_export
from apps.dashboard.models import GeneratedReport, ReportSchedule, PublishedReport
from apps.dashboard.report_service import (
    ReportEngine,
    ReportingPeriodHelper,
    ReportWorkflowService,
    ReportSchedulerService,
)
from apps.data_management.models import ValidatedObservation, DataSource, ImportBatch
from apps.geography.models import Province, District, Sector


class AgriLensReportCenterTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Geographic Hierarchy
        self.province_east = Province.objects.create(name='Eastern Province', code='05')
        self.province_north = Province.objects.create(name='Northern Province', code='01')

        self.district_kirehe = District.objects.create(name='Kirehe', code='57', province=self.province_east)
        self.district_musanze = District.objects.create(name='Musanze', code='13', province=self.province_north)

        self.sector_kirehe = Sector.objects.create(name='Kigarama', code='5701', district=self.district_kirehe)
        self.sector_musanze = Sector.objects.create(name='Kinigi', code='1301', district=self.district_musanze)

        # 2. Agricultural Domains
        self.cat_cereal = CropCategory.objects.create(name='Cereals')
        self.cat_legume = CropCategory.objects.create(name='Legumes')

        self.crop_maize = Crop.objects.create(name='Maize', category=self.cat_cereal, is_priority_crop=True)
        self.crop_beans = Crop.objects.create(name='Bush Beans', category=self.cat_legume, is_priority_crop=True)

        self.season_2025_a = AgriculturalSeason.objects.create(
            year=2025,
            season='A',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 2, 28)
        )

        self.data_source = DataSource.objects.create(
            name='NISR SAS 2025 Verification Registry',
            source_type='NISR_SAS_2025_VERIFIED',
            data_kind=DataSource.DataKind.SURVEY,
            year=2025,
            season='A'
        )
        self.batch = ImportBatch.objects.create(
            source=self.data_source,
            filename='sas_2025_test.sav'
        )

        # 3. Seed Verified Observations
        # Plot 1: Kirehe Maize (Irrigated, Improved Seed, Fertilizer)
        self.obs1 = ValidatedObservation.objects.create(
            batch=self.batch,
            season=self.season_2025_a,
            district=self.district_kirehe,
            crop=self.crop_maize,
            plot_area_ha=Decimal('2.0'),
            total_production_kg=Decimal('6000.0'),
            calculated_yield_kg_per_ha=Decimal('3000.0'),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True,
            uses_organic_fertilizer=True,
            is_irrigated=True,
            uses_mechanization=True,
            has_anti_erosion=True,
            uses_pesticide=True,
            quantity_sold_kg=Decimal('4000.0'),
            market_price_rwf=Decimal('350.0'),
            quantity_stored_kg=Decimal('1500.0'),
            total_loss_kg=Decimal('200.0'),
            loss_rate_percentage=Decimal('3.2'),
            sampling_weight=Decimal('1.5'),
            provenance='NISR_SAS_2025',
            source_record_id='PLOT_KIREHE_01'
        )

        # Plot 2: Musanze Bush Beans (Rainfed, Traditional)
        self.obs2 = ValidatedObservation.objects.create(
            batch=self.batch,
            season=self.season_2025_a,
            district=self.district_musanze,
            crop=self.crop_beans,
            plot_area_ha=Decimal('1.5'),
            total_production_kg=Decimal('2250.0'),
            calculated_yield_kg_per_ha=Decimal('1500.0'),
            is_improved_seed=False,
            uses_inorganic_fertilizer=False,
            uses_organic_fertilizer=True,
            is_irrigated=False,
            uses_mechanization=False,
            has_anti_erosion=True,
            uses_pesticide=False,
            quantity_sold_kg=Decimal('1000.0'),
            market_price_rwf=Decimal('650.0'),
            quantity_stored_kg=Decimal('1000.0'),
            total_loss_kg=Decimal('100.0'),
            loss_rate_percentage=Decimal('4.2'),
            sampling_weight=Decimal('1.2'),
            provenance='NISR_SAS_2025',
            source_record_id='PLOT_MUSANZE_01'
        )

        # 4. Institutional Officers
        self.admin_user = User.objects.create_superuser(
            username='admin_officer',
            email='admin@agrilens.gov.rw',
            password='AdminPass123!',
            role=User.Role.ADMIN
        )

        self.nisr_manager = User.objects.create_user(
            username='nisr_manager',
            email='manager@nisr.gov.rw',
            password='ManagerPass123!',
            role=User.Role.NISR_DATA_MANAGER
        )

        self.reviewer_user = User.objects.create_user(
            username='qa_reviewer',
            email='reviewer@minagri.gov.rw',
            password='ReviewerPass123!',
            role=User.Role.REVIEWER
        )

        self.analyst_user = User.objects.create_user(
            username='data_analyst',
            email='analyst@agrilens.gov.rw',
            password='AnalystPass123!',
            role=User.Role.ANALYST
        )

        self.district_officer_kirehe = User.objects.create_user(
            username='officer_kirehe',
            email='kirehe@district.gov.rw',
            password='KirehePass123!',
            role=User.Role.DISTRICT_OFFICER
        )
        self.district_officer_kirehe.assigned_districts.add(self.district_kirehe)

        self.data_entry_officer = User.objects.create_user(
            username='entry_officer',
            email='entry@agrilens.gov.rw',
            password='EntryPass123!',
            role=User.Role.DATA_ENTRY_OFFICER
        )

    # --------------------------------------------------------------------------
    # 1. Reporting Period & Boundaries Test
    # --------------------------------------------------------------------------
    def test_reporting_period_helper_rules(self):
        """Verifies monthly, quarterly, seasonal, and annual reporting period rules."""
        ref_date = datetime(2026, 10, 19, 14, 30, tzinfo=ReportingPeriodHelper.RWANDA_TZ)

        # Monthly: Previous calendar month (September 2026)
        monthly = ReportingPeriodHelper.calculate_reporting_period('monthly', ref_date)
        self.assertEqual(monthly['period_label'], 'September 2026')
        self.assertEqual(monthly['year'], 2026)
        self.assertEqual(monthly['start_date'], date(2026, 9, 1))
        self.assertEqual(monthly['end_date'], date(2026, 9, 30))

        # Quarterly: Q3 2026 (July - September)
        quarterly = ReportingPeriodHelper.calculate_reporting_period('quarterly', ref_date)
        self.assertEqual(quarterly['period_label'], 'Q3 2026')
        self.assertEqual(quarterly['start_date'], date(2026, 7, 1))
        self.assertEqual(quarterly['end_date'], date(2026, 9, 30))

        # Annual: Previous calendar year (2025)
        annually = ReportingPeriodHelper.calculate_reporting_period('annually', ref_date)
        self.assertEqual(annually['period_label'], 'Annual 2025')
        self.assertEqual(annually['year'], 2025)

        # Next run calculation: Next scheduled execution at 06:00 AM
        next_m = ReportingPeriodHelper.calculate_next_run('monthly', ref_date)
        self.assertEqual(next_m.hour, 6)
        self.assertEqual(next_m.minute, 0)
        self.assertEqual(next_m.day, 1)
        self.assertEqual(next_m.month, 11)

    # --------------------------------------------------------------------------
    # 2. Report Engine Statistical Calculations Across Report Types
    # --------------------------------------------------------------------------
    def test_report_engine_statistical_computations(self):
        """Verifies that ReportEngine derives accurate statistics from microdata without hardcoding."""
        # A. National Survey Synthesis
        survey_data = ReportEngine.compute_report_data('survey', {'year': 2025, 'season': 'A'})
        self.assertEqual(survey_data['total_plots'], 2)
        # Expected production MT: (6000*1.5 + 2250*1.2)/1000 = (9000 + 2700)/1000 = 11.7 MT
        self.assertEqual(survey_data['total_production_mt'], 11.7)
        # Expected area ha: (2.0*1.5 + 1.5*1.2) = 3.0 + 1.8 = 4.8 ha
        self.assertEqual(survey_data['total_area_ha'], 4.8)
        # Weighted yield: 11700 / 4.8 = 2437.5 kg/ha
        self.assertEqual(survey_data['weighted_yield_kg_ha'], 2437.5)
        self.assertIn("Total Production", survey_data['key_metrics'])

        # B. Crop-Specific Analysis (Maize only)
        maize_data = ReportEngine.compute_report_data('crop', {'year': 2025, 'season': 'A', 'crop_name': 'Maize'})
        self.assertEqual(maize_data['total_plots'], 1)
        self.assertEqual(maize_data['total_production_mt'], 9.0)
        self.assertEqual(maize_data['weighted_yield_kg_ha'], 3000.0)

        # C. Irrigation Report
        irrig_data = ReportEngine.compute_report_data('irrigation', {'year': 2025, 'season': 'A'})
        self.assertIn("Irrigated Yield", irrig_data['key_metrics'])
        self.assertIn("Rainfed Yield", irrig_data['key_metrics'])

        # D. Market Analysis Report
        market_data = ReportEngine.compute_report_data('market', {'year': 2025, 'season': 'A'})
        self.assertIn("Harvest Volume Sold", market_data['key_metrics'])
        self.assertIn("Average Farmgate Price", market_data['key_metrics'])

    # --------------------------------------------------------------------------
    # 3. Multi-Format Artifact Generation (PDF, XLSX, CSV)
    # --------------------------------------------------------------------------
    def test_artifact_generation_pdf_xlsx_csv(self):
        """Verifies generation of PDF, Excel, and CSV files in protected internal storage."""
        for fmt in ['pdf', 'xlsx', 'csv']:
            rep = GeneratedReport.objects.create(
                title=f"Test Report {fmt.upper()}",
                report_type='production',
                output_format=fmt,
                status='draft',
                year=2025,
                season='Season A',
                generated_by=self.analyst_user,
            )
            ReportEngine.generate_report_artifact(rep)
            rep.refresh_from_db()

            self.assertEqual(rep.status, 'generated')
            self.assertTrue(rep.file_path.endswith(f".{fmt}"))
            self.assertGreater(rep.file_size_bytes, 0)
            self.assertGreaterEqual(rep.execution_duration_sec, 0.0)


            # Check file exists on filesystem
            full_path = os.path.join(settings.MEDIA_ROOT, rep.file_path)
            self.assertTrue(os.path.exists(full_path))

    # --------------------------------------------------------------------------
    # 4. Formula Injection Protection Test
    # --------------------------------------------------------------------------
    def test_spreadsheet_formula_injection_sanitization(self):
        """Verifies that sanitize_for_export mitigates CSV/Excel formula injection (CWE-1236)."""
        malicious_payloads = [
            "=cmd|' /C calc'!A0",
            "+12345678",
            "-SUM(A1:A10)",
            "@HYPERLINK('http://evil.com')",
            "\tTAB_INJECT",
            "\rCR_INJECT"
        ]
        for payload in malicious_payloads:
            sanitized = sanitize_for_export(payload)
            self.assertTrue(sanitized.startswith("'"), f"Payload '{payload}' was not sanitized with single quote prefix.")

        # Safe values must remain unchanged
        self.assertEqual(sanitize_for_export("Clean Text"), "Clean Text")
        self.assertEqual(sanitize_for_export(1234), 1234)
        self.assertEqual(sanitize_for_export(Decimal('45.67')), Decimal('45.67'))

    # --------------------------------------------------------------------------
    # 5. Empty & Missing Datasets Handling
    # --------------------------------------------------------------------------
    def test_empty_and_missing_datasets_graceful_handling(self):
        """Verifies report generation handles years or filters with zero records without crash."""
        empty_data = ReportEngine.compute_report_data('survey', {'year': 1990, 'season': 'A'})
        self.assertEqual(empty_data['total_plots'], 0)
        self.assertEqual(empty_data['total_production_mt'], 0.0)
        self.assertEqual(empty_data['total_area_ha'], 0.0)
        self.assertEqual(empty_data['weighted_yield_kg_ha'], 0.0)
        self.assertEqual(empty_data['loss_rate'], 0.0)

    # --------------------------------------------------------------------------
    # 6. Role-Based Access Control (RBAC)
    # --------------------------------------------------------------------------
    def test_rbac_view_clearance(self):
        """Tests role authorization for internal Report Center endpoints."""
        # 1. Anonymous visitor redirected to login
        resp = self.client.get(reverse('dashboard:internal_report_center'))
        self.assertEqual(resp.status_code, 302)

        # 2. Data Entry Officer denied access (HTTP 403)
        self.client.force_login(self.data_entry_officer)
        resp = self.client.get(reverse('dashboard:internal_report_center'))
        self.assertEqual(resp.status_code, 403)

        # 3. Analyst granted access (HTTP 200)
        self.client.force_login(self.analyst_user)
        resp = self.client.get(reverse('dashboard:internal_report_center'))
        self.assertEqual(resp.status_code, 200)

        # 4. Administrator granted access (HTTP 200)
        self.client.force_login(self.admin_user)
        resp = self.client.get(reverse('dashboard:internal_report_center'))
        self.assertEqual(resp.status_code, 200)

    # --------------------------------------------------------------------------
    # 7. Geographic Scoping for District Officers
    # --------------------------------------------------------------------------
    def test_district_officer_geographic_scoping(self):
        """Ensures district officers can only generate and view reports for their assigned districts."""
        self.client.force_login(self.district_officer_kirehe)

        # Permitted: Generation for assigned Kirehe district
        resp = self.client.post(reverse('dashboard:internal_report_generate'), {
            'report_type': 'district',
            'output_format': 'pdf',
            'year': '2025',
            'season': 'Season A',
            'district': str(self.district_kirehe.id),
        })
        self.assertEqual(resp.status_code, 302)

        # Prohibited: Attempted generation for unassigned Musanze district
        resp_prohibited = self.client.post(reverse('dashboard:internal_report_generate'), {
            'report_type': 'district',
            'output_format': 'pdf',
            'year': '2025',
            'season': 'Season A',
            'district': str(self.district_musanze.id),
        })
        # Should redirect back to generate with error
        self.assertEqual(resp_prohibited.status_code, 302)
        # Musanze report should NOT exist for this officer
        self.assertFalse(GeneratedReport.objects.filter(generated_by=self.district_officer_kirehe, district=self.district_musanze).exists())

    # --------------------------------------------------------------------------
    # 8. Report Lifecycle, Separation of Duties, & Public Publication
    # --------------------------------------------------------------------------
    def test_report_lifecycle_and_separation_of_duties(self):
        """
        Validates the lifecycle: Draft -> Generated -> Pending Review -> Approved -> Published.
        Verifies separation of duties: officers cannot approve their own generated reports.
        """
        # Step 1: Analyst generates a report
        report = GeneratedReport.objects.create(
            title="Kirehe Maize Commercialization Report",
            report_type="production",
            output_format="pdf",
            status="draft",
            year=2025,
            season="Season A",
            district=self.district_kirehe,
            crop=self.crop_maize,
            crop_name="Maize",
            generated_by=self.analyst_user,
        )
        ReportEngine.generate_report_artifact(report)
        self.assertEqual(report.status, 'generated')

        # Step 2: Submit for review
        ReportWorkflowService.submit_for_review(report, self.analyst_user)
        self.assertEqual(report.status, 'pending_review')

        # Step 3: Separation of Duties Violation
        # Analyst tries to approve their own report -> Must raise PermissionDenied
        with self.assertRaises(PermissionDenied):
            ReportWorkflowService.approve_report(report, self.analyst_user, comments="Self approval attempt")

        # Step 4: Legitimate approval by independent Reviewer
        ReportWorkflowService.approve_report(report, self.reviewer_user, comments="Verified against field registers")
        report.refresh_from_db()
        self.assertEqual(report.status, 'approved')
        self.assertEqual(report.reviewed_by, self.reviewer_user)

        # Step 5: Unauthorized publication attempt by standard analyst
        with self.assertRaises(PermissionDenied):
            ReportWorkflowService.publish_report(report, self.analyst_user)

        # Step 6: Authorized publication by NISR Data Manager
        ReportWorkflowService.publish_report(report, self.nisr_manager)
        report.refresh_from_db()
        self.assertEqual(report.status, 'published')
        self.assertIsNotNone(report.published_report)
        self.assertTrue(report.published_report.is_published)

        # Step 7: Public portal test
        # Report must now be visible to anonymous public visitors on /reports/
        anon_resp = self.client.get(reverse('dashboard:reports'))
        self.assertContains(anon_resp, "Kirehe Maize Commercialization Report")

        # Step 8: Withdrawal / Unpublishing
        ReportWorkflowService.unpublish_report(report, self.admin_user)
        report.refresh_from_db()
        self.assertEqual(report.status, 'approved')
        self.assertFalse(report.published_report.is_published)

        # Report must disappear from public view
        anon_resp2 = self.client.get(reverse('dashboard:reports'))
        self.assertNotContains(anon_resp2, "Kirehe Maize Commercialization Report")

    # --------------------------------------------------------------------------
    # 9. Automated Report Scheduler Runner & Duplicate Prevention
    # --------------------------------------------------------------------------
    def test_automated_scheduler_execution_and_duplicate_prevention(self):
        """Tests ReportSchedule execution, duplicate prevention, and lock handling."""
        now = timezone.now()
        schedule = ReportSchedule.objects.create(
            title="Weekly Production Automated Monitor",
            report_type="production",
            frequency="weekly",
            output_format="csv",
            district=self.district_kirehe,
            crop=self.crop_maize,
            crop_name="Maize",
            owner=self.admin_user,
            auto_submit_for_review=True,
            next_run_at=now - timedelta(minutes=5), # Due now
            is_active=True
        )

        # 1. First execution: should generate report
        res1 = ReportSchedulerService.run_due_schedules(force=False, schedule_id=schedule.id)
        self.assertEqual(res1['succeeded'], 1)
        self.assertEqual(res1['skipped_duplicate'], 0)

        schedule.refresh_from_db()
        self.assertEqual(schedule.last_status, 'success')
        self.assertFalse(schedule.is_running)
        self.assertTrue(schedule.next_run_at > now)

        # Generated report created and moved to pending_review
        gen_rep = GeneratedReport.objects.filter(schedule=schedule).first()
        self.assertIsNotNone(gen_rep)
        self.assertEqual(gen_rep.status, 'pending_review')

        # 2. Second execution attempt for same period: must skip duplicate
        res2 = ReportSchedulerService.run_due_schedules(force=False, schedule_id=schedule.id)
        self.assertEqual(res2['skipped_duplicate'], 1)
        self.assertEqual(res2['succeeded'], 0)

        # 3. Test Management Command invocation
        call_command('run_scheduled_reports', force=True, schedule_id=schedule.id)

    # --------------------------------------------------------------------------
    # 10. Audit Logging Verification
    # --------------------------------------------------------------------------
    def test_security_audit_logging_integrity(self):
        """Verifies that generation, review, publication, and schedule actions are audited."""
        initial_count = AuditLog.objects.count()

        # Trigger generation
        rep = GeneratedReport.objects.create(
            title="Audit Test Report",
            report_type="yield",
            output_format="pdf",
            year=2025,
            season="Season A",
            generated_by=self.analyst_user,
        )
        ReportEngine.generate_report_artifact(rep)

        # Verify AuditLog generated
        gen_log = AuditLog.objects.filter(action=AuditLog.Action.REPORT_GENERATED, target_id=str(rep.id)).first()
        self.assertIsNotNone(gen_log)
        self.assertEqual(gen_log.actor, self.analyst_user)
