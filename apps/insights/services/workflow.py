"""
AgriLens Insight Lifecycle and Review Governance Workflow Service.
Enforces institutional maker-checker separation of duties, role-based transitions,
and tamper-evident security audit logging.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from apps.insights.models import AgriculturalInsight
from apps.accounts.permissions import AuditService
from apps.accounts.models import AuditLog


class InsightWorkflowService:
    """
    Manages state transitions, separation of duties, and audit logging for Agricultural Insights.
    """

    ALLOWED_REVIEWER_ROLES = [
        'ADMIN',
        'NISR_DATA_MANAGER',
        'ANALYST',
        'REVIEWER',
        'POLICY_MAKER',
    ]

    ALLOWED_PUBLISHER_ROLES = [
        'ADMIN',
        'NISR_DATA_MANAGER',
        'ANALYST',
        'POLICY_MAKER',
    ]

    @classmethod
    def can_review(cls, user) -> bool:
        """Checks if user possesses institutional privileges to review or approve insights."""
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_system_admin:
            return True
        return getattr(user, 'role', '') in cls.ALLOWED_REVIEWER_ROLES

    @classmethod
    def can_publish(cls, user) -> bool:
        """Checks if user possesses institutional privileges to publish insights to the public portal."""
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_system_admin:
            return True
        return getattr(user, 'role', '') in cls.ALLOWED_PUBLISHER_ROLES

    @classmethod
    def submit_for_review(cls, insight: AgriculturalInsight, actor, request=None) -> AgriculturalInsight:
        """Moves insight from GENERATED to UNDER_REVIEW."""
        if insight.status != AgriculturalInsight.Status.GENERATED:
            raise ValidationError(f"Cannot submit insight in '{insight.get_status_display()}' status for review.")

        insight.status = AgriculturalInsight.Status.UNDER_REVIEW
        insight.save(update_fields=['status', 'updated_at'])

        AuditService.log(
            action=AuditLog.Action.RECORD_SUBMITTED,
            actor=actor,
            target=insight,
            details=f"Insight '{insight.title}' submitted for institutional review.",
            request=request
        )
        return insight

    @classmethod
    def approve(cls, insight: AgriculturalInsight, actor, comments: str = "", request=None) -> AgriculturalInsight:
        """
        Approves an insight.
        Enforces separation-of-duties: An analyst cannot approve an insight they created,
        unless they possess superuser / system admin privileges.
        """
        if not cls.can_review(actor):
            raise PermissionDenied("You do not possess institutional privileges to approve agricultural insights.")

        # Separation of duties check
        if insight.created_by and insight.created_by == actor and not (actor.is_superuser or actor.is_system_admin):
            raise PermissionDenied(
                "Separation-of-duties violation: You cannot approve an insight you created. "
                "Another authorized analyst or supervisor must verify this finding."
            )

        if insight.status in [AgriculturalInsight.Status.APPROVED, AgriculturalInsight.Status.PUBLISHED]:
            return insight  # Already approved

        insight.status = AgriculturalInsight.Status.APPROVED
        insight.reviewed_by = actor
        insight.reviewed_at = timezone.now()
        if comments:
            insight.review_comments = comments
        insight.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comments', 'updated_at'])

        AuditService.log(
            action=AuditLog.Action.RECORD_APPROVED if hasattr(AuditLog.Action, 'RECORD_APPROVED') else AuditLog.Action.REPORT_APPROVED,
            actor=actor,
            target=insight,
            details=f"Insight '{insight.title}' approved by {actor.username}. Comments: {comments or 'None'}",
            request=request
        )
        return insight

    @classmethod
    def reject(cls, insight: AgriculturalInsight, actor, comments: str, request=None) -> AgriculturalInsight:
        """Rejects an insight with mandatory justification comments."""
        if not cls.can_review(actor):
            raise PermissionDenied("You do not possess institutional privileges to reject agricultural insights.")

        if not comments or not comments.strip():
            raise ValidationError("A clear explanatory justification is required when rejecting an insight.")

        insight.status = AgriculturalInsight.Status.REJECTED
        insight.reviewed_by = actor
        insight.reviewed_at = timezone.now()
        insight.review_comments = comments
        insight.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comments', 'updated_at'])

        AuditService.log(
            action=AuditLog.Action.SUBMISSION_RETURNED if hasattr(AuditLog.Action, 'SUBMISSION_RETURNED') else AuditLog.Action.REPORT_WITHDRAWN,
            actor=actor,
            target=insight,
            details=f"Insight '{insight.title}' rejected by {actor.username}. Reason: {comments}",
            request=request
        )
        return insight

    @classmethod
    def publish(cls, insight: AgriculturalInsight, actor, request=None) -> AgriculturalInsight:
        """
        Publishes an approved insight to make it visible to public audiences.
        If insight is currently UNDER_REVIEW or GENERATED, automatically performs approval first.
        """
        if not cls.can_publish(actor):
            raise PermissionDenied("You do not possess institutional privileges to publish agricultural insights.")

        # Ensure approved before publishing
        if insight.status != AgriculturalInsight.Status.APPROVED:
            cls.approve(insight, actor, comments="Auto-approved during publication workflow", request=request)

        insight.status = AgriculturalInsight.Status.PUBLISHED
        insight.published_at = timezone.now()
        insight.save(update_fields=['status', 'published_at', 'updated_at'])

        AuditService.log(
            action=AuditLog.Action.REPORT_PUBLISHED if hasattr(AuditLog.Action, 'REPORT_PUBLISHED') else AuditLog.Action.RECORD_CREATED,
            actor=actor,
            target=insight,
            details=f"Insight '{insight.title}' published to public portal by {actor.username}.",
            request=request
        )
        return insight

    @classmethod
    def unpublish(cls, insight: AgriculturalInsight, actor, comments: str = "", request=None) -> AgriculturalInsight:
        """Unpublishes an insight, returning it to UNDER_REVIEW status."""
        if not cls.can_publish(actor):
            raise PermissionDenied("You do not possess institutional privileges to unpublish agricultural insights.")

        insight.status = AgriculturalInsight.Status.UNDER_REVIEW
        if comments:
            insight.review_comments = f"Unpublished by {actor.username}: {comments}"
        insight.save(update_fields=['status', 'review_comments', 'updated_at'])

        AuditService.log(
            action=AuditLog.Action.REPORT_WITHDRAWN if hasattr(AuditLog.Action, 'REPORT_WITHDRAWN') else AuditLog.Action.RECORD_UPDATED,
            actor=actor,
            target=insight,
            details=f"Insight '{insight.title}' unpublished by {actor.username}. Comments: {comments or 'None'}",
            request=request
        )
        return insight

    @classmethod
    def mark_superseded(cls, insight: AgriculturalInsight, actor=None, reason: str = "") -> AgriculturalInsight:
        """Marks an older insight as superseded by a refreshed finding."""
        insight.status = AgriculturalInsight.Status.SUPERSEDED
        if reason:
            insight.review_comments = f"Superseded: {reason}"
        insight.save(update_fields=['status', 'review_comments', 'updated_at'])

        if actor:
            AuditService.log(
                action=AuditLog.Action.RECORD_SUPERSEDED if hasattr(AuditLog.Action, 'RECORD_SUPERSEDED') else AuditLog.Action.RECORD_UPDATED,
                actor=actor,
                target=insight,
                details=f"Insight '{insight.title}' marked superseded: {reason}"
            )
        return insight
