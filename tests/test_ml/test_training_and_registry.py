"""
Tests for ML Model Training, Evaluation Metrics, and Model Registry Persistence
"""
import pytest
import os
import numpy as np
from sklearn.dummy import DummyRegressor
from apps.ml.models import MLModel, DistrictTypology
from apps.ml.services.evaluation import ModelEvaluationService
from apps.ml.services.registry import ModelRegistry


@pytest.mark.django_db
class TestModelEvaluationService:
    def test_evaluate_regression_metrics(self):
        y_true = np.array([2000.0, 3000.0, 4000.0, 5000.0])
        y_pred = np.array([2100.0, 2900.0, 4100.0, 4900.0])
        weights = np.array([1.0, 1.0, 1.0, 1.0])

        metrics = ModelEvaluationService.evaluate_regression(y_true, y_pred, weights)

        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics
        assert metrics['mae'] == 100.0
        assert metrics['rmse'] == 100.0
        assert metrics['r2'] > 0.95

    def test_evaluate_baseline_comparison(self):
        y_train = np.array([2000.0, 3000.0, 4000.0])
        y_test = np.array([2500.0, 3500.0])

        baseline = ModelEvaluationService.compute_baseline_metrics(y_train, y_test)
        assert 'baseline_mae' in baseline
        assert 'baseline_rmse' in baseline
        assert baseline['baseline_value'] == 3000.0


@pytest.mark.django_db
class TestModelRegistry:
    def test_save_and_load_artifact(self, tmp_path):
        registry = ModelRegistry()
        dummy_model = DummyRegressor(strategy='mean')
        dummy_model.fit([[1], [2], [3]], [10, 20, 30])

        artifact_name = "test_dummy_model.joblib"
        save_path = registry.save_model_artifact(dummy_model, artifact_name)

        assert os.path.exists(save_path)

        loaded_model = registry.load_model_artifact(artifact_name)
        assert loaded_model is not None
        assert loaded_model.predict([[1]])[0] == 20.0

    def test_register_model_metadata(self):
        registry = ModelRegistry()
        ml_model = registry.register_model(
            name="Test Yield Model",
            model_type=MLModel.ModelType.YIELD_PREDICTION,
            version="v0.1-test",
            algorithm="RandomForestRegressor",
            features=["plot_area_ha", "is_improved_seed"],
            target="calculated_yield_kg_per_ha",
            metrics={"mae": 150.0, "rmse": 200.0, "r2": 0.72},
            artifact_filename="test_yield.joblib",
            notes="Automated test model"
        )

        assert ml_model.id is not None
        assert ml_model.status == MLModel.Status.TRAINED
        assert ml_model.metrics['r2'] == 0.72

    def test_load_active_model_fallback(self):
        registry = ModelRegistry()
        # Non-existent model type fallback should not throw an uncaught crash
        model_obj, pipeline = registry.load_active_model(model_type="NON_EXISTENT_TYPE")
        assert model_obj is None or pipeline is None
