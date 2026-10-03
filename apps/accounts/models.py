"""
User and Role models for AgriLens.
Roles: Policy Maker, Agricultural Analyst, Field Extension Officer, Admin.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Administrator'
        ANALYST = 'ANALYST', 'Agricultural Data Analyst'
        POLICY_MAKER = 'POLICY_MAKER', 'Policy Maker / MINAGRI'
        EXTENSION_OFFICER = 'EXTENSION_OFFICER', 'Field Extension Officer'
        RESEARCHER = 'RESEARCHER', 'Agricultural Researcher'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.ANALYST,
        help_text='User role and access tier'
    )
    organization = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
