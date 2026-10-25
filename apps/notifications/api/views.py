"""
REST API ViewSets and Views for Notifications.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from apps.notifications.models import Notification, NotificationPreference, SystemAnnouncement
from apps.notifications.services import NotificationService
from apps.notifications.api.serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    SystemAnnouncementSerializer,
)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    CRUD and workflow transitions for authenticated user's notifications.
    Strictly isolated: users can only see and manipulate their own notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = Notification.objects.filter(
            recipient=self.request.user,
            is_dismissed=False
        ).select_related('actor').order_by('-created_at')

        # Filter by read status
        is_read_param = self.request.query_params.get('is_read')
        if is_read_param is not None:
            if is_read_param.lower() in ['true', '1']:
                qs = qs.filter(is_read=True)
            elif is_read_param.lower() in ['false', '0']:
                qs = qs.filter(is_read=False)

        # Filter by priority
        priority_param = self.request.query_params.get('priority')
        if priority_param and priority_param.upper() in Notification.Priority.values:
            qs = qs.filter(priority=priority_param.upper())

        # Filter by type
        type_param = self.request.query_params.get('type')
        if type_param:
            qs = qs.filter(notification_type=type_param)

        return qs

    def perform_destroy(self, instance):
        """Soft-deletes notification to preserve audit history while dismissing from user inbox."""
        instance.dismiss()

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Marks a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'read', 'id': notification.id, 'unread_count': NotificationService.get_unread_count(request.user)})

    @action(detail=True, methods=['post'])
    def unread(self, request, pk=None):
        """Marks a single notification as unread."""
        notification = self.get_object()
        notification.mark_as_unread()
        return Response({'status': 'unread', 'id': notification.id, 'unread_count': NotificationService.get_unread_count(request.user)})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marks all active notifications for the current user as read."""
        unread_qs = Notification.objects.filter(recipient=request.user, is_read=False, is_dismissed=False)
        count = unread_qs.update(is_read=True, read_at=timezone.now(), updated_at=timezone.now())
        return Response({'status': 'all_marked_read', 'count': count, 'unread_count': 0})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Returns the current unread notification count."""
        count = NotificationService.get_unread_count(request.user)
        return Response({'unread_count': count})


class NotificationPreferenceAPIView(APIView):
    """
    Retrieves and updates notification preferences for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data)

    def put(self, request):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    patch = put


class IsSystemAdminUser(permissions.BasePermission):
    """Clearance check: Only active System Administrators can manage broadcast announcements."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_system_admin', False) or request.user.is_superuser


class SystemAnnouncementViewSet(viewsets.ModelViewSet):
    """
    Administrator API for managing and broadcasting system announcements.
    """
    queryset = SystemAnnouncement.objects.select_related('created_by').all().order_by('-created_at')
    serializer_class = SystemAnnouncementSerializer
    permission_classes = [IsSystemAdminUser]

    def perform_create(self, serializer):
        announcement = serializer.save(created_by=self.request.user)
        NotificationService.broadcast_announcement(announcement, request=self.request)
