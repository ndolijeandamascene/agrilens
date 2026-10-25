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
@role_required(User.Role.ADMIN, User.Role.NISR_DATA_MANAGER, User.Role.ANALYST, User.Role.RESEARCHER)
def data_source_edit(request, pk):
    """Edit an existing data source registration."""
    ds = get_object_or_404(DataSource, pk=pk)
    if request.method == 'POST':
        form = DataSourceForm(request.POST, instance=ds)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data Source '{ds.name}' updated successfully.")
            return redirect('data_management:hub')
    else:
        form = DataSourceForm(instance=ds)

    return render(request, 'data_management/data_source_form.html', {
        'page_title': f"Edit Data Source: {ds.name}",
        'form': form,
        'ds': ds,
        'is_edit': True,
    })


@login_required(login_url='accounts:login')
@role_required(User.Role.ADMIN, User.Role.NISR_DATA_MANAGER)
def data_source_delete(request, pk):
    """Delete a data source if no ingestion batches or validated observations depend on it."""
    ds = get_object_or_404(DataSource, pk=pk)
    if request.method == 'POST':
        name = ds.name
        batches_count = ds.batches.count()
        if batches_count > 0:
            messages.warning(request, f"Cannot delete '{name}' because {batches_count} ingestion batches depend on it.")
        else:
            ds.delete()
            messages.success(request, f"Data source '{name}' deleted.")
    return redirect('data_management:hub')


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


from apps.data_management.validation import apply_validation, INVALID
from apps.data_management.workflow import ObservationWorkflowService, WorkflowError
from django.core.exceptions import PermissionDenied


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
            entry.review_status = ManualObservation.ReviewStatus.DRAFT
            entry.save()

            apply_validation(entry)
            entry.save(update_fields=['validation_status', 'validation_messages'])

            AuditService.log(
                action=AuditLog.Action.RECORD_CREATED,
                actor=request.user,
                target=entry,
                details={'crop': entry.crop.name, 'district': entry.district.name, 'area_ha': str(entry.plot_area_ha)},
                request=request
            )

            # Action button determines initial transition
            action = request.POST.get('action', 'draft')
            if action == 'submit':
                try:
                    ObservationWorkflowService.submit(entry.id, request.user, request=request)
                    messages.success(request, "Record submitted successfully for authoritative review!")
                except WorkflowError as e:
                    messages.warning(request, f"Saved as draft: {e}")
            else:
                messages.info(request, "Draft record saved successfully. You may edit and submit later.")

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
        ManualObservation.objects.select_related('district__province', 'sector', 'crop', 'season', 'created_by', 'reviewed_by', 'data_source', 'supersedes'),
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

    can_correct = (
        entry.review_status == ManualObservation.ReviewStatus.APPROVED
        and not entry.is_superseded
        and (entry.created_by == request.user or request.user.is_superuser or request.user.role in [User.Role.ADMIN, User.Role.ANALYST, User.Role.REVIEWER])
    )

    context = {
        'page_title': f"Observation #{entry.id} - {entry.crop.name}",
        'entry': entry,
        'is_reviewer': is_reviewer,
        'can_correct': can_correct,
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
        messages.warning(request, "Approved records cannot be edited in place. Use the 'Create Correction Revision' action to propose an auditable correction.")
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

            updated.save()
            apply_validation(updated)
            updated.save(update_fields=['validation_status', 'validation_messages'])

            AuditService.log(
                action=AuditLog.Action.RECORD_UPDATED,
                actor=request.user,
                target=updated,
                details={'status': updated.review_status},
                request=request
            )

            action = request.POST.get('action', 'draft')
            if action == 'submit':
                try:
                    ObservationWorkflowService.submit(updated.id, request.user, request=request)
                    messages.success(request, "Record updated and submitted for review!")
                except WorkflowError as e:
                    messages.warning(request, f"Saved as draft: {e}")
            else:
                messages.info(request, "Draft record updated successfully.")
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
def manual_entry_submit(request, pk):
    """Explicit action to transition a draft or returned record to submitted."""
    if request.method != 'POST':
        return redirect('data_management:manual_entry_detail', pk=pk)

    try:
        ObservationWorkflowService.submit(pk, request.user, request=request)
        messages.success(request, f"Observation #{pk} submitted successfully for review!")
    except (WorkflowError, PermissionDenied) as e:
        messages.error(request, str(e))

    return redirect('data_management:manual_entry_detail', pk=pk)


@login_required(login_url='accounts:login')
def manual_entry_review(request, pk):
    """Authoritative action to approve or reject a submitted observation."""
    if request.method != 'POST':
        return redirect('data_management:manual_entry_detail', pk=pk)

    decision = request.POST.get('decision')
    comments = request.POST.get('review_comments', '')

    try:
        if decision == 'approve':
            ObservationWorkflowService.approve(pk, request.user, comments=comments, request=request)
            messages.success(request, f"Observation #{pk} has been APPROVED and added to authorized manual records.")
        elif decision == 'reject':
            ObservationWorkflowService.reject(pk, request.user, reason=comments, request=request)
            messages.warning(request, f"Observation #{pk} returned for correction with reviewer notes.")
        else:
            messages.error(request, f"Invalid decision: '{decision}'")
    except (WorkflowError, PermissionDenied) as e:
        messages.error(request, str(e))

    return redirect('data_management:manual_entry_detail', pk=pk)


@login_required(login_url='accounts:login')
def manual_entry_correction(request, pk):
    """Creates a new editable revision of an approved record."""
    if request.method != 'POST':
        return redirect('data_management:manual_entry_detail', pk=pk)

    try:
        revision = ObservationWorkflowService.create_correction(pk, request.user, request=request)
        messages.info(request, f"Correction revision #{revision.id} created for approved record #{pk}. Please adjust the fields and submit for review.")
        return redirect('data_management:manual_entry_edit', pk=revision.pk)
    except (WorkflowError, PermissionDenied) as e:
        messages.error(request, str(e))
        return redirect('data_management:manual_entry_detail', pk=pk)


@login_required(login_url='accounts:login')
def manual_entry_delete(request, pk):
    """Delete a manual observation draft or unapproved observation record."""
    entry = get_object_or_404(ManualObservation, pk=pk)
    if request.method == 'POST':
        if entry.review_status == ManualObservation.ReviewStatus.APPROVED:
            messages.warning(request, f"Approved manual observation #{pk} cannot be deleted directly. Use the correction revision workflow instead.")
            return redirect('data_management:manual_entry_detail', pk=pk)

        if not (request.user.is_superuser or getattr(request.user, 'role', '') in [User.Role.ADMIN, User.Role.NISR_DATA_MANAGER] or entry.created_by == request.user):
            messages.error(request, "Permission Denied: You cannot delete this observation.")
            return redirect('data_management:manual_entry_detail', pk=pk)

        entry_id = entry.id
        entry.delete()
        messages.success(request, f"Manual observation #{entry_id} has been deleted.")
        return redirect('data_management:manual_entry_list')
    return redirect('data_management:manual_entry_detail', pk=pk)



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
