"""
AgriLens ML Productivity & What-If Scenario Comparison Service.
Compares baseline/current agricultural practice scenarios against recommended
management practices using trained machine learning models.
"""
from typing import Dict, Any
from apps.markets.models import CommodityPrice
from .inference import YieldInferenceService


class MLProductivityService:
    """Provides comparative What-If scenarios between current and modern farming practices."""

    @classmethod
    def compare_scenarios(
        cls,
        district: str,
        crop: str,
        plot_area_ha: float,
        current_practices: Dict[str, Any],
        recommended_practices: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs dual inference for current vs alternative scenarios and estimates
        production uplift and indicative economic returns.
        """
        current_params = {
            'district': district,
            'crop': crop,
            'plot_area_ha': plot_area_ha,
            **current_practices,
        }
        recommended_params = {
            'district': district,
            'crop': crop,
            'plot_area_ha': plot_area_ha,
            **recommended_practices,
        }

        current_res = YieldInferenceService.predict(current_params)
        recommended_res = YieldInferenceService.predict(recommended_params)

        curr_yield = current_res['predicted_yield_kg_per_ha']
        rec_yield = recommended_res['predicted_yield_kg_per_ha']
        curr_prod = current_res['predicted_production_kg']
        rec_prod = recommended_res['predicted_production_kg']

        uplift_kg_ha = round(rec_yield - curr_yield, 1)
        uplift_pct = round(((rec_yield - curr_yield) / curr_yield) * 100.0, 1) if curr_yield > 0 else 0.0
        additional_prod_kg = round(rec_prod - curr_prod, 1)
        additional_prod_tonnes = round(additional_prod_kg / 1000.0, 2)

        # Prevailing commodity price lookup
        price_quote = CommodityPrice.objects.filter(
            crop__name__icontains=crop,
            status=CommodityPrice.Status.PUBLISHED
        ).order_by('-date_recorded').first()

        unit_price_rwf = float(price_quote.price_per_kg_rwf) if price_quote else 400.0
        indicative_revenue_gain_rwf = round(additional_prod_kg * unit_price_rwf, 0)

        return {
            'crop': crop,
            'district': district,
            'plot_area_ha': plot_area_ha,
            'unit_price_rwf': unit_price_rwf,
            'current_scenario': current_res,
            'recommended_scenario': recommended_res,
            'comparison': {
                'yield_uplift_kg_per_ha': uplift_kg_ha,
                'yield_uplift_tha': round(uplift_kg_ha / 1000.0, 2),
                'yield_uplift_percentage': uplift_pct,
                'additional_production_kg': additional_prod_kg,
                'additional_production_tonnes': additional_prod_tonnes,
                'indicative_revenue_gain_rwf': indicative_revenue_gain_rwf,
            },
            'model_info': recommended_res.get('model_info', {}),
            'disclaimer': current_res.get('disclaimer', ''),
        }
