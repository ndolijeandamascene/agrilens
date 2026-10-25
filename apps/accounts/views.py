"""
AgriLens Authentication and User Profile Views.
Enforces institutional role tiers: System Administrator, Agricultural Data Analyst,
Policy Maker / MINAGRI, Field Extension Officer, Agricultural Researcher.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import LoginForm, UserProfileForm


def login_view(request):
    """Handles official login for government officers and analysts."""
    if request.user.is_authenticated:
        return redirect('dashboard:overview')

    redirect_to = request.POST.get('next', request.GET.get('next', ''))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # expires on browser close

            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}! ({user.get_role_display()})")

            # Validate redirect URL safely to prevent open-redirect attacks
            if redirect_to and url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts={request.get_host()}):
                return redirect(redirect_to)
            return redirect('dashboard:overview')
        else:
            from django.contrib.auth.signals import user_login_failed
            attempted_username = request.POST.get('username', '').strip()
            user_login_failed.send(
                sender=form.__class__,
                credentials={'username': attempted_username},
                request=request
            )
            messages.error(request, "Invalid username or password. Please verify your official credentials.")
    else:
        form = LoginForm(request)

    context = {
        'page_title': 'Officer Sign In | AgriLens Rwanda',
        'form': form,
        'next': redirect_to,
    }
    return render(request, 'accounts/login.html', context)


def logout_view(request):
    """Terminates active session and redirects safely."""
    if request.user.is_authenticated:
        username = request.user.username
        auth_logout(request)
        messages.info(request, f"Officer {username} has been signed out successfully.")
    return redirect('dashboard:public_home')


@login_required(login_url='accounts:login')
def profile_view(request):
    """Displays and updates the authenticated officer's credentials and organization."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        'page_title': f"Officer Profile &bull; {request.user.username}",
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)


# ==============================================================================
# Administrative User Management Interface (Section 6)
# ==============================================================================
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from apps.geography.models import District
from apps.accounts.models import User, AuditLog
from apps.accounts.forms import (
    UserAdminCreationForm,
    UserAdminEditForm,
    PasswordSetupForm,
    PasswordChangeCustomForm,
    PasswordResetRequestForm,
)
from apps.accounts.permissions import role_required, AuditService, generate_password_setup_url, validate_password_setup_token


@role_required(User.Role.ADMIN)
def user_list(request):
    """
    Searchable, filterable, and paginated registry of all platform officers and accounts.
    Restricted strictly to System Administrators.
    """
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()
    district_filter = request.GET.get('district', '').strip()

    users = User.objects.select_related('assigned_province').prefetch_related('assigned_districts').all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(organization__icontains=query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    if district_filter and district_filter.isdigit():
        users = users.filter(assigned_districts__id=int(district_filter)).distinct()

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    districts = District.objects.all().order_by('name')

    context = {
        'page_title': 'User Management & Access Control | AgriLens',
        'page_heading': 'Officers & Role Management',
        'page_subheading': 'System administration, institutional roles, and security audit log',
        'page_obj': page_obj,
        'query': query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'district_filter': district_filter,
        'districts': districts,
        'roles': User.Role.choices,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    return render(request, 'accounts/user_list.html', context)


@role_required(User.Role.ADMIN)
def user_create(request):
    """
    Registers a new internal officer or analyst account.
    Generates a secure single-use password-setup link (Condition 6),
    avoiding transmission or display of initial plaintext passwords.
    """
    setup_link = None
    created_user = None

    if request.method == 'POST':
        form = UserAdminCreationForm(request.POST)
        if form.is_valid():
            created_user = form.save()
            setup_link = generate_password_setup_url(created_user, request)

            AuditService.log(
                action=AuditLog.Action.USER_CREATED,
                actor=request.user,
                target=created_user,
                details={'role': created_user.role, 'organization': created_user.organization},
                request=request
            )
            AuditService.log(
                action=AuditLog.Action.PASSWORD_RESET_LINK,
                actor=request.user,
                target=created_user,
                details={'channel': 'Admin Activation Link Generated'},
                request=request
            )

            messages.success(request, f"Officer account '{created_user.username}' created successfully!")

            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import Notification
                # 1. Dispatch official email with secure single-use password configuration link
                NotificationService.send(
                    recipient=created_user,
                    notification_type=Notification.NotificationType.PASSWORD_RESET_LINK,
                    title="Set Your AgriLens Password & Activate Account",
                    message=f"Welcome to AgriLens Rwanda! An official officer account has been created for you with clearance role: '{created_user.get_role_display()}'. Please click the link below to configure your password and activate your account.",
                    action_url=setup_link,
                    related_object=created_user,
                    actor=request.user,
                    priority=Notification.Priority.URGENT,
                    send_email=True,
                    request=request,
                    metadata={'action_label': 'Set Password & Activate Account'},
                )
                # 2. Inform platform administrators of new registration
                NotificationService.send_to_role(
                    role=User.Role.ADMIN,
                    notification_type=Notification.NotificationType.ACCOUNT_CREATED,
                    title=f"New Officer Registered: {created_user.username}",
                    message=f"Administrator {request.user.username} registered new officer '{created_user.username}' ({created_user.get_role_display()}).",
                    action_url=f"/accounts/users/{created_user.pk}/",
                    related_object=created_user,
                    actor=request.user,
                    priority=Notification.Priority.LOW,
                    exclude_users=[request.user, created_user],
                )
            except Exception:
                pass
        else:
            messages.error(request, "Please correct the highlighted errors to register the account.")
    else:
        form = UserAdminCreationForm()

    context = {
        'page_title': 'Register New Officer Account',
        'page_heading': 'Register Institutional Officer',
        'page_subheading': 'Institutional credentials, role clearances, and geographic jurisdictions',
        'form': form,
        'created_user': created_user,
        'setup_link': setup_link,
    }
    return render(request, 'accounts/user_form.html', context)


@role_required(User.Role.ADMIN)
def user_detail(request, pk):
    """Detailed profile, geographic assignments, and security audit log for a specific officer."""
    officer = get_object_or_404(
        User.objects.select_related('assigned_province').prefetch_related('assigned_districts'),
        pk=pk
    )
    recent_logs = AuditLog.objects.filter(
        Q(actor=officer) | Q(target_id=str(officer.pk), target_model='User')
    ).select_related('actor').order_by('-timestamp')[:20]

    context = {
        'page_title': f"Officer Dossier • {officer.username}",
        'page_heading': f"Officer Dossier • {officer.username}",
        'page_subheading': 'Institutional security profile, geographic jurisdiction, and audit trail',
        'officer': officer,
        'recent_logs': recent_logs,
    }
    return render(request, 'accounts/user_detail.html', context)


@role_required(User.Role.ADMIN)
def user_edit(request, pk):
    """
    Modifies officer details, role assignments, and geographic coverage.
    Guards strictly against privilege escalation and administrator self-lockout.
    """
    officer = get_object_or_404(User, pk=pk)
    prev_role = officer.role
    prev_districts = set(officer.assigned_districts.values_list('id', flat=True))

    if request.method == 'POST':
        form = UserAdminEditForm(request.POST, instance=officer, requesting_user=request.user)
        if form.is_valid():
            updated_user = form.save()

            # Audit role change if altered
            if prev_role != updated_user.role:
                AuditService.log(
                    action=AuditLog.Action.ROLE_CHANGED,
                    actor=request.user,
                    target=updated_user,
                    details={'from': prev_role, 'to': updated_user.role},
                    request=request
                )
                try:
                    from apps.notifications.services import NotificationService
                    from apps.notifications.models import Notification
                    NotificationService.send(
                        recipient=updated_user,
                        notification_type=Notification.Type.ROLE_CHANGED,
                        title="Institutional Clearance & Role Updated",
                        message=f"Your institutional role was updated from {prev_role} to {updated_user.role} by an administrator.",
                        action_url="/accounts/profile/",
                        related_object=updated_user,
                        actor=request.user,
                        priority=Notification.Priority.HIGH,
                    )
                except Exception:
                    pass

            # Audit geographic reassignment if altered
            new_districts = set(updated_user.assigned_districts.values_list('id', flat=True))
            if prev_districts != new_districts:
                AuditService.log(
                    action=AuditLog.Action.GEOGRAPHY_ASSIGNED,
                    actor=request.user,
                    target=updated_user,
                    details={'previous_district_ids': list(prev_districts), 'new_district_ids': list(new_districts)},
                    request=request
                )

            AuditService.log(
                action=AuditLog.Action.USER_UPDATED,
                actor=request.user,
                target=updated_user,
                details={'is_active': updated_user.is_active, 'organization': updated_user.organization},
                request=request
            )

            messages.success(request, f"Officer '{updated_user.username}' updated successfully.")
            return redirect('accounts:user_detail', pk=updated_user.pk)
        else:
            messages.error(request, "Failed to update officer. Please inspect the errors below.")
    else:
        form = UserAdminEditForm(instance=officer, requesting_user=request.user)

    context = {
        'page_title': f"Edit Officer • {officer.username}",
        'page_heading': f"Edit Officer • {officer.username}",
        'page_subheading': 'Institutional credentials, role clearances, and geographic jurisdictions',
        'form': form,
        'officer': officer,
    }
    return render(request, 'accounts/user_form.html', context)


@role_required(User.Role.ADMIN)
@require_POST
def user_toggle_status(request, pk):
    """Activates or deactivates an officer account with self-lockout protection."""
    officer = get_object_or_404(User, pk=pk)

    if request.user.pk == officer.pk:
        messages.error(request, "Security Guard: You cannot deactivate your own active administrator account.")
        return redirect('accounts:user_detail', pk=officer.pk)

    officer.is_active = not officer.is_active
    officer.save(update_fields=['is_active'])

    action = AuditLog.Action.USER_ACTIVATED if officer.is_active else AuditLog.Action.USER_DEACTIVATED
    AuditService.log(
        action=action,
        actor=request.user,
        target=officer,
        details={'is_active': officer.is_active},
        request=request
    )

    state_str = "ACTIVATED" if officer.is_active else "DEACTIVATED"
    messages.success(request, f"Account '{officer.username}' has been {state_str}.")

    try:
        from apps.notifications.services import NotificationService
        from apps.notifications.models import Notification
        NotificationService.send(
            recipient=officer,
            notification_type=Notification.Type.ACCOUNT_ACTIVATED if officer.is_active else Notification.Type.ACCOUNT_DEACTIVATED,
            title=f"Account Status Changed: {state_str.title()}",
            message=f"Your AgriLens institutional access was {state_str.lower()} by administrator {request.user.username}.",
            action_url="/accounts/login/",
            related_object=officer,
            actor=request.user,
            priority=Notification.Priority.HIGH,
        )
    except Exception:
        pass
    return redirect('accounts:user_detail', pk=officer.pk)


@role_required(User.Role.ADMIN)
@require_POST
def user_delete(request, pk):
    """Safely delete an officer account with self-deletion and superuser protection."""
    officer = get_object_or_404(User, pk=pk)

    if request.user.pk == officer.pk:
        messages.error(request, "Security Guard: You cannot delete your own administrator account.")
        return redirect('accounts:user_list')

    if officer.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
        messages.error(request, "Security Guard: Cannot delete the sole superuser account.")
        return redirect('accounts:user_list')

    username = officer.username
    officer_id = officer.id
    AuditService.log(
        action=AuditLog.Action.USER_DEACTIVATED,
        actor=request.user,
        target=officer,
        details={'deleted': True, 'username': username, 'user_id': officer_id},
        request=request
    )
    officer.delete()
    messages.success(request, f"Officer account '{username}' has been deleted.")
    return redirect('accounts:user_list')


@role_required(User.Role.ADMIN)
@require_POST
def user_generate_setup_link(request, pk):
    """Issues a fresh single-use password activation link for an officer."""
    officer = get_object_or_404(User, pk=pk)
    link = generate_password_setup_url(officer, request)

    AuditService.log(
        action=AuditLog.Action.PASSWORD_RESET_LINK,
        actor=request.user,
        target=officer,
        details={'reissue': True},
        request=request
    )

    try:
        from apps.notifications.services import NotificationService
        from apps.notifications.models import Notification
        NotificationService.send(
            recipient=officer,
            notification_type=Notification.NotificationType.PASSWORD_RESET_LINK,
            title="Your AgriLens Password Setup Link",
            message=f"Administrator {request.user.username} has issued a new password setup link for your officer account. Please click the button below to configure your password.",
            action_url=link,
            related_object=officer,
            actor=request.user,
            priority=Notification.Priority.URGENT,
            send_email=True,
            request=request,
            metadata={'action_label': 'Configure Password Now'},
        )
    except Exception:
        pass

    messages.info(request, f"Generated Single-Use Setup Link and sent via email to {officer.email}: {link}")
    return redirect('accounts:user_detail', pk=officer.pk)


def password_setup_view(request, uidb64, token):
    """
    Publicly accessible, token-authenticated single-use password setup portal.
    Enables newly registered officers to securely set their password and activate their credentials.
    """
    officer, is_valid = validate_password_setup_token(uidb64, token)

    if not is_valid or officer is None:
        context = {
            'page_title': 'Invalid or Expired Setup Link | AgriLens',
            'is_valid': False,
        }
        return render(request, 'accounts/password_setup.html', context)

    if request.method == 'POST':
        form = PasswordSetupForm(officer, request.POST)
        if form.is_valid():
            form.save()
            officer.is_active = True
            officer.save(update_fields=['is_active'])

            AuditService.log(
                action=AuditLog.Action.PASSWORD_CHANGED,
                actor=officer,
                target=officer,
                details={'method': 'Single-Use Token Activation'},
                request=request
            )

            messages.success(request, "Your password has been configured successfully! You may now sign in with your official credentials.")

            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import Notification
                NotificationService.send(
                    recipient=officer,
                    notification_type=Notification.Type.ACCOUNT_ACTIVATED,
                    title="Credentials Configured & Active",
                    message="Your AgriLens password has been configured successfully. You may now sign in to the platform.",
                    action_url="/accounts/login/",
                    related_object=officer,
                    priority=Notification.Priority.HIGH,
                )
            except Exception:
                pass
            return redirect('accounts:login')
    else:
        form = PasswordSetupForm(officer)

    context = {
        'page_title': f"Configure Password &bull; {officer.username}",
        'is_valid': True,
        'officer': officer,
        'form': form,
    }
    return render(request, 'accounts/password_setup.html', context)


# ==============================================================================
# Change Password & Forgot Password Workflows
# ==============================================================================
@login_required(login_url='accounts:login')
def password_change_view(request):
    """
    Self-service password change for authenticated officers.
    Requires verification of old password and re-hashes credentials without session termination.
    """
    if request.method == 'POST':
        form = PasswordChangeCustomForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            AuditService.log(
                action=AuditLog.Action.PASSWORD_CHANGED,
                actor=user,
                target=user,
                details={'method': 'Self-Service Password Change'},
                request=request
            )

            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import Notification
                NotificationService.send(
                    recipient=user,
                    notification_type=Notification.NotificationType.SECURITY_ALERT,
                    title="Security Notice: Password Changed Successfully",
                    message="Your AgriLens account password has been changed successfully. If you did not make this change, please contact system administration immediately.",
                    action_url="/accounts/profile/",
                    related_object=user,
                    priority=Notification.Priority.HIGH,
                    send_email=True,
                    request=request,
                )
            except Exception:
                pass

            messages.success(request, "Your password has been changed successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the highlighted errors to change your password.")
    else:
        form = PasswordChangeCustomForm(user=request.user)

    context = {
        'page_title': 'Change Account Password | AgriLens Rwanda',
        'form': form,
    }
    return render(request, 'accounts/password_change.html', context)


def password_reset_request_view(request):
    """
    Public self-service password reset request portal.
    Generates a secure cryptographic single-use token and dispatches an email.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:overview')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                reset_url = generate_password_setup_url(user, request)

                AuditService.log(
                    action=AuditLog.Action.PASSWORD_RESET_LINK,
                    actor=user,
                    target=user,
                    details={'channel': 'Self-Service Forgot Password'},
                    request=request
                )

                try:
                    from apps.notifications.services import NotificationService
                    from apps.notifications.models import Notification
                    NotificationService.send(
                        recipient=user,
                        notification_type=Notification.NotificationType.PASSWORD_RESET_LINK,
                        title="AgriLens — Password Reset Request",
                        message="We received a request to reset the password for your AgriLens officer account. Click the button below to choose a new password. If you did not request this, you can safely ignore this email.",
                        action_url=reset_url,
                        related_object=user,
                        priority=Notification.Priority.URGENT,
                        send_email=True,
                        request=request,
                        metadata={'action_label': 'Reset My Password'},
                    )
                except Exception:
                    pass

            return redirect('accounts:password_reset_done')
    else:
        form = PasswordResetRequestForm()

    context = {
        'page_title': 'Forgot Password &bull; Reset Credentials | AgriLens',
        'form': form,
    }
    return render(request, 'accounts/password_reset_form.html', context)


def password_reset_done_view(request):
    """Confirmation page after requesting password reset."""
    context = {
        'page_title': 'Password Reset Instructions Sent | AgriLens',
    }
    return render(request, 'accounts/password_reset_done.html', context)


def password_reset_confirm_view(request, uidb64, token):
    """Token validation and password reset confirmation view."""
    officer, is_valid = validate_password_setup_token(uidb64, token)

    if not is_valid or officer is None:
        context = {
            'page_title': 'Invalid or Expired Reset Link | AgriLens',
            'is_valid': False,
        }
        return render(request, 'accounts/password_reset_confirm.html', context)

    if request.method == 'POST':
        form = PasswordSetupForm(officer, request.POST)
        if form.is_valid():
            form.save()
            officer.is_active = True
            officer.save(update_fields=['is_active'])

            AuditService.log(
                action=AuditLog.Action.PASSWORD_CHANGED,
                actor=officer,
                target=officer,
                details={'method': 'Forgot Password Reset'},
                request=request
            )

            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import Notification
                NotificationService.send(
                    recipient=officer,
                    notification_type=Notification.NotificationType.SECURITY_ALERT,
                    title="AgriLens Password Reset Completed",
                    message="Your AgriLens password has been updated successfully. You may now sign in with your new credentials.",
                    action_url="/accounts/login/",
                    related_object=officer,
                    priority=Notification.Priority.HIGH,
                    send_email=True,
                    request=request,
                )
            except Exception:
                pass

            return redirect('accounts:password_reset_complete')
    else:
        form = PasswordSetupForm(officer)

    context = {
        'page_title': f"Set New Password &bull; {officer.username}",
        'is_valid': True,
        'officer': officer,
        'form': form,
    }
    return render(request, 'accounts/password_reset_confirm.html', context)


def password_reset_complete_view(request):
    """Success page informing user password has been reset."""
    context = {
        'page_title': 'Password Reset Complete | AgriLens',
    }
    return render(request, 'accounts/password_reset_complete.html', context)


@role_required(User.Role.ADMIN)
def audit_log_list(request):
    """
    Comprehensive, filterable security and operational compliance audit trail.
    Supports CSV export, action categorization, payload inspection, and actor filtering.
    """
    import csv
    from datetime import timedelta
    from django.utils import timezone
    from django.http import HttpResponse

    action_filter = request.GET.get('action', '').strip()
    category_filter = request.GET.get('category', '').strip()
    actor_filter = request.GET.get('actor', '').strip()
    query = request.GET.get('q', '').strip()
    export_format = request.GET.get('export', '').strip()

    # Category groupings for operational analysis
    CATEGORY_MAP = {
        'security': [
            AuditLog.Action.USER_CREATED, AuditLog.Action.USER_UPDATED,
            AuditLog.Action.USER_DEACTIVATED, AuditLog.Action.USER_ACTIVATED,
            AuditLog.Action.PASSWORD_RESET_LINK, AuditLog.Action.PASSWORD_CHANGED,
            AuditLog.Action.ROLE_CHANGED, AuditLog.Action.GEOGRAPHY_ASSIGNED
        ],
        'data': [
            AuditLog.Action.DATA_SOURCE_CREATED, AuditLog.Action.DATA_IMPORTED,
            AuditLog.Action.DATA_EXPORTED, AuditLog.Action.RECORD_CREATED,
            AuditLog.Action.RECORD_UPDATED, AuditLog.Action.RECORD_SUBMITTED,
            AuditLog.Action.CORRECTION_CREATED
        ],
        'approval': [
            AuditLog.Action.SUBMISSION_APPROVED, AuditLog.Action.SUBMISSION_RETURNED,
            AuditLog.Action.RECORD_SUPERSEDED
        ],
        'reports': [
            AuditLog.Action.REPORT_GENERATED, AuditLog.Action.REPORT_APPROVED,
            AuditLog.Action.REPORT_PUBLISHED, AuditLog.Action.REPORT_WITHDRAWN,
            AuditLog.Action.SCHEDULE_MODIFIED, AuditLog.Action.RECOMMENDATIONS_GENERATED,
            AuditLog.Action.ACTION_UPDATED, AuditLog.Action.OUTCOME_RECORDED
        ],
        'notifications': [
            AuditLog.Action.NOTIFICATION_CREATED, AuditLog.Action.EMAIL_SENT,
            AuditLog.Action.EMAIL_FAILED, AuditLog.Action.NOTIFICATION_READ,
            AuditLog.Action.ANNOUNCEMENT_CREATED,
        ],
    }

    logs = AuditLog.objects.select_related('actor').all().order_by('-timestamp')

    if category_filter and category_filter in CATEGORY_MAP:
        logs = logs.filter(action__in=CATEGORY_MAP[category_filter])

    if action_filter:
        logs = logs.filter(action=action_filter)

    if actor_filter:
        logs = logs.filter(actor__username=actor_filter)

    if query:
        logs = logs.filter(
            Q(target_repr__icontains=query) |
            Q(target_model__icontains=query) |
            Q(details__icontains=query) |
            Q(actor__username__icontains=query) |
            Q(ip_address__icontains=query)
        )

    # CSV Export Handler
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="agrilens_security_audit_{timezone.now():%Y%m%d_%H%M%S}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Timestamp (UTC)', 'Action Code', 'Action Name', 'Actor Username', 'Actor Role', 'Target Model', 'Target Repr', 'IP Address', 'Context Payload'])
        for item in logs[:2000]:
            writer.writerow([
                item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                item.action,
                item.get_action_display(),
                item.actor.username if item.actor else 'System / Anonymous',
                item.actor.get_role_display() if item.actor else 'N/A',
                item.target_model,
                item.target_repr,
                item.ip_address or '-',
                item.details or ''
            ])
        return response

    # Executive KPI summary metrics
    total_logs = AuditLog.objects.count()
    now = timezone.now()
    since_24h = now - timedelta(hours=24)

    events_24h = AuditLog.objects.filter(timestamp__gte=since_24h).count()
    security_count = AuditLog.objects.filter(action__in=CATEGORY_MAP['security']).count()
    report_count = AuditLog.objects.filter(action__in=CATEGORY_MAP['reports']).count()
    data_count = AuditLog.objects.filter(action__in=CATEGORY_MAP['data'] + CATEGORY_MAP['approval']).count()

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Security Audit Trail | AgriLens Rwanda',
        'page_heading': 'Security Audit Trail',
        'page_subheading': 'Immutable operational log & compliance stream',
        'page_obj': page_obj,
        'action_filter': action_filter,
        'category_filter': category_filter,
        'actor_filter': actor_filter,
        'query': query,
        'actions': AuditLog.Action.choices,
        'total_logs': total_logs,
        'events_24h': events_24h,
        'security_count': security_count,
        'report_count': report_count,
        'data_count': data_count,
    }
    return render(request, 'accounts/audit_log_list.html', context)


