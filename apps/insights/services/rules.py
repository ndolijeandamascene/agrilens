"""
AgriLens Comparison and Calculation Rules Service.
Implements robust mathematical, statistical, and period comparison logic:
- Strict handling of zero baselines (avoids division by zero, explicitly explains undefined %)
- Preservation of genuine zero values distinct from missing/null observations
- Year-over-Year (YoY) and cross-season reference period resolution
- Survey-weighted aggregation formulas adhering to official NISR methodology
"""
from decimal import Decimal
from typing import Optional, Tuple
from apps.agriculture.models import AgriculturalSeason


def calculate_percentage_change(
    current_val: Optional[float],
    previous_val: Optional[float]
) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Calculates percentage change between current and previous values:
        percentage_change = ((current_value - previous_value) / abs(previous_value)) * 100

    Rules:
    - If previous_val is None or current_val is None:
        Returns (None, "Missing baseline or current data for period comparison")
    - If previous_val is 0:
        Returns (None, "Baseline value is zero; percentage change cannot be calculated from a zero baseline")
    - Genuine zero handling:
        If current_val is 0 and previous_val > 0, returns (-100.0, None)
    - Returns:
        (percentage_change_decimal, explanation_limitation_note)
    """
    if current_val is None or previous_val is None:
        return None, "Missing baseline or current data for period comparison"

    curr_f = float(current_val)
    prev_f = float(previous_val)

    if prev_f == 0.0:
        return None, "Baseline value is zero; percentage change cannot be calculated from a zero baseline"

    pct = ((curr_f - prev_f) / abs(prev_f)) * 100.0
    return Decimal(str(round(pct, 2))), None


def calculate_absolute_change(
    current_val: Optional[float],
    previous_val: Optional[float]
) -> Optional[Decimal]:
    """
    Calculates absolute difference: current_value - previous_value.
    Preserves genuine zeroes; returns None if either input is None.
    """
    if current_val is None or previous_val is None:
        return None
    diff = float(current_val) - float(previous_val)
    return Decimal(str(round(diff, 2)))


def resolve_comparison_period(current_season: AgriculturalSeason) -> Optional[AgriculturalSeason]:
    """
    Determines the authoritative comparison period for Rwanda's agricultural seasons.
    
    Methodological Rule:
    In Rwanda, Year-over-Year same season (e.g. 2025A vs 2024A, 2025B vs 2024B, 2025C vs 2024C)
    is the primary valid comparison period because Season A (Sept-Feb), Season B (Feb-July),
    and Season C (marshland July-Sept) possess fundamentally distinct agro-climatic and rainfall profiles.
    
    If YoY same season is unavailable, falls back to the chronologically preceding season.
    """
    if not current_season:
        return None

    # Primary: Year-over-Year same season (e.g. 2024A for 2025A)
    yoy_season = AgriculturalSeason.objects.filter(
        year=current_season.year - 1,
        season=current_season.season
    ).first()
    if yoy_season:
        return yoy_season

    # Secondary: Chronologically preceding season
    if current_season.season == 'B':
        prev_code = 'A'
        prev_year = current_season.year
    elif current_season.season == 'C':
        prev_code = 'B'
        prev_year = current_season.year
    else:  # Season A
        prev_code = 'C'
        prev_year = current_season.year - 1

    preceding_season = AgriculturalSeason.objects.filter(
        year=prev_year,
        season=prev_code
    ).first()

    return preceding_season


def determine_direction(percentage_change: Optional[Decimal], threshold: float = 1.0) -> str:
    """
    Maps percentage change to directional trend:
    - percentage_change >= threshold: INCREASE
    - percentage_change <= -threshold: DECREASE
    - otherwise: STABLE
    """
    if percentage_change is None:
        return "stable"
    pct_f = float(percentage_change)
    if pct_f >= threshold:
        return "increase"
    elif pct_f <= -threshold:
        return "decrease"
    return "stable"


def compute_survey_weighted_diff_p_value(
    mean_current: Optional[float],
    mean_prev: Optional[float],
    var_current: Optional[float],
    var_prev: Optional[float],
    n_current: int = 0,
    n_prev: int = 0
) -> Tuple[Optional[Decimal], bool, str]:
    """
    Computes two-tailed p-value for the difference between two survey-weighted seasonal averages.
    
    Formula:
        SE(diff) = sqrt( Var(Y_current) + Var(Y_prev) )
        z = (Y_current - Y_prev) / SE(diff)
        p = 2 * (1 - NormalCDF(|z|))
    
    Returns:
        (p_value_decimal, is_significant, explanation_text)
    """
    if mean_current is None or mean_prev is None:
        return None, True, "Hypothesis test not applicable: missing mean estimates."

    if n_current < 3 or n_prev < 3:
        return None, True, f"Sample size too small for asymptotic hypothesis testing (n1={n_current}, n2={n_prev})."

    v_curr = float(var_current or 0.0)
    v_prev = float(var_prev or 0.0)
    pooled_se = (v_curr + v_prev) ** 0.5

    if pooled_se <= 1e-9:
        # Zero variance: deterministic identical observations
        diff = abs(float(mean_current) - float(mean_prev))
        if diff > 1e-6:
            return Decimal('0.0001'), True, "Deterministic shift with zero sample variance (p < 0.001)."
        return Decimal('1.0000'), False, "Zero difference between observation periods (p = 1.0)."

    import math
    diff = float(mean_current) - float(mean_prev)
    z_score = diff / pooled_se

    try:
        from scipy import stats
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_score))))
    except Exception:
        # Fallback approximation for standard normal CDF if scipy unavailable
        p_val = float(math.erfc(abs(z_score) / math.sqrt(2.0)))

    p_val_clamped = max(0.0001, min(1.0, p_val))
    p_dec = Decimal(str(round(p_val_clamped, 4)))
    is_sig = p_val_clamped < 0.05

    if is_sig:
        note = f"Statistically significant shift at 95% confidence level (z={z_score:+.2f}, p={p_val_clamped:.4f})."
    else:
        note = (
            f"Observed change is not statistically significant at 95% confidence (z={z_score:+.2f}, p={p_val_clamped:.4f}). "
            "Variation is consistent with survey sampling noise."
        )

    return p_dec, is_sig, note

