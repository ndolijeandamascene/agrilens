"""
Agricultural inputs (improved seeds, fertilizers: DAP, NPK, Urea, pesticides, lime).
Subsidy program tracking (e.g. Smart Nkunganire System integration).
"""
from django.db import models

class InputCategory(models.Model):
    name = models.CharField(max_length=50) # Fertilizer, Improved Seeds, Pesticides, Lime

    def __str__(self):
        return self.name

class AgriculturalInput(models.Model):
    category = models.ForeignKey(InputCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100) # e.g. DAP, Urea, Maize Seed H628
    unit = models.CharField(max_length=20, default='kg')
    unit_price_rwf = models.DecimalField(max_digits=10, decimal_places=2)
    subsidized_price_rwf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name
