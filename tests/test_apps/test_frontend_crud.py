"""
Integration and regression tests for frontend CRUD operations.
Validates Create, Read, Update, and Delete endpoints for non-system-generated data.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, AuditLog
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import CropCategory, Crop, AgriculturalSeason
from apps.farmers.models import Cooperative, Farmer
from apps.inputs.models import InputCategory, AgriculturalInput
from apps.markets.models import MarketLocation, MarketCommodity, CommodityPrice
from apps.surveys.models import SurveyCampaign, DistrictSocioeconomicProfile, FarmSurveySubmission
from apps.data_management.models import DataSource, ManualObservation
from apps.decision_support.models import Recommendation, ActionPlan


class FrontendCRUDTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin User
        self.admin = User.objects.create_superuser(
            username='admin_crud',
            email='admin@agrilens.rw',
            password='TestPassword123!',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # Standard Officer User
        self.officer = User.objects.create_user(
            username='officer_crud',
            email='officer@agrilens.rw',
            password='TestPassword123!',
            role=User.Role.DATA_ENTRY_OFFICER,
            is_staff=True
        )

        # Geography
        self.province = Province.objects.create(name='Northern Province', code='01')
        self.district = District.objects.create(name='Musanze', province=self.province, code='0101')
        self.sector = Sector.objects.create(name='Muhoza', district=self.district, code='010101')

        # Season
        self.season = AgriculturalSeason.objects.create(
            year=2025,
            season='A',
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

        # Agriculture
        self.crop_cat = CropCategory.objects.create(name='Cereals', description='Cereal grains')
        self.crop = Crop.objects.create(name='Maize Test', category=self.crop_cat, is_priority_crop=True)

    def test_cooperative_crud(self):
        self.client.force_login(self.admin)

        # Create
        res = self.client.post(reverse('farmers:cooperative_create'), {
            'name': 'Coop Rwanda Test',
            'registration_number': 'RCA/1234',
            'sector': self.sector.id,
            'contact_phone': '+250788111222'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        coop = Cooperative.objects.get(name='Coop Rwanda Test')
        self.assertEqual(coop.registration_number, 'RCA/1234')

        # Edit
        res = self.client.post(reverse('farmers:cooperative_edit', kwargs={'pk': coop.pk}), {
            'name': 'Coop Rwanda Updated',
            'registration_number': 'RCA/9999',
            'sector': self.sector.id,
            'contact_phone': '+250788999000'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        coop.refresh_from_db()
        self.assertEqual(coop.name, 'Coop Rwanda Updated')

        # Delete with attached member blocked
        farmer = Farmer.objects.create(
            first_name='Eric',
            last_name='Nshimiyimana',
            gender='M',
            cooperative=coop,
            sector=self.sector,
            land_size_ha=Decimal('1.5')
        )
        self.client.post(reverse('farmers:cooperative_delete', kwargs={'pk': coop.pk}), follow=True)
        self.assertTrue(Cooperative.objects.filter(pk=coop.pk).exists())

        # Delete succeeds once member is unlinked/deleted
        farmer.delete()
        self.client.post(reverse('farmers:cooperative_delete', kwargs={'pk': coop.pk}), follow=True)
        self.assertFalse(Cooperative.objects.filter(pk=coop.pk).exists())

    def test_farmer_crud(self):
        self.client.force_login(self.admin)

        # Create
        res = self.client.post(reverse('farmers:farmer_create'), {
            'first_name': 'Marie',
            'last_name': 'Mukamana',
            'national_id': '1199080012345678',
            'gender': 'F',
            'sector': self.sector.id,
            'land_size_ha': '2.25'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        farmer = Farmer.objects.get(first_name='Marie', last_name='Mukamana')

        # Edit
        res = self.client.post(reverse('farmers:farmer_edit', kwargs={'pk': farmer.pk}), {
            'first_name': 'Marie Claire',
            'last_name': 'Mukamana',
            'national_id': '1199080012345678',
            'gender': 'F',
            'sector': self.sector.id,
            'land_size_ha': '3.00'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        farmer.refresh_from_db()
        self.assertEqual(farmer.first_name, 'Marie Claire')
        self.assertEqual(farmer.land_size_ha, Decimal('3.00'))

        # Delete
        self.client.post(reverse('farmers:farmer_delete', kwargs={'pk': farmer.pk}), follow=True)
        self.assertFalse(Farmer.objects.filter(pk=farmer.pk).exists())

    def test_inputs_crud(self):
        self.client.force_login(self.admin)

        # Category Create
        res = self.client.post(reverse('inputs:category_create'), {'name': 'Bio Fertilizers'}, follow=True)
        self.assertEqual(res.status_code, 200)
        cat = InputCategory.objects.get(name='Bio Fertilizers')

        # Category Edit
        self.client.post(reverse('inputs:category_edit', kwargs={'pk': cat.pk}), {'name': 'Organic Fertilizers'}, follow=True)
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'Organic Fertilizers')

        # Input Item Create
        res = self.client.post(reverse('inputs:input_create'), {
            'category': cat.pk,
            'name': 'Compost Premium',
            'unit': 'kg',
            'unit_price_rwf': '250.00',
            'subsidized_price_rwf': '150.00'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        item = AgriculturalInput.objects.get(name='Compost Premium')

        # Input Item Edit
        self.client.post(reverse('inputs:input_edit', kwargs={'pk': item.pk}), {
            'category': cat.pk,
            'name': 'Compost Premium Grade A',
            'unit': 'kg',
            'unit_price_rwf': '280.00',
            'subsidized_price_rwf': '160.00'
        }, follow=True)
        item.refresh_from_db()
        self.assertEqual(item.name, 'Compost Premium Grade A')
        self.assertEqual(item.unit_price_rwf, Decimal('280.00'))

        # Category delete protected with item attached
        self.client.post(reverse('inputs:category_delete', kwargs={'pk': cat.pk}), follow=True)
        self.assertTrue(InputCategory.objects.filter(pk=cat.pk).exists())

        # Item Delete
        self.client.post(reverse('inputs:input_delete', kwargs={'pk': item.pk}), follow=True)
        self.assertFalse(AgriculturalInput.objects.filter(pk=item.pk).exists())

        # Category Delete succeeds
        self.client.post(reverse('inputs:category_delete', kwargs={'pk': cat.pk}), follow=True)
        self.assertFalse(InputCategory.objects.filter(pk=cat.pk).exists())

    def test_agriculture_crud(self):
        self.client.force_login(self.admin)

        # Category Create
        res = self.client.post(reverse('agriculture:category_create'), {
            'name': 'Horticulture Test',
            'description': 'Fruits and vegetables'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        cat = CropCategory.objects.get(name='Horticulture Test')

        # Category Edit
        self.client.post(reverse('agriculture:category_edit', kwargs={'pk': cat.pk}), {
            'name': 'Horticulture & Fruits',
            'description': 'Updated'
        }, follow=True)
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'Horticulture & Fruits')

        # Crop Create
        res = self.client.post(reverse('agriculture:crop_create'), {
            'category': cat.pk,
            'name': 'Tomato Test',
            'kinyarwanda_name': 'Inyanya',
            'scientific_name': 'Solanum lycopersicum',
            'is_priority_crop': True
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        crop = Crop.objects.get(name='Tomato Test')

        # Crop Edit
        self.client.post(reverse('agriculture:crop_edit', kwargs={'pk': crop.pk}), {
            'category': cat.pk,
            'name': 'Roma Tomato',
            'kinyarwanda_name': 'Inyanya Roma',
            'scientific_name': 'Solanum lycopersicum',
            'is_priority_crop': True
        }, follow=True)
        crop.refresh_from_db()
        self.assertEqual(crop.name, 'Roma Tomato')

        # Crop Delete
        self.client.post(reverse('agriculture:crop_delete', kwargs={'pk': crop.pk}), follow=True)
        self.assertFalse(Crop.objects.filter(pk=crop.pk).exists())

        # Category Delete
        self.client.post(reverse('agriculture:category_delete', kwargs={'pk': cat.pk}), follow=True)
        self.assertFalse(CropCategory.objects.filter(pk=cat.pk).exists())

    def test_markets_crud(self):
        self.client.force_login(self.admin)

        # Market Location Create
        market = MarketLocation.objects.create(
            name='Musanze Central Market',
            district=self.district,
            province=self.province,
            market_type='retail',
            latitude=Decimal('-1.50'),
            longitude=Decimal('29.63')
        )

        # Market Location Edit
        res = self.client.post(reverse('markets:internal_market_edit', kwargs={'pk': market.pk}), {
            'name': 'Musanze Modern Market',
            'district': self.district.pk,
            'province': self.province.pk,
            'market_type': 'wholesale',
            'latitude': '-1.500000',
            'longitude': '29.630000',
            'is_active': True
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        market.refresh_from_db()
        self.assertEqual(market.name, 'Musanze Modern Market')

        # Commodity Bounds Edit
        comm = MarketCommodity.objects.create(
            crop=self.crop,
            name='Maize Grain Market Test',
            category='Cereals',
            standard_unit='RWF/kg',
            min_expected_price=Decimal('200.00'),
            max_expected_price=Decimal('600.00')
        )
        self.client.post(reverse('markets:internal_commodity_edit', kwargs={'pk': comm.pk}), {
            'crop': self.crop.pk,
            'name': 'Maize Grain Bounds Updated',
            'category': 'Cereals',
            'standard_unit': 'RWF/kg',
            'min_expected_price': '220.00',
            'max_expected_price': '650.00',
            'is_active': True
        }, follow=True)
        comm.refresh_from_db()
        self.assertEqual(comm.name, 'Maize Grain Bounds Updated')

        # Commodity Price Record Create and Delete
        price_record = CommodityPrice.objects.create(
            market=market,
            crop=self.crop,
            price_per_kg_rwf=Decimal('450.00'),
            date_recorded=timezone.now().date(),
            collected_by=self.admin
        )
        # Market deletion blocked with price record attached
        self.client.post(reverse('markets:internal_market_delete', kwargs={'pk': market.pk}), follow=True)
        self.assertTrue(MarketLocation.objects.filter(pk=market.pk).exists())

        # Price Record Delete
        self.client.post(reverse('markets:internal_record_delete', kwargs={'pk': price_record.pk}), follow=True)
        self.assertFalse(CommodityPrice.objects.filter(pk=price_record.pk).exists())

        # Market deletion succeeds now
        self.client.post(reverse('markets:internal_market_delete', kwargs={'pk': market.pk}), follow=True)
        self.assertFalse(MarketLocation.objects.filter(pk=market.pk).exists())

        # Commodity Bounds Delete
        self.client.post(reverse('markets:internal_commodity_delete', kwargs={'pk': comm.pk}), follow=True)
        self.assertFalse(MarketCommodity.objects.filter(pk=comm.pk).exists())

    def test_surveys_crud(self):
        self.client.force_login(self.admin)

        # Create
        res = self.client.post(reverse('surveys:survey_campaign_create'), {
            'title': 'SAS 2025 Test Campaign',
            'season': self.season.pk,
            'is_active': True,
            'description': 'Test SAS round'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        campaign = SurveyCampaign.objects.get(title='SAS 2025 Test Campaign')

        # Edit
        self.client.post(reverse('surveys:survey_campaign_edit', kwargs={'pk': campaign.pk}), {
            'title': 'SAS 2025 Campaign Updated',
            'season': self.season.pk,
            'is_active': False,
            'description': 'Closed'
        }, follow=True)
        campaign.refresh_from_db()
        self.assertEqual(campaign.title, 'SAS 2025 Campaign Updated')
        self.assertFalse(campaign.is_active)

        # Delete
        self.client.post(reverse('surveys:survey_campaign_delete', kwargs={'pk': campaign.pk}), follow=True)
        self.assertFalse(SurveyCampaign.objects.filter(pk=campaign.pk).exists())

        # =====================================================================
        # District Socioeconomic Profile CRUD (AHS 2024)
        # =====================================================================
        # Create
        res = self.client.post(reverse('surveys:socioeconomic_create'), {
            'district': self.district.pk,
            'survey_year': 2024,
            'provenance': 'NISR_AHS_2024',
            'sample_households_count': 120,
            'total_plots_surveyed': 750,
            'extension_advisory_reach_pct': '68.5',
            'twigire_muhinzi_membership_pct': '15.2',
            'credit_access_pct': '12.0',
            'sacco_credit_share_pct': '8.5',
            'bank_credit_share_pct': '3.5',
            'formal_land_title_pct': '64.0',
            'avg_plots_per_household': '6.25',
            'avg_plot_area_sqm': '820.0',
            'sustainable_practices_pct': '35.0',
            'dairy_producing_households_pct': '28.0',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        profile = DistrictSocioeconomicProfile.objects.get(district=self.district, survey_year=2024)
        self.assertEqual(profile.sample_households_count, 120)

        # Edit
        self.client.post(reverse('surveys:socioeconomic_edit', kwargs={'pk': profile.pk}), {
            'district': self.district.pk,
            'survey_year': 2024,
            'provenance': 'NISR_AHS_2024',
            'sample_households_count': 135,
            'total_plots_surveyed': 800,
            'extension_advisory_reach_pct': '72.0',
            'twigire_muhinzi_membership_pct': '18.0',
            'credit_access_pct': '15.0',
            'sacco_credit_share_pct': '10.0',
            'bank_credit_share_pct': '5.0',
            'formal_land_title_pct': '68.0',
            'avg_plots_per_household': '6.10',
            'avg_plot_area_sqm': '850.0',
            'sustainable_practices_pct': '40.0',
            'dairy_producing_households_pct': '30.0',
        }, follow=True)
        profile.refresh_from_db()
        self.assertEqual(profile.sample_households_count, 135)
        self.assertEqual(profile.extension_advisory_reach_pct, Decimal('72.00'))

        # Delete
        self.client.post(reverse('surveys:socioeconomic_delete', kwargs={'pk': profile.pk}), follow=True)
        self.assertFalse(DistrictSocioeconomicProfile.objects.filter(pk=profile.pk).exists())

        # =====================================================================
        # Farm Survey Submission CRUD
        # =====================================================================
        campaign2 = SurveyCampaign.objects.create(
            title='SAS Round 2',
            season=self.season,
            is_active=True
        )
        # Create Submission
        res = self.client.post(reverse('surveys:submission_create'), {
            'campaign': campaign2.pk,
            'sector': self.sector.pk,
            'crop': self.crop.pk,
            'area_planted_ha': '0.75',
            'quantity_harvested_kg': '2250.00',
            'yield_kg_per_ha': '3000.00'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        sub = FarmSurveySubmission.objects.get(campaign=campaign2, crop=self.crop)
        self.assertEqual(sub.area_planted_ha, Decimal('0.75'))

        # Edit Submission
        self.client.post(reverse('surveys:submission_edit', kwargs={'pk': sub.pk}), {
            'campaign': campaign2.pk,
            'sector': self.sector.pk,
            'crop': self.crop.pk,
            'area_planted_ha': '1.00',
            'quantity_harvested_kg': '3500.00',
            'yield_kg_per_ha': '3500.00'
        }, follow=True)
        sub.refresh_from_db()
        self.assertEqual(sub.area_planted_ha, Decimal('1.00'))

        # Delete Submission
        self.client.post(reverse('surveys:submission_delete', kwargs={'pk': sub.pk}), follow=True)
        self.assertFalse(FarmSurveySubmission.objects.filter(pk=sub.pk).exists())

    def test_data_management_crud(self):
        self.client.force_login(self.admin)

        # Data Source Edit & Delete
        ds = DataSource.objects.create(
            name='Test Ministry Registry',
            source_type='custom_test_src',
            data_kind='ADMINISTRATIVE'
        )
        self.client.post(reverse('data_management:data_source_edit', kwargs={'pk': ds.pk}), {
            'name': 'Updated Ministry Registry',
            'source_type': 'custom_test_src_upd',
            'data_kind': 'ADMINISTRATIVE',
            'organization': 'MINAGRI Extension'
        }, follow=True)
        ds.refresh_from_db()
        self.assertEqual(ds.name, 'Updated Ministry Registry')

        self.client.post(reverse('data_management:data_source_delete', kwargs={'pk': ds.pk}), follow=True)
        self.assertFalse(DataSource.objects.filter(pk=ds.pk).exists())

        # Manual Observation Draft Delete
        entry = ManualObservation.objects.create(
            data_kind='EXTENSION_REPORT',
            created_by=self.admin,
            district=self.district,
            sector=self.sector,
            crop=self.crop,
            season=self.season,
            observation_date=timezone.now().date(),
            plot_area_ha=Decimal('1.00'),
            total_production_kg=Decimal('2500.00'),
            review_status=ManualObservation.ReviewStatus.DRAFT
        )
        self.client.post(reverse('data_management:manual_entry_delete', kwargs={'pk': entry.pk}), follow=True)
        self.assertFalse(ManualObservation.objects.filter(pk=entry.pk).exists())

    def test_decision_support_action_plan_delete(self):
        self.client.force_login(self.admin)

        rec = Recommendation.objects.create(
            target_stakeholder='GOVERNMENT',
            title='Recommendation for Musanze Maize',
            problem_statement='Low fertilizer uptake',
            recommendation_text='Distribute subsidized inputs',
            district=self.district,
            crop=self.crop,
            season=self.season
        )
        action = ActionPlan.objects.create(
            recommendation=rec,
            title='Procure DAP for Muhoza sector',
            action_details='50 metric tons',
            assigned_to=self.admin
        )

        res = self.client.post(reverse('decision_support:action_plan_delete', kwargs={'pk': action.pk}), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(ActionPlan.objects.filter(pk=action.pk).exists())

    def test_accounts_user_delete(self):
        self.client.force_login(self.admin)

        target_officer = User.objects.create_user(
            username='temp_officer',
            password='Password123!',
            role=User.Role.DATA_ENTRY_OFFICER
        )

        # Cannot delete self
        self.client.post(reverse('accounts:user_delete', kwargs={'pk': self.admin.pk}), follow=True)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

        # Can delete target officer
        res = self.client.post(reverse('accounts:user_delete', kwargs={'pk': target_officer.pk}), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(User.objects.filter(pk=target_officer.pk).exists())
