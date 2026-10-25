"""
Automated Report Generation:
- Executive briefs for policy makers
- Seasonal performance bulletins integrating descriptive indicators and ML projections
"""
from typing import Dict, Any
from apps.indicators.services import IndicatorService
from apps.ml.services.forecasting import ProductionForecastingService
from apps.ml.services.spatial import DistrictTypologyService


def generate_seasonal_bulletin(season: str = '2025A', crop: str = 'Maize') -> Dict[str, Any]:
    """Compile key findings, indicators, ML forecasts, and policy recommendations into a digest."""
    nat_summary = IndicatorService.get_national_summary(crop_name=crop)
    forecast = ProductionForecastingService.get_forecast(crop_name=crop, forecast_season='2026A')
    typologies = DistrictTypologyService.get_all_district_typologies()

    return {
        'season': season,
        'crop': crop,
        'national_summary': nat_summary,
        'forecast': forecast,
        'typology_count': len(typologies),
    }
