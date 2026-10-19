from django.db import models
from django.utils import timezone


class PublishedReport(models.Model):
    """
    Public and official published agricultural intelligence reports and bulletins.
    Published by NISR & MINAGRI, accessible to public citizens, researchers, and officers.
    """
    REPORT_TYPES = [
        ("survey", "Seasonal Agricultural Survey"),
        ("production", "Agricultural Production Report"),
        ("yield", "Crop Yield & Productivity Report"),
        ("land_use", "Land Use & Cultivated Area Report"),
        ("crop", "Crop-Specific Report"),
        ("livestock", "Livestock & Animal Production Report"),
        ("irrigation", "Irrigation & Water Management Report"),
        ("mechanization", "Agricultural Mechanization Report"),
        ("inputs", "Agricultural Inputs & Subsidies Report"),
        ("fertilizer", "Fertilizer Use Report"),
        ("seeds", "Seeds & Planting Materials Report"),
        ("soil", "Soil Health & Conservation Report"),
        ("pest_disease", "Pest & Crop Disease Report"),
        ("climate", "Climate & Weather Impact Report"),
        ("outlook", "Seasonal Agricultural Outlook"),
        ("food_security", "Food Security & Nutrition Report"),
        ("postharvest", "Post-Harvest Losses Report"),
        ("storage", "Agricultural Storage Report"),
        ("processing", "Agro-Processing & Value Addition Report"),
        ("market", "Agricultural Market Analysis"),
        ("prices", "Commodity Prices Report"),
        ("trade", "Agricultural Trade & Export Report"),
        ("supply_chain", "Agricultural Supply Chain Report"),
        ("farm_income", "Farm Income & Economic Analysis"),
        ("cost_benefit", "Agricultural Cost-Benefit Analysis"),
        ("finance", "Agricultural Finance & Credit Report"),
        ("insurance", "Agricultural Insurance & Risk Report"),
        ("district", "District Agricultural Performance Report"),
        ("province", "Provincial Agricultural Performance Report"),
        ("national", "National Agricultural Statistics Report"),
        ("research", "Agricultural Research Report"),
        ("impact", "Agricultural Impact Assessment"),
        ("policy", "Agricultural Policy Analysis"),
        ("brief", "Policy Brief"),
        ("annual", "Annual Agricultural Report"),
        ("quarterly", "Quarterly Agricultural Report"),
        ("monthly", "Monthly Agricultural Report"),
        ("data_quality", "Data Quality & Validation Report"),
        ("methodology", "Survey Methodology & Technical Report"),
        ("other", "Other Agricultural Report"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=300, blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='survey')
    report_type_label = models.CharField(max_length=100, default='Seasonal Survey')
    crop = models.CharField(max_length=100, default='All Crops')
    season = models.CharField(max_length=100, default='All Seasons')
    year = models.IntegerField(default=2025)
    publication_date = models.DateField(default=timezone.now)
    date_display = models.CharField(max_length=50, blank=True)
    executive_summary = models.TextField(blank=True)
    key_metrics = models.JSONField(default=dict, blank=True)
    pdf_filename = models.CharField(max_length=255, blank=True)
    downloads_count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publication_date', '-id']
        verbose_name = 'Published Agricultural Report'
        verbose_name_plural = 'Published Agricultural Reports'

    def __str__(self):
        return f"{self.title} ({self.date_display or self.publication_date})"
