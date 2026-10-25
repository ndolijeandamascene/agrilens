"""
Django Authentication Signals for Security & Login Monitoring.
Listens for user_logged_in and user_login_failed signals to dispatch
real-time alerts with IP address, location, and timestamp to ndolijeandamascene@gmail.com.
"""
import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from apps.accounts.security_alerts import trigger_login_security_alert

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    """Fired upon successful authentication of any user."""
    try:
        username = getattr(user, 'username', 'Unknown User')
        trigger_login_security_alert(
            event_type='LOGIN_SUCCESS',
            username=username,
            request=request,
            user=user
        )
    except Exception as exc:
        logger.error(f"Error handling user_logged_in signal: {exc}")


@receiver(user_login_failed)
def handle_user_login_failed(sender, credentials, request, **kwargs):
    """Fired upon failed authentication attempt."""
    try:
        username = credentials.get('username', 'Unknown User') if credentials else 'Unknown User'
        trigger_login_security_alert(
            event_type='LOGIN_FAILED',
            username=username,
            request=request,
            user=None
        )
    except Exception as exc:
        logger.error(f"Error handling user_login_failed signal: {exc}")
