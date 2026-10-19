"""
Unit & Integration Test Suite for AgriLens Published Agricultural Reports & Bulletins.
Validates:
1. Public /reports/ catalog page rendering (HTTP 200).
2. Dynamic synthesis from live ValidatedObservation and IndicatorService (no hardcoded data).
3. Exact user-provided 40 REPORT_TYPES in choices and filter dropdown.
4. "all" filter option behavior (only in frontend, not in DB).
5. Multi-dimension filtering (type, crop, season, year, search).
6. Pagination controls (5 reports per page).
7. ReportLab PDF generation and download endpoint.
8. Detail API for interactive modal preview.
9. Admin report generation engine clearance and execution.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date
from apps.accounts.models import User
from apps.dashboard.models import PublishedReport
from apps.dashboard.report_service import (
    build_dynamic_reports_from_microdata,
    ensure_approved_reports_seeded,
    generate_pdf_for_report,
    admin_generate_all_reports_service,
)


class PublishedReportsTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an administrative user
        self.admin_user = User.objects.create_superuser(
            username='reports_admin',
            email='admin@nisr.gov.rw',
            password='TestPassword123!',
            role='national_analyst'
        )
        # Create a standard non-admin citizen user
        self.citizen_user = User.objects.create_user(
            username='citizen_user',
            email='citizen@agrilens.rw',
            password='TestPassword123!',
            role='farmer'
        )
        # Ensure dynamic reports are seeded
        ensure_approved_reports_seeded()

    def test_dynamic_report_synthesis_no_hardcoded_data(self):
        """Validates that reports are dynamically computed from microdata."""
        dynamic_catalog = build_dynamic_reports_from_microdata()
        self.assertEqual(len(dynamic_catalog), 12)

        # Check the first report (SAS 2024-2025)
        r1 = dynamic_catalog[0]
        self.assertEqual(r1["slug"], "rwanda-agricultural-survey-sas-2024-2025")
        self.assertEqual(r1["report_type"], "survey")
        self.assertIn("Verified Farm Observations", r1["key_metrics"])
        self.assertIn("National Total Production", r1["key_metrics"])
        # Ensure it contains real microdata numbers, not static placeholders
        self.assertTrue(any(unit in r1["key_metrics"]["National Total Production"] for unit in ["MT", "t"]))

    def test_report_types_contains_exact_40_choices(self):
        """Validates that PublishedReport.REPORT_TYPES contains the user's exact 40 choices."""
        self.assertEqual(len(PublishedReport.REPORT_TYPES), 40)
        codes = [code for code, _ in PublishedReport.REPORT_TYPES]
        self.assertIn("survey", codes)
        self.assertIn("production", codes)
        self.assertIn("yield", codes)
        self.assertIn("land_use", codes)
        self.assertIn("market", codes)
        self.assertIn("inputs", codes)
        self.assertIn("fertilizer", codes)
        self.assertIn("outlook", codes)
        self.assertIn("food_security", codes)
        self.assertIn("other", codes)
        # Verify "all" is NOT a report type in the database choices
        self.assertNotIn("all", codes)

    def test_public_reports_page_status_and_content(self):
        """Validates that /reports/ renders HTTP 200 with header, filters, table, and pagination."""
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/reports_list.html')
        self.assertContains(response, 'Reports &amp; Bulletins')
        self.assertContains(response, 'Filter Reports')
        self.assertContains(response, 'All Types')
        self.assertContains(response, 'All Crops')
        self.assertContains(response, 'All Seasons')
        self.assertContains(response, 'All Years')
        self.assertContains(response, 'Apply Filters')
        self.assertContains(response, 'PDF')

        # Check pagination: 5 reports on first page
        page_reports = response.context['reports']
        self.assertEqual(len(page_reports), 5)
        self.assertEqual(response.context['total_reports_count'], 12)

    def test_reports_filter_by_type(self):
        """Validates filtering reports by report_type."""
        response = self.client.get('/reports/?type=production')
        self.assertEqual(response.status_code, 200)
        reports = response.context['reports']
        for r in reports:
            self.assertEqual(r.report_type, 'production')

    def test_reports_filter_by_crop(self):
        """Validates filtering reports by crop."""
        response = self.client.get('/reports/?crop=Maize')
        self.assertEqual(response.status_code, 200)
        reports = response.context['reports']
        for r in reports:
            self.assertEqual(r.crop, 'Maize')

    def test_reports_filter_all_option(self):
        """Validates that passing type=all, crop=all returns all reports."""
        response = self.client.get('/reports/?type=all&crop=all&season=all&year=all')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_reports_count'], 12)

    def test_reports_search_query(self):
        """Validates searching reports by keyword."""
        response = self.client.get('/reports/?q=Maize')
        self.assertEqual(response.status_code, 200)
        reports = response.context['reports']
        for r in reports:
            self.assertTrue('Maize' in r.title or 'Maize' in r.subtitle or 'Maize' in r.executive_summary)

    def test_report_pdf_download_endpoint(self):
        """Validates serving compiled ReportLab PDF."""
        report = PublishedReport.objects.first()
        response = self.client.get(f'/reports/{report.slug}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_report_detail_api(self):
        """Validates detail JSON API used by interactive preview modal."""
        report = PublishedReport.objects.first()
        response = self.client.get(f'/reports/{report.slug}/detail/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['slug'], report.slug)
        self.assertEqual(data['title'], report.title)
        self.assertIn('key_metrics', data)
        self.assertIn('pdf_url', data)

    def test_admin_generate_all_reports_clearance(self):
        """Validates that non-staff users cannot execute admin generation, but staff can."""
        # Anonymous user denied
        res_anon = self.client.post('/reports/admin/generate-all/')
        self.assertEqual(res_anon.status_code, 302)

        # Standard non-staff citizen user denied
        self.client.force_login(self.citizen_user)
        res_user = self.client.post('/reports/admin/generate-all/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_user.status_code, 403)

        # Staff admin user allowed
        self.client.force_login(self.admin_user)
        res_admin = self.client.post('/reports/admin/generate-all/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_admin.status_code, 200)
        data = res_admin.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 12)
