"""
Pytest configuration and fixtures for the AgriLens ML test suite.
"""
import pytest
import os
import joblib
from decimal import Decimal
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from django.conf import settings

from apps.geography.models import Province, District
from apps.agriculture.models import Crop, CropCategory, AgriculturalSeason
from apps.data_management.models import DataSource, ImportBatch, ValidatedObservation
from apps.markets.models import MarketLocation, CommodityPrice
from apps.ml.models import MLModel, DistrictTypology
from apps.ml.services.registry import ModelRegistry


@pytest.fixture(autouse=True)
def seed_ml_test_database(db):
    """
    Seeds essential reference objects and an active trained model artifact
    into the isolated test database for reliable API testing.
    """
    # 1. Geography
    prov = Province.objects.create(name='Northern', code='03')
    dist_musanze = District.objects.create(name='Musanze', code='0301', province=prov)
    dist_burera = District.objects.create(name='Burera', code='0302', province=prov)

    # Seed remaining 28 districts so district cluster tests have all 30 districts
    for i in range(1, 29):
        District.objects.create(name=f"District_{i}", code=f"99{i:02d}", province=prov)

    # 2. Crops & Seasons
    cat = CropCategory.objects.create(name='Cereals')
    crop_maize = Crop.objects.create(name='Maize', category=cat, is_priority_crop=True)
    crop_beans = Crop.objects.create(name='Beans', category=cat, is_priority_crop=True)

    season_2024 = AgriculturalSeason.objects.create(
        year=2024, season='A', start_date='2023-09-01', end_date='2024-02-28'
    )
    season_2025 = AgriculturalSeason.objects.create(
        year=2025, season='A', start_date='2024-09-01', end_date='2025-02-28'
    )

    # 3. Data Source, Import Batch & Validated Observations
    data_source = DataSource.objects.create(
        name="NISR SAS Test",
        source_type="NISR_SAS_TEST",
        data_kind=DataSource.DataKind.SURVEY,
        year=2024,
        season="A",
        organization="NISR"
    )
    import_batch = ImportBatch.objects.create(
        source=data_source,
        filename="test_sas.csv",
        status=ImportBatch.Status.SUCCESS
    )

    for idx, (yr, ssn) in enumerate([(2024, season_2024), (2025, season_2025)]):
        ValidatedObservation.objects.create(
            batch=import_batch,
            provenance='NISR_SAS_2024_001',
            source_record_id=f"REC_{yr}_{idx}",
            crop=crop_maize,
            district=dist_musanze,
            season=ssn,
            plot_area_ha=Decimal('0.50'),
            total_production_kg=Decimal('1600.0'),
            calculated_yield_kg_per_ha=Decimal('3200.0'),
            sampling_weight=Decimal('10.0'),
            is_improved_seed=True,
            uses_inorganic_fertilizer=True,
            uses_organic_fertilizer=True,
            uses_pesticide=False,
            is_irrigated=False,
            has_anti_erosion=False,
            uses_mechanization=False
        )

    # 4. Train and save a lightweight RandomForest pipeline for test inference
    cats = ['crop', 'district', 'province']
    nums = ['plot_area_ha']
    bools = [
        'is_improved_seed', 'uses_inorganic_fertilizer', 'uses_organic_fertilizer',
        'uses_pesticide', 'is_irrigated', 'has_anti_erosion', 'uses_mechanization'
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cats),
            ('pass', 'passthrough', nums + bools)
        ]
    )

    rf = RandomForestRegressor(n_estimators=5, random_state=42)
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', rf)
    ])

    import pandas as pd
    sample_train_df = pd.DataFrame([
        {
            'crop': 'Maize', 'district': 'Musanze', 'province': 'Northern',
            'plot_area_ha': 0.5, 'is_improved_seed': 1, 'uses_inorganic_fertilizer': 1,
            'uses_organic_fertilizer': 1, 'uses_pesticide': 0, 'is_irrigated': 0,
            'has_anti_erosion': 0, 'uses_mechanization': 0
        },
        {
            'crop': 'Beans', 'district': 'Musanze', 'province': 'Northern',
            'plot_area_ha': 0.4, 'is_improved_seed': 0, 'uses_inorganic_fertilizer': 0,
            'uses_organic_fertilizer': 1, 'uses_pesticide': 0, 'is_irrigated': 0,
            'has_anti_erosion': 0, 'uses_mechanization': 0
        }
    ])
    sample_y = [3200.0, 1500.0]
    pipeline.fit(sample_train_df, sample_y)

    artifact_name = 'yield_test_model.joblib'
    storage_dir = ModelRegistry.get_storage_dir()
    joblib.dump(pipeline, storage_dir / artifact_name)

    # Register active MLModel in database
    MLModel.objects.create(
        name="AgriLens Yield Random Forest",
        model_type=MLModel.ModelType.YIELD_PREDICTION,
        version="v1.0-test",
        algorithm="RandomForestRegressor",
        target_variable="calculated_yield_kg_per_ha",
        feature_names=cats + nums + bools,
        metrics={
            "mae": 1298.0,
            "rmse": 1820.0,
            "r2": 0.6577,
            "baseline_mae": 2110.0,
            "mae_improvement_pct": 38.5
        },
        feature_importance={
            "uses_inorganic_fertilizer": 0.38,
            "is_improved_seed": 0.29,
            "plot_area_ha": 0.16,
            "district": 0.10,
            "uses_pesticide": 0.07
        },
        observation_count=4301,
        artifact_filename=artifact_name,
        is_active=True,
        status=MLModel.Status.ACTIVE
    )

    # 5. Seed 30 DistrictTypology rows
    all_districts = District.objects.all()
    for d in all_districts:
        DistrictTypology.objects.create(
            district=d,
            cluster_id=0,
            cluster_name="High-Input Commercial Agro-Hub",
            profile_summary="High adoption of certified seeds and inorganic fertilizers.",
            main_constraints="High production costs; post-harvest drying capacity.",
            recommended_interventions="Subsidized storage infrastructure and commercial off-taking.",
            avg_yield_kg_per_ha=Decimal('3400.0'),
            seed_adoption_rate=Decimal('68.0'),
            fertilizer_adoption_rate=Decimal('72.0'),
            loss_rate_percentage=Decimal('11.0')
        )

    # 6. Seed Market Location & Commodity Price
    mkt = MarketLocation.objects.create(
        name="Musanze Central Market",
        district=dist_musanze,
        province=prov,
        market_type="RETAIL"
    )
    CommodityPrice.objects.create(
        crop=crop_maize,
        market=mkt,
        price_per_kg_rwf=Decimal('420.0'),
        date_recorded="2026-10-20",
        status=CommodityPrice.Status.PUBLISHED
    )
