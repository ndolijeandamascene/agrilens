"""
Seasonal Agricultural Surveys (SAS - inspired by NISR / MINAGRI methodology).
Field questionnaire submissions, parcel sampling, yield reports.
"""
from django.db import models
from apps.agriculture.models import AgriculturalSeason, Crop
from apps.farmers.models import Farmer
from apps.geography.models import Sector, District

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


class DistrictSocioeconomicProfile(models.Model):
    """
    NISR Agriculture Household Survey (AHS 2024) Socioeconomic Profile.
    Aggregated district-level structural indicators covering extension advisory,
    financial inclusion, land tenure, environmental sustainability, and dairy production.
    """
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='socioeconomic_profiles')
    survey_year = models.PositiveIntegerField(default=2024, db_index=True)
    provenance = models.CharField(max_length=60, default='NISR_AHS_2024')

    sample_households_count = models.PositiveIntegerField(default=0)
    total_plots_surveyed = models.PositiveIntegerField(default=0)

    # 1. Agricultural Extension & Advisory Reach (Section 6)
    extension_advisory_reach_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% households receiving extension/advisory services")
    twigire_muhinzi_membership_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% households in Twigire Muhinzi/Mworozi groups")

    # 2. Financial Inclusion & Agricultural Credit (Credits)
    credit_access_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% households obtaining agricultural credit")
    sacco_credit_share_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% of agricultural credit sourced from Umurenge SACCO")
    bank_credit_share_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% of credit sourced from Commercial Banks")

    # 3. Land Tenure Security & Parcel Fragmentation (Section 2)
    formal_land_title_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% of farm parcels holding formal registered land titles")
    avg_plots_per_household = models.DecimalField(max_digits=4, decimal_places=2, default=0.0, help_text="Average number of cultivated parcels per household")
    avg_plot_area_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Average plot area in square meters")

    # 4. Sustainable Agriculture & Environmental Risk (Section 8)
    sustainable_practices_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% households adopting soil/environmental conservation measures")

    # 5. Livestock & Dairy Milk Production (Section 11)
    dairy_producing_households_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="% households producing cattle milk (Girinka program indicator)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('district', 'survey_year')
        ordering = ['district__province__name', 'district__name']

    def __str__(self):
        return f"{self.district.name} ({self.survey_year} AHS Profile)"

