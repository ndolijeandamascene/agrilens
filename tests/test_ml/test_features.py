"""
Tests for ML Feature Engineering and Extraction Pipeline
"""
import pytest
import pandas as pd
import numpy as np
from apps.ml.services.features import FeatureExtractionPipeline


@pytest.mark.django_db
class TestFeatureExtractionPipeline:
    def test_extract_raw_observations(self):
        pipeline = FeatureExtractionPipeline()
        df = pipeline.extract_raw_observations()

        assert isinstance(df, pd.DataFrame)
        if not df.empty:
            assert 'calculated_yield_kg_per_ha' in df.columns
            assert 'plot_area_ha' in df.columns
            assert 'crop' in df.columns
            assert 'district' in df.columns
            assert 'season_year' in df.columns

    def test_clean_and_validate_bounds(self):
        pipeline = FeatureExtractionPipeline()
        raw_data = pd.DataFrame([
            {'crop': 'Maize', 'district': 'Musanze', 'season_year': 2024, 'season_code': 'A',
             'plot_area_ha': 0.5, 'calculated_yield_kg_per_ha': 5.0, 'survey_weight': 10.0,
             'is_improved_seed': True, 'uses_inorganic_fertilizer': True, 'uses_organic_fertilizer': True,
             'uses_pesticide': False, 'is_irrigated': False, 'has_anti_erosion': False, 'uses_mechanization': False},
            {'crop': 'Maize', 'district': 'Musanze', 'season_year': 2024, 'season_code': 'A',
             'plot_area_ha': 0.5, 'calculated_yield_kg_per_ha': 35000.0, 'survey_weight': 10.0,
             'is_improved_seed': True, 'uses_inorganic_fertilizer': True, 'uses_organic_fertilizer': True,
             'uses_pesticide': False, 'is_irrigated': False, 'has_anti_erosion': False, 'uses_mechanization': False},
            {'crop': 'Maize', 'district': 'Musanze', 'season_year': 2024, 'season_code': 'A',
             'plot_area_ha': 0.5, 'calculated_yield_kg_per_ha': 3200.0, 'survey_weight': 10.0,
             'is_improved_seed': True, 'uses_inorganic_fertilizer': True, 'uses_organic_fertilizer': True,
             'uses_pesticide': False, 'is_irrigated': False, 'has_anti_erosion': False, 'uses_mechanization': False},
        ])

        cleaned = pipeline.clean_and_validate(raw_data)
        # 5.0 is below min_yield (10 kg/ha), 35000 is above max_yield (25000 kg/ha)
        assert len(cleaned) == 1
        assert cleaned.iloc[0]['calculated_yield_kg_per_ha'] == 3200.0

    def test_build_feature_matrices_temporal_split(self):
        pipeline = FeatureExtractionPipeline()
        sample_data = pd.DataFrame([
            {'crop': 'Maize', 'district': 'Musanze', 'season_year': 2024, 'season_code': 'A',
             'plot_area_ha': 0.4, 'calculated_yield_kg_per_ha': 3100.0, 'survey_weight': 10.0,
             'is_improved_seed': True, 'uses_inorganic_fertilizer': True, 'uses_organic_fertilizer': True,
             'uses_pesticide': False, 'is_irrigated': False, 'has_anti_erosion': False, 'uses_mechanization': False},
            {'crop': 'Beans', 'district': 'Nyagatare', 'season_year': 2024, 'season_code': 'A',
             'plot_area_ha': 0.6, 'calculated_yield_kg_per_ha': 1400.0, 'survey_weight': 12.0,
             'is_improved_seed': False, 'uses_inorganic_fertilizer': False, 'uses_organic_fertilizer': True,
             'uses_pesticide': False, 'is_irrigated': False, 'has_anti_erosion': False, 'uses_mechanization': False},
            {'crop': 'Maize', 'district': 'Musanze', 'season_year': 2025, 'season_code': 'A',
             'plot_area_ha': 0.5, 'calculated_yield_kg_per_ha': 3300.0, 'survey_weight': 11.0,
             'is_improved_seed': True, 'uses_inorganic_fertilizer': True, 'uses_organic_fertilizer': True,
             'uses_pesticide': True, 'is_irrigated': False, 'has_anti_erosion': False, 'uses_mechanization': False},
        ])

        matrices = pipeline.build_feature_matrices(sample_data, test_season_year=2025)
        assert len(matrices['y_train']) == 2  # 2024 rows
        assert len(matrices['y_test']) == 1   # 2025 rows
        assert 'calculated_yield_kg_per_ha' not in matrices['X_train'].columns
        assert 'survey_weight' not in matrices['X_train'].columns

    def test_transform_single_plot(self):
        pipeline = FeatureExtractionPipeline()
        # Mock feature names
        pipeline.feature_columns = [
            'plot_area_ha', 'is_improved_seed', 'uses_inorganic_fertilizer',
            'uses_organic_fertilizer', 'uses_pesticide', 'is_irrigated',
            'has_anti_erosion', 'uses_mechanization',
            'crop_Maize', 'district_Musanze'
        ]

        plot_input = {
            'crop': 'Maize',
            'district': 'Musanze',
            'plot_area_ha': 0.75,
            'is_improved_seed': True,
            'uses_inorganic_fertilizer': True,
            'uses_organic_fertilizer': False,
            'uses_pesticide': True,
            'is_irrigated': False,
            'has_anti_erosion': False,
            'uses_mechanization': False
        }

        X_vec = pipeline.transform_single_plot(plot_input)
        assert isinstance(X_vec, pd.DataFrame)
        assert X_vec.shape[0] == 1
        assert X_vec.shape[1] == len(pipeline.feature_columns)
        assert X_vec['plot_area_ha'].iloc[0] == 0.75
        assert X_vec['is_improved_seed'].iloc[0] == 1.0
        assert X_vec['crop_Maize'].iloc[0] == 1.0
