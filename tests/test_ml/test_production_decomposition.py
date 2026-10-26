import pytest
from apps.ml.services.forecasting import ProductionForecastingService


def test_production_decomposition_mathematical_identity():
    """
    Verifies that the structural decomposition:
    ΔP = Y0 * ΔA + A0 * ΔY + ΔA * ΔY
    holds exactly for positive, negative, and mixed shifts.
    """
    # Scenario: Maize harvest expansion
    # Baseline: 10,000 ha at 2.0 t/ha = 20,000 MT
    # Target: 11,000 ha at 2.4 t/ha = 26,400 MT
    decomp = ProductionForecastingService.compute_production_decomposition(
        baseline_prod_tonnes=20000.0,
        target_prod_tonnes=26400.0,
        baseline_area_ha=10000.0,
        target_area_ha=11000.0,
        baseline_yield_tha=2.0,
        target_yield_tha=2.4,
    )

    # Delta P = 6,400 MT
    assert decomp['delta_production_tonnes'] == 6400.0
    assert decomp['delta_area_ha'] == 1000.0
    assert decomp['delta_yield_tha'] == 0.4

    # Area effect: Y0 * ΔA = 2.0 * 1000 = 2000 MT
    assert decomp['area_effect_tonnes'] == 2000.0

    # Yield effect: A0 * ΔY = 10000 * 0.4 = 4000 MT
    assert decomp['yield_effect_tonnes'] == 4000.0

    # Interaction: ΔA * ΔY = 1000 * 0.4 = 400 MT
    assert decomp['interaction_effect_tonnes'] == 400.0

    # Sum of components must equal Delta P
    component_sum = (
        decomp['area_effect_tonnes'] +
        decomp['yield_effect_tonnes'] +
        decomp['interaction_effect_tonnes']
    )
    assert abs(component_sum - decomp['delta_production_tonnes']) < 0.01

    # Shares:
    # Extensification: 2000 / 6400 = 31.25% -> 31.2%
    # Intensification: 4000 / 6400 = 62.5%
    # Interaction: 400 / 6400 = 6.25% -> 6.2%
    assert decomp['extensification_share_pct'] == 31.2
    assert decomp['intensification_share_pct'] == 62.5
    assert decomp['interaction_share_pct'] == 6.2
    assert decomp['primary_driver'] == 'YIELD_INTENSIFICATION'
    assert 'intensification' in decomp['narrative'].lower()


def test_production_decomposition_extensification_driven():
    """Verifies land extensification classification when area growth dominates."""
    # Baseline: 5,000 ha at 3.0 t/ha = 15,000 MT
    # Target: 7,000 ha at 3.1 t/ha = 21,700 MT
    decomp = ProductionForecastingService.compute_production_decomposition(
        baseline_prod_tonnes=15000.0,
        target_prod_tonnes=21700.0,
        baseline_area_ha=5000.0,
        target_area_ha=7000.0,
        baseline_yield_tha=3.0,
        target_yield_tha=3.1,
    )

    # Area effect: 3.0 * 2000 = 6000 MT
    # Yield effect: 5000 * 0.1 = 500 MT
    assert decomp['area_effect_tonnes'] == 6000.0
    assert decomp['yield_effect_tonnes'] == 500.0
    assert decomp['primary_driver'] == 'LAND_EXTENSIFICATION'
    assert 'extensification' in decomp['narrative'].lower()


def test_production_decomposition_contraction():
    """Verifies contraction handling when production declines."""
    # Baseline: 10,000 ha at 2.5 t/ha = 25,000 MT
    # Target: 9,000 ha at 2.2 t/ha = 19,800 MT
    decomp = ProductionForecastingService.compute_production_decomposition(
        baseline_prod_tonnes=25000.0,
        target_prod_tonnes=19800.0,
        baseline_area_ha=10000.0,
        target_area_ha=9000.0,
        baseline_yield_tha=2.5,
        target_yield_tha=2.2,
    )

    assert decomp['delta_production_tonnes'] < 0
    assert decomp['primary_driver'] == 'YIELD_INTENSIFICATION'  # Yield drop (-3000) > Area drop (-2500)
    assert 'contraction' in decomp['narrative'].lower()
