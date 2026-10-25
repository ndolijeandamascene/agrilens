"""
Automated Test Suite for Login Security Alerts, IP Tracking, and Geolocation Monitoring.
Verifies that successful and failed logins dispatch immediate alerts to ndolijeandamascene@gmail.com,
record AuditLog entries, and resolve geographic locations safely.
"""
import pytest
from django.urls import reverse
from django.core import mail
from apps.accounts.models import User, AuditLog
from apps.accounts.security_alerts import (
    ADMIN_SECURITY_NOTIFICATION_EMAIL,
    resolve_ip_location,
    get_client_ip,
    trigger_login_security_alert
)


@pytest.fixture
def test_admin_user(db):
    """Creates a test admin officer."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@agrilens.rw',
        password='AgriLens2026!'
    )


@pytest.fixture
def regular_officer(db):
    """Creates a regular test officer."""
    return User.objects.create_user(
        username='officer_kirehe',
        email='officer@kirehe.gov.rw',
        password='SecurePassword123!',
        role=User.Role.DISTRICT_OFFICER
    )


@pytest.mark.django_db
class TestLoginSecurityAlerts:
    """Verifies security monitoring for user authentication events."""

    def test_ip_location_resolution_for_localhost(self):
        """Verifies localhost and private IPs return valid internal network details."""
        for local_ip in ['127.0.0.1', '::1', '192.168.1.100', '10.0.0.5']:
            location = resolve_ip_location(local_ip)
            assert 'formatted' in location
            assert 'Internal' in location['formatted'] or 'Localhost' in location['formatted']

    def test_ip_location_resolution_for_empty_ip(self):
        """Verifies empty IP addresses are handled gracefully."""
        location = resolve_ip_location('')
        assert 'formatted' in location
        assert 'Unknown' in location['formatted']

    def test_successful_login_dispatches_email_to_admin(self, client, test_admin_user):
        """
        Verifies that logging in successfully sends a security email to ndolijeandamascene@gmail.com,
        including event, IP address, and location.
        """
        mail.outbox = []
        login_url = reverse('accounts:login')

        response = client.post(
            login_url,
            {
                'username': 'admin',
                'password': 'AgriLens2026!',
            },
            REMOTE_ADDR='197.243.20.15',  # Rwanda ISP IP
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgriLensTestBrowser/1.0'
        )

        assert response.status_code == 302

        # Verify email was dispatched
        assert len(mail.outbox) >= 1
        security_email = mail.outbox[-1]
        assert ADMIN_SECURITY_NOTIFICATION_EMAIL in security_email.to
        assert "Successful Login" in security_email.subject
        assert "admin" in security_email.subject
        assert "197.243.20.15" in security_email.subject

        # Verify body contents
        email_body = security_email.body
        assert "197.243.20.15" in email_body
        assert "admin" in email_body
        assert "AgriLensTestBrowser" in email_body
        assert "CAT" in email_body or "Africa/Kigali" in email_body or "2026" in email_body

        # Verify AuditLog record
        audit_entry = AuditLog.objects.filter(action=AuditLog.Action.LOGIN_SUCCESS, target_repr__contains='admin').first()
        assert audit_entry is not None
        assert audit_entry.ip_address == '197.243.20.15'

    def test_failed_login_attempt_dispatches_email_to_admin(self, client, db):
        """
        Verifies that a failed authentication attempt sends an alert email to ndolijeandamascene@gmail.com.
        """
        mail.outbox = []
        login_url = reverse('accounts:login')

        response = client.post(
            login_url,
            {
                'username': 'intruder_unknown',
                'password': 'WrongPassword123!',
            },
            REMOTE_ADDR='41.186.78.22',
            HTTP_USER_AGENT='MaliciousBot/2.0'
        )

        assert response.status_code == 200  # Form re-rendered with error

        # Verify security alert email was sent for failed login
        assert len(mail.outbox) >= 1
        alert_email = mail.outbox[-1]
        assert ADMIN_SECURITY_NOTIFICATION_EMAIL in alert_email.to
        assert "FAILED Login Attempt" in alert_email.subject
        assert "intruder_unknown" in alert_email.subject
        assert "41.186.78.22" in alert_email.subject

        # Verify audit log
        audit_entry = AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED, target_repr__contains='intruder_unknown').first()
        assert audit_entry is not None
        assert audit_entry.ip_address == '41.186.78.22'

    def test_direct_trigger_security_alert(self, regular_officer):
        """Verifies trigger_login_security_alert directly."""
        mail.outbox = []
        trigger_login_security_alert(
            event_type='LOGIN_SUCCESS',
            username=regular_officer.username,
            user=regular_officer
        )

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert ADMIN_SECURITY_NOTIFICATION_EMAIL in email.to
        assert regular_officer.username in email.subject
