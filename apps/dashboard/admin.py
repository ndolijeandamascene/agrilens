from django.contrib import admin
from .models import PublishedReport


@admin.register(PublishedReport)
class PublishedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'crop', 'season', 'year', 'publication_date', 'is_published')
    list_filter = ('report_type', 'crop', 'season', 'year', 'is_published')
    search_fields = ('title', 'subtitle', 'executive_summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publication_date'
    actions = ['publish_reports', 'unpublish_reports']

    def publish_reports(self, request, queryset):
        queryset.update(is_published=True)
    publish_reports.short_description = "Publish selected reports"

    def unpublish_reports(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_reports.short_description = "Unpublish selected reports"
