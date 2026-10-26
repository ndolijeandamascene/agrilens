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
            p10_kg = max(50.0, round(baseline_yield_kg * 0.75, 1))
            p90_kg = round(baseline_yield_kg * 1.25, 1)
            conf_interval = {
                'lower_p10_kg_per_ha': p10_kg,
                'lower_p10_tha': round(p10_kg / 1000.0, 2),
                'median_p50_kg_per_ha': baseline_yield_kg,
                'median_p50_tha': round(baseline_yield_kg / 1000.0, 2),
                'upper_p90_kg_per_ha': p90_kg,
                'upper_p90_tha': round(p90_kg / 1000.0, 2),
                'downside_risk_tha': round((baseline_yield_kg - p10_kg) / 1000.0, 2),
                'upside_potential_tha': round((p90_kg - baseline_yield_kg) / 1000.0, 2),
                'risk_classification': 'BASELINE_ESTIMATION',
            }
            attributions = []
            applied_taxonomy = 'BASELINE'
            model_info = {
                'model_name': 'Empirical Survey Baseline (Model Pending Retraining)',
                'version': 'baseline-v0',
                'algorithm': 'Survey-Weighted Ratio Aggregator',
                'is_ml_active': False,
                'r2_score': None,
                'mae_kg_per_ha': None,
                'has_quantiles': False,
                'crop_submodel_applied': 'BASELINE',
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
                if hasattr(pipeline, 'predict_with_uncertainty'):
                    unc_dict = pipeline.predict_with_uncertainty(input_df)
                    pred_yield_kg = unc_dict['point_prediction_kg_ha']
                    conf_interval = {
                        'lower_p10_kg_per_ha': unc_dict['p10_lower_kg_ha'],
                        'lower_p10_tha': unc_dict['p10_lower_tha'],
                        'median_p50_kg_per_ha': unc_dict['p50_median_kg_ha'],
                        'median_p50_tha': unc_dict['p50_median_tha'],
                        'upper_p90_kg_per_ha': unc_dict['p90_upper_kg_ha'],
                        'upper_p90_tha': unc_dict['p90_upper_tha'],
                        'downside_risk_tha': unc_dict['downside_risk_tha'],
                        'upside_potential_tha': unc_dict['upside_potential_tha'],
                        'risk_classification': (
                            'LOW_DOWNSIDE_VARIANCE' if unc_dict['downside_risk_tha'] < 0.6
                            else ('HIGH_DOWNSIDE_VARIANCE' if unc_dict['downside_risk_tha'] > 1.2 else 'MODERATE_DOWNSIDE_VARIANCE')
                        ),
                    }
                    attributions = pipeline.compute_local_attributions(input_df)
                    applied_taxonomy = unc_dict.get('crop_taxonomy_applied', 'GLOBAL')
                else:
                    raw_pred = float(pipeline.predict(input_df)[0])
                    pred_yield_kg = max(50.0, round(raw_pred, 1))
                    p10_kg = max(50.0, round(pred_yield_kg * 0.78, 1))
                    p90_kg = round(pred_yield_kg * 1.22, 1)
                    conf_interval = {
                        'lower_p10_kg_per_ha': p10_kg,
                        'lower_p10_tha': round(p10_kg / 1000.0, 2),
                        'median_p50_kg_per_ha': pred_yield_kg,
                        'median_p50_tha': round(pred_yield_kg / 1000.0, 2),
                        'upper_p90_kg_per_ha': p90_kg,
                        'upper_p90_tha': round(p90_kg / 1000.0, 2),
                        'downside_risk_tha': round((pred_yield_kg - p10_kg) / 1000.0, 2),
                        'upside_potential_tha': round((p90_kg - pred_yield_kg) / 1000.0, 2),
                        'risk_classification': 'MODERATE_DOWNSIDE_VARIANCE',
                    }
                    attributions = []
                    applied_taxonomy = 'GLOBAL'

                metrics = model_record.metrics or {}
                model_info = {
                    'model_name': model_record.name,
                    'version': model_record.version,
                    'algorithm': model_record.algorithm,
                    'is_ml_active': True,
                    'r2_score': metrics.get('r2'),
                    'mae_kg_per_ha': metrics.get('mae'),
                    'coverage_80_pct': metrics.get('coverage_80_pct'),
                    'crop_submodel_applied': applied_taxonomy,
                    'training_provenance': model_record.training_provenance,
                    'observation_count': model_record.observation_count,
                    'validation_methodology': model_record.validation_methodology,
                }
            except Exception as exc:
                logger.error("Inference pipeline error: %s", exc)
                pred_yield_kg = baseline_yield_kg
                p10_kg = max(50.0, round(baseline_yield_kg * 0.75, 1))
                p90_kg = round(baseline_yield_kg * 1.25, 1)
                conf_interval = {
                    'lower_p10_kg_per_ha': p10_kg,
                    'lower_p10_tha': round(p10_kg / 1000.0, 2),
                    'median_p50_kg_per_ha': baseline_yield_kg,
                    'median_p50_tha': round(baseline_yield_kg / 1000.0, 2),
                    'upper_p90_kg_per_ha': p90_kg,
                    'upper_p90_tha': round(p90_kg / 1000.0, 2),
                    'downside_risk_tha': round((baseline_yield_kg - p10_kg) / 1000.0, 2),
                    'upside_potential_tha': round((p90_kg - baseline_yield_kg) / 1000.0, 2),
                    'risk_classification': 'FALLBACK_ESTIMATION',
                }
                attributions = []
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
            'confidence_interval_80': conf_interval,
            'local_attributions': attributions,
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
