"""
Agricultural Productivity & Yield Gap Analytics.
Integrates empirical ratio estimators with ML scenario prediction.
"""
from typing import Dict, Any, Optional
from apps.ml.services.inference import YieldInferenceService
from apps.ml.services.productivity import MLProductivityService


def calculate_yield_gap(observed_yield: float, potential_yield: float) -> Dict[str, float]:
    """
    Return percentage yield deficit against agronomic benchmark:
    Absolute gap = max(0, potential - observed)
    Relative gap % = (potential - observed) / potential * 100
    """
    if potential_yield <= 0:
        return {'absolute_gap': 0.0, 'relative_gap_pct': 0.0}

    diff = potential_yield - observed_yield
    rel_pct = round((diff / potential_yield) * 100.0, 2)
    return {
        'observed_yield': float(observed_yield),
        'potential_yield': float(potential_yield),
        'absolute_gap': max(0.0, round(diff, 2)),
        'relative_gap_pct': rel_pct,
    }


def predict_farm_yield(farm_params: Dict[str, Any]) -> Dict[str, Any]:
    """Predicts yield using the active ML model pipeline."""
    return YieldInferenceService.predict(farm_params)


def compare_farming_scenarios(
    district: str,
    crop: str,
    plot_area_ha: float,
    current_practices: Dict[str, Any],
    recommended_practices: Dict[str, Any]
) -> Dict[str, Any]:
    """Simulates farm productivity uplift between current and modern farming scenarios."""
    return MLProductivityService.compare_scenarios(
        district, crop, plot_area_ha, current_practices, recommended_practices
    )
