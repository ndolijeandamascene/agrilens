"""
AgriLens Internal Report Center Views.
Role-protected reporting workspace for authorized agricultural officers and administrators.
Supports on-demand report generation, automated schedule configuration, review & approval
workflows with separation of duties, and secure artifact downloads.
"""
import os
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User, AuditLog
from apps.accounts.permissions import role_required, can_access_district, AuditService
from apps.agriculture.models import Crop, AgriculturalSeason
from apps.dashboard.models import GeneratedReport, ReportSchedule, PublishedReport
from apps.dashboard.report_service import (
    ReportEngine,
    ReportingPeriodHelper,
    ReportWorkflowService,
    ReportSchedulerService,
)
from apps.geography.models import Province, District


ALLOWED_OFFICER_ROLES = (
    User.Role.ADMIN,
    User.Role.NISR_DATA_MANAGER,
    User.Role.ANALYST,
    User.Role.NATIONAL_OFFICER,
    User.Role.DISTRICT_OFFICER,
    User.Role.REVIEWER,
)


# ==============================================================================
# 1. REPORT CENTER OVERVIEW
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_overview(request):
    """
    Overview dashboard for internal reporting workspace.
    Displays dynamic statistical KPIs, recent execution jobs, and upcoming schedules.
    """
    now = timezone.now()
    base_qs = GeneratedReport.objects.all()

    # Scope for district officers
    if not request.user.is_national_scope():
        user_districts = request.user.get_authorized_district_ids() or []
        base_qs = base_qs.filter(district_id__in=user_districts)

    total_generated = base_qs.count()
    this_month_count = base_qs.filter(created_at__year=now.year, created_at__month=now.month).count()
    failed_count = base_qs.filter(status='failed').count()
    awaiting_review_count = base_qs.filter(status='pending_review').count()
    awaiting_pub_count = base_qs.filter(status='approved').count()

    latest_report = base_qs.filter(status__in=['generated', 'pending_review', 'approved', 'published']).order_by('-created_at').first()
    recent_reports = base_qs.select_related('generated_by', 'province', 'district').order_by('-created_at')[:8]

    # Schedules overview
    schedules_qs = ReportSchedule.objects.all()
    if not request.user.is_national_scope():
        schedules_qs = schedules_qs.filter(district_id__in=request.user.get_authorized_district_ids() or [])
    active_schedules_count = schedules_qs.filter(is_active=True).count()
    upcoming_schedules = schedules_qs.filter(is_active=True).select_related('owner', 'district').order_by('next_run_at')[:5]

    context = {
        'page_title': 'Internal Report Center | AgriLens',
        'active_tab': 'overview',
        'total_generated': total_generated,
        'this_month_count': this_month_count,
        'failed_count': failed_count,
        'awaiting_review_count': awaiting_review_count,
        'awaiting_pub_count': awaiting_pub_count,
        'active_schedules_count': active_schedules_count,
        'latest_report': latest_report,
        'recent_reports': recent_reports,
        'upcoming_schedules': upcoming_schedules,
    }
    return render(request, 'dashboard/reports/overview.html', context)


# ==============================================================================
# 2. GENERATE REPORT (ON-DEMAND WORKFLOW)
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_generate(request):
    """
    On-demand report generation form & execution controller.
    Validates user choices against database, checks geographic clearances,
    queries verified microdata, computes statistics, and generates multi-format files.
    """
    user = request.user

    # Fetch available filter options
    crops = Crop.objects.all().order_by('name')
    provinces = Province.objects.all().order_by('name')

    # District scoping by RBAC
    if user.is_national_scope():
        districts = District.objects.select_related('province').all().order_by('name')
    else:
        districts = user.assigned_districts.select_related('province').all().order_by('name')

    seasons = AgriculturalSeason.objects.all().order_by('-year', '-season')
    report_types = PublishedReport.REPORT_TYPES
    output_formats = [
        ('pdf', 'PDF Document (Executive Dossier)'),
        ('xlsx', 'Excel Spreadsheet (XLSX Workbook)'),
        ('csv', 'Comma-Separated Values (CSV Data)'),
    ]

    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'survey')
        output_format = request.POST.get('output_format', 'pdf')
        year_str = request.POST.get('year') or '2025'
        season_str = request.POST.get('season') or 'All Seasons'
        province_id = request.POST.get('province') or None
        district_id = request.POST.get('district') or None
        crop_id = request.POST.get('crop') or None
        data_source = request.POST.get('data_source', 'official')
        reporting_period_custom = request.POST.get('reporting_period', '').strip()

        try:
            year = int(year_str)
        except ValueError:
            year = 2025

        # Enforce geographic access
        if not user.is_national_scope():
            if district_id:
                if not user.can_access_district(int(district_id)):
                    messages.error(request, "Permission Denied: You are not authorized to generate reports for the selected district.")
                    return redirect('dashboard:internal_report_generate')
            else:
                assigned = user.get_authorized_district_ids()
                if assigned:
                    district_id = assigned[0]
                else:
                    messages.error(request, "Permission Denied: Your account has no assigned districts.")
                    return redirect('dashboard:internal_report_center')

        # Crop name resolution
        crop_obj = None
        crop_name = 'All Crops'
        if crop_id:
            crop_obj = Crop.objects.filter(id=crop_id).first()
            if crop_obj:
                crop_name = crop_obj.name

        district_obj = District.objects.filter(id=district_id).first() if district_id else None
        province_obj = Province.objects.filter(id=province_id).first() if province_id else None
        if district_obj and not province_obj:
            province_obj = district_obj.province

        # Build parameters dictionary
        parameters = {
            'report_type': report_type,
            'output_format': output_format,
            'year': year,
            'season': season_str,
            'crop_id': crop_obj.id if crop_obj else None,
            'crop_name': crop_name,
            'province_id': province_obj.id if province_obj else None,
            'district_id': district_obj.id if district_obj else None,
            'data_source': data_source,
            'reporting_period': reporting_period_custom or f"SAS {year} {season_str}",
        }

        # Create GeneratedReport record
        report = GeneratedReport.objects.create(
            title=f"Report Generation Pending...",
            report_type=report_type,
            output_format=output_format,
            status='draft',
            reporting_period=parameters['reporting_period'],
            season=season_str,
            year=year,
            province=province_obj,
            district=district_obj,
            crop=crop_obj,
            crop_name=crop_name,
            data_source=data_source,
            parameters=parameters,
            generated_by=user,
        )

        try:
            # Execute Generation Engine
            ReportEngine.generate_report_artifact(report)
            messages.success(request, f"Report '{report.title}' successfully generated in {report.execution_duration_sec}s.")
            return redirect('dashboard:internal_report_detail', report_id=report.id)

        except Exception as e:
            messages.error(request, f"Report generation failed: {str(e)}")
            return redirect('dashboard:internal_report_detail', report_id=report.id)

    context = {
        'page_title': 'Generate Agricultural Report | AgriLens',
        'active_tab': 'generate',
        'report_types': report_types,
        'crops': crops,
        'provinces': provinces,
        'districts': districts,
        'seasons': seasons,
        'output_formats': output_formats,
    }
    return render(request, 'dashboard/reports/generate.html', context)


# ==============================================================================
# 3. GENERATED REPORTS & SEARCHABLE HISTORY
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_history(request):
    """
    Searchable internal report history table with filters and download shortcuts.
    """
    user = request.user
    qs = GeneratedReport.objects.select_related('generated_by', 'province', 'district').order_by('-created_at')

    # Geographic scoping
    if not user.is_national_scope():
        user_districts = user.get_authorized_district_ids() or []
        qs = qs.filter(district_id__in=user_districts)

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(crop_name__icontains=q) | qs.filter(reporting_period__icontains=q)

    # Filters
    status_filter = request.GET.get('status', '').strip()
    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)

    format_filter = request.GET.get('format', '').strip()
    if format_filter and format_filter != 'all':
        qs = qs.filter(output_format=format_filter)

    type_filter = request.GET.get('type', '').strip()
    if type_filter and type_filter != 'all':
        qs = qs.filter(report_type=type_filter)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Generated Report History | AgriLens',
        'active_tab': 'history',
        'page_obj': page_obj,
        'query_q': q,
        'selected_status': status_filter,
        'selected_format': format_filter,
        'selected_type': type_filter,
        'report_types': PublishedReport.REPORT_TYPES,
        'status_choices': GeneratedReport.STATUS_CHOICES,
    }
    return render(request, 'dashboard/reports/history.html', context)


# ==============================================================================
# 4. REPORT DETAIL & AUDIT DOSSIER
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_detail(request, report_id):
    """
    Detailed dossier view showing parameters, computed statistics, execution logs,
    and contextual workflow buttons (Submit, Approve, Reject, Publish, Download).
    """
    user = request.user
    report = get_object_or_404(GeneratedReport.objects.select_related('generated_by', 'reviewed_by', 'province', 'district', 'published_report'), id=report_id)

    # Geographic access check
    if not user.is_national_scope() and report.district_id:
        if not user.can_access_district(report.district_id):
            raise PermissionDenied("You do not have geographic clearance to view this report dossier.")

    # Permissions calculation
    can_submit_review = report.status in ['draft', 'generated', 'rejected']
    can_approve = (
        (user.is_superuser or user.role in [User.Role.ADMIN, User.Role.NISR_DATA_MANAGER, User.Role.REVIEWER])
        and (user.id != report.generated_by_id or user.is_superuser)
        and report.status == 'pending_review'
    )
    can_reject = can_approve
    can_publish = (
        (user.is_superuser or user.role in [User.Role.ADMIN, User.Role.NISR_DATA_MANAGER])
        and report.status == 'approved'
    )
    can_unpublish = (
        (user.is_superuser or user.role in [User.Role.ADMIN, User.Role.NISR_DATA_MANAGER])
        and report.status == 'published'
    )
    can_download = bool(report.file_path)

    # Related security audit logs
    audit_trail = AuditLog.objects.filter(target_model='GeneratedReport', target_id=str(report.id)).order_by('-timestamp')[:10]

    context = {
        'page_title': f"{report.title} | AgriLens Dossier",
        'active_tab': 'history',
        'report': report,
        'can_submit_review': can_submit_review,
        'can_approve': can_approve,
        'can_reject': can_reject,
        'can_publish': can_publish,
        'can_unpublish': can_unpublish,
        'can_download': can_download,
        'audit_trail': audit_trail,
    }
    return render(request, 'dashboard/reports/detail.html', context)


# ==============================================================================
# 5. SECURE PERMISSION-CHECKED FILE DOWNLOAD
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_download(request, report_id):
    """
    Secure file streaming endpoint.
    Guarantees authorization before delivering private internal files.
    Formula injection protection is enforced during artifact creation.
    """
    user = request.user
    report = get_object_or_404(GeneratedReport, id=report_id)

    # Enforce geographic access
    if not user.is_national_scope() and report.district_id:
        if not user.can_access_district(report.district_id):
            raise PermissionDenied("Access Denied: You do not have permission to download reports for this district.")

    if not report.file_path:
        raise Http404("Report file has not been generated or is unavailable.")

    abs_path = os.path.join(settings.MEDIA_ROOT, report.file_path)
    if not os.path.exists(abs_path):
        raise Http404("Report file was not found on storage.")

    content_types = {
        'pdf': 'application/pdf',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv; charset=utf-8',
    }
    content_type = content_types.get(report.output_format.lower(), 'application/octet-stream')

    filename = os.path.basename(report.file_path)
    response = FileResponse(open(abs_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Audit log download
    AuditService.log(
        action=AuditLog.Action.DATA_EXPORTED,
        actor=user,
        target=report,
        details={"action": "downloaded", "format": report.output_format, "file_path": report.file_path}
    )
    return response


# ==============================================================================
# 6. LIFECYCLE WORKFLOW ACTION CONTROLLERS
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_action_submit_review(request, report_id):
    """Submits generated report for reviewer examination."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    report = get_object_or_404(GeneratedReport, id=report_id)
    try:
        ReportWorkflowService.submit_for_review(report, request.user)
        messages.success(request, f"Report '{report.title}' successfully submitted for review.")
    except Exception as e:
        messages.error(request, f"Could not submit report: {str(e)}")

    return redirect('dashboard:internal_report_detail', report_id=report.id)


@role_required(*ALLOWED_OFFICER_ROLES)
def report_action_approve(request, report_id):
    """Approves report. Enforces separation of duties."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    report = get_object_or_404(GeneratedReport, id=report_id)
    comments = request.POST.get('comments', '').strip()

    try:
        ReportWorkflowService.approve_report(report, request.user, comments=comments)
        messages.success(request, f"Report '{report.title}' successfully approved.")
    except PermissionDenied as pe:
        messages.error(request, str(pe))
    except Exception as e:
        messages.error(request, f"Could not approve report: {str(e)}")

    return redirect('dashboard:internal_report_detail', report_id=report.id)


@role_required(*ALLOWED_OFFICER_ROLES)
def report_action_reject(request, report_id):
    """Returns/rejects report with review comments."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    report = get_object_or_404(GeneratedReport, id=report_id)
    comments = request.POST.get('comments', '').strip()

    try:
        ReportWorkflowService.reject_report(report, request.user, comments=comments)
        messages.warning(request, f"Report '{report.title}' has been returned / rejected.")
    except PermissionDenied as pe:
        messages.error(request, str(pe))
    except Exception as e:
        messages.error(request, f"Action failed: {str(e)}")

    return redirect('dashboard:internal_report_detail', report_id=report.id)


@role_required(User.Role.ADMIN, User.Role.NISR_DATA_MANAGER)
def report_action_publish(request, report_id):
    """Promotes approved internal report to the public portal."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    report = get_object_or_404(GeneratedReport, id=report_id)
    try:
        ReportWorkflowService.publish_report(report, request.user)
        messages.success(request, f"Report '{report.title}' has been published to the Public Reports & Bulletins portal.")
    except Exception as e:
        messages.error(request, f"Publication failed: {str(e)}")

    return redirect('dashboard:internal_report_detail', report_id=report.id)


@role_required(User.Role.ADMIN, User.Role.NISR_DATA_MANAGER)
def report_action_unpublish(request, report_id):
    """Withdraws report from public view back into approved state."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    report = get_object_or_404(GeneratedReport, id=report_id)
    try:
        ReportWorkflowService.unpublish_report(report, request.user)
        messages.info(request, f"Report '{report.title}' has been withdrawn from public access.")
    except Exception as e:
        messages.error(request, f"Withdrawal failed: {str(e)}")

    return redirect('dashboard:internal_report_detail', report_id=report.id)


# ==============================================================================
# 7. AUTOMATED REPORT SCHEDULES
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_schedules(request):
    """
    Manages automated recurring reporting schedules.
    Provides options to create new schedules, pause/resume, and trigger runs on demand.
    """
    user = request.user
    qs = ReportSchedule.objects.select_related('owner', 'reviewer', 'province', 'district', 'crop').order_by('next_run_at')

    if not user.is_national_scope():
        qs = qs.filter(district_id__in=user.get_authorized_district_ids() or [])

    context = {
        'page_title': 'Automated Report Schedules | AgriLens',
        'active_tab': 'schedules',
        'schedules': qs,
        'report_types': PublishedReport.REPORT_TYPES,
        'frequency_choices': ReportSchedule.FREQUENCY_CHOICES,
        'crops': Crop.objects.all().order_by('name'),
        'districts': District.objects.all().order_by('name') if user.is_national_scope() else user.assigned_districts.all().order_by('name'),
    }
    return render(request, 'dashboard/reports/schedules.html', context)


@role_required(*ALLOWED_OFFICER_ROLES)
def report_schedule_create(request):
    """Creates a persistent report schedule with automatic next_run_at calculation."""
    if request.method != 'POST':
        return redirect('dashboard:internal_report_schedules')

    user = request.user
    title = request.POST.get('title', '').strip()
    report_type = request.POST.get('report_type', 'survey')
    frequency = request.POST.get('frequency', 'monthly')
    output_format = request.POST.get('output_format', 'pdf')
    district_id = request.POST.get('district') or None
    crop_id = request.POST.get('crop') or None
    auto_submit = request.POST.get('auto_submit_for_review') == 'on'

    if not title:
        title = f"Scheduled {dict(PublishedReport.REPORT_TYPES).get(report_type, 'Agricultural')} ({frequency.capitalize()})"

    district_obj = None
    if district_id:
        if not user.is_national_scope() and not user.can_access_district(int(district_id)):
            messages.error(request, "Permission denied for selected district.")
            return redirect('dashboard:internal_report_schedules')
        district_obj = District.objects.filter(id=district_id).first()

    crop_obj = Crop.objects.filter(id=crop_id).first() if crop_id else None
    next_run = ReportingPeriodHelper.calculate_next_run(frequency)

    schedule = ReportSchedule.objects.create(
        title=title,
        report_type=report_type,
        frequency=frequency,
        output_format=output_format,
        district=district_obj,
        province=district_obj.province if district_obj else None,
        crop=crop_obj,
        crop_name=crop_obj.name if crop_obj else 'All Crops',
        auto_submit_for_review=auto_submit,
        owner=user,
        next_run_at=next_run,
        is_active=True,
    )

    AuditService.log(
        action=AuditLog.Action.SCHEDULE_MODIFIED,
        actor=user,
        target=schedule,
        details={"action": "created", "frequency": frequency, "next_run": next_run.isoformat()}
    )

    messages.success(request, f"Schedule '{schedule.title}' configured. Next execution: {next_run.strftime('%b %d, %Y %H:%M')}.")
    return redirect('dashboard:internal_report_schedules')


@role_required(*ALLOWED_OFFICER_ROLES)
def report_schedule_toggle(request, schedule_id):
    """Pauses or resumes an automated schedule."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    schedule = get_object_or_404(ReportSchedule, id=schedule_id)
    schedule.is_active = not schedule.is_active
    schedule.save(update_fields=['is_active', 'updated_at'])

    status_word = "resumed" if schedule.is_active else "paused"
    messages.info(request, f"Schedule '{schedule.title}' is now {status_word}.")

    AuditService.log(
        action=AuditLog.Action.SCHEDULE_MODIFIED,
        actor=request.user,
        target=schedule,
        details={"action": "toggled_status", "is_active": schedule.is_active}
    )
    return redirect('dashboard:internal_report_schedules')


@role_required(*ALLOWED_OFFICER_ROLES)
def report_schedule_run_now(request, schedule_id):
    """Executes a schedule immediately on demand."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    schedule = get_object_or_404(ReportSchedule, id=schedule_id)
    results = ReportSchedulerService.run_due_schedules(force=True, schedule_id=schedule.id)

    if results['succeeded'] > 0:
        messages.success(request, f"Scheduled job '{schedule.title}' successfully executed.")
    elif results['skipped_duplicate'] > 0:
        messages.info(request, f"Execution skipped: A report for this schedule and period already exists.")
    else:
        err = results['jobs'][0].get('error', 'Unknown error') if results['jobs'] else 'Execution error'
        messages.error(request, f"Schedule execution failed: {err}")

    return redirect('dashboard:internal_report_schedules')


# ==============================================================================
# 8. INTERNAL PUBLISHED REPORTS CATALOG
# ==============================================================================
@role_required(*ALLOWED_OFFICER_ROLES)
def report_center_published(request):
    """
    Internal catalog of published institutional reports.
    Provides administrators and officers with quick links to public bulletins
    and withdrawal controls.
    """
    reports = PublishedReport.objects.all().order_by('-publication_date', '-id')
    context = {
        'page_title': 'Published Institutional Reports | AgriLens',
        'active_tab': 'published',
        'reports': reports,
    }
    return render(request, 'dashboard/reports/published.html', context)
