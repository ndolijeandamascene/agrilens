"""
AgriLens Crop Yield Inference Service.
Processes incoming farm scenarios, runs the active trained model pipeline,
and computes baseline comparisons with non-causal disclosures.
"""
import time
import logging
from decimal import Decimal
from typing import Dict, Any
import pandas as pd
import numpy as np

from apps.ml.models import MLModel, PredictionLog
from apps.indicators.services import IndicatorService
from .registry import ModelRegistry

logger = logging.getLogger(__name__)

MANDATORY_ML_DISCLAIMER = (
    "These results are statistical model predictions based on historical agricultural survey data. "
    "They are not official NISR statistics and do not guarantee actual farm outcomes. "
    "Predicted differences are associations and should not be interpreted as guaranteed causal effects."
)


class YieldInferenceService:
    """Provides farm-level yield predictions and what-if simulation results."""

    @classmethod
    def predict(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes prediction with comprehensive validation, baseline benchmarking,
        and safe fallback if model artifact is unavailable.
        """
        start_time = time.time()

        crop_name = str(params.get('crop', 'Maize')).strip()
        district_name = str(params.get('district', 'Musanze')).strip()
        
        try:
            plot_area = float(params.get('plot_area_ha', 0.5))
            if plot_area <= 0:
                plot_area = 0.5
        except (ValueError, TypeError):
            plot_area = 0.5

        seed = 1 if params.get('is_improved_seed') in (True, 'true', '1', 1) else 0
        inorg = 1 if params.get('uses_inorganic_fertilizer') in (True, 'true', '1', 1) else 0
        org = 1 if params.get('uses_organic_fertilizer') in (True, 'true', '1', 1) else 0
        pest = 1 if params.get('uses_pesticide') in (True, 'true', '1', 1) else 0
        irrig = 1 if params.get('is_irrigated') in (True, 'true', '1', 1) else 0
        anti = 1 if params.get('has_anti_erosion') in (True, 'true', '1', 1) else 0
        mech = 1 if params.get('uses_mechanization') in (True, 'true', '1', 1) else 0

        model_record, pipeline = ModelRegistry.get_active_pipeline(MLModel.ModelType.YIELD_PREDICTION)

        # Baseline lookup from historical statistical aggregates
        baseline_yield_kg = cls._get_baseline_yield(crop_name, district_name)

        if not pipeline or not model_record:
            # Safe Fallback: Informative estimation using survey-weighted benchmarks
            logger.info("Active yield ML model not loaded; using empirical statistical baseline.")
            pred_yield_kg = baseline_yield_kg
            model_info = {
                'model_name': 'Empirical Survey Baseline (Model Pending Retraining)',
                'version': 'baseline-v0',
                'algorithm': 'Survey-Weighted Ratio Aggregator',
                'is_ml_active': False,
                'r2_score': None,
                'mae_kg_per_ha': None,
            }
        else:
            # Resolve district province if present in model features
            from apps.geography.models import District
            dist_obj = District.objects.filter(name__iexact=district_name).select_related('province').first()
            province_name = dist_obj.province.name if dist_obj and dist_obj.province else 'Northern'

            # Prepare feature DataFrame matching exact training feature schema
            input_df = pd.DataFrame([{
                'crop': crop_name,
                'district': district_name,
                'province': province_name,
                'plot_area_ha': plot_area,
                'is_improved_seed': seed,
                'uses_inorganic_fertilizer': inorg,
                'uses_organic_fertilizer': org,
                'uses_pesticide': pest,
                'is_irrigated': irrig,
                'has_anti_erosion': anti,
                'uses_mechanization': mech,
            }])

            try:
                raw_pred = float(pipeline.predict(input_df)[0])
                # Ensure plausible bounds (> 0)
                pred_yield_kg = max(50.0, round(raw_pred, 1))
                metrics = model_record.metrics or {}
                model_info = {
                    'model_name': model_record.name,
                    'version': model_record.version,
                    'algorithm': model_record.algorithm,
                    'is_ml_active': True,
                    'r2_score': metrics.get('r2'),
                    'mae_kg_per_ha': metrics.get('mae'),
                    'training_provenance': model_record.training_provenance,
                    'observation_count': model_record.observation_count,
                    'validation_methodology': model_record.validation_methodology,
                }
            except Exception as exc:
                logger.error("Inference pipeline error: %s", exc)
                pred_yield_kg = baseline_yield_kg
                model_info = {
                    'model_name': 'Fallback Baseline',
                    'version': 'fallback',
                    'algorithm': 'Empirical Baseline',
                    'is_ml_active': False,
                    'r2_score': None,
                    'mae_kg_per_ha': None,
                }

        # Calculations & Uplift
        pred_yield_tha = round(pred_yield_kg / 1000.0, 2)
        pred_production_kg = round(pred_yield_kg * plot_area, 1)
        pred_production_tonnes = round(pred_production_kg / 1000.0, 2)

        baseline_yield_tha = round(baseline_yield_kg / 1000.0, 2)
        baseline_prod_tonnes = round((baseline_yield_kg * plot_area) / 1000.0, 2)
        diff_kg = round(pred_yield_kg - baseline_yield_kg, 1)
        diff_pct = round(((pred_yield_kg - baseline_yield_kg) / baseline_yield_kg) * 100.0, 1) if baseline_yield_kg > 0 else 0.0

        latency_ms = round((time.time() - start_time) * 1000.0, 2)

        result = {
            'crop': crop_name,
            'district': district_name,
            'plot_area_ha': plot_area,
            'practices': {
                'is_improved_seed': bool(seed),
                'uses_inorganic_fertilizer': bool(inorg),
                'uses_organic_fertilizer': bool(org),
                'uses_pesticide': bool(pest),
                'is_irrigated': bool(irrig),
                'has_anti_erosion': bool(anti),
                'uses_mechanization': bool(mech),
            },
            'predicted_yield_kg_per_ha': pred_yield_kg,
            'predicted_yield_tha': pred_yield_tha,
            'predicted_production_kg': pred_production_kg,
            'predicted_production_tonnes': pred_production_tonnes,
            'baseline_yield_kg_per_ha': baseline_yield_kg,
            'baseline_yield_tha': baseline_yield_tha,
            'baseline_production_tonnes': baseline_prod_tonnes,
            'yield_difference_kg_per_ha': diff_kg,
            'yield_difference_percentage': diff_pct,
            'baseline_comparison': {
                'baseline_yield_kg_per_ha': baseline_yield_kg,
                'baseline_yield_tha': baseline_yield_tha,
                'baseline_production_tonnes': baseline_prod_tonnes,
                'yield_difference_kg_per_ha': diff_kg,
                'yield_difference_percentage': diff_pct,
            },
            'model_info': model_info,
            'disclaimer': MANDATORY_ML_DISCLAIMER,
            'latency_ms': latency_ms,
        }

        # Log prediction asynchronously / non-blocking
        try:
            PredictionLog.objects.create(
                model_type=MLModel.ModelType.YIELD_PREDICTION,
                input_payload=params,
                output_payload={
                    'predicted_yield_kg_per_ha': pred_yield_kg,
                    'diff_pct': diff_pct,
                    'latency_ms': latency_ms,
                },
                latency_ms=latency_ms
            )
        except Exception:
            pass

        return result

    @classmethod
    def _get_baseline_yield(cls, crop_name: str, district_name: str) -> float:
        """Returns empirical survey-weighted baseline yield for the crop and district."""
        try:
            rankings = IndicatorService.get_district_rankings(
                crop_name=crop_name, district_name=district_name, min_plots=1
            )
            if rankings and len(rankings) > 0 and rankings[0].get('yield_kg_per_ha', 0) > 0:
                return float(rankings[0]['yield_kg_per_ha'])

            # National fallback
            summary = IndicatorService.get_national_summary(crop_name=crop_name)
            nat_yield = float(summary.get('weighted_yield_kg_per_ha', 0.0))
            if nat_yield > 0:
                return nat_yield
        except Exception:
            pass

        # Standard agronomic reference fallback
        return {
            'Maize': 2800.0,
            'Bush Beans': 1400.0,
            'Cassava': 12500.0,
            'Irish Potato': 14000.0,
            'Marshland Rice': 4200.0,
            'Cooking Banana': 8500.0,
        }.get(crop_name, 2000.0)
