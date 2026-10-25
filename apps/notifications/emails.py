"""
Email Notification Service for AgriLens Rwanda.
Builds branded, accessible emails, checks recipient preferences,
and integrates with background task dispatchers.
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from apps.notifications.models import EmailDeliveryLog, NotificationPreference


class EmailService:
    """
    Centralized email dispatch and rendering service for platform notifications.
    """

    @classmethod
    def get_base_url(cls, request=None):
        """Constructs canonical application base URL for absolute links in emails."""
        if request:
            try:
                return request.build_absolute_uri('/')[:-1]
            except Exception:
                pass
        
        # Default configured domain or localhost
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        host = 'agrilens.ndoli.dev'
        if allowed_hosts and allowed_hosts[0] not in ['*', 'localhost', '127.0.0.1', '[::1]', 'testserver']:
            host = allowed_hosts[0]
        return f"https://{host}"

    @classmethod
    def format_subject(cls, notification):
        """Generates clear, standardized subject lines per AgriLens convention."""
        prefix = "AgriLens — "
        return f"{prefix}{notification.title}"

    @classmethod
    def render_notification_email(cls, notification, request=None):
        """
        Renders HTML and plain-text email bodies for a given Notification record.
        """
        base_url = cls.get_base_url(request)
        action_url = notification.action_url
        if action_url and not action_url.startswith(('http://', 'https://')):
            action_url = f"{base_url}{action_url if action_url.startswith('/') else '/' + action_url}"

        preferences_url = f"{base_url}/notifications/preferences/"

        meta = notification.metadata or {}
        action_label = meta.get('action_label')
        if not action_label:
            if 'password' in (action_url or '').lower() or 'setup' in (action_url or '').lower():
                action_label = "Configure Password & Activate Credentials"
            else:
                action_label = "View in AgriLens"

        context = {
            'notification': notification,
            'subject': cls.format_subject(notification),
            'action_url': action_url,
            'action_label': action_label,
            'preferences_url': preferences_url,
            'details': meta.get('details', {}),
            'current_year': timezone.now().year,
        }

        html_body = render_to_string('notifications/emails/notification_email.html', context)
        text_body = render_to_string('notifications/emails/notification_email.txt', context)

        return html_body, text_body

    @classmethod
    def send_for_notification(cls, notification, request=None):
        """
        Evaluates user notification preferences and dispatches email via background worker.
        Enforces idempotency: does not duplicate delivery logs if already sent.
        """
        recipient = notification.recipient
        if not recipient or not recipient.email:
            return None

        # Check user notification preferences
        pref, _ = NotificationPreference.objects.get_or_create(user=recipient)
        if not pref.can_send_email(notification.notification_type):
            return None

        # Idempotency check: Don't re-create or duplicate sent logs
        existing_log = EmailDeliveryLog.objects.filter(
            notification=notification,
            status=EmailDeliveryLog.Status.SENT
        ).first()
        if existing_log:
            return existing_log

        subject = cls.format_subject(notification)
        delivery_log, created = EmailDeliveryLog.objects.get_or_create(
            notification=notification,
            recipient_email=recipient.email,
            subject=subject,
            defaults={'status': EmailDeliveryLog.Status.PENDING}
        )

        from apps.notifications.tasks import enqueue_email_delivery
        enqueue_email_delivery(delivery_log.id)
        return delivery_log

    @classmethod
    def retry_failed_email(cls, delivery_log_id):
        """
        Retries an email delivery that previously failed.
        """
        try:
            log = EmailDeliveryLog.objects.get(pk=delivery_log_id)
            log.status = EmailDeliveryLog.Status.PENDING
            log.attempts += 1
            log.error_message = ""
            log.save(update_fields=['status', 'attempts', 'error_message'])

            from apps.notifications.tasks import enqueue_email_delivery
            enqueue_email_delivery(log.id)
            return True
        except EmailDeliveryLog.DoesNotExist:
            return False
