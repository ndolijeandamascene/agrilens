from django.contrib import admin
from .models import RecommendationRule, Recommendation, ActionPlan, OutcomeMeasurement


@admin.register(RecommendationRule)
class RecommendationRuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'target_stakeholder', 'version', 'is_active')
    list_filter = ('target_stakeholder', 'is_active')
    search_fields = ('code', 'title', 'description')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_stakeholder', 'district', 'crop', 'priority', 'status', 'created_at')
    list_filter = ('target_stakeholder', 'priority', 'status', 'season')
    search_fields = ('title', 'problem_statement', 'recommendation_text')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'recommendation', 'assigned_to', 'assigned_organization', 'target_date', 'status')
    list_filter = ('status', 'target_date')
    search_fields = ('title', 'action_details', 'assigned_organization')


@admin.register(OutcomeMeasurement)
class OutcomeMeasurementAdmin(admin.ModelAdmin):
    list_display = ('action_plan', 'district', 'crop', 'baseline_yield_kg_per_ha', 'evaluation_yield_kg_per_ha', 'observed_yield_change_pct', 'measured_at')
    list_filter = ('district', 'crop')
