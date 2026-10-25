"""
Background Email Delivery & Asynchronous Task Processing.
Delivers emails asynchronously without delaying user requests, with safe failure handling,
idempotency, and audit logging.
"""
import sys
import logging
import threading
from django.db import transaction
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.accounts.permissions import AuditService
from apps.accounts.models import AuditLog

logger = logging.getLogger(__name__)


def is_running_tests():
    """Returns True if running under pytest or manage.py test."""
    return 'test' in sys.argv or any('pytest' in arg for arg in sys.argv)


def deliver_email_record(delivery_log_id):
    """
    Executes email dispatch for a specific EmailDeliveryLog record.
    Guarantees idempotency: will not re-send an email already marked SENT.
    """
    from apps.notifications.models import EmailDeliveryLog, Notification

    try:
        log = EmailDeliveryLog.objects.select_related('notification__recipient').get(pk=delivery_log_id)
    except EmailDeliveryLog.DoesNotExist:
        logger.error(f"EmailDeliveryLog #{delivery_log_id} not found.")
        return False

    if log.status == EmailDeliveryLog.Status.SENT:
        logger.info(f"EmailDeliveryLog #{delivery_log_id} already sent. Skipping duplicate.")
        return True

    notification = log.notification
    recipient_email = log.recipient_email
    subject = log.subject

    if not recipient_email or '@' not in recipient_email:
        log.status = EmailDeliveryLog.Status.FAILED
        log.error_message = f"Invalid recipient email address: '{recipient_email}'"
        log.save(update_fields=['status', 'error_message'])
        return False

    try:
        from apps.notifications.emails import EmailService
        html_content, text_content = EmailService.render_notification_email(notification)

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'AgriLens Rwanda <ndolijeandamascene3@gmail.com>')
        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient_email]
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send(fail_silently=False)

        # Mark log as sent
        log.status = EmailDeliveryLog.Status.SENT
        log.sent_at = timezone.now()
        log.save(update_fields=['status', 'sent_at'])

        # Update notification record
        if notification:
            notification.email_sent = True
            notification.email_sent_at = log.sent_at
            notification.save(update_fields=['email_sent', 'email_sent_at'])

        # Audit log entry
        AuditService.log(
            action=AuditLog.Action.EMAIL_SENT,
            actor=notification.actor if notification else None,
            target=notification,
            details={
                'recipient_email': recipient_email,
                'subject': subject,
                'notification_id': notification.id if notification else None,
                'status': 'SENT'
            }
        )
        return True

    except Exception as exc:
        logger.exception(f"Failed to deliver email for log #{delivery_log_id}: {exc}")
        log.status = EmailDeliveryLog.Status.FAILED
        log.error_message = str(exc)
        log.save(update_fields=['status', 'error_message'])

        if notification:
            AuditService.log(
                action=AuditLog.Action.EMAIL_FAILED,
                actor=notification.actor if notification else None,
                target=notification,
                details={
                    'recipient_email': recipient_email,
                    'subject': subject,
                    'error': str(exc)
                }
            )
        return False


def enqueue_email_delivery(delivery_log_id):
    """
    Dispatches email delivery safely.
    In testing environments, runs synchronously for immediate test verification.
    In normal runtime, defers execution until transaction commits, then spawns a daemon thread.
    """
    if is_running_tests():
        deliver_email_record(delivery_log_id)
        return

    def _threaded_delivery():
        deliver_email_record(delivery_log_id)

    transaction.on_commit(lambda: threading.Thread(target=_threaded_delivery, daemon=True).start())
