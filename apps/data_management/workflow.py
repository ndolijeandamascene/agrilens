"""
AgriLens Maker-Checker Workflow Service.
Handles state transitions, segregation of duties, concurrency locks,
revision management, and tamper-resistant audit logging for agricultural observations.
"""
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from apps.data_management.models import ManualObservation
from apps.data_management.validation import apply_validation, INVALID
from apps.accounts.models import User, AuditLog
from apps.accounts.permissions import AuditService, can_access_district


class WorkflowError(Exception):
    """Custom exception raised when a workflow rule or permission constraint is violated."""
    pass


class ObservationWorkflowService:
    """
    State machine and review authority engine for ManualObservation.
    Lifecycle:
        DRAFT -> SUBMITTED -> APPROVED / REJECTED
    Approved Correction Lifecycle:
        APPROVED -> Create Revision (DRAFT with supersedes=original) -> SUBMITTED -> APPROVED (marks original is_superseded=True)
    """

    REVIEW_ROLES = [
        User.Role.ADMIN,
        User.Role.REVIEWER,
        User.Role.NISR_DATA_MANAGER,
        User.Role.ANALYST,
        User.Role.POLICY_MAKER,
    ]

    @classmethod
    @transaction.atomic
    def submit(cls, observation_id, actor, request=None):
        """
        Transitions a DRAFT or REJECTED record to SUBMITTED.
        Requires actor to be the creator or an authorized administrator/analyst.
        Freezes the record against invalid submission.
        """
        obs = ManualObservation.objects.select_for_update().get(pk=observation_id)

        # 1. State check
        if obs.review_status not in [ManualObservation.ReviewStatus.DRAFT, ManualObservation.ReviewStatus.REJECTED]:
            raise WorkflowError(f"Cannot submit observation in status '{obs.get_review_status_display()}'.")

        # 2. Permission check
        can_submit = (
            obs.created_by == actor or 
            actor.is_superuser or 
            actor.role in [User.Role.ADMIN, User.Role.ANALYST]
        )
        if not can_submit:
            raise PermissionDenied("You are not authorized to submit records created by another officer.")

        if not can_access_district(actor, obs.district_id):
            raise PermissionDenied(f"You do not possess clearance for {obs.district.name} District.")

        # 3. Server-side validation check
        result = apply_validation(obs)
        if result.status == INVALID:
            errors_str = "; ".join([e['message'] for e in result.errors])
            raise WorkflowError(f"Cannot submit invalid observation: {errors_str}")

        obs.review_status = ManualObservation.ReviewStatus.SUBMITTED
        obs.submitted_at = timezone.now()
        obs.save()

        AuditService.log(
            action=AuditLog.Action.RECORD_SUBMITTED,
            actor=actor,
            target=obs,
            details={
                'transition': 'SUBMIT',
                'district': obs.district.name,
                'crop': obs.crop.name,
                'validation_status': obs.validation_status,
                'warnings_count': len(result.warnings)
            },
            request=request
        )

        # Trigger In-App & Email Notifications to Authorized Reviewers
        try:
            from apps.notifications.services import NotificationService
            from apps.notifications.models import Notification
            review_url = f"/data-management/manual/{obs.id}/review/"
            if obs.supersedes:
                NotificationService.send_to_reviewers(
                    district_id=obs.district_id,
                    notification_type=Notification.NotificationType.CORRECTION_SUBMITTED,
                    title=f"Correction Revision: {obs.crop.name} in {obs.district.name}",
                    message=f"Officer {actor.username} submitted a correction revision for observation #{obs.supersedes_id} awaiting your verification.",
                    related_object=obs,
                    action_url=review_url,
                    priority=Notification.Priority.HIGH,
                    actor=actor,
                    metadata={'district': obs.district.name, 'crop': obs.crop.name, 'yield': str(obs.calculated_yield_kg_per_ha)},
                    exclude_user=actor,
                    request=request
                )
            else:
                NotificationService.send_to_reviewers(
                    district_id=obs.district_id,
                    notification_type=Notification.NotificationType.DATA_SUBMITTED,
                    title=f"New Field Observation: {obs.crop.name} ({obs.district.name})",
                    message=f"Officer {actor.username} submitted a field observation for {obs.crop.name} ({obs.calculated_yield_kg_per_ha} kg/ha) awaiting review.",
                    related_object=obs,
                    action_url=review_url,
                    priority=Notification.Priority.HIGH,
                    actor=actor,
                    metadata={'district': obs.district.name, 'crop': obs.crop.name, 'yield': str(obs.calculated_yield_kg_per_ha)},
                    exclude_user=actor,
                    request=request
                )
        except Exception:
            pass

        return obs

    @classmethod
    @transaction.atomic
    def approve(cls, observation_id, reviewer, comments="", request=None):
        """
        Transitions a SUBMITTED observation to APPROVED.
        Enforces segregation of duties: reviewer cannot be the record creator (unless superuser).
        If record supersedes another, marks previous record as is_superseded=True.
        """
        obs = ManualObservation.objects.select_for_update().get(pk=observation_id)

        if obs.review_status != ManualObservation.ReviewStatus.SUBMITTED:
            raise WorkflowError(f"Only SUBMITTED records can be approved. Current status: '{obs.get_review_status_display()}'.")

        # Role authority
        is_authorized_role = reviewer.is_superuser or reviewer.role in cls.REVIEW_ROLES
        if not is_authorized_role:
            raise PermissionDenied("Your account role is not authorized to approve agricultural observations.")

        # Segregation of duties / self-approval guard
        if obs.created_by == reviewer and not reviewer.is_superuser:
            raise PermissionDenied("Segregation of duties violation: You cannot approve your own manual submissions.")

        # Geographic clearance
        if not can_access_district(reviewer, obs.district_id):
            raise PermissionDenied(f"Geographic clearance violation: You cannot review records for {obs.district.name} District.")

        # Re-run validation to guarantee data integrity before official approval
        result = apply_validation(obs)
        if result.status == INVALID:
            errors_str = "; ".join([e['message'] for e in result.errors])
            raise WorkflowError(f"Cannot approve invalid observation: {errors_str}")

        obs.review_status = ManualObservation.ReviewStatus.APPROVED
        obs.reviewed_by = reviewer
        obs.review_comments = comments
        obs.reviewed_at = timezone.now()
        obs.save()

        # Handle correction superseding if this was a revision of an existing approved record
        if obs.supersedes:
            orig = ManualObservation.objects.select_for_update().get(pk=obs.supersedes_id)
            orig.is_superseded = True
            orig.save(update_fields=['is_superseded'])

            AuditService.log(
                action=AuditLog.Action.RECORD_SUPERSEDED,
                actor=reviewer,
                target=orig,
                details={'superseded_by_id': obs.pk, 'comments': comments},
                request=request
            )

        AuditService.log(
            action=AuditLog.Action.SUBMISSION_APPROVED,
            actor=reviewer,
            target=obs,
            details={
                'decision': 'APPROVE',
                'district': obs.district.name,
                'crop': obs.crop.name,
                'yield_kg_per_ha': str(obs.calculated_yield_kg_per_ha),
                'comments': comments
            },
            request=request
        )

        # Trigger In-App & Email Notification to Submitting Officer
        try:
            from apps.notifications.services import NotificationService
            from apps.notifications.models import Notification
            NotificationService.send(
                recipient=obs.created_by,
                notification_type=Notification.NotificationType.DATA_APPROVED,
                title=f"Submission Approved: {obs.crop.name} in {obs.district.name}",
                message=f"Your field observation for {obs.crop.name} ({obs.calculated_yield_kg_per_ha} kg/ha) in {obs.district.name} has been approved by {reviewer.username}.{(' Comments: ' + comments) if comments else ''}",
                related_object=obs,
                action_url=f"/data-management/manual/{obs.id}/",
                priority=Notification.Priority.MEDIUM,
                actor=reviewer,
                metadata={'district': obs.district.name, 'crop': obs.crop.name, 'comments': comments},
                request=request
            )
        except Exception:
            pass

        return obs

    @classmethod
    @transaction.atomic
    def reject(cls, observation_id, reviewer, reason, request=None):
        """
        Returns a SUBMITTED observation to REJECTED for correction.
        Requires a meaningful rejection reason.
        """
        if not reason or not reason.strip():
            raise WorkflowError("A meaningful rejection reason is strictly required when returning an observation.")

        obs = ManualObservation.objects.select_for_update().get(pk=observation_id)

        if obs.review_status != ManualObservation.ReviewStatus.SUBMITTED:
            raise WorkflowError(f"Only SUBMITTED records can be rejected. Current status: '{obs.get_review_status_display()}'.")

        is_authorized_role = reviewer.is_superuser or reviewer.role in cls.REVIEW_ROLES
        if not is_authorized_role:
            raise PermissionDenied("Your account role is not authorized to reject agricultural observations.")

        if obs.created_by == reviewer and not reviewer.is_superuser:
            raise PermissionDenied("Segregation of duties violation: You cannot review your own manual submissions.")

        if not can_access_district(reviewer, obs.district_id):
            raise PermissionDenied(f"Geographic clearance violation: You cannot review records for {obs.district.name} District.")

        obs.review_status = ManualObservation.ReviewStatus.REJECTED
        obs.reviewed_by = reviewer
        obs.review_comments = reason.strip()
        obs.reviewed_at = timezone.now()
        obs.save()

        AuditService.log(
            action=AuditLog.Action.SUBMISSION_RETURNED,
            actor=reviewer,
            target=obs,
            details={
                'decision': 'REJECT',
                'district': obs.district.name,
                'crop': obs.crop.name,
                'reason': reason.strip()
            },
            request=request
        )

        # Trigger In-App & Email Notification to Submitting Officer with Rejection Reason
        try:
            from apps.notifications.services import NotificationService
            from apps.notifications.models import Notification
            NotificationService.send(
                recipient=obs.created_by,
                notification_type=Notification.NotificationType.DATA_RETURNED,
                title=f"Corrections Required: {obs.crop.name} in {obs.district.name}",
                message=f"Your field observation for {obs.crop.name} in {obs.district.name} was returned for correction by {reviewer.username}. Review reason: \"{reason.strip()}\".",
                related_object=obs,
                action_url=f"/data-management/manual/{obs.id}/edit/",
                priority=Notification.Priority.HIGH,
                actor=reviewer,
                metadata={'district': obs.district.name, 'crop': obs.crop.name, 'reason': reason.strip()},
                request=request
            )
        except Exception:
            pass

        return obs

    @classmethod
    @transaction.atomic
    def create_correction(cls, original_id, creator, request=None):
        """
        Clones an APPROVED record into a new DRAFT revision with supersedes pointer.
        Original remains active in indicators until the revision is reviewed and APPROVED.
        """
        orig = ManualObservation.objects.select_for_update().get(pk=original_id)

        if orig.review_status != ManualObservation.ReviewStatus.APPROVED:
            raise WorkflowError("Only currently APPROVED records can be revised through a formal correction workflow.")

        if orig.is_superseded:
            raise WorkflowError("This record has already been superseded by a newer correction revision.")

        can_revise = (
            orig.created_by == creator or 
            creator.is_superuser or 
            creator.role in [User.Role.ADMIN, User.Role.ANALYST, User.Role.REVIEWER]
        )
        if not can_revise:
            raise PermissionDenied("You are not authorized to create a correction revision for this record.")

        # Create clone
        correction = ManualObservation.objects.create(
            supersedes=orig,
            is_superseded=False,
            review_status=ManualObservation.ReviewStatus.DRAFT,
            created_by=creator,
            reporting_organization=orig.reporting_organization,
            observation_reference=f"{orig.observation_reference}-REV" if orig.observation_reference else "",
            observation_date=orig.observation_date,
            data_source=orig.data_source,
            data_kind=orig.data_kind,
            season=orig.season,
            district=orig.district,
            sector=orig.sector,
            crop=orig.crop,
            plot_area_ha=orig.plot_area_ha,
            total_production_kg=orig.total_production_kg,
            calculated_yield_kg_per_ha=orig.calculated_yield_kg_per_ha,
            is_irrigated=orig.is_irrigated,
            is_improved_seed=orig.is_improved_seed,
            uses_inorganic_fertilizer=orig.uses_inorganic_fertilizer,
            uses_organic_fertilizer=orig.uses_organic_fertilizer,
            has_soil_conservation=orig.has_soil_conservation,
            uses_mechanization=orig.uses_mechanization,
            inorganic_fertilizer_kg=orig.inorganic_fertilizer_kg,
            loss_quantity_kg=orig.loss_quantity_kg,
            primary_loss_cause=orig.primary_loss_cause,
            quantity_sold_kg=orig.quantity_sold_kg,
            farmgate_price_rwf=orig.farmgate_price_rwf,
            latitude=orig.latitude,
            longitude=orig.longitude,
            gps_accuracy_m=orig.gps_accuracy_m,
            remarks=f"Revision for approved record #{orig.id}. {orig.remarks}",
        )

        apply_validation(correction)
        correction.save()

        AuditService.log(
            action=AuditLog.Action.CORRECTION_CREATED,
            actor=creator,
            target=correction,
            details={'original_id': orig.id, 'revision_id': correction.id},
            request=request
        )
        return correction
