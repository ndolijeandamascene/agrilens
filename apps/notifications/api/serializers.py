"""
Serializers for Notification REST API endpoints.
"""
from rest_framework import serializers
from apps.notifications.models import Notification, NotificationPreference, SystemAnnouncement


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True, default=None)
    category = serializers.CharField(read_only=True)
    icon_class = serializers.CharField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'related_object_type',
            'related_object_id',
            'action_url',
            'is_read',
            'read_at',
            'priority',
            'category',
            'icon_class',
            'actor_username',
            'metadata',
            'email_sent',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'actor_username', 'category', 'icon_class', 'email_sent']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled',
            'in_app_enabled',
            'notify_data_submissions',
            'notify_approvals',
            'notify_market_prices',
            'notify_reports',
            'notify_announcements',
            'updated_at',
        ]
        read_only_fields = ['updated_at']


class SystemAnnouncementSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = SystemAnnouncement
        fields = [
            'id',
            'title',
            'message',
            'priority',
            'target_role',
            'action_url',
            'send_email',
            'is_active',
            'created_by_username',
            'broadcast_count',
            'created_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'created_by_username', 'broadcast_count', 'created_at']
