"""
Agricultural domain models:
- Crops (Maize, Beans, Irish Potato, Cassava, Rice, Coffee, Tea)
- Agricultural Seasons in Rwanda (Season A, Season B, Season C)
- Cultivation practices and farming categories.
"""
from django.db import models

class CropCategory(models.Model):
    name = models.CharField(max_length=50) # Cereals, Legumes, Tubers, Cash crops
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Crop(models.Model):
    category = models.ForeignKey(CropCategory, on_delete=models.PROTECT, related_name='crops')
    name = models.CharField(max_length=100)
    kinyarwanda_name = models.CharField(max_length=100, blank=True)
    scientific_name = models.CharField(max_length=120, blank=True)
    is_priority_crop = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class AgriculturalSeason(models.Model):
    class SeasonCode(models.TextChoices):
        SEASON_A = 'A', 'Season A (Sept - Feb)'
        SEASON_B = 'B', 'Season B (Mar - June)'
        SEASON_C = 'C', 'Season C (July - Sept / Marshlands)'

    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SeasonCode.choices)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('year', 'season')

    def __str__(self):
        return f"{self.year} {self.get_season_display()}"
