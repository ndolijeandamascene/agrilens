"""
AgriLens Machine Learning Permissions.
Enforces institutional role tiers for model retraining and management.
"""
from rest_framework import permissions
from apps.accounts.models import User


class CanTrainMLModel(permissions.BasePermission):
    """
    Only Administrators, NISR Data Managers, and Agricultural Data Analysts
    are authorized to trigger model retraining and deploy updated artifacts.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        allowed_roles = [
            User.Role.ADMIN,
            User.Role.NISR_DATA_MANAGER,
            User.Role.ANALYST,
        ]
        return getattr(request.user, 'role', None) in allowed_roles


class CanViewML(permissions.BasePermission):
    """Public read-only access for agricultural intelligence and decision support."""
    def has_permission(self, request, view):
        return True
