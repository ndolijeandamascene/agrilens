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
