from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.geography.models import Province, District
from apps.agriculture.models import Crop, CropCategory
from apps.markets.models import (
    MarketLocation,
    MarketCommodity,
    CommodityPrice,
    PriceAuditLog,
)

User = get_user_model()


class CommodityMarketPricesTests(TestCase):
    """Test suite for Public Market Prices Portal and 10-page Staff Surveillance Suite."""

    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        # Users
        self.admin = User.objects.create_superuser(
            username='staff_officer',
            email='officer@agrilens.gov.rw',
            password='TestPassword123!'
        )
        self.collector = User.objects.create_user(
            username='field_collector',
            email='collector@agrilens.gov.rw',
            password='TestPassword123!',
            is_staff=True  # Has staff access
        )

        # Geography & Crop
        self.province = Province.objects.create(name='Kigali City', code='01')
        self.district_nyarugenge = District.objects.create(name='Nyarugenge', code='0101', province=self.province)
        self.district_gasabo = District.objects.create(name='Gasabo', code='0102', province=self.province)

        self.cat_cereals = CropCategory.objects.create(name='Cereals')
        self.cat_legumes = CropCategory.objects.create(name='Legumes')

        self.crop_maize = Crop.objects.create(name='Maize', category=self.cat_cereals, is_priority_crop=True)
        self.crop_beans = Crop.objects.create(name='Climbing Beans', category=self.cat_legumes, is_priority_crop=True)

        # Markets
        self.market_nyabugogo = MarketLocation.objects.create(
            name='Nyabugogo Central Market',
            district=self.district_nyarugenge,
            province=self.province,
            is_major_hub=True
        )
        self.market_kimironko = MarketLocation.objects.create(
            name='Kimironko Modern Market',
            district=self.district_gasabo,
            province=self.province,
            is_major_hub=True
        )

        # Commodity Catalog
        self.commodity_maize = MarketCommodity.objects.create(
            name='Maize Grain',
            crop=self.crop_maize,
            category='Cereals',
            standard_unit='RWF/kg',
            min_expected_price=Decimal('200.00'),
            max_expected_price=Decimal('800.00')
        )

        # Create 12 published prices to verify 5-row pagination
        for i in range(12):
            CommodityPrice.objects.create(
                market=self.market_nyabugogo if i % 2 == 0 else self.market_kimironko,
                crop=self.crop_maize if i % 2 == 0 else self.crop_beans,
                price_per_kg_rwf=Decimal(str(400 + i * 5)),
                wholesale_price_rwf=Decimal(str(380 + i * 5)),
                date_recorded=self.today,
                status=CommodityPrice.Status.PUBLISHED,
                collected_by=self.collector,
                approved_by=self.admin
            )

        # Create unapproved/draft records to ensure they never appear on public portal
        self.draft_price = CommodityPrice.objects.create(
            market=self.market_nyabugogo,
            crop=self.crop_maize,
            price_per_kg_rwf=Decimal('999.00'),
            date_recorded=self.today,
            status=CommodityPrice.Status.DRAFT,
            collected_by=self.collector
        )
        self.submitted_price = CommodityPrice.objects.create(
            market=self.market_kimironko,
            crop=self.crop_beans,
            price_per_kg_rwf=Decimal('888.00'),
            date_recorded=self.today,
            status=CommodityPrice.Status.SUBMITTED,
            collected_by=self.collector
        )

    # ==========================================================================
    # 1. PUBLIC PORTAL TESTS
    # ==========================================================================

    def test_public_market_list_renders_and_has_hero_banner(self):
        """Public market prices resolves 200 and renders hero banner with market vendors image."""
        resp = self.client.get(reverse('markets:market_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "AgriLens Market Prices")
        self.assertContains(resp, "Real-time Commodity Market Prices in Rwanda")
        self.assertContains(resp, "market_hero_vendors.png")
        self.assertContains(resp, "Top Market Trends")
        self.assertContains(resp, "National Price Heatmap")

    def test_public_market_list_enforces_5_rows_per_page(self):
        """Verifies pagination allows strictly 5 rows on first page."""
        resp = self.client.get(reverse('markets:market_list'))
        self.assertEqual(resp.status_code, 200)
        page_obj = resp.context['page_obj']
        self.assertEqual(len(page_obj.object_list), 5)
        self.assertEqual(page_obj.number, 1)
        self.assertTrue(page_obj.has_next())

        # Test page 2 has next 5 rows
        resp_p2 = self.client.get(reverse('markets:market_list'), {'page': 2})
        self.assertEqual(resp_p2.status_code, 200)
        self.assertEqual(len(resp_p2.context['page_obj'].object_list), 5)
        self.assertEqual(resp_p2.context['page_obj'].number, 2)

    def test_public_market_list_only_shows_published_records(self):
        """Unpublished (Draft, Submitted, Under Review) prices must never appear on public portal."""
        resp = self.client.get(reverse('markets:market_list'))
        self.assertEqual(resp.status_code, 200)
        # 999.00 and 888.00 belong to draft and submitted
        self.assertNotContains(resp, "999.00")
        self.assertNotContains(resp, "888.00")

    # ==========================================================================
    # 2. INTERNAL SURVEILLANCE SUITE (10 SUB-PAGES)
    # ==========================================================================

    def test_internal_suite_requires_auth(self):
        """Internal management suite requires authenticated staff access."""
        resp = self.client.get(reverse('markets:internal_dashboard'))
        self.assertEqual(resp.status_code, 302)  # Redirects to login

    def test_internal_suite_all_10_pages_render_for_staff(self):
        """All 10 internal sidebar menu pages resolve with status 200 for staff."""
        self.client.login(username='staff_officer', password='TestPassword123!')

        pages = [
            'markets:internal_dashboard',
            'markets:internal_records',
            'markets:internal_markets',
            'markets:internal_commodities',
            'markets:internal_collection',
            'markets:internal_approvals',
            'markets:internal_analytics',
            'markets:internal_reports',
            'markets:internal_publications',
            'markets:internal_audit_log',
        ]
        for page_name in pages:
            with self.subTest(page=page_name):
                resp = self.client.get(reverse(page_name))
                self.assertEqual(resp.status_code, 200)

    # ==========================================================================
    # 3. WORKFLOW & AUDIT TRAIL LOGIC
    # ==========================================================================

    def test_collector_cannot_self_approve(self):
        """Governance check: Collector cannot approve or publish their own collected price record."""
        self.client.login(username='field_collector', password='TestPassword123!')
        
        # Try to approve their own submitted record
        resp = self.client.post(
            reverse('markets:internal_approval_action', args=[self.submitted_price.id]),
            {'action': 'publish'}
        )
        self.submitted_price.refresh_from_db()
        # Record should remain SUBMITTED because self-approval was blocked
        self.assertEqual(self.submitted_price.status, CommodityPrice.Status.SUBMITTED)

    def test_staff_approval_and_publish_workflow(self):
        """Supervisor approves and publishes record; logs immutable audit entry."""
        self.client.login(username='staff_officer', password='TestPassword123!')

        resp = self.client.post(
            reverse('markets:internal_approval_action', args=[self.submitted_price.id]),
            {'action': 'publish'}
        )
        self.submitted_price.refresh_from_db()
        self.assertEqual(self.submitted_price.status, CommodityPrice.Status.PUBLISHED)
        self.assertIsNotNone(self.submitted_price.published_at)

        # Audit log verification
        log = PriceAuditLog.objects.filter(price_record=self.submitted_price).first()
        self.assertIsNotNone(log)
        self.assertIn('publish', log.action)

    def test_supervisor_return_for_correction(self):
        """Supervisor returns record with reason; status changes to needs_correction."""
        self.client.login(username='staff_officer', password='TestPassword123!')

        resp = self.client.post(
            reverse('markets:internal_approval_action', args=[self.submitted_price.id]),
            {'action': 'return_for_correction', 'reason': 'Unit mismatch: price is for 50kg bag.'}
        )
        self.submitted_price.refresh_from_db()
        self.assertEqual(self.submitted_price.status, CommodityPrice.Status.NEEDS_CORRECTION)
        self.assertIn("Unit mismatch", self.submitted_price.correction_reason)

    def test_record_edit_preserves_original_price_and_audit(self):
        """Editing price preserves original_price without silent overwrite."""
        self.client.login(username='staff_officer', password='TestPassword123!')

        old_p = self.submitted_price.price_per_kg_rwf
        new_p = Decimal('450.00')

        resp = self.client.post(
            reverse('markets:internal_record_edit', args=[self.submitted_price.id]),
            {
                'price_per_kg_rwf': str(new_p),
                'unit': 'RWF/kg',
                'correction_reason': 'Corrected per verified market receipt slip #882.'
            }
        )
        self.submitted_price.refresh_from_db()
        self.assertEqual(self.submitted_price.price_per_kg_rwf, new_p)
        self.assertEqual(self.submitted_price.original_price, old_p)

        # Check audit log entry
        edit_log = PriceAuditLog.objects.filter(price_record=self.submitted_price, action='corrected').first()
        self.assertIsNotNone(edit_log)
        self.assertIn('slip #882', edit_log.reason)
