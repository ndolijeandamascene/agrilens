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

