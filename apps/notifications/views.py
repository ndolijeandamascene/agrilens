"""
AgriLens Notification Center & Preference Views.
Provides full in-app inbox management, filtering, preferences configuration,
and administrator broadcast tools.
"""
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from apps.notifications.models import Notification, NotificationPreference, SystemAnnouncement, EmailDeliveryLog
from apps.notifications.services import NotificationService
from apps.notifications.emails import EmailService


@login_required
def notification_center(request):
    """
    Primary In-App Notification Center.
    Supports filtering by read/unread status, category, priority, date range, and search.
    """
    tab = request.GET.get('tab', 'all').strip().lower()
    category = request.GET.get('category', '').strip().lower()
    priority = request.GET.get('priority', '').strip().upper()
    date_filter = request.GET.get('date', '').strip().lower()
    query = request.GET.get('q', '').strip()

    qs = Notification.objects.filter(recipient=request.user, is_dismissed=False)

    # 1. Tab filtering (All vs Unread vs Read)
    if tab == 'unread':
        qs = qs.filter(is_read=False)
    elif tab == 'read':
        qs = qs.filter(is_read=True)

    # 2. Category filtering
    if category == 'security':
        qs = qs.filter(notification_type__in=[
            Notification.NotificationType.ACCOUNT_CREATED,
            Notification.NotificationType.ACCOUNT_ACTIVATED,
            Notification.NotificationType.ACCOUNT_DEACTIVATED,
            Notification.NotificationType.ROLE_CHANGED,
            Notification.NotificationType.GEOGRAPHY_ASSIGNED,
            Notification.NotificationType.PASSWORD_RESET_LINK,
            Notification.NotificationType.SECURITY_ALERT,
        ])
    elif category == 'data':
        qs = qs.filter(notification_type__in=[
            Notification.NotificationType.DATA_SUBMITTED,
            Notification.NotificationType.DATA_APPROVED,
            Notification.NotificationType.DATA_RETURNED,
            Notification.NotificationType.DATA_REJECTED,
            Notification.NotificationType.CORRECTION_SUBMITTED,
            Notification.NotificationType.DATA_SUPERSEDED,
            Notification.NotificationType.DATA_IMPORTED,
            Notification.NotificationType.DATA_IMPORT_FAILED,
        ])
    elif category == 'market':
        qs = qs.filter(notification_type__in=[
            Notification.NotificationType.PRICE_SUBMITTED,
            Notification.NotificationType.PRICE_APPROVED,
            Notification.NotificationType.PRICE_RETURNED,
            Notification.NotificationType.PRICE_REJECTED,
            Notification.NotificationType.PRICE_PUBLISHED,
        ])
    elif category == 'reports':
        qs = qs.filter(notification_type__in=[
            Notification.NotificationType.REPORT_GENERATED,
            Notification.NotificationType.REPORT_FAILED,
            Notification.NotificationType.SCHEDULED_REPORT_GENERATED,
            Notification.NotificationType.ML_MODEL_TRAINED,
            Notification.NotificationType.ML_MODEL_FAILED,
        ])
    elif category == 'announcements':
        qs = qs.filter(notification_type__in=[
            Notification.NotificationType.SYSTEM_ANNOUNCEMENT,
            Notification.NotificationType.SYSTEM_ERROR,
        ])

    # 3. Priority filtering
    if priority in Notification.Priority.values:
        qs = qs.filter(priority=priority)

    # 4. Date filtering
    now = timezone.now()
    if date_filter == 'today':
        qs = qs.filter(created_at__date=now.date())
    elif date_filter == '7days':
        qs = qs.filter(created_at__gte=now - timedelta(days=7))
    elif date_filter == '30days':
        qs = qs.filter(created_at__gte=now - timedelta(days=30))

    # 5. Search query
    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(message__icontains=query) |
            Q(related_object_type__icontains=query)
        )

    # Counts for header pill badges
    base_qs = Notification.objects.filter(recipient=request.user, is_dismissed=False)
    total_count = base_qs.count()
    unread_count = base_qs.filter(is_read=False).count()
    read_count = base_qs.filter(is_read=True).count()

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Notification Center | AgriLens Rwanda',
        'page_heading': 'Notification Center',
        'page_subheading': 'Review approvals, field submissions, bulletins, and security communications',
        'page_obj': page_obj,
        'tab': tab,
        'category': category,
        'priority': priority,
        'date_filter': date_filter,
        'query': query,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_mark_read(request, pk):
    """Marks a single notification as read."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'success', 'is_read': True, 'unread_count': NotificationService.get_unread_count(request.user)})

    messages.success(request, "Notification marked as read.")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'notifications:notification_center'
    return redirect(next_url)


@login_required
def notification_mark_unread(request, pk):
    """Marks a single notification as unread."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_unread()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'success', 'is_read': False, 'unread_count': NotificationService.get_unread_count(request.user)})

    messages.success(request, "Notification marked as unread.")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'notifications:notification_center'
    return redirect(next_url)


@login_required
def notification_mark_all_read(request):
    """Marks all unread notifications for the current user as read."""
    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False, is_dismissed=False)
    count = unread_qs.update(is_read=True, read_at=timezone.now(), updated_at=timezone.now())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'success', 'marked_count': count, 'unread_count': 0})

    messages.success(request, f"Marked {count} notification(s) as read.")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'notifications:notification_center'
    return redirect(next_url)


@login_required
def notification_dismiss(request, pk):
    """Dismisses / deletes a notification from the user's active view."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.dismiss()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'success', 'dismissed': True})

    messages.success(request, "Notification dismissed.")
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'notifications:notification_center'
    return redirect(next_url)


@login_required
def notification_preferences_view(request):
    """
    Configures personal notification preferences for channels and categories.
    """
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        pref.email_enabled = 'email_enabled' in request.POST
        pref.in_app_enabled = 'in_app_enabled' in request.POST
        pref.notify_data_submissions = 'notify_data_submissions' in request.POST
        pref.notify_approvals = 'notify_approvals' in request.POST
        pref.notify_market_prices = 'notify_market_prices' in request.POST
        pref.notify_reports = 'notify_reports' in request.POST
        pref.notify_announcements = 'notify_announcements' in request.POST
        pref.save()

        messages.success(request, "Your notification preferences have been saved successfully.")
        return redirect('notifications:preferences')

    context = {
        'page_title': 'Notification Preferences | AgriLens Rwanda',
        'page_heading': 'Notification Preferences',
        'page_subheading': 'Manage email subscriptions and in-app communications',
        'pref': pref,
    }
    return render(request, 'notifications/preferences.html', context)


@login_required
def admin_announcements_view(request):
    """
    Administrator announcement center and delivery monitoring hub.
    Only authorized system administrators can broadcast or monitor system announcements.
    """
    if not request.user.is_system_admin:
        return HttpResponseForbidden("Access Denied: Only system administrators can manage announcements and delivery logs.")

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message_body = request.POST.get('message', '').strip()
        priority = request.POST.get('priority', Notification.Priority.HIGH)
        target_role = request.POST.get('target_role', '').strip()
        action_url = request.POST.get('action_url', '').strip()
        send_email = 'send_email' in request.POST

        if not title or not message_body:
            messages.error(request, "Both announcement title and message content are required.")
            return redirect('notifications:admin_announcements')

        announcement = SystemAnnouncement.objects.create(
            title=title,
            message=message_body,
            priority=priority,
            target_role=target_role,
            action_url=action_url,
            send_email=send_email,
            created_by=request.user,
        )

        recipient_count = NotificationService.broadcast_announcement(announcement, request=request)
        messages.success(request, f"Announcement '{title}' broadcasted to {recipient_count} user(s).")
        return redirect('notifications:admin_announcements')

    announcements = SystemAnnouncement.objects.select_related('created_by').all()[:15]
    failed_deliveries = EmailDeliveryLog.objects.filter(status=EmailDeliveryLog.Status.FAILED).select_related('notification')[:20]
    recent_deliveries = EmailDeliveryLog.objects.select_related('notification').order_by('-created_at')[:20]

    delivery_stats = {
        'total': EmailDeliveryLog.objects.count(),
        'sent': EmailDeliveryLog.objects.filter(status=EmailDeliveryLog.Status.SENT).count(),
        'failed': EmailDeliveryLog.objects.filter(status=EmailDeliveryLog.Status.FAILED).count(),
        'pending': EmailDeliveryLog.objects.filter(status=EmailDeliveryLog.Status.PENDING).count(),
    }

    from apps.accounts.models import User
    roles = User.Role.choices

    context = {
        'page_title': 'Notification Administration | AgriLens Rwanda',
        'page_heading': 'Notification Administration',
        'page_subheading': 'Broadcast announcements, monitor delivery history, and manage communication health',
        'announcements': announcements,
        'failed_deliveries': failed_deliveries,
        'recent_deliveries': recent_deliveries,
        'delivery_stats': delivery_stats,
        'roles': roles,
    }
    return render(request, 'notifications/admin_announcements.html', context)


@login_required
def admin_retry_email(request, pk):
    """Administrator action to retry a failed email delivery."""
    if not request.user.is_system_admin:
        return HttpResponseForbidden("Access Denied: Administrator clearance required.")

    success = EmailService.retry_failed_email(pk)
    if success:
        messages.success(request, f"Email delivery log #{pk} re-queued for transmission.")
    else:
        messages.error(request, f"Failed to re-queue email log #{pk}.")
    return redirect('notifications:admin_announcements')


@login_required
def api_unread_count(request):
    """Returns unread notification count as JSON for asynchronous header polling."""
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'unread_count': count})
