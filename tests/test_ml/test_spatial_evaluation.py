"""
Tests for Spatial Holdout Cross-Validation (LODO-CV) in ModelEvaluationService
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from apps.ml.services.evaluation import ModelEvaluationService


class TestSpatialEvaluation:
    def test_evaluate_spatial_holdout_synthetic(self):
        # Create synthetic spatial dataset with 4 districts
        np.random.seed(42)
        rows = []
        districts = ['Musanze', 'Nyagatare', 'Huye', 'Rubavu']
        for d in districts:
            for _ in range(30):
                area = np.random.uniform(0.2, 2.0)
                # Yield varies by district and area
                base = {'Musanze': 3500.0, 'Nyagatare': 2800.0, 'Huye': 2400.0, 'Rubavu': 3100.0}[d]
                yield_val = base + area * 200.0 + np.random.normal(0, 150)
                rows.append({
                    'district': d,
                    'plot_area_ha': area,
                    'sampling_weight': 1.0,
                    'yield': yield_val
                })
        df = pd.DataFrame(rows)

        def make_pipeline():
            return Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', Ridge())
            ])

        result = ModelEvaluationService.evaluate_spatial_holdout(
            pipeline_builder_fn=make_pipeline,
            df=df,
            feature_cols=['plot_area_ha'],
            target_col='yield',
            district_col='district',
            max_districts=4
        )

        assert result['total_districts_evaluated'] == 4
        assert result['mean_spatial_mae'] is not None
        assert result['mean_spatial_mae'] > 0
        assert len(result['district_breakdown']) == 4
        assert 'spatial_generalization_note' in result

    def test_evaluate_spatial_holdout_insufficient_samples(self):
        # Single district only -> cannot perform spatial holdout
        df = pd.DataFrame([
            {'district': 'Musanze', 'plot_area_ha': 0.5, 'yield': 2500.0}
        ])

        result = ModelEvaluationService.evaluate_spatial_holdout(
            pipeline_builder_fn=lambda: Ridge(),
            df=df,
            feature_cols=['plot_area_ha'],
            target_col='yield',
            district_col='district'
        )

        assert result['total_districts_evaluated'] == 0
        assert result['mean_spatial_mae'] is None
