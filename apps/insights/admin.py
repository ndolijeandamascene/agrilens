from django.contrib import admin
from .models import AgriculturalInsight


@admin.register(AgriculturalInsight)
class AgriculturalInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'crop', 'district', 'current_season', 'percentage_change', 'status', 'is_featured', 'created_at']
    list_filter = ['status', 'category', 'is_featured', 'current_season', 'data_quality_status']
    search_fields = ['title', 'summary', 'headline', 'investigation_next_steps', 'fingerprint']
    readonly_fields = ['fingerprint', 'created_at', 'updated_at']
