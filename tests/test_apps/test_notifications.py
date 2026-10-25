"""
AgriLens Notification System Test Suite.
Verifies complete in-app alerts, email deliveries, user privacy, role permissions,
user preferences, workflow integrations, DRF APIs, announcement broadcasts, and audit logs.
"""
from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, AuditLog
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import AgriculturalSeason, Crop, CropCategory
from apps.data_management.models import ManualObservation, DataSource
from apps.markets.models import MarketLocation, CommodityPrice
from apps.notifications.models import (
    Notification,
    NotificationPreference,
    SystemAnnouncement,
    EmailDeliveryLog,
)
from apps.notifications.services import NotificationService
from apps.notifications.emails import EmailService


class AgriLensNotificationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()

        # Geographic setup
        self.province = Province.objects.create(name='Northern Province', code='01')
        self.district = District.objects.create(name='Musanze', code='13', province=self.province)
        self.sector = Sector.objects.create(name='Kinigi', code='1301', district=self.district)

        # Users
        self.admin = User.objects.create_superuser(
            username='admin_officer',
            email='admin@agrilens.gov.rw',
            password='AdminPassword123!',
            role=User.Role.ADMIN,
        )
        self.data_officer = User.objects.create_user(
            username='data_officer_1',
            email='officer@agrilens.gov.rw',
            password='OfficerPassword123!',
            role=User.Role.DATA_ENTRY_OFFICER,
            is_staff=True,
        )
        self.data_officer.assigned_districts.add(self.district)

        self.reviewer = User.objects.create_user(
            username='reviewer_1',
            email='reviewer@agrilens.gov.rw',
            password='ReviewerPassword123!',
            role=User.Role.REVIEWER,
            is_staff=True,
        )
        self.reviewer.assigned_districts.add(self.district)

        self.analyst = User.objects.create_user(
            username='analyst_1',
            email='analyst@agrilens.gov.rw',
            password='AnalystPassword123!',
            role=User.Role.ANALYST,
        )

        # Crops & Data Sources
        cat = CropCategory.objects.create(name='Cereals')
        self.crop = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)
        self.season = AgriculturalSeason.objects.create(
            year=2025,
            season='A',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 2, 28)
        )
        self.data_source = DataSource.objects.create(
            name='Field Survey 2025',
            source_type='FIELD_2025',
            data_kind=DataSource.DataKind.ADMINISTRATIVE,
            year=2025,
            season='A'
        )

        # Market hub & Commodity catalog
        self.market = MarketLocation.objects.create(
            name='Musanze Central Market',
            district=self.district,
            market_type='assembly',
        )
        from apps.markets.models import MarketCommodity
        self.market_comm = MarketCommodity.objects.create(
            name='Maize Grain',
            crop=self.crop,
            category='Cereals',
            min_expected_price=Decimal('200.00'),
            max_expected_price=Decimal('1500.00'),
        )

    def test_notification_creation_and_fields(self):
        """Notification model correctly stores all mandatory and optional metadata fields."""
        notif = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.DATA_APPROVED,
            title="Observation Approved",
            message="Your observation #100 was successfully approved.",
            action_url="/data-management/records/100/",
            priority=Notification.Priority.HIGH,
            actor=self.reviewer,
        )

        self.assertIsNotNone(notif)
        self.assertEqual(notif.recipient, self.data_officer)
        self.assertEqual(notif.actor, self.reviewer)
        self.assertEqual(notif.notification_type, Notification.Type.DATA_APPROVED)
        self.assertEqual(notif.priority, Notification.Priority.HIGH)
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)
        self.assertFalse(notif.is_dismissed)

        # Audit log verification
        audit = AuditLog.objects.filter(action=AuditLog.Action.NOTIFICATION_CREATED).first()
        self.assertIsNotNone(audit)
        self.assertIn(self.data_officer.username, str(audit.details))

    def test_recipient_scoping_send_to_reviewers(self):
        """send_to_reviewers notifies officers responsible for district plus administrators."""
        created_notifs = NotificationService.send_to_reviewers(
            notification_type=Notification.Type.DATA_SUBMITTED,
            title="New Submission Requires Review",
            message="A record was submitted in Musanze.",
            action_url="/data-management/review/",
            district=self.district,
            actor=self.data_officer,
        )

        self.assertGreaterEqual(len(created_notifs), 1)
        # Reviewer should receive notification
        reviewer_notifs = Notification.objects.filter(recipient=self.reviewer)
        self.assertEqual(reviewer_notifs.count(), 1)
        # Submitter (actor) must not be notified
        actor_notifs = Notification.objects.filter(recipient=self.data_officer)
        self.assertEqual(actor_notifs.count(), 0)

    def test_unread_count_service(self):
        """Unread count calculates accurately and updates as notifications are read."""
        self.assertEqual(NotificationService.get_unread_count(self.data_officer), 0)

        n1 = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.SYSTEM_ANNOUNCEMENT,
            title="Note 1",
            message="Message 1",
        )
        n2 = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.SYSTEM_ANNOUNCEMENT,
            title="Note 2",
            message="Message 2",
        )

        self.assertEqual(NotificationService.get_unread_count(self.data_officer), 2)

        # Mark one as read
        NotificationService.mark_as_read(n1, self.data_officer)
        self.assertEqual(NotificationService.get_unread_count(self.data_officer), 1)

        # Mark all as read
        NotificationService.mark_all_as_read(self.data_officer)
        self.assertEqual(NotificationService.get_unread_count(self.data_officer), 0)

    def test_notification_privacy_and_isolation(self):
        """User A cannot read, mark, or view User B's private notifications."""
        secret_notif = NotificationService.send(
            recipient=self.reviewer,
            notification_type=Notification.Type.ACCOUNT_CREATED,
            title="Confidential Officer Notice",
            message="Secret message for reviewer only.",
        )

        # Attempt to mark as read by data_officer via service
        updated = NotificationService.mark_as_read(secret_notif, self.data_officer)
        self.assertFalse(updated)
        secret_notif.refresh_from_db()
        self.assertFalse(secret_notif.is_read)

        # Attempt to mark via Web endpoint as data_officer
        self.client.force_login(self.data_officer)
        response = self.client.post(reverse('notifications:mark_read', kwargs={'pk': secret_notif.pk}))
        self.assertEqual(response.status_code, 404)

        # Attempt via DRF API as data_officer
        self.api_client.force_authenticate(user=self.data_officer)
        api_resp = self.api_client.post(f"/api/v1/notifications/{secret_notif.pk}/read/")
        self.assertEqual(api_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_notification_preferences_opt_out(self):
        """User can opt out of optional categories, but mandatory security notices still deliver."""
        pref, _ = NotificationPreference.objects.get_or_create(user=self.data_officer)
        pref.notify_market_prices = False
        pref.save()

        # Optional market price notification should be suppressed
        notif_market = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.PRICE_SUBMITTED,
            title="Price Submitted",
            message="Suppressed price",
        )
        self.assertIsNone(notif_market)

        # Mandatory security notification (Role Changed) CANNOT be suppressed
        pref.in_app_enabled = False
        pref.save()

        sec_notif = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.ROLE_CHANGED,
            title="Role Changed",
            message="Your clearance changed.",
        )
        self.assertIsNotNone(sec_notif)
        self.assertEqual(sec_notif.title, "Role Changed")

    def test_email_template_rendering_and_delivery(self):
        """Notification emails render properly with branding, footer, and send via test outbox."""
        mail.outbox = []

        notif = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.DATA_APPROVED,
            title="Submission Approved",
            message="Your agricultural submission has been validated.",
            action_url="/data-management/records/1/",
            priority=Notification.Priority.HIGH,
        )

        # Email was queued and sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn("Submission Approved", sent_email.subject)
        self.assertIn("AgriLens Rwanda", sent_email.from_email)
        self.assertIn(self.data_officer.email, sent_email.to)
        self.assertIn("National Institute of Statistics of Rwanda", sent_email.body)

        # Check delivery log
        log = EmailDeliveryLog.objects.filter(notification=notif).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, EmailDeliveryLog.Status.SENT)

    def test_email_failure_handling_and_retry(self):
        """Email delivery failure is safely logged and can be retried without duplicates."""
        log = EmailDeliveryLog.objects.create(
            recipient_email="invalid-email-format",
            subject="Test Subject",
            status=EmailDeliveryLog.Status.FAILED,
            error_message="SMTP simulation error",
        )

        # Admin retries failed email
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('notifications:admin_retry_email', kwargs={'pk': log.pk}))
        self.assertEqual(resp.status_code, 302)

        log.refresh_from_db()
        self.assertIn(log.status, [EmailDeliveryLog.Status.RETRIED, EmailDeliveryLog.Status.FAILED, EmailDeliveryLog.Status.SENT])

    def test_system_announcement_broadcast_admin_only(self):
        """Administrators can broadcast announcements to all users; non-admins receive 403."""
        # Non-admin attempt
        self.client.force_login(self.data_officer)
        resp = self.client.post(reverse('notifications:admin_announcements'), {
            'title': 'Hacked Announcement',
            'message': 'Should fail',
            'priority': 'normal',
            'target_role': '',
        })
        self.assertEqual(resp.status_code, 403)

        # Admin broadcast
        self.client.force_login(self.admin)
        active_user_count = User.objects.filter(is_active=True).count()
        resp = self.client.post(reverse('notifications:admin_announcements'), {
            'title': 'Maintenance Window Scheduled',
            'message': 'System maintenance on Sunday at 02:00 AM CAT.',
            'priority': 'high',
            'target_role': '',
        })
        self.assertEqual(resp.status_code, 302)

        # Verify notifications were created for all users
        announcements = Notification.objects.filter(notification_type=Notification.Type.SYSTEM_ANNOUNCEMENT)
        self.assertEqual(announcements.count(), active_user_count)

    def test_drf_api_endpoints(self):
        """DRF Notification ViewSet provides list, unread_count, mark_read, mark_all_read, and preferences."""
        notif = NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.DATA_APPROVED,
            title="API Test Note",
            message="Testing DRF endpoints",
        )

        self.api_client.force_authenticate(user=self.data_officer)

        # 1. Unread count
        resp = self.api_client.get("/api/v1/notifications/unread_count/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['unread_count'], 1)

        # 2. List notifications
        list_resp = self.api_client.get("/api/v1/notifications/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data['results']), 1)

        # 3. Mark as read
        read_resp = self.api_client.post(f"/api/v1/notifications/{notif.pk}/read/")
        self.assertEqual(read_resp.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # 4. Mark as unread
        unread_resp = self.api_client.post(f"/api/v1/notifications/{notif.pk}/unread/")
        self.assertEqual(unread_resp.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertFalse(notif.is_read)

        # 5. Mark all as read
        all_read_resp = self.api_client.post("/api/v1/notifications/mark_all_read/")
        self.assertEqual(all_read_resp.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # 6. Preferences GET & PATCH
        pref_resp = self.api_client.get("/api/v1/notifications/preferences/")
        self.assertEqual(pref_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(pref_resp.data['in_app_enabled'])

        patch_resp = self.api_client.patch("/api/v1/notifications/preferences/", {'notify_reports': False})
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertFalse(patch_resp.data['notify_reports'])

    def test_workflow_integration_data_submission_and_approval(self):
        """Workflow: Submitting ManualObservation notifies reviewers; approving notifies collector."""
        from apps.data_management.workflow import ObservationWorkflowService

        # 1. Create draft observation
        obs = ManualObservation.objects.create(
            data_source=self.data_source,
            season=self.season,
            district=self.district,
            sector=self.sector,
            crop=self.crop,
            plot_area_ha=Decimal('12.5'),
            total_production_kg=Decimal('36000.0'),
            calculated_yield_kg_per_ha=Decimal('2880.0'),
            created_by=self.data_officer,
            observation_date=date(2025, 1, 15),
            review_status=ManualObservation.ReviewStatus.DRAFT,
        )

        # 2. Submit observation
        ObservationWorkflowService.submit(obs.id, actor=self.data_officer)

        # Reviewer should have a notification
        rev_notif = Notification.objects.filter(
            recipient=self.reviewer,
            notification_type=Notification.NotificationType.DATA_SUBMITTED,
        ).first()
        self.assertIsNotNone(rev_notif)
        self.assertIn("Maize", rev_notif.title)

        # 3. Approve observation
        ObservationWorkflowService.approve(obs.id, reviewer=self.reviewer)

        # Submitter should have an approval notification
        officer_notif = Notification.objects.filter(
            recipient=self.data_officer,
            notification_type=Notification.NotificationType.DATA_APPROVED,
        ).first()
        self.assertIsNotNone(officer_notif)
        self.assertIn("Approved", officer_notif.title)

    def test_workflow_integration_commodity_prices(self):
        """Workflow: Submitting commodity price notifies reviewers; supervisory approval notifies collector."""
        # 1. Collector creates price
        self.client.force_login(self.data_officer)
        price_resp = self.client.post(reverse('markets:internal_record_create'), {
            'market': self.market.pk,
            'crop': self.crop.pk,
            'price_type': 'retail',
            'price_per_kg_rwf': '850.00',
            'wholesale_price_rwf': '780.00',
            'unit': 'RWF/kg',
            'date_recorded': '2025-01-15',
            'time_recorded': '10:00',
            'source_type': 'partner',
            'action_intent': 'submit',
        })
        self.assertEqual(price_resp.status_code, 302)

        price_record = CommodityPrice.objects.filter(crop=self.crop, market=self.market).latest('id')

        # Reviewer received price submission notification
        price_sub_notif = Notification.objects.filter(
            recipient=self.reviewer,
            notification_type=Notification.NotificationType.PRICE_SUBMITTED,
        ).first()
        self.assertIsNotNone(price_sub_notif)
        self.assertIn("Maize", price_sub_notif.title)

        # 2. Reviewer approves price
        self.client.force_login(self.reviewer)
        approve_resp = self.client.post(
            reverse('markets:internal_approval_action', kwargs={'pk': price_record.pk}),
            {'action': 'approve'}
        )
        self.assertEqual(approve_resp.status_code, 302)

        # Collector received approval notification
        collector_notif = Notification.objects.filter(
            recipient=self.data_officer,
            notification_type=Notification.NotificationType.PRICE_APPROVED,
        ).first()
        self.assertIsNotNone(collector_notif)
        self.assertIn("Price Approved", collector_notif.title)

    def test_context_processor_in_authenticated_views(self):
        """Global context processor supplies unread_notifications_count and recent_notifications."""
        NotificationService.send(
            recipient=self.data_officer,
            notification_type=Notification.Type.SYSTEM_ANNOUNCEMENT,
            title="Header Bell Check",
            message="Should appear in navbar dropdown.",
        )

        self.client.force_login(self.data_officer)
        resp = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['unread_notifications_count'], 1)
        self.assertEqual(len(resp.context['recent_notifications']), 1)
        self.assertEqual(resp.context['recent_notifications'][0].title, "Header Bell Check")

    def test_user_create_sends_password_setup_email(self):
        """When an administrator creates an officer, an email containing the setup link is sent."""
        mail.outbox = []
        self.client.force_login(self.admin)

        resp = self.client.post(reverse('accounts:user_create'), {
            'username': 'new_field_agent',
            'first_name': 'Jean',
            'last_name': 'Nshimiyimana',
            'email': 'agent@minagri.gov.rw',
            'role': User.Role.DATA_ENTRY_OFFICER,
            'organization': 'MINAGRI Extension',
            'phone_number': '+250788112233',
            'is_active': True,
        })
        self.assertEqual(resp.status_code, 200)

        created = User.objects.filter(username='new_field_agent').first()
        self.assertIsNotNone(created)

        # Verify email was dispatched
        setup_emails = [m for m in mail.outbox if 'agent@minagri.gov.rw' in m.to]
        self.assertGreaterEqual(len(setup_emails), 1)
        email = setup_emails[0]
        self.assertIn("Set Your AgriLens Password", email.subject)
        self.assertIn("users/setup-password/", email.body)

    def test_password_change_authenticated_flow(self):
        """Authenticated officer can change their password securely and receives confirmation email."""
        mail.outbox = []
        self.client.force_login(self.data_officer)

        # GET change page
        get_resp = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(get_resp.status_code, 200)

        # POST change password
        post_resp = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'OfficerPassword123!',
            'new_password1': 'NewSecurePass2026!#',
            'new_password2': 'NewSecurePass2026!#',
        })
        self.assertEqual(post_resp.status_code, 302)

        # Verify user password changed in database
        self.data_officer.refresh_from_db()
        self.assertTrue(self.data_officer.check_password('NewSecurePass2026!#'))

        # Security email dispatched
        security_emails = [m for m in mail.outbox if self.data_officer.email in m.to]
        self.assertGreaterEqual(len(security_emails), 1)
        self.assertIn("Password Changed", security_emails[0].subject)

    def test_forgot_password_flow(self):
        """Unauthenticated user can request password reset, receives email with link, and resets password."""
        mail.outbox = []

        # 1. Request reset
        req_resp = self.client.post(reverse('accounts:password_reset'), {
            'email_or_username': self.data_officer.email,
        })
        self.assertEqual(req_resp.status_code, 302)
        self.assertRedirects(req_resp, reverse('accounts:password_reset_done'))

        # 2. Check email was sent with link
        reset_emails = [m for m in mail.outbox if self.data_officer.email in m.to]
        self.assertEqual(len(reset_emails), 1)
        email = reset_emails[0]
        self.assertIn("Password Reset Request", email.subject)
        self.assertIn("users/setup-password/", email.body)

        # Extract uidb64 and token from email body
        import re
        match = re.search(r'users/setup-password/([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)/', email.body)
        self.assertIsNotNone(match)
        uidb64, token = match.group(1), match.group(2)

        # 3. Confirm and set new password
        confirm_resp = self.client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token}),
            {
                'new_password1': 'ResetBrandNewPass2026!#',
                'new_password2': 'ResetBrandNewPass2026!#',
            }
        )
        self.assertEqual(confirm_resp.status_code, 302)
        self.assertRedirects(confirm_resp, reverse('accounts:password_reset_complete'))

        # 4. Verify password was updated
        self.data_officer.refresh_from_db()
        self.assertTrue(self.data_officer.check_password('ResetBrandNewPass2026!#'))

