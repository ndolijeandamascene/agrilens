"""
AgriLens Machine Learning Models & Metadata Registry.
Stores versioned ML model artifacts, training metrics, provenance lineage,
and computed district agricultural typologies.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class MLModel(models.Model):
    """
    Model Registry & Governance.
    Tracks trained model artifacts, cross-validation metrics, feature schemas,
    and empirical provenance based on verified NISR microdata.
    """
    class ModelType(models.TextChoices):
        YIELD_PREDICTION = 'YIELD_PREDICTION', 'Farm-Level Crop Yield Prediction'
        DISTRICT_CLUSTERING = 'DISTRICT_CLUSTERING', 'District Agro-Ecological Typology Clustering'
        PRODUCTION_FORECAST = 'PRODUCTION_FORECAST', 'Seasonal Crop Production Forecasting'
        PRICE_FORECAST = 'PRICE_FORECAST', 'Commodity Market Price Surveillance Forecasting'

    class Status(models.TextChoices):
        TRAINED = 'TRAINED', 'Trained & Verified'
        ACTIVE = 'ACTIVE', 'Active / In Serving'
        DEPRECATED = 'DEPRECATED', 'Deprecated'
        FAILED = 'FAILED', 'Training Failed'

    name = models.CharField(max_length=150, help_text="Human-readable model name")
    model_type = models.CharField(max_length=50, choices=ModelType.choices, db_index=True)
    version = models.CharField(max_length=30, default='v1.0', help_text="Semantic version (e.g. v1.0)")
    algorithm = models.CharField(max_length=100, help_text="e.g. RandomForestRegressor, KMeans")
    target_variable = models.CharField(max_length=100, blank=True, help_text="Target metric name")
    
    # Feature Schema & Metrics
    feature_names = models.JSONField(default=list, help_text="Ordered list of model input features")
    metrics = models.JSONField(default=dict, help_text="Validation metrics: R2, MAE, RMSE, baseline comparisons")
    feature_importance = models.JSONField(default=dict, blank=True, help_text="Feature importance mapping")
    
    # Provenance & Data Lineage
    training_provenance = models.CharField(max_length=100, default='NISR_SAS_2024_2025', help_text="Origin dataset slug")
    observation_count = models.PositiveIntegerField(default=0, help_text="Number of training observations")
    validation_methodology = models.TextField(blank=True, help_text="Validation scheme details")
    
    # Artifact Storage
    artifact_filename = models.CharField(max_length=255, blank=True, help_text="Artifact file name relative to ML_MODEL_DIR")
    is_active = models.BooleanField(default=True, db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ACTIVE)
    
    training_notes = models.TextField(blank=True)
    trained_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trained_ml_models'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ML Model Metadata'
        verbose_name_plural = 'ML Model Registry'
        unique_together = ('model_type', 'version')

    def __str__(self):
        return f"{self.name} ({self.version}) - {self.algorithm} [{self.get_status_display()}]"


class DistrictTypology(models.Model):
    """
    District Agro-Ecological Typology & Constraint Profile.
    Generated via unsupervised ML clustering (K-Means) across Rwanda's 30 districts
    grounded in official SAS microdata indicators.
    """
    district = models.OneToOneField(
        'geography.District',
        on_delete=models.CASCADE,
        related_name='typology'
    )
    cluster_id = models.IntegerField(help_text="Numeric cluster ID (0-indexed)")
    cluster_name = models.CharField(max_length=150, help_text="Domain-meaningful cluster title")
    profile_summary = models.TextField(help_text="Detailed agro-ecological and farming system profile")
    main_constraints = models.JSONField(default=list, help_text="Primary agricultural limiting factors")
    recommended_interventions = models.JSONField(default=list, help_text="Targeted public and private policy interventions")
    
    # Centroid summary metrics
    avg_yield_kg_per_ha = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    seed_adoption_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    fertilizer_adoption_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    loss_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    model = models.ForeignKey(
        MLModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='district_typologies'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cluster_id', 'district__name']
        verbose_name = 'District Typology'
        verbose_name_plural = 'District Typologies'

    def __str__(self):
        return f"{self.district.name}: Cluster {self.cluster_id} - {self.cluster_name}"


class PredictionLog(models.Model):
    """
    Inference Audit Log.
    Tracks prediction requests, inputs, and output latency for operational monitoring.
    """
    model_type = models.CharField(max_length=50, db_index=True)
    input_payload = models.JSONField()
    output_payload = models.JSONField()
    latency_ms = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
