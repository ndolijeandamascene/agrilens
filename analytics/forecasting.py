"""
Harvest and Production Forecasting:
- Seasonal crop production estimates using early-season survey samples, historical area trends,
  and input adoption models.
"""
from typing import Dict, Any, Optional
from apps.ml.services.forecasting import (
    ProductionForecastingService,
    MarketPriceForecastingService,
)


def forecast_seasonal_harvest(
    crop: str = 'Maize',
    season: str = '2026A',
    province: Optional[str] = None,
    district: Optional[str] = None
) -> Dict[str, Any]:
    """Forecast expected seasonal harvest in Metric Tons and food supply early-warning alerts."""
    return ProductionForecastingService.get_forecast(
        crop_name=crop,
        forecast_season=season,
        province_name=province,
        district_name=district
    )


def analyze_market_price_trends(crop: str = 'Maize') -> Dict[str, Any]:
    """Analyzes commodity prices across surveillance markets and verifies time-series forecast eligibility."""
    return MarketPriceForecastingService.get_market_analysis(crop_name=crop)
