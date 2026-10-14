"""
AgriLens Milestone 4: Comprehensive Test Suite for RBAC, User Management,
Geographic Access Scoping, Self-Approval Guards, Single-Use Password Tokens, and Audit Logging.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from apps.accounts.models import User, AuditLog
from apps.accounts.permissions import (
    scope_queryset_by_geography, can_access_district,
    generate_password_setup_url, validate_password_setup_token,
    AuditService
)
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import ManualObservation, DataSource, ValidatedObservation


class Milestone4RBACTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # Geography
        self.prov_north = Province.objects.create(name='Northern Province', code='01')
        self.prov_south = Province.objects.create(name='Southern Province', code='02')

        self.dist_musanze = District.objects.create(name='Musanze', code='13', province=self.prov_north)
        self.dist_huye = District.objects.create(name='Huye', code='24', province=self.prov_south)

        self.sec_kinigi = Sector.objects.create(name='Kinigi', code='1301', district=self.dist_musanze)
        self.sec_tumba = Sector.objects.create(name='Tumba', code='2401', district=self.dist_huye)

        # Agriculture
        self.season = AgriculturalSeason.objects.create(
            year=2025,
            season='A',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 2, 28)
        )
        cat = CropCategory.objects.create(name='Cereals')
        self.crop_maize = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)

        self.data_source = DataSource.objects.create(
            name='Field Registry 2025',
            source_type='MANUAL_FIELD_2025',
            data_kind=DataSource.DataKind.ADMINISTRATIVE,
            year=2025,
            season='A'
        )

        # Institutional Users
        self.admin_user = User.objects.create_superuser(
            username='system_admin',
            email='admin@agrilens.gov.rw',
            password='AdminPassword123!',
            role=User.Role.ADMIN,
            first_name='Eric',
            last_name='Kagabo'
        )
        self.nisr_manager = User.objects.create_user(
            username='nisr_mgr',
            email='manager@statistics.gov.rw',
            password='Password123!',
            role=User.Role.NISR_DATA_MANAGER,
            first_name='Diane',
            last_name='Uwase'
        )
        self.analyst = User.objects.create_user(
            username='agri_analyst',
            email='analyst@minagri.gov.rw',
            password='Password123!',
            role=User.Role.ANALYST,
            first_name='Patrick',
            last_name='Habimana'
        )
        self.reviewer_officer = User.objects.create_user(
            username='data_reviewer',
            email='reviewer@minagri.gov.rw',
            password='Password123!',
            role=User.Role.REVIEWER,
            first_name='Grace',
            last_name='Ingabire'
        )
        self.district_officer = User.objects.create_user(
            username='musanze_officer',
            email='officer.musanze@gov.rw',
            password='Password123!',
            role=User.Role.DISTRICT_OFFICER,
            assigned_province=self.prov_north,
            first_name='Jean',
            last_name='Bizimana'
        )
        self.district_officer.assigned_districts.add(self.dist_musanze)

        self.unassigned_officer = User.objects.create_user(
            username='unassigned_officer',
            email='unassigned@gov.rw',
            password='Password123!',
            role=User.Role.DISTRICT_OFFICER,
            first_name='Clarisse',
            last_name='Mutoni'
        )

    def test_user_roles_and_properties(self):
        """Validates all 7 institutional roles and role convenience methods."""
        self.assertTrue(self.admin_user.is_system_admin)
        self.assertTrue(self.admin_user.is_national_scope())

        self.assertTrue(self.nisr_manager.is_nisr_manager)
        self.assertTrue(self.nisr_manager.is_national_scope())

        self.assertTrue(self.analyst.is_analyst)
        self.assertTrue(self.analyst.is_national_scope())

        self.assertTrue(self.district_officer.is_district_officer)
        self.assertFalse(self.district_officer.is_national_scope())

        # Legacy role alias test
        legacy_user = User(role=User.Role.POLICY_MAKER)
        self.assertTrue(legacy_user.is_analyst)
        self.assertTrue(legacy_user.is_national_scope())

    def test_geographic_jurisdiction_scoping(self):
        """District Officer is strictly restricted to assigned districts."""
        self.assertTrue(self.district_officer.can_access_district(self.dist_musanze.id))
        self.assertFalse(self.district_officer.can_access_district(self.dist_huye.id))
        self.assertEqual(self.district_officer.get_authorized_district_ids(), [self.dist_musanze.id])

        # Unassigned officer has 0 access
        self.assertFalse(self.unassigned_officer.can_access_district(self.dist_musanze.id))
        self.assertEqual(self.unassigned_officer.get_authorized_district_ids(), [])

        # National scope officer has access to all
        self.assertTrue(self.analyst.can_access_district(self.dist_musanze.id))
        self.assertTrue(self.analyst.can_access_district(self.dist_huye.id))

    def test_scope_queryset_by_geography(self):
        """Database-level queryset filtering applies geographic boundaries."""
        obs_musanze = ManualObservation.objects.create(
            data_source=self.data_source, district=self.dist_musanze, sector=self.sec_kinigi,
            season=self.season, crop=self.crop_maize, plot_area_ha=Decimal('1.5'),
            total_production_kg=Decimal('3000'), observation_date=date(2025, 1, 15),
            created_by=self.admin_user
        )
        obs_huye = ManualObservation.objects.create(
            data_source=self.data_source, district=self.dist_huye, sector=self.sec_tumba,
            season=self.season, crop=self.crop_maize, plot_area_ha=Decimal('2.0'),
            total_production_kg=Decimal('4000'), observation_date=date(2025, 1, 15),
            created_by=self.admin_user
        )

        qs = ManualObservation.objects.all()

        # Scoped for District Officer
        scoped_do = scope_queryset_by_geography(qs, self.district_officer, district_field='district')
        self.assertEqual(scoped_do.count(), 1)
        self.assertEqual(scoped_do.first(), obs_musanze)

        # Scoped for National Analyst
        scoped_analyst = scope_queryset_by_geography(qs, self.analyst, district_field='district')
        self.assertEqual(scoped_analyst.count(), 2)

        # Scoped for unassigned District Officer
        scoped_unassigned = scope_queryset_by_geography(qs, self.unassigned_officer, district_field='district')
        self.assertEqual(scoped_unassigned.count(), 0)

    def test_user_management_access_control(self):
        """Only administrators can access user management views."""
        user_list_url = reverse('accounts:user_list')

        # Anonymous user redirected to login
        resp_anon = self.client.get(user_list_url)
        self.assertEqual(resp_anon.status_code, 302)
        self.assertIn('/accounts/login/', resp_anon.url)

        # Analyst receives 403 Forbidden
        self.client.force_login(self.analyst)
        resp_analyst = self.client.get(user_list_url)
        self.assertEqual(resp_analyst.status_code, 403)

        # Admin receives 200 OK
        self.client.force_login(self.admin_user)
        resp_admin = self.client.get(user_list_url)
        self.assertEqual(resp_admin.status_code, 200)
        self.assertContains(resp_admin, 'system_admin')
        self.assertContains(resp_admin, 'agri_analyst')

    def test_user_creation_with_single_use_setup_link(self):
        """Administrator creates officer; password setup link generated without raw password disclosure."""
        self.client.force_login(self.admin_user)

        post_data = {
            'username': 'new_officer_2026',
            'email': 'new.officer@agrilens.gov.rw',
            'first_name': 'Innocent',
            'last_name': 'Mugabo',
            'role': User.Role.DATA_ENTRY_OFFICER,
            'organization': 'NISR Agricultural Unit',
            'phone_number': '+250788111222',
        }
        response = self.client.post(reverse('accounts:user_create'), post_data)
        self.assertEqual(response.status_code, 200)

        # Officer exists but has no usable password until setup
        created = User.objects.get(username='new_officer_2026')
        self.assertFalse(created.has_usable_password())
        self.assertEqual(created.role, User.Role.DATA_ENTRY_OFFICER)

        # Setup link displayed in response (Condition 6)
        self.assertContains(response, 'users/setup-password/')

        # AuditLog recorded
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.USER_CREATED,
                target_repr__contains='new_officer_2026'
            ).exists()
        )

    def test_single_use_password_setup_activation(self):
        """Newly created officer uses cryptographic token to configure password and activate account."""
        new_officer = User.objects.create_user(
            username='token_test_officer',
            email='token@agrilens.gov.rw',
            role=User.Role.ANALYST,
            is_active=False
        )
        new_officer.set_unusable_password()
        new_officer.save()

        # Generate setup link
        uidb64 = urlsafe_base64_encode(force_bytes(new_officer.pk))
        token = default_token_generator.make_token(new_officer)
        setup_url = reverse('accounts:password_setup', kwargs={'uidb64': uidb64, 'token': token})

        # GET setup page
        resp_get = self.client.get(setup_url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, 'AgriLens Password Setup')

        # POST valid password
        resp_post = self.client.post(setup_url, {
            'new_password1': 'StrongPassword2026!',
            'new_password2': 'StrongPassword2026!',
        })
        self.assertEqual(resp_post.status_code, 302) # Redirect to login

        # Account is now active and has password
        new_officer.refresh_from_db()
        self.assertTrue(new_officer.is_active)
        self.assertTrue(new_officer.has_usable_password())
        self.assertTrue(new_officer.check_password('StrongPassword2026!'))

        # Single-Use enforcement: Reusing the same token fails
        resp_reuse = self.client.get(setup_url)
        self.assertEqual(resp_reuse.status_code, 200)
        self.assertContains(resp_reuse, 'Invalid or Expired Activation Link')

    def test_administrator_self_lockout_prevention(self):
        """Administrator cannot deactivate their own active account."""
        self.client.force_login(self.admin_user)

        # Try to deactivate self
        toggle_url = reverse('accounts:user_toggle_status', kwargs={'pk': self.admin_user.pk})
        resp = self.client.post(toggle_url)
        self.assertEqual(resp.status_code, 302)

        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active) # Must remain active

    def test_self_approval_conflict_of_interest_guard(self):
        """A user cannot review or approve their own manual submission (Milestone 4 Condition 5)."""
        # Reviewer creates a submission
        entry = ManualObservation.objects.create(
            data_source=self.data_source,
            district=self.dist_musanze,
            sector=self.sec_kinigi,
            season=self.season,
            crop=self.crop_maize,
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('2500'),
            observation_date=date(2025, 1, 15),
            review_status=ManualObservation.ReviewStatus.SUBMITTED,
            created_by=self.reviewer_officer
        )

        # Creator attempts to approve their own entry
        self.client.force_login(self.reviewer_officer)
        review_url = reverse('data_management:manual_entry_review', kwargs={'pk': entry.pk})
        resp_self = self.client.post(review_url, {
            'decision': 'approve',
            'review_comments': 'Self approving'
        })
        self.assertEqual(resp_self.status_code, 302)

        entry.refresh_from_db()
        # Must NOT be approved
        self.assertEqual(entry.review_status, ManualObservation.ReviewStatus.SUBMITTED)

        # A different authorized officer (admin) approves the entry
        self.client.force_login(self.admin_user)
        resp_admin = self.client.post(review_url, {
            'decision': 'approve',
            'review_comments': 'Approved by senior administrator.'
        })
        self.assertEqual(resp_admin.status_code, 302)

        entry.refresh_from_db()
        self.assertEqual(entry.review_status, ManualObservation.ReviewStatus.APPROVED)
        self.assertEqual(entry.reviewed_by, self.admin_user)

    def test_district_officer_boundary_enforcement(self):
        """District Officer cannot view or review records from unassigned districts."""
        entry_huye = ManualObservation.objects.create(
            data_source=self.data_source,
            district=self.dist_huye,
            sector=self.sec_tumba,
            season=self.season,
            crop=self.crop_maize,
            plot_area_ha=Decimal('1.0'),
            total_production_kg=Decimal('2000'),
            observation_date=date(2025, 1, 15),
            review_status=ManualObservation.ReviewStatus.SUBMITTED,
            created_by=self.admin_user
        )

        self.client.force_login(self.district_officer)

        # Cannot view Huye record (returns 403 Forbidden)
        detail_url = reverse('data_management:manual_entry_detail', kwargs={'pk': entry_huye.pk})
        resp_detail = self.client.get(detail_url)
        self.assertEqual(resp_detail.status_code, 403)

        # Cannot access Huye district intelligence (returns 403)
        geo_detail_url = reverse('geography:district_detail', kwargs={'pk': self.dist_huye.pk})
        resp_geo = self.client.get(geo_detail_url)
        self.assertEqual(resp_geo.status_code, 403)

        # Can access Musanze district intelligence (returns 200)
        musanze_url = reverse('geography:district_detail', kwargs={'pk': self.dist_musanze.pk})
        resp_musanze = self.client.get(musanze_url)
        self.assertEqual(resp_musanze.status_code, 200)

    def test_national_and_district_reports(self):
        """National and District report endpoints render correctly."""
        # National report
        nat_url = reverse('dashboard:reports_national')
        resp_nat = self.client.get(nat_url)
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, 'National Agricultural Productivity')

        # District dossier (Musanze)
        dist_url = reverse('dashboard:reports_district_detail', kwargs={'district_id': self.dist_musanze.pk})
        resp_dist = self.client.get(dist_url)
        self.assertEqual(resp_dist.status_code, 200)
        self.assertContains(resp_dist, 'Musanze')
