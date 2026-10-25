"""
Tests for AgriLens Machine Learning Prediction & Analytics REST APIs
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestMLPredictionAPIs:
    def test_predict_yield_valid_input(self, api_client):
        payload = {
            "crop": "Maize",
            "district": "Musanze",
            "plot_area_ha": 0.5,
            "is_improved_seed": True,
            "uses_inorganic_fertilizer": True,
            "uses_organic_fertilizer": True,
            "uses_pesticide": False,
            "is_irrigated": False,
            "has_anti_erosion": False,
            "uses_mechanization": False
        }

        response = api_client.post('/api/v1/ml/predict-yield/', data=payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'predicted_yield_kg_per_ha' in data
        assert 'predicted_yield_tha' in data
        assert 'predicted_production_tonnes' in data
        assert 'baseline_comparison' in data
        assert 'disclaimer' in data
        assert data['predicted_yield_kg_per_ha'] > 0
        assert data['predicted_yield_tha'] > 0
        assert "not official NISR statistics" in data['disclaimer']

    def test_predict_yield_invalid_input(self, api_client):
        # Negative plot area and missing crop
        payload = {
            "plot_area_ha": -1.5,
            "district": "Musanze"
        }

        response = api_client.post('/api/v1/ml/predict-yield/', data=payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_simulate_scenario_comparison(self, api_client):
        payload = {
            "crop": "Maize",
            "district": "Musanze",
            "plot_area_ha": 1.0,
            "current_practices": {
                "is_improved_seed": False,
                "uses_inorganic_fertilizer": False,
                "uses_organic_fertilizer": True,
                "uses_pesticide": False,
                "is_irrigated": False,
                "has_anti_erosion": False,
                "uses_mechanization": False
            },
            "recommended_practices": {
                "is_improved_seed": True,
                "uses_inorganic_fertilizer": True,
                "uses_organic_fertilizer": True,
                "uses_pesticide": True,
                "is_irrigated": False,
                "has_anti_erosion": False,
                "uses_mechanization": False
            }
        }

        response = api_client.post('/api/v1/ml/simulate-scenario/', data=payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'current_scenario' in data
        assert 'recommended_scenario' in data
        assert 'comparison' in data
        assert 'yield_uplift_tha' in data['comparison']
        assert 'additional_production_tonnes' in data['comparison']

    def test_district_clusters_endpoint(self, api_client):
        response = api_client.get('/api/v1/ml/district-clusters/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'clusters' in data
        assert len(data['clusters']) >= 30  # All 30 Rwanda districts

        first = data['clusters'][0]
        assert 'district_name' in first
        assert 'cluster_name' in first
        assert 'profile_summary' in first
        assert 'style' in first
        assert 'fillColor' in first['style']

    def test_seasonal_production_forecast_endpoint(self, api_client):
        response = api_client.get('/api/v1/ml/forecast/?crop=Maize')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['crop'] == 'Maize'
        assert 'historical_series' in data
        assert 'projected_production_tonnes' in data
        assert 'early_warning' in data
        assert 'level' in data['early_warning']
        assert 'disclaimer' in data

    def test_market_price_forecast_endpoint(self, api_client):
        response = api_client.get('/api/v1/ml/price-forecast/?crop=Maize')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'status' in data
        # Demonstrates honest handling of insufficient time-series data
        assert data['status'] == 'INSUFFICIENT_TIME_SERIES'
        assert 'explanatory_note' in data
        assert 'regional_price_spreads' in data
        assert 'disclaimer' in data

    def test_models_metadata_endpoint(self, api_client):
        response = api_client.get('/api/v1/ml/models/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'models' in data
        assert len(data['models']) >= 1
        m = data['models'][0]
        assert 'name' in m
        assert 'algorithm' in m
        assert 'version' in m
        assert 'metrics' in m

    def test_explainability_endpoint(self, api_client):
        response = api_client.get('/api/v1/ml/explainability/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'feature_importance' in data
        assert len(data['feature_importance']) > 0
        assert 'model_algorithm' in data
        assert 'model_limitations' in data
        assert 'mandatory_disclaimer' in data
