"""
Market price monitoring across major Rwandan markets (e.g. Kimironko, Nyabugogo, Musanze, Huye).
Daily and weekly commodity prices for food basket and cash crops.
"""
from django.db import models
from apps.geography.models import District
from apps.agriculture.models import Crop

class MarketLocation(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='markets')
    is_major_hub = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.district.name})"

class CommodityPrice(models.Model):
    market = models.ForeignKey(MarketLocation, on_delete=models.CASCADE, related_name='prices')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='market_prices')
    price_per_kg_rwf = models.DecimalField(max_digits=8, decimal_places=2)
    wholesale_price_rwf = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    date_recorded = models.DateField()

    class Meta:
        ordering = ['-date_recorded']

    def __str__(self):
        return f"{self.crop.name} at {self.market.name}: {self.price_per_kg_rwf} RWF ({self.date_recorded})"
