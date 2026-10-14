"""
User, Role, and Security Audit models for AgriLens Rwanda.
Roles: System Administrator, NISR Data Manager, Agricultural Data Analyst,
National Agriculture Officer, District Agriculture Officer, Data Entry Officer, Reviewer / Approver.
Maintains legacy compatibility with Policy Maker, Field Extension Officer, and Researcher.
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        # Primary Milestone 4 Roles
        ADMIN = 'ADMIN', 'System Administrator'
        NISR_DATA_MANAGER = 'NISR_DATA_MANAGER', 'NISR Data Manager'
        ANALYST = 'ANALYST', 'Agricultural Data Analyst'
        NATIONAL_OFFICER = 'NATIONAL_OFFICER', 'National Agriculture Officer'
        DISTRICT_OFFICER = 'DISTRICT_OFFICER', 'District Agriculture Officer'
        DATA_ENTRY_OFFICER = 'DATA_ENTRY_OFFICER', 'Data Entry Officer'
        REVIEWER = 'REVIEWER', 'Reviewer / Approver'

        # Preserved Legacy Aliases for 100% Backward Compatibility
        POLICY_MAKER = 'POLICY_MAKER', 'Policy Maker / MINAGRI (Legacy)'
        EXTENSION_OFFICER = 'EXTENSION_OFFICER', 'Field Extension Officer (Legacy)'
        RESEARCHER = 'RESEARCHER', 'Agricultural Researcher (Legacy)'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.ANALYST,
        help_text='Institutional role and access tier'
    )
    organization = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Geographic Access Assignments
    assigned_province = models.ForeignKey(
        'geography.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users',
        help_text="Province-level institutional assignment if applicable"
    )
    assigned_districts = models.ManyToManyField(
        'geography.District',
        blank=True,
        related_name='assigned_users',
        help_text="Districts assigned to this officer for scoped geographic access"
    )

    # Role Convenience Properties
    @property
    def is_system_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_nisr_manager(self):
        return self.role in [self.Role.ADMIN, self.Role.NISR_DATA_MANAGER] or self.is_superuser

    @property
    def is_analyst(self):
        return self.role in [self.Role.ADMIN, self.Role.NISR_DATA_MANAGER, self.Role.ANALYST, self.Role.RESEARCHER, self.Role.POLICY_MAKER] or self.is_superuser

    @property
    def is_national_officer(self):
        return self.role in [self.Role.ADMIN, self.Role.NISR_DATA_MANAGER, self.Role.ANALYST, self.Role.NATIONAL_OFFICER, self.Role.POLICY_MAKER] or self.is_superuser

    @property
    def is_district_officer(self):
        return self.role == self.Role.DISTRICT_OFFICER

    @property
    def is_data_entry_officer(self):
        return self.role in [self.Role.DATA_ENTRY_OFFICER, self.Role.EXTENSION_OFFICER, self.Role.ADMIN]

    @property
    def is_reviewer(self):
        return self.role in [self.Role.REVIEWER, self.Role.ADMIN, self.Role.NISR_DATA_MANAGER, self.Role.ANALYST, self.Role.POLICY_MAKER] or self.is_superuser

    # Geographic Access Scoping Methods
    def is_national_scope(self):
        """Returns True if the officer has national-level data visibility."""
        if self.is_superuser or self.role in [
            self.Role.ADMIN,
            self.Role.NISR_DATA_MANAGER,
            self.Role.ANALYST,
            self.Role.NATIONAL_OFFICER,
            self.Role.POLICY_MAKER,
            self.Role.RESEARCHER,
        ]:
            return True
        return False

    def get_authorized_district_ids(self):
        """Returns a list of authorized district IDs, or None if national unconstrained scope."""
        if self.is_national_scope():
            return None
        return list(self.assigned_districts.values_list('id', flat=True))

    def can_access_district(self, district_id):
        """Returns True if user has authorization to view or manage data for the specified district."""
        if self.is_national_scope():
            return True
        if not district_id:
            return False
        return self.assigned_districts.filter(id=district_id).exists()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    """
    Append-only security audit trail for sensitive administrative actions,
    privilege changes, geographic reassignments, and submission reviews.
    """
    class Action(models.TextChoices):
        USER_CREATED = 'USER_CREATED', 'User Created'
        USER_UPDATED = 'USER_UPDATED', 'User Updated'
        USER_DEACTIVATED = 'USER_DEACTIVATED', 'User Deactivated'
        USER_ACTIVATED = 'USER_ACTIVATED', 'User Activated'
        ROLE_CHANGED = 'ROLE_CHANGED', 'Role Changed'
        GEOGRAPHY_ASSIGNED = 'GEOGRAPHY_ASSIGNED', 'Geographic Assignment Modified'
        PASSWORD_RESET_LINK = 'PASSWORD_RESET_LINK', 'Password Setup Link Issued'
        PASSWORD_CHANGED = 'PASSWORD_CHANGED', 'Password Changed'
        SUBMISSION_APPROVED = 'SUBMISSION_APPROVED', 'Manual Submission Approved'
        SUBMISSION_RETURNED = 'SUBMISSION_RETURNED', 'Manual Submission Returned'
        DATA_SOURCE_CREATED = 'DATA_SOURCE_CREATED', 'Data Source Registered'
        DATA_EXPORTED = 'DATA_EXPORTED', 'Analytical Data Exported'

        # Data lifecycle events
        RECORD_CREATED = 'RECORD_CREATED', 'Observation Record Created'
        RECORD_UPDATED = 'RECORD_UPDATED', 'Observation Record Updated'
        RECORD_SUBMITTED = 'RECORD_SUBMITTED', 'Observation Submitted for Review'
        CORRECTION_CREATED = 'CORRECTION_CREATED', 'Correction Revision Created'
        RECORD_SUPERSEDED = 'RECORD_SUPERSEDED', 'Approved Record Superseded by Correction'
        DATA_IMPORTED = 'DATA_IMPORTED', 'Official Dataset Imported'

        # Decision support & impact events
        RECOMMENDATIONS_GENERATED = 'RECOMMENDATIONS_GENERATED', 'Recommendation Rules Executed'
        RECOMMENDATION_TRANSITION = 'RECOMMENDATION_TRANSITION', 'Recommendation Status Changed'
        ACTION_UPDATED = 'ACTION_UPDATED', 'Action Plan Assigned or Updated'
        OUTCOME_RECORDED = 'OUTCOME_RECORDED', 'Outcome Measurement Recorded'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions',
        help_text="Officer who executed the action (null if automated or anonymous)"
    )
    action = models.CharField(max_length=40, choices=Action.choices, db_index=True)
    target_model = models.CharField(max_length=60, blank=True, help_text="Target entity model name")
    target_id = models.CharField(max_length=60, blank=True, help_text="Target entity ID/Key")
    target_repr = models.CharField(max_length=150, blank=True, help_text="Human-readable label of target")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, help_text="Contextual details (strictly redacts passwords & tokens)")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Security Audit Log'
        verbose_name_plural = 'Security Audit Logs'

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor_name} -> {self.get_action_display()} ({self.target_repr})"
