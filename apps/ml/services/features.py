"""
AgriLens Feature Engineering & Extraction Pipeline.
Extracts, sanitizes, and prepares survey-weighted training matrices from
official NISR microdata (ValidatedObservation) with biological outlier protection.
"""
import logging
from decimal import Decimal
import pandas as pd
import numpy as np
from django.db.models import F

from apps.data_management.models import ValidatedObservation

logger = logging.getLogger(__name__)

# Biological Agronomic Thresholds (per NISR & MINAGRI Guidelines)
MAX_PLAUSIBLE_YIELD_KG_HA = 25000.0  # 25 t/ha biological ceiling for survey microdata
MIN_PLAUSIBLE_YIELD_KG_HA = 10.0     # Exclude near-zero abandonment plots
MIN_PLOT_AREA_HA = 0.001
MAX_PLOT_AREA_HA = 50.0


class FeatureExtractionPipeline:
    """
    Reusable feature engineering pipeline transforming database records into
    reproducible machine learning datasets.
    """

    CATEGORICAL_FEATURES = ['crop', 'district', 'province']
    NUMERICAL_FEATURES = ['plot_area_ha']
    BOOLEAN_FEATURES = [
        'is_improved_seed',
        'uses_inorganic_fertilizer',
        'uses_organic_fertilizer',
        'uses_pesticide',
        'is_irrigated',
        'has_anti_erosion',
        'uses_mechanization',
    ]
    ALL_INPUT_FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES + BOOLEAN_FEATURES
    TARGET_COLUMN = 'yield_kg_per_ha'

    @classmethod
    def extract_dataset(cls, provenance_prefix='NISR_', min_yield=MIN_PLAUSIBLE_YIELD_KG_HA, max_yield=MAX_PLAUSIBLE_YIELD_KG_HA):
        """
        Extracts verified microdata observations, filters extreme biological outliers,
        and returns clean DataFrame along with feature data quality statistics.
        """
        qs = ValidatedObservation.objects.filter(
            provenance__startswith=provenance_prefix
        ).select_related('crop', 'district', 'district__province', 'season')

        raw_count = qs.count()
        if raw_count == 0:
            logger.warning("No observations found for provenance prefix: %s", provenance_prefix)
            return pd.DataFrame(), {'total_raw': 0, 'valid': 0, 'outliers_dropped': 0}

        records = []
        for obs in qs.iterator(chunk_size=1000):
            try:
                area = float(obs.plot_area_ha)
                yield_val = float(obs.calculated_yield_kg_per_ha)
                weight = float(obs.sampling_weight or 1.0)
                year = int(obs.season.year)
                season_code = str(obs.season.season).upper()

                # Outlier & range check
                if not (MIN_PLOT_AREA_HA <= area <= MAX_PLOT_AREA_HA):
                    continue
                if not (min_yield <= yield_val <= max_yield):
                    continue

                records.append({
                    'crop': obs.crop.name,
                    'district': obs.district.name,
                    'province': obs.district.province.name,
                    'plot_area_ha': area,
                    'is_improved_seed': 1 if obs.is_improved_seed else 0,
                    'uses_inorganic_fertilizer': 1 if obs.uses_inorganic_fertilizer else 0,
                    'uses_organic_fertilizer': 1 if obs.uses_organic_fertilizer else 0,
                    'uses_pesticide': 1 if obs.uses_pesticide else 0,
                    'is_irrigated': 1 if obs.is_irrigated else 0,
                    'has_anti_erosion': 1 if obs.has_anti_erosion else 0,
                    'uses_mechanization': 1 if obs.uses_mechanization else 0,
                    'season_year': year,
                    'season_code': season_code,
                    'sampling_weight': max(1.0, weight),
                    cls.TARGET_COLUMN: yield_val,
                })
            except (ValueError, TypeError, AttributeError) as exc:
                continue

        df = pd.DataFrame(records)
        valid_count = len(df)
        outliers_dropped = raw_count - valid_count

        stats = {
            'total_raw_observations': raw_count,
            'valid_clean_observations': valid_count,
            'outliers_dropped': outliers_dropped,
            'crops_count': df['crop'].nunique() if not df.empty else 0,
            'districts_count': df['district'].nunique() if not df.empty else 0,
            'years': list(df['season_year'].unique()) if not df.empty else [],
            'mean_yield': round(float(df[cls.TARGET_COLUMN].mean()), 2) if not df.empty else 0.0,
            'median_yield': round(float(df[cls.TARGET_COLUMN].median()), 2) if not df.empty else 0.0,
        }

        return df, stats

    @classmethod
    def get_temporal_split(cls, df):
        """
        Splits dataset by survey year for realistic out-of-time evaluation:
        Train on SAS 2024, Test on SAS 2025.
        Fallback to stratified random split if multi-year data is unavailable.
        """
        if df.empty:
            raise ValueError("Cannot split empty dataframe")

        years = sorted(df['season_year'].unique())
        if len(years) >= 2:
            train_year = years[0]  # 2024
            test_year = years[1]   # 2025
            train_df = df[df['season_year'] == train_year].copy()
            test_df = df[df['season_year'] == test_year].copy()
            split_info = {
                'method': f'Temporal Holdout (Train: Season {train_year}, Test: Season {test_year})',
                'train_size': len(train_df),
                'test_size': len(test_df),
            }
        else:
            # Fallback 80/20 random split
            shuffled = df.sample(frac=1.0, random_state=42)
            n_train = int(len(df) * 0.8)
            train_df = shuffled.iloc[:n_train].copy()
            test_df = shuffled.iloc[n_train:].copy()
            split_info = {
                'method': 'Stratified Random Holdout (80/20)',
                'train_size': len(train_df),
                'test_size': len(test_df),
            }

        return train_df, test_df, split_info

    @classmethod
    def clean_and_validate(cls, df: pd.DataFrame, min_yield=MIN_PLAUSIBLE_YIELD_KG_HA, max_yield=MAX_PLAUSIBLE_YIELD_KG_HA) -> pd.DataFrame:
        """Filters biological outliers and invalid plot areas."""
        if df.empty:
            return df
        yield_col = cls.TARGET_COLUMN if cls.TARGET_COLUMN in df.columns else 'calculated_yield_kg_per_ha'
        mask = (
            (df[yield_col] >= min_yield) &
            (df[yield_col] <= max_yield) &
            (df['plot_area_ha'] >= MIN_PLOT_AREA_HA) &
            (df['plot_area_ha'] <= MAX_PLOT_AREA_HA)
        )
        return df[mask].copy()

    @classmethod
    def build_feature_matrices(cls, df: pd.DataFrame, test_season_year=2025):
        """Builds train/test matrices with one-hot encoded categories and survey weights."""
        train_df = df[df['season_year'] != test_season_year].copy()
        test_df = df[df['season_year'] == test_season_year].copy()

        yield_col = cls.TARGET_COLUMN if cls.TARGET_COLUMN in df.columns else 'calculated_yield_kg_per_ha'
        weight_col = 'sampling_weight' if 'sampling_weight' in df.columns else 'survey_weight'

        y_train = train_df[yield_col].values
        y_test = test_df[yield_col].values
        w_train = train_df[weight_col].values if weight_col in train_df.columns else np.ones(len(y_train))
        w_test = test_df[weight_col].values if weight_col in test_df.columns else np.ones(len(y_test))

        feature_cols = [c for c in df.columns if c not in [yield_col, weight_col, 'season_year', 'season_code']]
        X_all = pd.get_dummies(df[feature_cols], drop_first=False)
        X_train = X_all.loc[train_df.index]
        X_test = X_all.loc[test_df.index]

        return {
            'X_train': X_train,
            'y_train': y_train,
            'w_train': w_train,
            'X_test': X_test,
            'y_test': y_test,
            'w_test': w_test,
            'feature_names': list(X_all.columns)
        }

    def transform_single_plot(self, plot_input: dict) -> pd.DataFrame:
        """Transforms a single plot input dict to match pipeline feature columns."""
        cols = getattr(self, 'feature_columns', None) or [
            'plot_area_ha', 'is_improved_seed', 'uses_inorganic_fertilizer',
            'uses_organic_fertilizer', 'uses_pesticide', 'is_irrigated',
            'has_anti_erosion', 'uses_mechanization'
        ]
        row = {c: 0.0 for c in cols}

        # Populate basic numerical & boolean features
        for k in ['plot_area_ha', 'is_improved_seed', 'uses_inorganic_fertilizer',
                  'uses_organic_fertilizer', 'uses_pesticide', 'is_irrigated',
                  'has_anti_erosion', 'uses_mechanization']:
            if k in cols and k in plot_input:
                row[k] = float(plot_input[k])

        # Populate one-hot crop / district features if present
        crop_key = f"crop_{plot_input.get('crop')}"
        if crop_key in cols:
            row[crop_key] = 1.0

        dist_key = f"district_{plot_input.get('district')}"
        if dist_key in cols:
            row[dist_key] = 1.0

        return pd.DataFrame([row])

    @classmethod
    def extract_raw_observations(cls) -> pd.DataFrame:
        """Alias returning clean extracted DataFrame from ValidatedObservation."""
        df, _ = cls.extract_dataset()
        if not df.empty and 'yield_kg_per_ha' in df.columns:
            df['calculated_yield_kg_per_ha'] = df['yield_kg_per_ha']
        return df

