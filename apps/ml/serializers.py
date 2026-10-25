"""
AgriLens DRF Serializers for Machine Learning & Decision Intelligence.
"""
from rest_framework import serializers
from apps.ml.models import MLModel, DistrictTypology, PredictionLog


class PracticesSerializer(serializers.Serializer):
    is_improved_seed = serializers.BooleanField(default=False)
    uses_inorganic_fertilizer = serializers.BooleanField(default=False)
    uses_organic_fertilizer = serializers.BooleanField(default=False)
    uses_pesticide = serializers.BooleanField(default=False)
    is_irrigated = serializers.BooleanField(default=False)
    has_anti_erosion = serializers.BooleanField(default=False)
    uses_mechanization = serializers.BooleanField(default=False)


class YieldPredictionInputSerializer(serializers.Serializer):
    crop = serializers.CharField(max_length=100, default='Maize')
    district = serializers.CharField(max_length=100, default='Musanze')
    plot_area_ha = serializers.FloatField(min_value=0.001, max_value=1000.0, default=0.5)
    is_improved_seed = serializers.BooleanField(default=False)
    uses_inorganic_fertilizer = serializers.BooleanField(default=False)
    uses_organic_fertilizer = serializers.BooleanField(default=False)
    uses_pesticide = serializers.BooleanField(default=False)
    is_irrigated = serializers.BooleanField(default=False)
    has_anti_erosion = serializers.BooleanField(default=False)
    uses_mechanization = serializers.BooleanField(default=False)


class ScenarioComparisonInputSerializer(serializers.Serializer):
    crop = serializers.CharField(max_length=100, default='Maize')
    district = serializers.CharField(max_length=100, default='Musanze')
    plot_area_ha = serializers.FloatField(min_value=0.001, max_value=1000.0, default=0.5)
    current_practices = PracticesSerializer(required=False, default=dict)
    recommended_practices = PracticesSerializer(required=False, default=dict)


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = [
            'id',
            'name',
            'model_type',
            'version',
            'algorithm',
            'target_variable',
            'feature_names',
            'metrics',
            'feature_importance',
            'training_provenance',
            'observation_count',
            'validation_methodology',
            'is_active',
            'status',
            'training_notes',
            'created_at',
            'updated_at',
        ]


class DistrictTypologySerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    district_code = serializers.CharField(source='district.code', read_only=True)
    province_name = serializers.CharField(source='district.province.name', read_only=True)

    class Meta:
        model = DistrictTypology
        fields = [
            'id',
            'district_id',
            'district_name',
            'district_code',
            'province_name',
            'cluster_id',
            'cluster_name',
            'profile_summary',
            'main_constraints',
            'recommended_interventions',
            'avg_yield_kg_per_ha',
            'seed_adoption_rate',
            'fertilizer_adoption_rate',
            'loss_rate_percentage',
            'updated_at',
        ]
