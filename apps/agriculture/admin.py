from django.contrib import admin
from django.utils.html import format_html
from .models import CropCategory, Crop, AgriculturalSeason

@admin.register(CropCategory)
class CropCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_preview', 'name', 'category', 'is_priority_crop', 'icon')
    list_filter = ('category', 'is_priority_crop')
    search_fields = ('name', 'kinyarwanda_name', 'scientific_name')
    fields = ('name', 'category', 'kinyarwanda_name', 'scientific_name', 'is_priority_crop', 'image', 'icon')

    def thumbnail_preview(self, obj):
        img_url = obj.image_url_or_default
        if img_url:
            return format_html('<img src="{}" style="width: 36px; height: 36px; object-fit: cover; border-radius: 6px; border: 1px solid #e2e8f0;" />', img_url)
        return format_html('<div style="width: 36px; height: 36px; border-radius: 6px; background: #ecfdf5; border: 1px solid #d1fae5; display: inline-flex; align-items: center; justify-content: center; color: #059669;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6"/></svg></div>')
    thumbnail_preview.short_description = 'Thumbnail'

@admin.register(AgriculturalSeason)
class AgriculturalSeasonAdmin(admin.ModelAdmin):
    list_display = ('year', 'season', 'start_date', 'end_date')
    list_filter = ('season', 'year')
