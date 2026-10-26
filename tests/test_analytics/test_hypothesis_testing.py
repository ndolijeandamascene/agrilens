"""
Tests for Survey-Weighted Statistical Hypothesis Testing in Agricultural Insights
"""
import pytest
from decimal import Decimal
from apps.insights.services.rules import compute_survey_weighted_diff_p_value
from apps.insights.models import AgriculturalInsight
from apps.agriculture.models import Crop, AgriculturalSeason


class TestStatisticalHypothesisTesting:
    def test_significant_difference_large_samples(self):
        # Mean 1 = 3000, Mean 2 = 2500, small variance (SE = 50), n=500
        # z = 500 / 50 = 10 -> p < 0.0001
        p_val, is_sig, note = compute_survey_weighted_diff_p_value(
            mean_current=3000.0,
            mean_prev=2500.0,
            var_current=1250.0,
            var_prev=1250.0,
            n_current=500,
            n_prev=500
        )
        assert p_val is not None
        assert p_val < Decimal('0.001')
        assert is_sig is True
        assert "statistically significant" in note.lower()

    def test_insignificant_noisy_difference(self):
        # Mean 1 = 2800, Mean 2 = 2750 (+1.8%), large variance (SE = 200), n=20
        # z = 50 / 200 = 0.25 -> p ~ 0.80
        p_val, is_sig, note = compute_survey_weighted_diff_p_value(
            mean_current=2800.0,
            mean_prev=2750.0,
            var_current=20000.0,
            var_prev=20000.0,
            n_current=20,
            n_prev=20
        )
        assert p_val is not None
        assert p_val > Decimal('0.50')
        assert is_sig is False
        assert "not statistically significant" in note.lower()

    def test_small_sample_size_fallback(self):
        # Samples < 3
        p_val, is_sig, note = compute_survey_weighted_diff_p_value(
            mean_current=3000.0,
            mean_prev=2000.0,
            var_current=100.0,
            var_prev=100.0,
            n_current=2,
            n_prev=1
        )
        assert p_val is None
        assert is_sig is True
        assert "too small" in note.lower()

    def test_missing_means_fallback(self):
        p_val, is_sig, note = compute_survey_weighted_diff_p_value(
            mean_current=None,
            mean_prev=2000.0,
            var_current=100.0,
            var_prev=100.0,
            n_current=10,
            n_prev=10
        )
        assert p_val is None
        assert is_sig is True
        assert "not applicable" in note.lower()
