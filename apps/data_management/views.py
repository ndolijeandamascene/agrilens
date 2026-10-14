"""
AgriLens Data Management Views.
Handles manual data entry forms, geographic dropdown APIs, review/approval workflow, and batch auditing.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count, Q

from django.contrib.auth.decorators import login_required
from apps.accounts.models import User, AuditLog
from apps.accounts.permissions import (
    role_required, scope_queryset_by_geography, 
    can_access_district, AuditService
)
from apps.geography.models import Province, District, Sector
from apps.data_management.models import (
    DataSource, ImportBatch, ValidatedObservation, 
    ManualObservation, DataQualityIssue
)
from apps.data_management.forms import ManualObservationForm, DataSourceForm


@login_required(login_url='accounts:login')
@role_required(
    User.Role.ADMIN, User.Role.NISR_DATA_MANAGER, User.Role.ANALYST,
    User.Role.POLICY_MAKER, User.Role.RESEARCHER
)
def data_hub_dashboard(request):
    """
    Central Data Management Hub:
    Displays status of all Import Batches, Dynamic Data Sources, Data Quality Issues, and Manual Entry Review Queue.
    """
    batches = ImportBatch.objects.select_related('source').order_by('-started_at')[:10]
    qa_issues = DataQualityIssue.objects.order_by('-created_at')[:15]
    data_sources = DataSource.objects.all().order_by('-year', 'season', 'name')
    
    manual_counts = ManualObservation.objects.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(review_status=ManualObservation.ReviewStatus.SUBMITTED)),
        approved=Count('id', filter=Q(review_status=ManualObservation.ReviewStatus.APPROVED)),
        draft=Count('id', filter=Q(review_status=ManualObservation.ReviewStatus.DRAFT)),
    )
    
    total_validated_obs = ValidatedObservation.objects.count()

    context = {
        'page_title': 'Data Lineage & Ingestion Hub',
        'batches': batches,
        'data_sources': data_sources,
        'qa_issues': qa_issues,
        'manual_counts': manual_counts,
        'total_validated_obs': total_validated_obs,
    }
    return render(request, 'data_management/hub_dashboard.html', context)


@login_required(login_url='accounts:login')
@role_required(User.Role.ADMIN, User.Role.NISR_DATA_MANAGER, User.Role.ANALYST, User.Role.RESEARCHER)
def data_source_create(request):
    """Register a new dynamic data source (custom survey, administrative records, field project)."""
    if request.method == 'POST':
        form = DataSourceForm(request.POST)
        if form.is_valid():
            ds = form.save()
            messages.success(request, f"Data Source '{ds.name}' ({ds.source_type}) registered successfully!")
            return redirect('data_management:hub')
        else:
            messages.error(request, "Please correct the highlighted errors to register the data source.")
    else:
        form = DataSourceForm()

    context = {
        'page_title': 'Register New Agricultural Data Source',
        'form': form,
    }
    return render(request, 'data_management/data_source_form.html', context)


@login_required(login_url='accounts:login')
def manual_entry_list(request):
    """List manual agricultural entries with status filtering, kind filtering, search, and geographic scoping."""
    status_filter = request.GET.get('status', '')
    kind_filter = request.GET.get('kind', '')
    query = request.GET.get('q', '')

    entries = ManualObservation.objects.select_related(
        'district', 'sector', 'crop', 'season', 'created_by', 'data_source'
    ).all()

    # Geographic scoping: District Officers strictly scoped to assigned districts
    entries = scope_queryset_by_geography(entries, request.user, district_field='district')

    if status_filter:
        entries = entries.filter(review_status=status_filter)

    if kind_filter:
        entries = entries.filter(data_kind=kind_filter)

    if query:
        entries = entries.filter(
            Q(crop__name__icontains=query) |
            Q(district__name__icontains=query) |
            Q(observation_reference__icontains=query) |
            Q(reporting_organization__icontains=query)
        )

    paginator = Paginator(entries, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Manual Agricultural Records Registry',
        'page_obj': page_obj,
        'status_filter': status_filter,
        'kind_filter': kind_filter,
        'query': query,
        'statuses': ManualObservation.ReviewStatus.choices,
        'kinds': DataSource.DataKind.choices,
    }
    return render(request, 'data_management/manual_entry_list.html', context)


@login_required(login_url='accounts:login')
@role_required(
    User.Role.ADMIN, User.Role.DATA_ENTRY_OFFICER, User.Role.DISTRICT_OFFICER,
    User.Role.NISR_DATA_MANAGER, User.Role.ANALYST, User.Role.EXTENSION_OFFICER
)
def manual_entry_create(request):
    """Create a new manual agricultural observation with geographic authorization checks."""
    if request.method == 'POST':
        form = ManualObservationForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)

            # Geographic scope enforcement for District Officers
            if not can_access_district(request.user, entry.district_id):
                messages.error(request, f"Permission Denied: You are not authorized to submit observations for {entry.district.name} District.")
                context = {'page_title': 'New Manual Agricultural Observation', 'form': form}
                return render(request, 'data_management/manual_entry_form.html', context)

            entry.created_by = request.user
            
            # Action button determines initial status
            action = request.POST.get('action', 'draft')
            if action == 'submit':
                entry.review_status = ManualObservation.ReviewStatus.SUBMITTED
                messages.success(request, "Record submitted successfully for authoritative review!")
            else:
                entry.review_status = ManualObservation.ReviewStatus.DRAFT
                messages.info(request, "Draft record saved successfully. You may edit and submit later.")

            entry.save()
            return redirect('data_management:manual_entry_detail', pk=entry.pk)
        else:
            messages.error(request, "Please correct the highlighted validation errors below.")
    else:
        form = ManualObservationForm()

    context = {
        'page_title': 'New Manual Agricultural Observation',
        'form': form,
    }
    return render(request, 'data_management/manual_entry_form.html', context)


@login_required(login_url='accounts:login')
def manual_entry_detail(request, pk):
    """Display comprehensive details and review workflow for a manual record."""
    entry = get_object_or_404(
        ManualObservation.objects.select_related('district__province', 'sector', 'crop', 'season', 'created_by', 'reviewed_by', 'data_source'),
        pk=pk
    )

    # Geographic boundary enforcement
    if not can_access_district(request.user, entry.district_id):
        return render(request, '403.html', {
            'reason': f"Geographic Access Restricted: You are not authorized to view records from {entry.district.name} District."
        }, status=403)

    # Review authorization: Must hold review role AND not be the record creator (self-approval conflict guard)
    REVIEW_ROLES = [User.Role.ADMIN, User.Role.REVIEWER, User.Role.NISR_DATA_MANAGER, User.Role.ANALYST, User.Role.POLICY_MAKER]
    is_reviewer = (
        (request.user.role in REVIEW_ROLES or request.user.is_superuser)
        and (entry.created_by != request.user or request.user.is_superuser)
    )

    context = {
        'page_title': f"Observation #{entry.id} - {entry.crop.name}",
        'entry': entry,
        'is_reviewer': is_reviewer,
    }
    return render(request, 'data_management/manual_entry_detail.html', context)


@login_required(login_url='accounts:login')
def manual_entry_edit(request, pk):
    """Edit draft or returned records."""
    entry = get_object_or_404(ManualObservation, pk=pk)

    if not can_access_district(request.user, entry.district_id):
        return render(request, '403.html', {
            'reason': f"Geographic Access Restricted: You cannot modify records for {entry.district.name} District."
        }, status=403)
    
    if entry.review_status == ManualObservation.ReviewStatus.APPROVED:
        messages.warning(request, "Approved records are locked and cannot be directly modified without an audit amendment.")
        return redirect('data_management:manual_entry_detail', pk=entry.pk)

    # Permission check: creator or elevated analyst/admin
    can_edit = (
        entry.created_by == request.user 
        or request.user.role in [User.Role.ADMIN, User.Role.ANALYST] 
        or request.user.is_superuser
    )
    if not can_edit:
        messages.error(request, "Permission Denied: You cannot modify records created by other officers.")
        return redirect('data_management:manual_entry_detail', pk=entry.pk)

    if request.method == 'POST':
        form = ManualObservationForm(request.POST, instance=entry)
        if form.is_valid():
            updated = form.save(commit=False)

            if not can_access_district(request.user, updated.district_id):
                messages.error(request, f"Permission Denied: You are not authorized to assign this record to {updated.district.name} District.")
                context = {'page_title': f"Edit Observation #{entry.id}", 'form': form, 'entry': entry}
                return render(request, 'data_management/manual_entry_form.html', context)

            action = request.POST.get('action', 'draft')
            if action == 'submit':
                updated.review_status = ManualObservation.ReviewStatus.SUBMITTED
                messages.success(request, "Record updated and submitted for review!")
            else:
                updated.review_status = ManualObservation.ReviewStatus.DRAFT
                messages.info(request, "Draft record updated successfully.")
            updated.save()
            return redirect('data_management:manual_entry_detail', pk=updated.pk)
    else:
        form = ManualObservationForm(instance=entry)

    context = {
        'page_title': f"Edit Observation #{entry.id}",
        'form': form,
        'entry': entry,
    }
    return render(request, 'data_management/manual_entry_form.html', context)


@login_required(login_url='accounts:login')
def manual_entry_review(request, pk):
    """Authoritative action to approve or reject a submitted observation."""
    entry = get_object_or_404(ManualObservation, pk=pk)

    AUTHORIZED_ROLES = [
        User.Role.ADMIN, User.Role.REVIEWER, User.Role.NISR_DATA_MANAGER,
        User.Role.ANALYST, User.Role.POLICY_MAKER
    ]
    if request.user.role not in AUTHORIZED_ROLES and not request.user.is_superuser:
        messages.error(request, "Permission Denied: Your account role is not authorized to review or approve entries.")
        return redirect('data_management:manual_entry_detail', pk=entry.pk)

    # Self-Approval Conflict of Interest Guard (Milestone 4 Condition 5)
    if entry.created_by == request.user and not request.user.is_superuser:
        messages.error(request, "Conflict of Interest Guard: You cannot review or approve your own manual submissions.")
        return redirect('data_management:manual_entry_detail', pk=entry.pk)

    # Geographic boundary check
    if not can_access_district(request.user, entry.district_id):
        messages.error(request, "Geographic Access Restricted: You cannot review records outside your assigned districts.")
        return redirect('data_management:manual_entry_detail', pk=entry.pk)

    reviewer = request.user

    if request.method == 'POST':
        decision = request.POST.get('decision')
        comments = request.POST.get('review_comments', '')

        if decision == 'approve':
            entry.review_status = ManualObservation.ReviewStatus.APPROVED
            entry.reviewed_by = reviewer
            entry.review_comments = comments
            entry.reviewed_at = timezone.now()
            entry.save()

            AuditService.log(
                action=AuditLog.Action.SUBMISSION_APPROVED,
                actor=request.user,
                target=entry,
                details={'decision': 'approve', 'district': entry.district.name, 'comments': comments},
                request=request
            )
            messages.success(request, f"Observation #{entry.id} has been APPROVED and added to authorized manual records.")
        elif decision == 'reject':
            entry.review_status = ManualObservation.ReviewStatus.REJECTED
            entry.reviewed_by = reviewer
            entry.review_comments = comments
            entry.reviewed_at = timezone.now()
            entry.save()

            AuditService.log(
                action=AuditLog.Action.SUBMISSION_RETURNED,
                actor=request.user,
                target=entry,
                details={'decision': 'reject', 'district': entry.district.name, 'comments': comments},
                request=request
            )
            messages.warning(request, f"Observation #{entry.id} returned for correction with reviewer notes.")

    return redirect('data_management:manual_entry_detail', pk=entry.pk)



# ------------------------------------------------------------------------------
# Dynamic Geographic Cascading Dropdown APIs
# ------------------------------------------------------------------------------
def api_districts_by_province(request, province_id):
    """Returns districts filtered by province for interactive UI selection."""
    districts = District.objects.filter(province_id=province_id).order_by('name').values('id', 'name', 'code')
    return JsonResponse({'districts': list(districts)})


def api_sectors_by_district(request, district_id):
    """Returns sectors filtered by district for interactive UI selection."""
    sectors = Sector.objects.filter(district_id=district_id).order_by('name').values('id', 'name', 'code')
    return JsonResponse({'sectors': list(sectors)})
