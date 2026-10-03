"""
Rwanda Administrative Boundary Models:
Province (5) -> District (30) -> Sector (416) -> Cell -> Village.
Agro-ecological zones (e.g., Central Plateau, Eastern Savanna, Volcanic Ranges).
"""
from django.db import models

class Province(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.province.name})"

class Sector(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='sectors')
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f"{self.name}, {self.district.name}"
