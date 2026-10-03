"""
Seasonal Agricultural Surveys (SAS - inspired by NISR / MINAGRI methodology).
Field questionnaire submissions, parcel sampling, yield reports.
"""
from django.db import models
from apps.agriculture.models import AgriculturalSeason, Crop
from apps.farmers.models import Farmer
from apps.geography.models import Sector

class SurveyCampaign(models.Model):
    title = models.CharField(max_length=150)
    season = models.ForeignKey(AgriculturalSeason, on_delete=models.CASCADE, related_name='survey_campaigns')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.season}"

class FarmSurveySubmission(models.Model):
    campaign = models.ForeignKey(SurveyCampaign, on_delete=models.CASCADE, related_name='submissions')
    farmer = models.ForeignKey(Farmer, on_delete=models.SET_NULL, null=True, blank=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    area_planted_ha = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_harvested_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    yield_kg_per_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey #{self.id} - {self.crop.name} ({self.campaign.season})"
