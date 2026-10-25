"""
Security Login Event Monitoring & Administrator Alert Dispatcher for AgriLens Rwanda.
Monitors user authentication events, extracts client IP and user-agent metadata,
resolves approximate geographic location, and dispatches immediate security alert
emails to ndolijeandamascene@gmail.com.
"""
import sys
import logging
import threading
import ipaddress
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from django.utils.timezone import get_current_timezone as ZoneInfo
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from apps.accounts.models import AuditLog, User
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)

# Primary Administrator Recipient for Critical Security & Login Alerts
ADMIN_SECURITY_NOTIFICATION_EMAIL = "ndolijeandamascene@gmail.com"


def is_running_tests():
    """Detects whether code is executing within automated test runner."""
    return 'test' in sys.argv or any('pytest' in arg for arg in sys.argv)


def get_client_ip(request):
    """
    Safely extracts client IP address accounting for reverse proxies (Traefik, Easypanel, Cloudflare).
    """
    if not request:
        return "127.0.0.1"

    # Cloudflare header
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip.strip()

    # Standard proxy forwarded header
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    # Real IP header
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip.strip()

    # Direct remote address fallback
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def resolve_ip_location(ip_address):
    """
    Resolves geographic location (City, Region, Country, Organization) for a given IP address.
    Features fast timeout and graceful fallback for localhost/private networks.
    """
    if not ip_address:
        return {
            'city': 'Unknown',
            'region': 'Unknown',
            'country': 'Unknown',
            'country_code': '',
            'org': 'Unknown',
            'formatted': 'Unknown IP Address',
        }

    # Check if IP is private, loopback, or reserved
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
            return {
                'city': 'Internal / Localhost',
                'region': 'Internal Network',
                'country': 'Rwanda (Internal/Local)',
                'country_code': 'RW',
                'org': 'Deployment Reverse Proxy / Local Development',
                'formatted': 'Localhost / Internal Server Network',
            }
    except ValueError:
        pass

    # Fast external geolocation lookup (2.0s timeout to never block background workers)
    try:
        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,regionName,city,org,isp,query"
        resp = requests.get(url, timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                city = data.get('city') or 'Unknown City'
                region = data.get('regionName') or 'Unknown Region'
                country = data.get('country') or 'Unknown Country'
                country_code = data.get('countryCode') or ''
                org = data.get('org') or data.get('isp') or 'Unknown Provider'
                
                parts = [p for p in [city, region, country] if p and p != 'Unknown']
                location_str = ", ".join(parts) if parts else "Location Resolved"
                if org and org != 'Unknown':
                    location_str = f"{location_str} ({org})"

                return {
                    'city': city,
                    'region': region,
                    'country': country,
                    'country_code': country_code,
                    'org': org,
                    'formatted': location_str,
                }
    except Exception as exc:
        logger.debug(f"GeoIP resolution failed for {ip_address}: {exc}")

    return {
        'city': 'Unknown',
        'region': 'Unknown',
        'country': 'Unknown',
        'country_code': '',
        'org': 'Unknown',
        'formatted': 'Approximate location lookup timed out',
    }


def _execute_security_alert_dispatch(event_type, username, ip_address, user_agent, user_id=None, raw_timestamp=None):
    """
    Internal delivery function executed synchronously or within a daemon background thread.
    Renders email, logs to AuditLog, and dispatches to ndolijeandamascene@gmail.com.
    """
    user = None
    role_display = "Unknown Role"
    user_email = ""
    user_full_name = ""

    if user_id:
        try:
            user = User.objects.get(pk=user_id)
            role_display = user.get_role_display()
            user_email = user.email
            user_full_name = user.get_full_name() or user.username
        except User.DoesNotExist:
            pass

    # Format timestamp in Rwanda Standard Time (Africa/Kigali)
    event_time = raw_timestamp or timezone.now()
    kigali_time = timezone.localtime(event_time)
    formatted_time = kigali_time.strftime("%A, %d %B %Y at %H:%M:%S CAT")

    # Resolve IP Location
    location_info = resolve_ip_location(ip_address)
    formatted_location = location_info.get('formatted', 'Unknown Location')

    # Subject Line
    is_success = (event_type == 'LOGIN_SUCCESS')
    if is_success:
        subject = f"🚨 [AgriLens Security] Successful Login: '{username}' from {ip_address}"
        status_badge_color = "#10B981"  # Emerald
        status_label = "AUTHENTICATION SUCCESSFUL"
        event_heading = "Official Officer Login Detected"
    else:
        subject = f"⚠️ [AgriLens Security] FAILED Login Attempt: '{username}' from {ip_address}"
        status_badge_color = "#EF4444"  # Red
        status_label = "AUTHENTICATION FAILED"
        event_heading = "Failed Login Attempt Detected"

    # Base Application URL
    base_url = "https://agrilens.ndoli.dev"
    audit_log_url = f"{base_url}/accounts/audit-log/"

    # Render HTML Email Body
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>{subject}</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; color: #1e293b; }}
        .container {{ max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }}
        .header {{ background: #001F3B; padding: 24px 30px; text-align: left; border-bottom: 3px solid {status_badge_color}; }}
        .header h1 {{ margin: 0; color: #ffffff; font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }}
        .header p {{ margin: 4px 0 0 0; color: #94a3b8; font-size: 13px; }}
        .content {{ padding: 30px; }}
        .badge {{ display: inline-block; padding: 6px 12px; font-size: 12px; font-weight: 700; border-radius: 6px; color: #ffffff; background-color: {status_badge_color}; text-transform: uppercase; letter-spacing: 0.5px; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        .details-table th {{ text-align: left; padding: 10px 14px; background: #f8fafc; color: #475569; width: 35%; border-bottom: 1px solid #e2e8f0; font-weight: 600; }}
        .details-table td {{ padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #0f172a; word-break: break-all; }}
        .footer {{ background: #f8fafc; padding: 20px 30px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
        .btn {{ display: inline-block; padding: 10px 20px; background-color: #005CAB; color: #ffffff !important; text-decoration: none; font-weight: 600; font-size: 14px; border-radius: 6px; margin-top: 10px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🌾 AgriLens &bull; Security & Access Monitor</h1>
          <p>National Agricultural Productivity Intelligence Platform — Rwanda</p>
        </div>
        <div class="content">
          <div style="margin-bottom: 16px;">
            <span class="badge">{status_label}</span>
          </div>
          <h2 style="margin: 0 0 10px 0; font-size: 18px; color: #0f172a;">{event_heading}</h2>
          <p style="margin: 0 0 20px 0; font-size: 14px; color: #475569; line-height: 1.5;">
            An authentication event has been logged for your AgriLens deployment at <strong>{base_url}</strong>. Full event parameters are detailed below:
          </p>
          <table class="details-table">
            <tr>
              <th>Event Type</th>
              <td><strong>{event_type}</strong> ({status_label})</td>
            </tr>
            <tr>
              <th>Target Username</th>
              <td><strong>{username}</strong></td>
            </tr>
            <tr>
              <th>Account Profile</th>
              <td>{user_full_name} ({role_display})</td>
            </tr>
            <tr>
              <th>Registered Email</th>
              <td>{user_email or 'None / Unregistered'}</td>
            </tr>
            <tr>
              <th>Client IP Address</th>
              <td><code>{ip_address}</code></td>
            </tr>
            <tr>
              <th>Geographic Location</th>
              <td>📍 <strong>{formatted_location}</strong></td>
            </tr>
            <tr>
              <th>Timestamp (Kigali)</th>
              <td>🕒 <strong>{formatted_time}</strong></td>
            </tr>
            <tr>
              <th>Device / User-Agent</th>
              <td style="font-size: 12px; color: #475569;">{user_agent or 'Unknown Client'}</td>
            </tr>
          </table>
          <div style="text-align: center; margin-top: 25px;">
            <a href="{audit_log_url}" class="btn" target="_blank">Review Live Security Audit Trail &rarr;</a>
          </div>
        </div>
        <div class="footer">
          <p style="margin: 0 0 6px 0;">This security notification was automatically dispatched to the authorized administrator.</p>
          <p style="margin: 0;">AgriLens Intelligence Engine &bull; Developed for 2026 NISR Big Data Hackathon &bull; Kigali, Rwanda</p>
        </div>
      </div>
    </body>
    </html>
    """

    # Plain text fallback
    plain_content = f"""
AgriLens Security Alert: {event_heading}
======================================================
Status: {status_label}
Event: {event_type}
Username: {username}
Officer: {user_full_name} ({role_display})
Email: {user_email or 'None'}
Client IP: {ip_address}
Location: {formatted_location}
Time (Kigali): {formatted_time}
User-Agent: {user_agent or 'Unknown Client'}
Live Portal: {base_url}
Security Audit Log: {audit_log_url}
======================================================
AgriLens Intelligence Engine - Kigali, Rwanda
    """.strip()

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'AgriLens Security <notifications@agrilens.ndoli.dev>')

    # 1. Dispatch Email to ndolijeandamascene@gmail.com
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=from_email,
            to=[ADMIN_SECURITY_NOTIFICATION_EMAIL]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
        logger.info(f"Security login alert email delivered to {ADMIN_SECURITY_NOTIFICATION_EMAIL} for user '{username}' from {ip_address}")
    except Exception as exc:
        logger.error(f"Failed to dispatch security alert email to {ADMIN_SECURITY_NOTIFICATION_EMAIL}: {exc}")

    # 2. Record in Immutable Security AuditLog
    try:
        audit_action = AuditLog.Action.LOGIN_SUCCESS if is_success else AuditLog.Action.LOGIN_FAILED
        AuditLog.objects.create(
            actor=user,
            action=audit_action,
            target_model='User',
            target_id=str(user.pk) if user else username,
            target_repr=f"User: {username}",
            ip_address=ip_address if ('.' in ip_address or ':' in ip_address) else None,
            details=f"Event: {event_type} | Location: {formatted_location} | Time: {formatted_time} | Agent: {(user_agent or '')[:120]}"
        )
    except Exception as exc:
        logger.error(f"Failed to record login AuditLog: {exc}")

    # 3. Create In-App Notification for Admin User (if admin user exists)
    try:
        admin_user = User.objects.filter(role=User.Role.ADMIN, is_active=True).first()
        if admin_user:
            notif_title = f"Login Alert: {username} from {ip_address}" if is_success else f"Failed Login: {username} from {ip_address}"
            notif_msg = f"{event_heading} on {formatted_time}. IP: {ip_address} ({formatted_location})."
            Notification.objects.create(
                recipient=admin_user,
                notification_type=Notification.NotificationType.SECURITY_ALERT,
                title=notif_title[:200],
                message=notif_msg,
                action_url="/accounts/audit-log/",
                priority=Notification.Priority.HIGH if is_success else Notification.Priority.CRITICAL,
                actor=user,
                metadata={
                    'event_type': event_type,
                    'username': username,
                    'ip_address': ip_address,
                    'location': formatted_location,
                    'timestamp': formatted_time,
                }
            )
    except Exception as exc:
        logger.debug(f"Could not create in-app notification for admin: {exc}")


def trigger_login_security_alert(event_type, username, request=None, user=None):
    """
    Public entry point to trigger a login security alert.
    Executes in a non-blocking daemon thread so the user experiences zero login latency.
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
    user_id = user.pk if user else None
    now_time = timezone.now()

    if is_running_tests():
        # Execute synchronously during test runs for predictable assertion
        _execute_security_alert_dispatch(
            event_type=event_type,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            raw_timestamp=now_time
        )
    else:
        # Launch non-blocking background daemon thread in production/live server
        thread = threading.Thread(
            target=_execute_security_alert_dispatch,
            kwargs={
                'event_type': event_type,
                'username': username,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'user_id': user_id,
                'raw_timestamp': now_time
            },
            daemon=True
        )
        thread.start()
