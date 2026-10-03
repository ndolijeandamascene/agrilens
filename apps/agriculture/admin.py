from django.contrib import admin
from .models import CropCategory, Crop, AgriculturalSeason

admin.site.register(CropCategory)
admin.site.register(Crop)
admin.site.register(AgriculturalSeason)
