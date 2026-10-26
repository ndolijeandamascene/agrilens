"""
AgriLens Model Evaluation Service.
Computes standard and survey-weighted regression metrics (MAE, RMSE, R²),
and benchmarks performance against empirical baselines.
"""
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


class ModelEvaluationService:
    """Provides standard, survey-weighted, and baseline comparative evaluation metrics."""

    @staticmethod
    def evaluate_regression(y_true, y_pred, sample_weight=None, y_train=None):
        """
        Computes regression metrics for predictions against true values.
        Also evaluates a baseline mean predictor for comparison.
        """
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        weights = np.asarray(sample_weight, dtype=float) if sample_weight is not None else None

        # Standard metrics
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))

        # Weighted metrics if sample weights are supplied
        weighted_mae = float(mean_absolute_error(y_true, y_pred, sample_weight=weights)) if weights is not None else mae
        weighted_rmse = float(np.sqrt(mean_squared_error(y_true, y_pred, sample_weight=weights))) if weights is not None else rmse
        weighted_r2 = float(r2_score(y_true, y_pred, sample_weight=weights)) if weights is not None else r2

        # Baseline: Naive prediction using mean of training set or test set
        baseline_pred_val = float(np.mean(y_train) if y_train is not None and len(y_train) > 0 else np.mean(y_true))
        baseline_preds = np.full_like(y_true, baseline_pred_val)
        baseline_mae = float(mean_absolute_error(y_true, baseline_preds))
        baseline_rmse = float(np.sqrt(mean_squared_error(y_true, baseline_preds)))
        baseline_r2 = float(r2_score(y_true, baseline_preds))

        mae_improvement_pct = round(((baseline_mae - mae) / baseline_mae) * 100.0, 2) if baseline_mae > 0 else 0.0

        return {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'r2': round(r2, 4),
            'weighted_mae': round(weighted_mae, 2),
            'weighted_rmse': round(weighted_rmse, 2),
            'weighted_r2': round(weighted_r2, 4),
            'baseline_mae': round(baseline_mae, 2),
            'baseline_rmse': round(baseline_rmse, 2),
            'baseline_r2': round(baseline_r2, 4),
            'mae_improvement_pct': mae_improvement_pct,
            'mean_actual_yield': round(float(np.mean(y_true)), 2),
            'mean_predicted_yield': round(float(np.mean(y_pred)), 2),
        }

    @staticmethod
    def compute_baseline_metrics(y_train, y_test):
        """Computes baseline metrics using mean target value on holdout set."""
        y_train = np.asarray(y_train, dtype=float)
        y_test = np.asarray(y_test, dtype=float)
        baseline_val = float(np.mean(y_train) if len(y_train) > 0 else np.mean(y_test))
        preds = np.full_like(y_test, baseline_val)
        return {
            'baseline_value': baseline_val,
            'baseline_mae': float(mean_absolute_error(y_test, preds)),
            'baseline_rmse': float(np.sqrt(mean_squared_error(y_test, preds))),
            'baseline_r2': float(r2_score(y_test, preds)),
        }

    @classmethod
    def evaluate_spatial_holdout(
        cls,
        pipeline_builder_fn,
        df,
        feature_cols: list,
        target_col: str,
        district_col: str = 'district',
        sample_weight_col: str = 'sampling_weight',
        max_districts: int = 10
    ):
        """
        Executes Leave-One-District-Out (LODO) Spatial Cross-Validation.
        Iteratively trains on N-1 districts and measures out-of-fold error on the held-out district.
        """
        districts = sorted(df[district_col].unique())
        if max_districts and len(districts) > max_districts:
            # Select top districts by sample count for computational efficiency
            top_districts = df[district_col].value_counts().index[:max_districts].tolist()
            eval_districts = sorted(top_districts)
        else:
            eval_districts = districts

        district_results = []
        spatial_maes = []
        spatial_rmses = []

        for target_dist in eval_districts:
            train_mask = df[district_col] != target_dist
            test_mask = df[district_col] == target_dist

            train_df = df[train_mask]
            test_df = df[test_mask]

            if len(test_df) < 5 or len(train_df) < 20:
                continue

            try:
                pipeline = pipeline_builder_fn()
                weights = train_df[sample_weight_col].values if sample_weight_col in train_df.columns else None

                if weights is not None:
                    pipeline.fit(train_df[feature_cols], train_df[target_col], regressor__sample_weight=weights)
                else:
                    pipeline.fit(train_df[feature_cols], train_df[target_col])

                preds = pipeline.predict(test_df[feature_cols])
                y_true = test_df[target_col].values

                d_mae = float(mean_absolute_error(y_true, preds))
                d_rmse = float(np.sqrt(mean_squared_error(y_true, preds)))
                spatial_maes.append(d_mae)
                spatial_rmses.append(d_rmse)

                district_results.append({
                    'district': str(target_dist),
                    'test_samples': int(len(test_df)),
                    'mae_kg_per_ha': round(d_mae, 1),
                    'rmse_kg_per_ha': round(d_rmse, 1),
                    'mean_actual_yield': round(float(np.mean(y_true)), 1),
                    'mean_predicted_yield': round(float(np.mean(preds)), 1),
                })
            except Exception:
                continue

        if not spatial_maes:
            return {
                'method': 'Leave-One-District-Out Spatial Cross-Validation (LODO-CV)',
                'total_districts_evaluated': 0,
                'mean_spatial_mae': None,
                'spatial_generalization_note': 'Insufficient district sample splits for spatial holdout.',
            }

        mean_mae = float(np.mean(spatial_maes))
        std_mae = float(np.std(spatial_maes))

        # Best and worst generalizing districts
        sorted_d = sorted(district_results, key=lambda x: x['mae_kg_per_ha'])

        return {
            'method': 'Leave-One-District-Out Spatial Cross-Validation (LODO-CV)',
            'total_districts_evaluated': len(district_results),
            'mean_spatial_mae': round(mean_mae, 1),
            'spatial_mae_std': round(std_mae, 1),
            'mean_spatial_rmse': round(float(np.mean(spatial_rmses)), 1),
            'best_generalizing_district': sorted_d[0]['district'] if sorted_d else None,
            'most_challenging_district': sorted_d[-1]['district'] if sorted_d else None,
            'district_breakdown': district_results,
            'spatial_generalization_note': (
                f"LODO-CV evaluated across {len(district_results)} districts. "
                f"Average cross-district prediction error is {mean_mae:,.0f} kg/ha (std: {std_mae:,.0f} kg/ha). "
                f"Lowest error observed in {sorted_d[0]['district']}, highest error in {sorted_d[-1]['district']}."
            ) if sorted_d else "Spatial CV completed.",
        }


