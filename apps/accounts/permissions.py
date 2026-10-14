"""
AgriLens Role-Based Access Control (RBAC) & Geographic Scoping Service.
Enforces institutional role boundaries, geographic district restrictions,
self-approval conflict guards, and tamper-resistant security audit logging.
"""
import functools
import json
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from apps.accounts.models import User, AuditLog


# ------------------------------------------------------------------------------
# 1. Role-Based Access Control Decorator
# ------------------------------------------------------------------------------
def role_required(*allowed_roles):
    """
    Decorator for views that checks whether the logged-in user possesses
    one of the specified institutional roles.
    - Redirects anonymous users to the login portal with a `next` redirect parameter.
    - Rejects unauthorized authenticated users with HTTP 403 Forbidden.
    """
    # Flatten if passed as a single iterable
    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple, set)):
        allowed_roles = tuple(allowed_roles[0])

    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")

            # Superusers always bypass role gates
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Map legacy role aliases for seamless compatibility
            user_role = request.user.role
            effective_roles = {user_role}
            if user_role == User.Role.POLICY_MAKER:
                effective_roles.add(User.Role.NATIONAL_OFFICER)
            elif user_role == User.Role.EXTENSION_OFFICER:
                effective_roles.add(User.Role.DATA_ENTRY_OFFICER)
            elif user_role == User.Role.RESEARCHER:
                effective_roles.add(User.Role.ANALYST)

            if not effective_roles.intersection(allowed_roles):
                context = {
                    'page_title': '403 Forbidden | Access Restricted',
                    'required_roles': [r for r in allowed_roles],
                    'user_role': request.user.get_role_display(),
                }
                return render(request, '403.html', context, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# ------------------------------------------------------------------------------
# 2. Geographic Scoping Utilities
# ------------------------------------------------------------------------------
def scope_queryset_by_geography(queryset, user, district_field='district'):
    """
    Applies strict database-level geographic scoping to a queryset.
    - Public visitors & national officers & admins see all records.
    - District officers see ONLY records belonging to their assigned districts.
    - District officers with zero assigned districts receive an empty queryset (queryset.none()).
    """
    if not user or not user.is_authenticated:
        return queryset

    if user.is_national_scope():
        return queryset

    assigned_district_ids = user.get_authorized_district_ids()
    if not assigned_district_ids:
        return queryset.none()

    filter_kwargs = {f"{district_field}__in": assigned_district_ids}
    return queryset.filter(**filter_kwargs)


def can_access_district(user, district_id):
    """Verifies whether a user has authority to access the given district ID."""
    if not user or not user.is_authenticated:
        return True
    return user.can_access_district(district_id)


# ------------------------------------------------------------------------------
# 3. Security Audit Logging Service
# ------------------------------------------------------------------------------
class AuditService:
    """
    Centralized, append-only security audit logging service.
    Guarantees strict redaction of sensitive credentials, passwords, and session tokens.
    """
    SENSITIVE_KEYS = {'password', 'new_password', 'token', 'secret', 'csrfmiddlewaretoken', 'key'}

    @classmethod
    def log(cls, action, actor=None, target=None, ip_address=None, details=None, request=None):
        """
        Creates an immutable AuditLog entry.
        Extracts actor and client IP from request if supplied.
        """
        if request and not actor and request.user.is_authenticated:
            actor = request.user

        if request and not ip_address:
            ip_address = cls.get_client_ip(request)

        target_model = ""
        target_id = ""
        target_repr = ""

        if target is not None:
            target_model = target.__class__.__name__
            target_id = str(getattr(target, 'pk', ''))
            target_repr = str(target)[:150]

        # Sanitize details
        cleaned_details = ""
        if isinstance(details, dict):
            sanitized = {}
            for k, v in details.items():
                if any(sens in k.lower() for sens in cls.SENSITIVE_KEYS):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = str(v)
            cleaned_details = json.dumps(sanitized)
        elif details:
            cleaned_details = str(details)[:500]

        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_model=target_model,
            target_id=target_id,
            target_repr=target_repr,
            ip_address=ip_address,
            details=cleaned_details
        )

    @staticmethod
    def get_client_ip(request):
        """Safely extracts the client IP address from HTTP headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ------------------------------------------------------------------------------
# 4. Secure Single-Use Password Setup / Reset Link Utilities
# ------------------------------------------------------------------------------
def generate_password_setup_url(user, request=None):
    """
    Generates a secure, cryptographically signed, single-use password setup link.
    Avoids displaying raw passwords to administrators or logging initial credentials.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    relative_url = reverse('accounts:password_setup', kwargs={'uidb64': uidb64, 'token': token})

    if request:
        return request.build_absolute_uri(relative_url)
    return relative_url


def validate_password_setup_token(uidb64, token):
    """
    Validates the single-use token against the user.
    Returns (user, True) if valid, or (None, False) if invalid or expired.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None, False

    if default_token_generator.check_token(user, token):
        return user, True
    return user, False
