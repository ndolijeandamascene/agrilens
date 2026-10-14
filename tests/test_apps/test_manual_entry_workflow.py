"""
Unit and integration tests for AgriLens Manual Data Entry,
Geographic hierarchy validation, Review workflow lifecycle, and Provenance segregation.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import ManualObservation, ValidatedObservation, DataSource, ImportBatch
from apps.data_management.forms import ManualObservationForm
from apps.indicators.services import IndicatorService


class ManualDataEntryWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.officer = User.objects.create_user(
            username='field_officer',
            password='Password123!',
            role=User.Role.EXTENSION_OFFICER,
            first_name='Jean',
            last_name='Nshimiyimana'
        )
        self.reviewer = User.objects.create_user(
            username='qa_reviewer',
            password='Password123!',
            role=User.Role.ANALYST,
            first_name='Aline',
            last_name='Mukamana'
        )

        # Geography
        self.prov_north = Province.objects.create(name='Northern Province', code='01')
        self.prov_south = Province.objects.create(name='Southern Province', code='02')

        self.dist_musanze = District.objects.create(name='Musanze', code='13', province=self.prov_north)
        self.dist_huye = District.objects.create(name='Huye', code='24', province=self.prov_south)

        self.sec_kinigi = Sector.objects.create(name='Kinigi', code='1301', district=self.dist_musanze)
        self.sec_tumba = Sector.objects.create(name='Tumba', code='2401', district=self.dist_huye)

        # Agriculture
        self.season_2025a = AgriculturalSeason.objects.create(
            year=2025,
            season='A',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 2, 28)
        )
        cat = CropCategory.objects.create(name='Tubers')
        self.crop_potato = Crop.objects.create(name='Irish Potato', category=cat, is_priority_crop=True)

    def test_form_validation_valid_input(self):
        """Valid submission should pass form validation cleanly."""
        data = {
            'season': self.season_2025a.id,
            'province': self.prov_north.id,
            'district': self.dist_musanze.id,
            'sector': self.sec_kinigi.id,
            'crop': self.crop_potato.id,
            'observation_date': '2025-01-15',
            'reporting_organization': 'RAB Musanze Station',
            'observation_reference': 'OBS-MUS-001',
            'plot_area_ha': '0.5000',
            'total_production_kg': '9000.00',
            'is_irrigated': True,
            'is_improved_seed': True,
            'uses_inorganic_fertilizer': True,
            'uses_organic_fertilizer': True,
            'has_soil_conservation': True,
            'uses_mechanization': False,
            'loss_quantity_kg': '450.00',
            'quantity_sold_kg': '7000.00',
            'farmgate_price_rwf': '250.00',
            'remarks': 'Healthy harvest under gravity irrigation',
        }
        form = ManualObservationForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())

    def test_form_validation_rejects_geography_mismatch(self):
        """Server-side validation must reject Sector that does not belong to District."""
        data = {
            'season': self.season_2025a.id,
            'province': self.prov_north.id,
            'district': self.dist_musanze.id, # Musanze is North
            'sector': self.sec_tumba.id,       # Tumba belongs to Huye in South!
            'crop': self.crop_potato.id,
            'observation_date': '2025-01-15',
            'plot_area_ha': '1.0000',
            'total_production_kg': '15000.00',
        }
        form = ManualObservationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('sector', form.errors)

    def test_form_validation_rejects_zero_or_negative_area(self):
        """Plot area must be strictly positive."""
        data = {
            'season': self.season_2025a.id,
            'province': self.prov_north.id,
            'district': self.dist_musanze.id,
            'sector': self.sec_kinigi.id,
            'crop': self.crop_potato.id,
            'observation_date': '2025-01-15',
            'plot_area_ha': '0.0000', # Invalid!
            'total_production_kg': '500.00',
        }
        form = ManualObservationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('plot_area_ha', form.errors)

    def test_draft_and_approval_workflow(self):
        """Test complete lifecycle: Create Draft -> Submit -> Review -> Approve."""
        # 1. Create as Draft
        obs = ManualObservation.objects.create(
            season=self.season_2025a,
            district=self.dist_musanze,
            sector=self.sec_kinigi,
            crop=self.crop_potato,
            observation_date=date(2025, 1, 15),
            plot_area_ha=Decimal('0.5000'),
            total_production_kg=Decimal('8000.00'),
            created_by=self.officer,
            review_status=ManualObservation.ReviewStatus.DRAFT
        )
        self.assertEqual(obs.review_status, ManualObservation.ReviewStatus.DRAFT)
        self.assertEqual(obs.calculated_yield_kg_per_ha, Decimal('16000.00')) # 8000 / 0.5

        # 2. Officer submits for review
        obs.review_status = ManualObservation.ReviewStatus.SUBMITTED
        obs.save()
        self.assertEqual(obs.review_status, ManualObservation.ReviewStatus.SUBMITTED)

        # 3. Reviewer approves
        obs.review_status = ManualObservation.ReviewStatus.APPROVED
        obs.reviewed_by = self.reviewer
        obs.review_comments = 'Verified with Musanze agronomist report.'
        obs.save()

        obs.refresh_from_db()
        self.assertEqual(obs.review_status, ManualObservation.ReviewStatus.APPROVED)
        self.assertEqual(obs.reviewed_by, self.reviewer)
        self.assertIn('Verified', obs.review_comments)

    def test_strict_provenance_isolation(self):
        """Official analytical aggregates MUST isolate official NISR data from manual entries."""
        # 1. Create Official observation
        ds = DataSource.objects.create(name='NISR SAS 2025', source_type='NISR_SAS_2025', is_official_survey=True)
        batch = ImportBatch.objects.create(source=ds, filename='test.sav')
        ValidatedObservation.objects.create(
            batch=batch,
            provenance='NISR_SAS_2025',
            season=self.season_2025a,
            district=self.dist_musanze,
            crop=self.crop_potato,
            source_record_id='OFFICIAL_001',
            plot_area_ha=Decimal('1.0000'),
            total_production_kg=Decimal('15000.00'),
            calculated_yield_kg_per_ha=Decimal('15000.00'),
            sampling_weight=Decimal('1.0')
        )

        # 2. Create Approved Manual observation
        ManualObservation.objects.create(
            season=self.season_2025a,
            district=self.dist_musanze,
            sector=self.sec_kinigi,
            crop=self.crop_potato,
            observation_date=date(2025, 1, 15),
            plot_area_ha=Decimal('2.0000'),
            total_production_kg=Decimal('50000.00'),
            created_by=self.officer,
            review_status=ManualObservation.ReviewStatus.APPROVED
        )

        # 3. Official summary should ONLY calculate from ValidatedObservation with provenance=NISR_
        official_summary = IndicatorService.get_national_summary(year=2025, season_code='A', include_manual=False)
        self.assertEqual(official_summary['total_plots'], 1)
        self.assertEqual(official_summary['weighted_yield_kg_per_ha'], 15000.00)

    def test_unauthorized_role_cannot_review(self):
        """Field extension officer cannot approve or reject a submitted observation."""
        obs = ManualObservation.objects.create(
            season=self.season_2025a,
            district=self.dist_musanze,
            sector=self.sec_kinigi,
            crop=self.crop_potato,
            observation_date=date(2025, 1, 15),
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('10000.0'),
            created_by=self.officer,
            review_status=ManualObservation.ReviewStatus.SUBMITTED
        )

        # Log in as Field Extension Officer (not authorized to approve)
        self.client.force_login(self.officer)
        response = self.client.post(reverse('data_management:manual_entry_review', args=[obs.id]), {
            'decision': 'approve',
            'review_comments': 'Attempting unauthorized approval'
        })
        obs.refresh_from_db()
        self.assertEqual(obs.review_status, ManualObservation.ReviewStatus.SUBMITTED) # Must remain SUBMITTED!
        self.assertIsNone(obs.reviewed_by)

    def test_user_cannot_edit_other_user_entry(self):
        """Officer cannot edit drafts submitted by a different officer."""
        other_officer = User.objects.create_user(
            username='other_officer',
            password='Password123!',
            role=User.Role.EXTENSION_OFFICER
        )
        obs = ManualObservation.objects.create(
            season=self.season_2025a,
            district=self.dist_musanze,
            sector=self.sec_kinigi,
            crop=self.crop_potato,
            observation_date=date(2025, 1, 15),
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('10000.0'),
            created_by=self.officer,
            review_status=ManualObservation.ReviewStatus.DRAFT
        )

        # Log in as other officer and try to edit
        self.client.force_login(other_officer)
        response = self.client.post(reverse('data_management:manual_entry_edit', args=[obs.id]), {
            'total_production_kg': '99999.00'
        })
        obs.refresh_from_db()
        self.assertEqual(obs.total_production_kg, Decimal('10000.0')) # Must remain unchanged!

    def test_dynamic_data_source_auto_generation_on_manual_entry(self):
        """Manual observation without explicit data_source dynamically creates and links an auditable DataSource."""
        season_2026b = AgriculturalSeason.objects.create(
            year=2026,
            season='B',
            start_date=date(2026, 3, 1),
            end_date=date(2026, 6, 30)
        )
        obs = ManualObservation.objects.create(
            season=season_2026b,
            district=self.dist_musanze,
            sector=self.sec_kinigi,
            crop=self.crop_potato,
            data_kind=DataSource.DataKind.COOPERATIVE_DATA,
            reporting_organization='Musanze Potato Growers Cooperative',
            observation_date=date(2026, 5, 10),
            plot_area_ha=Decimal('2.5'),
            total_production_kg=Decimal('35000.0'),
            created_by=self.officer
        )
        self.assertIsNotNone(obs.data_source)
        self.assertEqual(obs.data_source.data_kind, DataSource.DataKind.COOPERATIVE_DATA)
        self.assertEqual(obs.data_source.year, 2026)
        self.assertEqual(obs.data_source.season, 'B')
        self.assertEqual(obs.data_source.organization, 'Musanze Potato Growers Cooperative')
        self.assertIn('MANUAL_COOPERATIVE_DATA_2026_B', obs.data_source.source_type)
        self.assertFalse(obs.data_source.is_official_survey)

    def test_manual_entry_form_with_explicit_dynamic_data_source(self):
        """User can explicitly bind a manual entry to a registered dynamic data source."""
        custom_ds = DataSource.objects.create(
            name='RAB Highland Seed Trial 2026',
            source_type='RAB_TRIAL_2026_A',
            data_kind=DataSource.DataKind.RESEARCH_TRIAL,
            year=2026,
            season='A',
            organization='Rwanda Agriculture Board',
            is_official_survey=False
        )
        form_data = {
            'data_kind': DataSource.DataKind.RESEARCH_TRIAL,
            'data_source': custom_ds.id,
            'season': self.season_2025a.id,
            'province': self.prov_north.id,
            'district': self.dist_musanze.id,
            'sector': self.sec_kinigi.id,
            'crop': self.crop_potato.id,
            'observation_date': '2025-01-20',
            'reporting_organization': 'RAB Research Team',
            'plot_area_ha': '1.2000',
            'total_production_kg': '24000.00',
        }
        form = ManualObservationForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        obs = form.save(commit=False)
        obs.created_by = self.officer
        obs.save()
        self.assertEqual(obs.data_source, custom_ds)
        self.assertEqual(obs.calculated_yield_kg_per_ha, Decimal('20000.00'))

    def test_register_new_dynamic_data_source_view(self):
        """Authorized user can register new dynamic data sources for future years and arbitrary seasons."""
        self.client.force_login(self.reviewer)
        post_data = {
            'name': 'MINAGRI Marshland Survey 2027 Season C',
            'source_type': 'MINAGRI_MARSH_2027_C',
            'data_kind': DataSource.DataKind.ADMINISTRATIVE,
            'year': 2027,
            'season': 'C',
            'organization': 'MINAGRI Planning Directorate',
            'description': 'Targeted marshland irrigation monitoring',
            'citation': 'MINAGRI-DEC-2027-C',
            'is_official_survey': False,
        }
        response = self.client.post(reverse('data_management:data_source_create'), post_data)
        self.assertEqual(response.status_code, 302) # Redirect to hub
        ds = DataSource.objects.get(source_type='MINAGRI_MARSH_2027_C')
        self.assertEqual(ds.year, 2027)
        self.assertEqual(ds.season, 'C')
        self.assertEqual(ds.data_kind, DataSource.DataKind.ADMINISTRATIVE)
        self.assertEqual(ds.organization, 'MINAGRI Planning Directorate')

