"""
AgriLens Model Explainability & Transparency Service.
Provides feature importance mappings, validation benchmarks, data provenance details,
and non-causal limitations.
"""
from typing import Dict, Any
from apps.ml.models import MLModel
from .inference import MANDATORY_ML_DISCLAIMER


class ModelExplainabilityService:
    """Provides algorithmic transparency and feature importance reports."""

    LIMITATIONS = [
        "Observational Survey Design: Models are trained on cross-sectional survey microdata (SAS 2024/2025). Predictions reflect observed statistical associations, not verified randomized agronomic trial effects.",
        "Unobserved Confounders: Soil chemical pH, micro-topography, pest outbreaks, and hyper-local precipitation are not fully captured in household survey questionnaires.",
        "Survey Expansion Weights: Sample weights reflect administrative stratum expansion factors, which may introduce variance on small sub-district sample slices.",
        "Zero Causal Guarantee: Adopting an input practice does not automatically guarantee modeled yield uplift under adverse agro-climatic conditions.",
    ]

    @classmethod
    def get_report(cls) -> Dict[str, Any]:
        """Returns full transparency report for the active yield prediction model."""
        model_record = MLModel.objects.filter(
            model_type=MLModel.ModelType.YIELD_PREDICTION,
            is_active=True
        ).order_by('-created_at').first()

        if not model_record:
            return {
                'status': 'NO_ACTIVE_MODEL',
                'model_name': 'AgriLens Crop Yield Predictor',
                'algorithm': 'RandomForestRegressor (Awaiting Training)',
                'version': 'N/A',
                'metrics': {},
                'feature_importances': {},
                'training_provenance': 'NISR_SAS_2024_2025',
                'observation_count': 0,
                'validation_methodology': 'Temporal hold-out across survey seasons',
                'limitations': cls.LIMITATIONS,
                'disclaimer': MANDATORY_ML_DISCLAIMER,
            }

        metrics = model_record.metrics or {}
        feature_imp = model_record.feature_importance or {}

        # Sort feature importances descending
        sorted_imp = dict(sorted(feature_imp.items(), key=lambda x: x[1], reverse=True))

        return {
            'status': 'ACTIVE',
            'model_name': model_record.name,
            'algorithm': model_record.algorithm,
            'version': model_record.version,
            'training_timestamp': model_record.created_at.isoformat() if model_record.created_at else None,
            'training_provenance': model_record.training_provenance,
            'observation_count': model_record.observation_count,
            'target_variable': model_record.target_variable,
            'validation_methodology': model_record.validation_methodology,
            'metrics': {
                'r2_score': metrics.get('r2'),
                'mae_kg_per_ha': metrics.get('mae'),
                'rmse_kg_per_ha': metrics.get('rmse'),
                'weighted_r2': metrics.get('weighted_r2'),
                'weighted_mae': metrics.get('weighted_mae'),
                'baseline_mae': metrics.get('baseline_mae'),
                'mae_improvement_pct': metrics.get('mae_improvement_pct'),
            },
            'feature_importances': sorted_imp,
            'feature_importance': sorted_imp,
            'model_algorithm': model_record.algorithm,
            'limitations': cls.LIMITATIONS,
            'model_limitations': cls.LIMITATIONS,
            'disclaimer': MANDATORY_ML_DISCLAIMER,
            'mandatory_disclaimer': MANDATORY_ML_DISCLAIMER,
        }
