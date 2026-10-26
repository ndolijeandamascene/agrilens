"""
AgriLens Insight Quality and Reliability Evaluator.
Enforces statistical adequacy, sample size thresholds, and non-causal integrity.
"""
from apps.insights.models import AgriculturalInsight


class QualityPolicy:
    """Configurable threshold parameters for insight reliability."""
    MIN_DISTRICT_PLOTS_SUFFICIENT = 15
    MIN_DISTRICT_PLOTS_LIMITED = 5
    MIN_NATIONAL_PLOTS_SUFFICIENT = 30
    MIN_NATIONAL_PLOTS_LIMITED = 10
    MAX_PLAUSIBLE_YIELD_KG_HA = 60000.0


def evaluate_data_quality(sample_size_current, sample_size_comparison=None, is_national=False, yield_val=None):
    """
    Evaluates data quality and assigns an explicit, rule-based status:
    - SUFFICIENT_DATA: Statistically representative sample size.
    - LIMITED_DATA: Small sample size (5-14 plots), interpret with caution.
    - INSUFFICIENT_DATA: Below minimum threshold (< 5 plots), insufficient baseline.
    - UNDER_REVIEW: Contains flagged outliers or potential measurement errors.

    Returns:
        (status_code, explanation_notes, is_eligible_for_generation)
    """
    thresh_suff = QualityPolicy.MIN_NATIONAL_PLOTS_SUFFICIENT if is_national else QualityPolicy.MIN_DISTRICT_PLOTS_SUFFICIENT
    thresh_lim = QualityPolicy.MIN_NATIONAL_PLOTS_LIMITED if is_national else QualityPolicy.MIN_DISTRICT_PLOTS_LIMITED

    # Plausibility check
    if yield_val is not None and float(yield_val) > QualityPolicy.MAX_PLAUSIBLE_YIELD_KG_HA:
        return (
            AgriculturalInsight.DataQualityStatus.UNDER_REVIEW,
            f"Observed yield ({yield_val:,.1f} kg/ha) exceeds typical agronomic plausibility threshold ({QualityPolicy.MAX_PLAUSIBLE_YIELD_KG_HA:,.0f} kg/ha). Flagged for technical review.",
            False
        )

    # Determine effective sample size
    effective_n = sample_size_current
    if sample_size_comparison is not None:
        effective_n = min(sample_size_current, sample_size_comparison)

    if effective_n >= thresh_suff:
        notes = f"Sufficient sample size (n={sample_size_current} plots"
        if sample_size_comparison is not None:
            notes += f", comparison n={sample_size_comparison} plots"
        notes += "). Computed using official NISR survey expansion weights."
        return (
            AgriculturalInsight.DataQualityStatus.SUFFICIENT_DATA,
            notes,
            True
        )

    elif effective_n >= thresh_lim:
        notes = f"Limited sample size (n={sample_size_current} plots"
        if sample_size_comparison is not None:
            notes += f", comparison n={sample_size_comparison} plots"
        notes += f"; threshold for high certainty is {thresh_suff}). Findings should be interpreted as indicative rather than conclusive."
        return (
            AgriculturalInsight.DataQualityStatus.LIMITED_DATA,
            notes,
            True
        )

    else:
        notes = f"Insufficient sample size (n={effective_n} plots; minimum required threshold is {thresh_lim} plots). Baseline data is inadequate for reliable statistical inference."
        return (
            AgriculturalInsight.DataQualityStatus.INSUFFICIENT_DATA,
            notes,
            False
        )
