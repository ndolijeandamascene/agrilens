"""
Aggregated indicators and productivity KPIs:
- Yield per Hectare (kg/ha) by district/season
- Post-harvest loss rate
- Commercialization index
- Climate shock vulnerability score
"""
from django.db import models
from apps.geography.models import District
from apps.agriculture.models import AgriculturalSeason, Crop

class ProductivityMetric(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='productivity_metrics')
    season = models.ForeignKey(AgriculturalSeason, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    avg_yield_kg_per_ha = models.DecimalField(max_digits=10, decimal_places=2)
    total_production_mt = models.DecimalField(max_digits=12, decimal_places=2) # Metric Tons
    post_harvest_loss_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.district.name} - {self.crop.name} - {self.season}"
