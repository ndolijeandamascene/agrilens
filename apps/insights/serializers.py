"""
AgriLens Agricultural Insights REST API Serializers.
"""
from rest_framework import serializers
from apps.insights.models import AgriculturalInsight


class AgriculturalInsightListSerializer(serializers.ModelSerializer):
    """Compact serializer for public and internal catalog listings."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    data_quality_display = serializers.CharField(source='get_data_quality_status_display', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True, default=None)
    district_name = serializers.CharField(source='district.name', read_only=True, default=None)
    province_name = serializers.CharField(source='province.name', read_only=True, default=None)
    current_season_label = serializers.CharField(source='current_season.__str__', read_only=True)
    comparison_season_label = serializers.CharField(source='comparison_season.__str__', read_only=True, default=None)
    formatted_change = serializers.CharField(read_only=True)
    scope_label = serializers.CharField(read_only=True)

    class Meta:
        model = AgriculturalInsight
        fields = [
            'id',
            'title',
            'headline',
            'category',
            'category_display',
            'crop',
            'crop_name',
            'district',
            'district_name',
            'province',
            'province_name',
            'current_season',
            'current_season_label',
            'comparison_season',
            'comparison_season_label',
            'indicator_name',
            'indicator_unit',
            'current_value',
            'previous_value',
            'absolute_change',
            'percentage_change',
            'formatted_change',
            'direction',
            'direction_display',
            'source',
            'data_quality_status',
            'data_quality_display',
            'sample_size_current',
            'sample_size_comparison',
            'scope_label',
            'status',
            'status_display',
            'is_featured',
            'published_at',
            'created_at',
        ]


class AgriculturalInsightDetailSerializer(AgriculturalInsightListSerializer):
    """Complete serializer with narrative story, calculation evidence, and analyst investigation steps."""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default=None)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, default=None)

    class Meta(AgriculturalInsightListSerializer.Meta):
        fields = AgriculturalInsightListSerializer.Meta.fields + [
            'summary',
            'data_quality_notes',
            'investigation_next_steps',
            'evidence_metadata',
            'fingerprint',
            'created_by',
            'created_by_name',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'review_comments',
            'updated_at',
        ]


class InsightActionSerializer(serializers.Serializer):
    """Payload for review, approve, reject, publish, and unpublish operations."""
    comments = serializers.CharField(required=False, allow_blank=True, default="")


class InsightGenerateSerializer(serializers.Serializer):
    """Payload for triggering the insight engine via API."""
    year = serializers.IntegerField(default=2025)
    season = serializers.CharField(default='A')
    auto_publish = serializers.BooleanField(default=False)
    min_pct = serializers.FloatField(default=5.0)


class InsightStatisticsSerializer(serializers.Serializer):
    """Aggregated governance and category metrics."""
    total_insights = serializers.IntegerField()
    published_count = serializers.IntegerField()
    under_review_count = serializers.IntegerField()
    generated_count = serializers.IntegerField()
    approved_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    by_category = serializers.DictField()
    by_province = serializers.DictField()
    by_data_quality = serializers.DictField()
