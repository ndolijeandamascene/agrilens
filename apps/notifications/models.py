"""
AgriLens Enterprise Notification and Communication Models.
Supports in-app alerts, user notification preferences, broadcast system announcements,
and robust email delivery audit logging.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    Individual user notification record.
    Associated strictly with a single recipient to enforce privacy and access isolation.
    """
    class NotificationType(models.TextChoices):
        # 1. Account and User Management
        ACCOUNT_CREATED = 'account_created', 'New User Account Created'
        ACCOUNT_ACTIVATED = 'account_activated', 'Account Activated'
        ACCOUNT_DEACTIVATED = 'account_deactivated', 'Account Deactivated'
        ROLE_CHANGED = 'role_changed', 'User Role Modified'
        GEOGRAPHY_ASSIGNED = 'geography_assigned', 'Geographic Jurisdiction Assigned'
        PASSWORD_RESET_LINK = 'password_reset_link', 'Password Setup Link Issued'
        SECURITY_ALERT = 'security_alert', 'Security & Access Alert'

        # 2. Agricultural Data Management
        DATA_SUBMITTED = 'data_submitted', 'New Field Observation Submitted'
        DATA_APPROVED = 'data_approved', 'Observation Record Approved'
        DATA_RETURNED = 'data_returned', 'Observation Returned for Correction'
        DATA_REJECTED = 'data_rejected', 'Observation Rejected'
        CORRECTION_SUBMITTED = 'correction_submitted', 'Correction Revision Submitted'
        DATA_SUPERSEDED = 'data_superseded', 'Record Superseded by Correction'
        DATA_IMPORTED = 'data_imported', 'Official Dataset Import Completed'
        DATA_IMPORT_FAILED = 'data_import_failed', 'Dataset Import Failed'

        # 3. Commodity Prices & Market Surveillance
        PRICE_SUBMITTED = 'price_submitted', 'Commodity Price Submitted'
        PRICE_APPROVED = 'price_approved', 'Commodity Price Approved'
        PRICE_RETURNED = 'price_returned', 'Commodity Price Returned for Correction'
        PRICE_REJECTED = 'price_rejected', 'Commodity Price Rejected'
        PRICE_PUBLISHED = 'price_published', 'Commodity Price Published'

        # 4. Reports and Analytics
        REPORT_GENERATED = 'report_generated', 'Agricultural Report Generated'
        REPORT_FAILED = 'report_failed', 'Report Generation Failed'
        SCHEDULED_REPORT_GENERATED = 'scheduled_report_generated', 'Scheduled Report Published'
        ML_MODEL_TRAINED = 'ml_model_trained', 'ML Model Training Completed'
        ML_MODEL_FAILED = 'ml_model_failed', 'ML Model Training Failed'

        # 5. Support and System Administration
        SYSTEM_ANNOUNCEMENT = 'system_announcement', 'System Announcement'
        SYSTEM_ERROR = 'system_error', 'System Administrator Alert'

    Type = NotificationType

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
        help_text="Authorized user who owns this notification"
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Linkage to domain entities
    related_object_type = models.CharField(max_length=80, blank=True, db_index=True)
    related_object_id = models.CharField(max_length=80, blank=True, db_index=True)
    action_url = models.CharField(max_length=255, blank=True)

    # State
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False, db_index=True)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True
    )

    # Provenance
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text="User who initiated this event (or null if system daemon)"
    )
    metadata = models.JSONField(default=dict, blank=True)

    # Delivery audit tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['recipient', 'is_dismissed']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} -> {self.recipient.username}"

    def mark_as_read(self, save=True):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            if save:
                self.save(update_fields=['is_read', 'read_at', 'updated_at'])

    def mark_as_unread(self, save=True):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            if save:
                self.save(update_fields=['is_read', 'read_at', 'updated_at'])

    def dismiss(self, save=True):
        self.is_dismissed = True
        if save:
            self.save(update_fields=['is_dismissed', 'updated_at'])

    @property
    def category(self):
        """Returns human-friendly category slug for filtering."""
        t = self.notification_type
        if t in [
            self.NotificationType.ACCOUNT_CREATED,
            self.NotificationType.ACCOUNT_ACTIVATED,
            self.NotificationType.ACCOUNT_DEACTIVATED,
            self.NotificationType.ROLE_CHANGED,
            self.NotificationType.GEOGRAPHY_ASSIGNED,
            self.NotificationType.PASSWORD_RESET_LINK,
            self.NotificationType.SECURITY_ALERT,
        ]:
            return 'security'
        elif t in [
            self.NotificationType.DATA_SUBMITTED,
            self.NotificationType.DATA_APPROVED,
            self.NotificationType.DATA_RETURNED,
            self.NotificationType.DATA_REJECTED,
            self.NotificationType.CORRECTION_SUBMITTED,
            self.NotificationType.DATA_SUPERSEDED,
            self.NotificationType.DATA_IMPORTED,
            self.NotificationType.DATA_IMPORT_FAILED,
        ]:
            return 'data'
        elif t in [
            self.NotificationType.PRICE_SUBMITTED,
            self.NotificationType.PRICE_APPROVED,
            self.NotificationType.PRICE_RETURNED,
            self.NotificationType.PRICE_REJECTED,
            self.NotificationType.PRICE_PUBLISHED,
        ]:
            return 'market'
        elif t in [
            self.NotificationType.REPORT_GENERATED,
            self.NotificationType.REPORT_FAILED,
            self.NotificationType.SCHEDULED_REPORT_GENERATED,
            self.NotificationType.ML_MODEL_TRAINED,
            self.NotificationType.ML_MODEL_FAILED,
        ]:
            return 'reports'
        elif t in [self.NotificationType.SYSTEM_ANNOUNCEMENT, self.NotificationType.SYSTEM_ERROR]:
            return 'announcements'
        return 'other'

    @property
    def icon_class(self):
        """FontAwesome icon name based on notification type."""
        cat = self.category
        if cat == 'security':
            return 'fa-solid fa-shield-halved'
        elif cat == 'data':
            if 'APPROVED' in self.notification_type.upper():
                return 'fa-solid fa-circle-check'
            elif 'RETURNED' in self.notification_type.upper() or 'REJECTED' in self.notification_type.upper():
                return 'fa-solid fa-arrow-rotate-left'
            return 'fa-solid fa-database'
        elif cat == 'market':
            return 'fa-solid fa-chart-line'
        elif cat == 'reports':
            return 'fa-solid fa-file-chart-column'
        elif cat == 'announcements':
            return 'fa-solid fa-bullhorn'
        return 'fa-solid fa-bell'

    @property
    def color_theme(self):
        """Color theme based on priority and type."""
        if self.priority == self.Priority.URGENT:
            return {'bg': '#FEF2F2', 'text': '#DC2626', 'border': '#FECACA', 'badge': '#DC2626'}
        elif self.priority == self.Priority.HIGH:
            return {'bg': '#FFFBEB', 'text': '#D97706', 'border': '#FDE68A', 'badge': '#D97706'}
        elif 'APPROVED' in self.notification_type.upper():
            return {'bg': '#F0FDF4', 'text': '#15803D', 'border': '#BBF7D0', 'badge': '#15803D'}
        return {'bg': '#EFF6FF', 'text': '#2563EB', 'border': '#BFDBFE', 'badge': '#2563EB'}


class NotificationPreference(models.Model):
    """
    Granular user notification preferences.
    Users can configure channels and optional business categories.
    Mandatory security, account, and administrative notifications cannot be disabled.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Master Channel Toggles
    email_enabled = models.BooleanField(
        default=True,
        help_text="Receive email notifications for enabled categories"
    )
    in_app_enabled = models.BooleanField(
        default=True,
        help_text="Receive in-app notification center alerts"
    )

    # Optional Category Subscriptions
    notify_data_submissions = models.BooleanField(
        default=True,
        help_text="Field observation submissions, reviews, and corrections"
    )
    notify_approvals = models.BooleanField(
        default=True,
        help_text="Approvals, rejections, and supervisor decisions"
    )
    notify_market_prices = models.BooleanField(
        default=True,
        help_text="Commodity price surveillance, validations, and bulletins"
    )
    notify_reports = models.BooleanField(
        default=True,
        help_text="On-demand report generation, scheduled bulletins, and ML models"
    )
    notify_announcements = models.BooleanField(
        default=True,
        help_text="General platform updates and administrative announcements"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"

    @classmethod
    def is_mandatory(cls, notification_type):
        """Returns True if the notification is a mandatory security or critical alert."""
        mandatory_types = {
            Notification.NotificationType.ACCOUNT_CREATED,
            Notification.NotificationType.ACCOUNT_ACTIVATED,
            Notification.NotificationType.ACCOUNT_DEACTIVATED,
            Notification.NotificationType.ROLE_CHANGED,
            Notification.NotificationType.PASSWORD_RESET_LINK,
            Notification.NotificationType.SECURITY_ALERT,
            Notification.NotificationType.SYSTEM_ERROR,
        }
        return notification_type in mandatory_types

    def can_send_in_app(self, notification_type):
        """Evaluates whether an in-app notification should be stored for this user."""
        if self.is_mandatory(notification_type):
            return True
        if not self.in_app_enabled:
            return False
        return self._check_category(notification_type)

    def can_send_email(self, notification_type):
        """Evaluates whether an email dispatch should be attempted for this user."""
        if self.is_mandatory(notification_type):
            return True
        if not self.email_enabled:
            return False
        return self._check_category(notification_type)

    def _check_category(self, notification_type):
        """Maps notification type to user preference category."""
        data_types = {
            Notification.NotificationType.DATA_SUBMITTED,
            Notification.NotificationType.CORRECTION_SUBMITTED,
            Notification.NotificationType.DATA_SUPERSEDED,
            Notification.NotificationType.DATA_IMPORTED,
            Notification.NotificationType.DATA_IMPORT_FAILED,
        }
        if notification_type in data_types:
            return self.notify_data_submissions

        approval_types = {
            Notification.NotificationType.DATA_APPROVED,
            Notification.NotificationType.DATA_RETURNED,
            Notification.NotificationType.DATA_REJECTED,
            Notification.NotificationType.PRICE_APPROVED,
            Notification.NotificationType.PRICE_RETURNED,
            Notification.NotificationType.PRICE_REJECTED,
            Notification.NotificationType.GEOGRAPHY_ASSIGNED,
        }
        if notification_type in approval_types:
            return self.notify_approvals

        market_types = {
            Notification.NotificationType.PRICE_SUBMITTED,
            Notification.NotificationType.PRICE_PUBLISHED,
        }
        if notification_type in market_types:
            return self.notify_market_prices

        report_types = {
            Notification.NotificationType.REPORT_GENERATED,
            Notification.NotificationType.REPORT_FAILED,
            Notification.NotificationType.SCHEDULED_REPORT_GENERATED,
            Notification.NotificationType.ML_MODEL_TRAINED,
            Notification.NotificationType.ML_MODEL_FAILED,
        }
        if notification_type in report_types:
            return self.notify_reports

        if notification_type == Notification.NotificationType.SYSTEM_ANNOUNCEMENT:
            return self.notify_announcements

        return True


class SystemAnnouncement(models.Model):
    """
    Administrator-broadcasted platform announcements.
    Can target all authenticated users, specific roles, or selected individuals.
    """
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=Notification.Priority.choices,
        default=Notification.Priority.HIGH
    )
    target_role = models.CharField(
        max_length=30,
        blank=True,
        help_text="Target role (e.g. DATA_ENTRY_OFFICER, DISTRICT_OFFICER). Leave blank for all users."
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='targeted_announcements',
        help_text="Specific users to notify. Leave empty if targeting role or all."
    )
    action_url = models.CharField(max_length=255, blank=True)
    send_email = models.BooleanField(
        default=True,
        help_text="Also dispatch email notifications to recipient inboxes"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_announcements'
    )
    broadcast_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Announcement'
        verbose_name_plural = 'System Announcements'

    def __str__(self):
        target = f"Role: {self.target_role}" if self.target_role else "All Users"
        return f"Announcement: {self.title} ({target})"


class EmailDeliveryLog(models.Model):
    """
    Append-only email delivery and retry tracking.
    Enforces idempotency to avoid sending duplicate emails during retries.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent Successfully'
        FAILED = 'FAILED', 'Delivery Failed'
        RETRIED = 'RETRIED', 'Retried'

    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_logs'
    )
    recipient_email = models.CharField(max_length=255, db_index=True)
    subject = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    error_message = models.TextField(blank=True)
    attempts = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Delivery Log'
        verbose_name_plural = 'Email Delivery Logs'

    def __str__(self):
        return f"Email to {self.recipient_email} - {self.subject} [{self.status}]"
