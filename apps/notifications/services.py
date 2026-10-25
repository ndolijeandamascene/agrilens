"""
Unified Notification Service for AgriLens Rwanda.
Coordinates in-app notification creation, role-based targeting,
user preference enforcement, audit logging, and email delivery.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.permissions import AuditService
from apps.accounts.models import AuditLog
from apps.notifications.models import Notification, NotificationPreference, SystemAnnouncement
from apps.notifications.emails import EmailService

User = get_user_model()


class NotificationService:
    """
    Central business facade for dispatching notifications across AgriLens.
    """

    @classmethod
    def send(
        cls,
        recipient,
        notification_type,
        title,
        message,
        related_object=None,
        action_url='',
        priority=Notification.Priority.MEDIUM,
        actor=None,
        metadata=None,
        request=None,
        send_email=True
    ):
        """
        Creates an in-app Notification and dispatches email per recipient preferences.
        """
        if not recipient:
            return None

        # Fetch or initialize recipient preferences
        pref, _ = NotificationPreference.objects.get_or_create(user=recipient)

        # Evaluate related object
        related_object_type = ""
        related_object_id = ""
        if related_object is not None:
            related_object_type = related_object.__class__.__name__
            related_object_id = str(getattr(related_object, 'pk', ''))

        safe_metadata = dict(metadata or {})

        # Check in-app preference (mandatory events bypass user opt-out)
        notification = None
        if pref.can_send_in_app(notification_type):
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                title=title[:200],
                message=message,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                action_url=action_url,
                priority=priority,
                actor=actor,
                metadata=safe_metadata,
            )

            # Audit trail
            AuditService.log(
                action=AuditLog.Action.NOTIFICATION_CREATED,
                actor=actor,
                target=notification,
                details={
                    'recipient': recipient.username,
                    'type': notification_type,
                    'priority': priority,
                    'title': title[:100]
                },
                request=request
            )

        # Dispatch email if enabled
        if send_email and notification and recipient.email:
            if pref.can_send_email(notification_type):
                EmailService.send_for_notification(notification, request=request)

        return notification

    @classmethod
    def send_to_users(cls, recipients, notification_type, title, message, **kwargs):
        """Dispatches identical notification to an iterable of users."""
        created_list = []
        for u in recipients:
            n = cls.send(recipient=u, notification_type=notification_type, title=title, message=message, **kwargs)
            if n:
                created_list.append(n)
        return created_list

    @classmethod
    def send_to_role(cls, role, notification_type, title, message, district_id=None, **kwargs):
        """
        Dispatches notification to all active users with a specified role.
        If district_id is provided and the role is DISTRICT_OFFICER, scopes to officers assigned to that district.
        """
        qs = User.objects.filter(is_active=True, role=role)
        if district_id and role == User.Role.DISTRICT_OFFICER:
            qs = qs.filter(assigned_districts__id=district_id)

        recipients = list(qs.distinct())
        return cls.send_to_users(recipients, notification_type=notification_type, title=title, message=message, **kwargs)

    @classmethod
    def send_to_reviewers(cls, district_id=None, notification_type=None, title="", message="", exclude_user=None, actor=None, district=None, **kwargs):
        """
        Identifies authorized reviewers for a given district:
        Includes assigned District Agriculture Officers, NISR Data Managers, and System Admins.
        Enforces segregation of duties by excluding the submitting officer.
        """
        if district and not district_id:
            district_id = getattr(district, 'id', None)

        filter_q = (
            models.Q(role=User.Role.ADMIN) |
            models.Q(role=User.Role.NISR_DATA_MANAGER) |
            models.Q(role=User.Role.REVIEWER)
        )
        if district_id:
            filter_q |= (models.Q(role=User.Role.DISTRICT_OFFICER) & models.Q(assigned_districts__id=district_id))
        else:
            filter_q |= models.Q(role=User.Role.DISTRICT_OFFICER)

        reviewers = User.objects.filter(is_active=True).filter(filter_q).distinct()

        ex = exclude_user or actor
        if ex:
            reviewers = reviewers.exclude(pk=ex.pk)

        return cls.send_to_users(reviewers, notification_type=notification_type, title=title, message=message, actor=actor, **kwargs)

    @classmethod
    def mark_as_read(cls, notification, user, request=None):
        """Marks a notification as read with ownership validation and audit logging."""
        if not notification or notification.recipient_id != getattr(user, 'id', None):
            return False
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
            AuditService.log(
                action=AuditLog.Action.NOTIFICATION_READ,
                actor=user,
                target=notification,
                details={'notification_id': notification.id},
                request=request
            )
        return True

    @classmethod
    def mark_as_unread(cls, notification, user):
        """Marks a notification as unread with ownership validation."""
        if not notification or notification.recipient_id != getattr(user, 'id', None):
            return False
        if notification.is_read:
            notification.is_read = False
            notification.read_at = None
            notification.save(update_fields=['is_read', 'read_at'])
        return True

    @classmethod
    def mark_all_as_read(cls, user, request=None):
        """Marks all unread notifications as read for a user."""
        if not user or not user.is_authenticated:
            return 0
        count = Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return count

    @classmethod
    def dismiss(cls, notification, user):
        """Dismisses/archives a notification."""
        if not notification or notification.recipient_id != getattr(user, 'id', None):
            return False
        notification.is_dismissed = True
        notification.save(update_fields=['is_dismissed'])
        return True

    @classmethod
    def broadcast_announcement(cls, announcement, request=None):
        """
        Broadcasts a SystemAnnouncement record to its intended target audience.
        """
        if announcement.target_users.exists():
            recipients = list(announcement.target_users.filter(is_active=True))
        elif announcement.target_role:
            recipients = list(User.objects.filter(is_active=True, role=announcement.target_role))
        else:
            recipients = list(User.objects.filter(is_active=True))

        count = 0
        for u in recipients:
            cls.send(
                recipient=u,
                notification_type=Notification.NotificationType.SYSTEM_ANNOUNCEMENT,
                title=announcement.title,
                message=announcement.message,
                action_url=announcement.action_url,
                priority=announcement.priority,
                actor=announcement.created_by,
                request=request,
                send_email=announcement.send_email
            )
            count += 1

        announcement.broadcast_count = count
        announcement.save(update_fields=['broadcast_count'])

        AuditService.log(
            action=AuditLog.Action.ANNOUNCEMENT_CREATED,
            actor=announcement.created_by,
            target=announcement,
            details={
                'title': announcement.title,
                'target_role': announcement.target_role or 'ALL',
                'recipient_count': count
            },
            request=request
        )
        return count

    @classmethod
    def get_unread_count(cls, user):
        """Returns the current count of unread, undismissed notifications for user."""
        if not user or not user.is_authenticated:
            return 0
        return Notification.objects.filter(recipient=user, is_read=False, is_dismissed=False).count()

    @classmethod
    def get_recent_notifications(cls, user, limit=5):
        """Returns the most recent notifications for header notification bell dropdown."""
        if not user or not user.is_authenticated:
            return []
        return list(
            Notification.objects.filter(recipient=user, is_dismissed=False)
            .select_related('actor')
            .order_by('-created_at')[:limit]
        )
