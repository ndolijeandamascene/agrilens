"""
AgriLens ML & Grounded Agricultural Intelligence Assistant Intents Test Suite.
Verifies all advanced ML decision-support capabilities:
1. ML Yield Simulation (Random Forest + Quantiles)
2. Crop Suitability & Recommendation Scorecard
3. Dual-Scenario Counterfactual Comparison
4. Agro-Ecological District Typology (K-Means)
5. Production Harvest Forecasting
6. Market Price Surveillance & Trajectory
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.geography.models import Province, District
from apps.agriculture.models import Crop, CropCategory, AgriculturalSeason
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation
from apps.assistant.services.parser import GroundedAgriculturalAssistant
from apps.ml.models import MLModel, DistrictTypology


@pytest.fixture(autouse=True)
def seed_ml_assistant_test_data(db):
    """Seeds test observations, typology, and seasons for ML Assistant intents."""
    prov_north = Province.objects.create(name='Northern Province', code='NP')
    prov_east = Province.objects.create(name='Eastern Province', code='EP')
    prov_west = Province.objects.create(name='Western Province', code='WP')

    dist_musanze = District.objects.create(name='Musanze', code='11', province=prov_north)
    dist_nyagatare = District.objects.create(name='Nyagatare', code='21', province=prov_east)
    dist_karongi = District.objects.create(name='Karongi', code='31', province=prov_west)
    dist_burera = District.objects.create(name='Burera', code='12', province=prov_north)

    cat = CropCategory.objects.create(name='Staples')
    crop_potato = Crop.objects.create(name='Irish Potato', category=cat, is_priority_crop=True)
    crop_maize = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)
    crop_beans = Crop.objects.create(name='Climbing Beans', category=cat, is_priority_crop=True)

    season_2025a = AgriculturalSeason.objects.create(
        year=2025, season='A', start_date='2024-09-01', end_date='2025-02-28'
    )

    ds = DataSource.objects.create(
        name="NISR SAS 2025",
        source_type="NISR_SAS_2025",
        data_kind=DataSource.DataKind.SURVEY,
        year=2025,
        season="A",
        organization="NISR"
    )
    batch = ImportBatch.objects.create(
        source=ds,
        filename="sas_2025a.csv",
        total_rows=15,
        rows_accepted=15
    )

    # Musanze Irish Potato observations
    for i in range(5):
        ValidatedObservation.objects.create(
            batch=batch,
            provenance="NISR_SAS_2025A",
            season=season_2025a,
            district=dist_musanze,
            crop=crop_potato,
            source_record_id=f"musanze_pot_{i}",
            plot_area_ha=Decimal("1.0"),
            total_production_kg=Decimal("10000.0"),
            calculated_yield_kg_per_ha=Decimal("10000.0"),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True,
            loss_rate_percentage=Decimal("7.5"),
            sampling_weight=Decimal("1.0")
        )

    # Nyagatare Maize observations
    for i in range(5):
        ValidatedObservation.objects.create(
            batch=batch,
            provenance="NISR_SAS_2025A",
            season=season_2025a,
            district=dist_nyagatare,
            crop=crop_maize,
            source_record_id=f"nyag_maize_{i}",
            plot_area_ha=Decimal("1.5"),
            total_production_kg=Decimal("4500.0"),
            calculated_yield_kg_per_ha=Decimal("3000.0"),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True,
            loss_rate_percentage=Decimal("5.0"),
            sampling_weight=Decimal("1.0")
        )

    # District typologies
    DistrictTypology.objects.create(
        district=dist_musanze,
        cluster_id=3,
        cluster_name='Diversified Transition Zone',
        profile_summary='Highland fertile volcanic zone with high potato productivity.',
        main_constraints='Steep slope erosion and land fragmentation.',
        recommended_interventions='Bench terracing and certified disease-free seed multiplication.',
        avg_yield_kg_per_ha=Decimal("9500.0"),
        seed_adoption_rate=Decimal("65.0"),
        fertilizer_adoption_rate=Decimal("78.0"),
        loss_rate_percentage=Decimal("8.0")
    )
    DistrictTypology.objects.create(
        district=dist_karongi,
        cluster_id=2,
        cluster_name='Post-Harvest Loss Hotspot',
        profile_summary='High-rainfall Western lakeside zone with steep gradients.',
        main_constraints='Severe post-harvest storage losses and transport hurdles.',
        recommended_interventions='Community drying centers and hermetic storage bags.',
        avg_yield_kg_per_ha=Decimal("2100.0"),
        seed_adoption_rate=Decimal("25.0"),
        fertilizer_adoption_rate=Decimal("30.0"),
        loss_rate_percentage=Decimal("19.5")
    )


@pytest.mark.django_db
def test_assistant_ml_simulation_intent():
    """Verifies that what-if simulation queries invoke the ML Yield inference service."""
    res = GroundedAgriculturalAssistant.answer_query(
        "Simulate maize yield in Nyagatare with fertilizer and improved seed on 2 hectares"
    )
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'ML_SIMULATION'
    assert 'Maize' in res['answer']
    assert 'Nyagatare' in res['answer']
    assert 'Predicted Yield' in res['answer']
    assert 'YieldInferenceService.predict' in res['orm_query']
    assert 'metrics' in res
    assert 'predicted_yield_kg_per_ha' in res['metrics']


@pytest.mark.django_db
def test_assistant_crop_recommendation_intent():
    """Verifies that crop recommendation queries invoke CropRecommendationService."""
    res = GroundedAgriculturalAssistant.answer_query(
        "What crop is best to grow in Musanze?"
    )
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'CROP_RECOMMENDATION'
    assert 'Musanze' in res['answer']
    assert 'Scorecard' in res['answer']
    assert 'CropRecommendationService.recommend_for_district' in res['orm_query']
    assert len(res['metrics']['recommendations']) > 0


@pytest.mark.django_db
def test_assistant_scenario_comparison_intent():
    """Verifies that comparative practice queries run counterfactual scenario models."""
    res = GroundedAgriculturalAssistant.answer_query(
        "Compare current vs recommended practices for climbing beans in Burera"
    )
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'SCENARIO_COMPARISON'
    assert 'Climbing Beans' in res['answer']
    assert 'Burera' in res['answer']
    assert 'Productivity Uplift' in res['answer']
    assert 'MLProductivityService.compare_scenarios' in res['orm_query']


@pytest.mark.django_db
def test_assistant_district_typology_intent():
    """Verifies that agro-ecological cluster questions return spatial typologies."""
    res = GroundedAgriculturalAssistant.answer_query(
        "What agro-ecological cluster is Karongi in?"
    )
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'DISTRICT_TYPOLOGY'
    assert 'Karongi' in res['answer']
    assert 'Post-Harvest Loss Hotspot' in res['answer']
    assert 'DistrictTypologyService.get_typology_by_district' in res['orm_query']


@pytest.mark.django_db
def test_assistant_production_forecast_intent():
    """Verifies that production forecasting queries project upcoming harvests."""
    res = GroundedAgriculturalAssistant.answer_query(
        "Forecast maize production for 2026A in Eastern Province"
    )
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'PRODUCTION_FORECAST'
    assert 'Maize' in res['answer']
    assert '2026A' in res['answer']
    assert 'ProductionForecastingService.get_forecast' in res['orm_query']


@pytest.mark.django_db
def test_assistant_price_trend_intent():
    """Verifies that price surveillance queries analyze price trends."""
    res = GroundedAgriculturalAssistant.answer_query(
        "What is the price trend for Irish Potato?"
    )
    assert res['status'] == 'SUCCESS'
    assert res['intent'] == 'PRICE_TREND'
    assert 'Irish Potato' in res['answer']
    assert 'MarketPriceForecastingService.get_market_analysis' in res['orm_query']
