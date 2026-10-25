"""
AgriLens Authentication and User Profile Views.
Enforces institutional role tiers: System Administrator, Agricultural Data Analyst,
Policy Maker / MINAGRI, Field Extension Officer, Agricultural Researcher.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
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
from apps.accounts.forms import UserAdminCreationForm, UserAdminEditForm, PasswordSetupForm
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
        else:
            messages.error(request, "Please correct the highlighted errors to register the account.")
    else:
        form = UserAdminCreationForm()

    context = {
        'page_title': 'Register New Officer Account',
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
        'page_title': f"Officer Dossier &bull; {officer.username}",
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
        'page_title': f"Edit Officer &bull; {officer.username}",
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

    messages.info(request, f"Generated Single-Use Setup Link: {link}")
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


@role_required(User.Role.ADMIN)
def audit_log_list(request):
    """Comprehensive, filterable security audit trail."""
    action_filter = request.GET.get('action', '').strip()
    query = request.GET.get('q', '').strip()

    logs = AuditLog.objects.select_related('actor').all().order_by('-timestamp')

    if action_filter:
        logs = logs.filter(action=action_filter)

    if query:
        logs = logs.filter(
            Q(target_repr__icontains=query) |
            Q(details__icontains=query) |
            Q(actor__username__icontains=query)
        )

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Security & Compliance Audit Trail | AgriLens',
        'page_obj': page_obj,
        'action_filter': action_filter,
        'query': query,
        'actions': AuditLog.Action.choices,
        'total_logs': AuditLog.objects.count(),
    }
    return render(request, 'accounts/audit_log_list.html', context)


