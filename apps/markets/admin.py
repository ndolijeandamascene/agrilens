from django.contrib import admin
from .models import MarketLocation, CommodityPrice

admin.site.register(MarketLocation)
admin.site.register(CommodityPrice)
