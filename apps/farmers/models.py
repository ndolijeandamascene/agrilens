"""
Farmer profiles, cooperatives, household plots, and demographic segments.
"""
from django.db import models
from apps.geography.models import Sector

class Cooperative(models.Model):
    name = models.CharField(max_length=150)
    registration_number = models.CharField(max_length=50, blank=True)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name='cooperatives')
    contact_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Farmer(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    national_id = models.CharField(max_length=16, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    cooperative = models.ForeignKey(Cooperative, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name='farmers')
    land_size_ha = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
