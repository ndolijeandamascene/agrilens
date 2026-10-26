"""
AgriLens Machine Learning URL Configuration.
Exposes endpoints for crop yield prediction, district typology clustering,
seasonal harvest forecasting, and model explainability.
"""
from django.urls import path
from . import views

app_name = 'ml'

urlpatterns = [
    # Prediction & What-If Simulation
    path('predict-yield/', views.PredictYieldAPIView.as_view(), name='predict_yield'),
    path('simulate-scenario/', views.SimulateScenarioAPIView.as_view(), name='simulate_scenario'),

    # Spatial District Clustering & Vulnerability Index
    path('district-clusters/', views.DistrictClustersAPIView.as_view(), name='district_clusters'),
    path('vulnerability/', views.DistrictVulnerabilityAPIView.as_view(), name='district_vulnerability'),

    # Seasonal Forecasting
    path('forecast/', views.ProductionForecastAPIView.as_view(), name='production_forecast'),
    path('price-forecast/', views.MarketPriceForecastAPIView.as_view(), name='price_forecast'),

    # Model Registry & Transparency
    path('models/', views.ModelListAPIView.as_view(), name='model_list'),
    path('explainability/', views.ModelExplainabilityAPIView.as_view(), name='explainability'),

    # Training Management (Staff Protected)
    path('train/', views.TrainModelsAPIView.as_view(), name='train_models'),
]
