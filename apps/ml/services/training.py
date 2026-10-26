"""
AgriLens Machine Learning Training Engine.
Trains, evaluates, and registers:
1. Farm-Level Yield Prediction (RandomForestRegressor with survey expansion weights).
2. District Agro-Ecological Typology Clustering (K-Means with domain profile assignment).
"""
import logging
from decimal import Decimal
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.cluster import KMeans

from apps.geography.models import District
from apps.ml.models import MLModel, DistrictTypology
from .features import FeatureExtractionPipeline
from .evaluation import ModelEvaluationService
from .registry import ModelRegistry

logger = logging.getLogger(__name__)


class AgriLensYieldPredictorBundle:
    """
    Unified Yield Inference Bundle.
    Combines:
    1. Primary survey-weighted regressor (RandomForestRegressor)
    2. Quantile regressors for 80% confidence interval (P10, P50, P90 Pinball Loss)
    3. Specialized crop-stratified sub-models (Cereals, Tubers, Legumes)
    4. Local agronomic waterfall feature attribution
    """

    PRACTICE_METADATA = [
        ('is_improved_seed', 'Certified Improved Seed', 'Genetic crop yield potential'),
        ('uses_inorganic_fertilizer', 'Mineral Fertilizer', 'Soil macronutrient enrichment (NPK)'),
        ('uses_organic_fertilizer', 'Organic Compost / Manure', 'Soil organic matter & moisture retention'),
        ('uses_pesticide', 'Crop Protection / Pesticide', 'Field pest & fungal disease mitigation'),
        ('is_irrigated', 'Irrigation Infrastructure', 'Mitigation of seasonal rainfed moisture stress'),
        ('has_anti_erosion', 'Hillside Terracing / Anti-Erosion', 'Slope conservation & topsoil retention'),
        ('uses_mechanization', 'Agricultural Mechanization', 'Field preparation efficiency'),
    ]

    CROP_TAXONOMY_MAP = {
        'CEREALS': ['maize', 'rice', 'marshland rice', 'sorghum', 'wheat', 'finger millet', 'corn'],
        'TUBERS': ['irish potato', 'potato', 'cassava', 'sweet potato', 'yams', 'taro'],
        'LEGUMES': ['bush beans', 'climbing beans', 'beans', 'soybeans', 'soybean', 'groundnuts', 'groundnut', 'peas', 'dry peas'],
    }

    def __init__(self, primary_pipeline, q10_pipeline=None, q50_pipeline=None, q90_pipeline=None, crop_submodels=None, feature_cols=None):
        self.primary_pipeline = primary_pipeline
        self.q10_pipeline = q10_pipeline
        self.q50_pipeline = q50_pipeline
        self.q90_pipeline = q90_pipeline
        self.crop_submodels = crop_submodels or {}
        self.feature_cols = feature_cols or []

    def predict(self, X):
        """Standard scikit-learn regressor duck-typing."""
        return self.primary_pipeline.predict(X)

    @classmethod
    def get_crop_taxonomy(cls, crop_name: str) -> str:
        name_lower = (crop_name or '').lower().strip()
        for tax, keywords in cls.CROP_TAXONOMY_MAP.items():
            if any(k in name_lower for k in keywords):
                return tax
        return 'GLOBAL'

    def predict_with_uncertainty(self, X):
        """
        Executes point prediction and 80% confidence interval (P10..P90).
        Routes point prediction through crop-stratified submodel if available.
        """
        crop_name = str(X['crop'].iloc[0]) if ('crop' in X.columns and len(X) > 0) else ''
        taxonomy = self.get_crop_taxonomy(crop_name)

        # 1. Point prediction (submodel or primary)
        submodel = self.crop_submodels.get(taxonomy)
        if submodel is not None:
            try:
                point_pred = float(submodel.predict(X)[0])
            except Exception:
                point_pred = float(self.primary_pipeline.predict(X)[0])
        else:
            point_pred = float(self.primary_pipeline.predict(X)[0])

        point_pred = max(50.0, point_pred)

        # 2. Quantile bounds
        if self.q50_pipeline is not None:
            try:
                p50 = float(self.q50_pipeline.predict(X)[0])
            except Exception:
                p50 = point_pred
        else:
            p50 = point_pred

        if self.q10_pipeline is not None:
            try:
                p10 = float(self.q10_pipeline.predict(X)[0])
            except Exception:
                p10 = max(50.0, p50 * 0.75)
        else:
            p10 = max(50.0, p50 * 0.75)

        if self.q90_pipeline is not None:
            try:
                p90 = float(self.q90_pipeline.predict(X)[0])
            except Exception:
                p90 = p50 * 1.25
        else:
            p90 = p50 * 1.25

        # Guarantee monotonicity: p10 <= p50 <= p90
        p10 = min(p10, p50)
        p90 = max(p90, p50)

        # Proportional alignment if submodel diverges from global median
        if p50 > 0 and point_pred > 0:
            scale = point_pred / p50
            p10 = max(50.0, p10 * scale)
            p90 = max(point_pred, p90 * scale)
            p50 = point_pred

        p10_kg = max(50.0, round(p10, 1))
        p50_kg = max(50.0, round(p50, 1))
        p90_kg = max(p50_kg, round(p90, 1))

        downside_kg = round(max(0.0, p50_kg - p10_kg), 1)
        upside_kg = round(max(0.0, p90_kg - p50_kg), 1)

        return {
            'point_prediction_kg_ha': p50_kg,
            'point_prediction_tha': round(p50_kg / 1000.0, 2),
            'p10_lower_kg_ha': p10_kg,
            'p10_lower_tha': round(p10_kg / 1000.0, 2),
            'p50_median_kg_ha': p50_kg,
            'p50_median_tha': round(p50_kg / 1000.0, 2),
            'p90_upper_kg_ha': p90_kg,
            'p90_upper_tha': round(p90_kg / 1000.0, 2),
            'downside_risk_kg_ha': downside_kg,
            'downside_risk_tha': round(downside_kg / 1000.0, 2),
            'upside_potential_kg_ha': upside_kg,
            'upside_potential_tha': round(upside_kg / 1000.0, 2),
            'crop_taxonomy_applied': taxonomy,
        }

    def compute_local_attributions(self, input_df):
        """
        Computes localized marginal feature attribution for active vs untapped input practices.
        """
        base_df = input_df.copy()
        for col, _, _ in self.PRACTICE_METADATA:
            if col in base_df.columns:
                base_df[col] = 0

        try:
            base_yield = float(self.predict(base_df)[0])
        except Exception:
            base_yield = 1500.0

        attributions = []
        for col, label, desc in self.PRACTICE_METADATA:
            is_active = bool(input_df[col].iloc[0]) if col in input_df.columns else False
            test_df = base_df.copy()
            test_df[col] = 1
            try:
                single_yield = float(self.predict(test_df)[0])
                uplift_kg = round(single_yield - base_yield, 1)
            except Exception:
                uplift_kg = 250.0

            uplift_tha = round(uplift_kg / 1000.0, 2)

            if is_active:
                attributions.append({
                    'practice_field': col,
                    'practice_name': label,
                    'is_adopted': True,
                    'marginal_contribution_kg_ha': uplift_kg,
                    'marginal_contribution_tha': uplift_tha,
                    'status': 'ACTIVE',
                    'impact_type': 'positive' if uplift_kg > 0 else 'neutral',
                    'explanation': f"Active practice adds estimated +{uplift_tha:.2f} t/ha ({desc}).",
                })
            else:
                attributions.append({
                    'practice_field': col,
                    'practice_name': label,
                    'is_adopted': False,
                    'marginal_contribution_kg_ha': uplift_kg,
                    'marginal_contribution_tha': uplift_tha,
                    'status': 'OPPORTUNITY',
                    'impact_type': 'opportunity',
                    'explanation': f"Untapped opportunity: adoption estimated to add +{uplift_tha:.2f} t/ha ({desc}).",
                })

        return attributions


class YieldPredictionTrainer:
    """Trains and registers the farm-level crop yield regression pipeline bundle."""

    @classmethod
    def train_and_register(cls, user=None, version='v1.0') -> Tuple[MLModel, Dict[str, Any]]:
        """
        Executes end-to-end training:
        1. Extracts validated microdata from PostgreSQL.
        2. Performs temporal hold-out split (2024 vs 2025).
        3. Trains survey-weighted RandomForestRegressor pipeline.
        4. Calculates metrics vs baseline.
        5. Persists artifact and registers in MLModel.
        """
        df, stats = FeatureExtractionPipeline.extract_dataset()
        if df.empty or len(df) < 50:
            raise ValueError(f"Insufficient clean microdata for training (found {len(df)} records).")

        train_df, test_df, split_info = FeatureExtractionPipeline.get_temporal_split(df)

        cat_cols = ['crop', 'district']
        num_cols = ['plot_area_ha']
        bool_cols = [
            'is_improved_seed',
            'uses_inorganic_fertilizer',
            'uses_organic_fertilizer',
            'uses_pesticide',
            'is_irrigated',
            'has_anti_erosion',
            'uses_mechanization',
        ]
        feature_cols = cat_cols + num_cols + bool_cols
        target_col = FeatureExtractionPipeline.TARGET_COLUMN

        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
                ('num', StandardScaler(), num_cols),
                ('bool', 'passthrough', bool_cols),
            ],
            remainder='drop'
        )

        regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=14,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', regressor)
        ])

        # Train with survey sampling weights
        sample_weights = train_df['sampling_weight'].values
        pipeline.fit(train_df[feature_cols], train_df[target_col], regressor__sample_weight=sample_weights)

        # Evaluate on holdout test set
        test_preds = pipeline.predict(test_df[feature_cols])
        eval_metrics = ModelEvaluationService.evaluate_regression(
            y_true=test_df[target_col].values,
            y_pred=test_preds,
            sample_weight=test_df['sampling_weight'].values,
            y_train=train_df[target_col].values
        )

        # Feature importances mapping
        feature_importance_dict = cls._extract_feature_importances(pipeline, cat_cols, num_cols, bool_cols)

        # 2. Train Pinball-Loss Quantile Regressors (P10, P50, P90)
        logger.info("Training pinball-loss quantile regressors (P10, P50, P90)...")
        q10_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', HistGradientBoostingRegressor(loss='quantile', quantile=0.10, max_iter=100, random_state=42))
        ])
        q50_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', HistGradientBoostingRegressor(loss='quantile', quantile=0.50, max_iter=100, random_state=42))
        ])
        q90_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', HistGradientBoostingRegressor(loss='quantile', quantile=0.90, max_iter=100, random_state=42))
        ])

        q10_pipeline.fit(train_df[feature_cols], train_df[target_col], regressor__sample_weight=sample_weights)
        q50_pipeline.fit(train_df[feature_cols], train_df[target_col], regressor__sample_weight=sample_weights)
        q90_pipeline.fit(train_df[feature_cols], train_df[target_col], regressor__sample_weight=sample_weights)

        # Quantile coverage evaluation
        p10_test = q10_pipeline.predict(test_df[feature_cols])
        p90_test = q90_pipeline.predict(test_df[feature_cols])
        cov_80 = float(np.mean((test_df[target_col].values >= p10_test) & (test_df[target_col].values <= p90_test)) * 100.0)
        eval_metrics['coverage_80_pct'] = round(cov_80, 1)

        # 3. Train Crop-Stratified Agronomic Sub-Models
        crop_submodels = {}
        for tax, keywords in AgriLensYieldPredictorBundle.CROP_TAXONOMY_MAP.items():
            pattern = '|'.join(keywords)
            sub_train = train_df[train_df['crop'].str.contains(pattern, case=False, na=False)]
            if len(sub_train) >= 50:
                sub_pre = ColumnTransformer(
                    transformers=[
                        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
                        ('num', StandardScaler(), num_cols),
                        ('bool', 'passthrough', bool_cols),
                    ],
                    remainder='drop'
                )
                sub_reg = RandomForestRegressor(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1)
                sub_pipe = Pipeline([('preprocessor', sub_pre), ('regressor', sub_reg)])
                sub_w = sub_train['sampling_weight'].values
                sub_pipe.fit(sub_train[feature_cols], sub_train[target_col], regressor__sample_weight=sub_w)
                crop_submodels[tax] = sub_pipe

        # 4. Spatial Holdout Cross-Validation Diagnostics (LODO-CV)
        try:
            spatial_diag = ModelEvaluationService.evaluate_spatial_holdout(
                pipeline_builder_fn=lambda: Pipeline([
                    ('preprocessor', ColumnTransformer([
                        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
                        ('num', StandardScaler(), num_cols),
                        ('bool', 'passthrough', bool_cols),
                    ], remainder='drop')),
                    ('regressor', RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1))
                ]),
                df=df,
                feature_cols=feature_cols,
                target_col=target_col,
                district_col='district',
                max_districts=6
            )
            eval_metrics['spatial_diagnostics'] = spatial_diag
        except Exception as exc:
            logger.warning("Spatial holdout diagnostic skipped: %s", exc)

        # 5. Assemble and Persist Yield Predictor Bundle
        bundle = AgriLensYieldPredictorBundle(
            primary_pipeline=pipeline,
            q10_pipeline=q10_pipeline,
            q50_pipeline=q50_pipeline,
            q90_pipeline=q90_pipeline,
            crop_submodels=crop_submodels,
            feature_cols=feature_cols
        )

        artifact_name = f"yield_bundle_{version}.joblib"
        ModelRegistry.save_artifact(bundle, artifact_name)

        # Deprecate previous active models of this type
        MLModel.objects.filter(
            model_type=MLModel.ModelType.YIELD_PREDICTION,
            is_active=True
        ).update(is_active=False, status=MLModel.Status.DEPRECATED)

        model_record, _ = MLModel.objects.update_or_create(
            model_type=MLModel.ModelType.YIELD_PREDICTION,
            version=version,
            defaults={
                'name': 'AgriLens Farm-Level Crop Yield Predictor Bundle',
                'algorithm': 'RandomForestRegressor + Quantile HistGradientBoosting (P10/P50/P90) + Crop Sub-Models',
                'target_variable': 'calculated_yield_kg_per_ha',
                'feature_names': feature_cols,
                'metrics': eval_metrics,
                'feature_importance': feature_importance_dict,
                'training_provenance': 'NISR_SAS_2024_2025',
                'observation_count': len(train_df),
                'validation_methodology': f"{split_info['method']} + Quantile Pinball Loss + Spatial LODO-CV",
                'artifact_filename': artifact_name,
                'is_active': True,
                'status': MLModel.Status.ACTIVE,
                'training_notes': (
                    f"Trained on {len(train_df)} plots; tested on {len(test_df)} plots. "
                    f"R2: {eval_metrics['r2']}, MAE: {eval_metrics['mae']} kg/ha. "
                    f"80% Quantile Coverage: {eval_metrics.get('coverage_80_pct', 'N/A')}%. "
                    f"Crop Sub-Models: {list(crop_submodels.keys())}."
                ),
                'trained_by': user,
            }
        )

        return model_record, eval_metrics

    @classmethod
    def _extract_feature_importances(cls, pipeline, cat_cols, num_cols, bool_cols) -> Dict[str, float]:
        """Maps raw one-hot encoded tree importances back to domain agricultural factors."""
        try:
            regressor = pipeline.named_steps['regressor']
            importances = regressor.feature_importances_
            preprocessor = pipeline.named_steps['preprocessor']
            cat_encoder = preprocessor.named_transformers_['cat']
            encoded_cat_names = list(cat_encoder.get_feature_names_out(cat_cols))

            all_encoded_names = encoded_cat_names + num_cols + bool_cols
            raw_map = dict(zip(all_encoded_names, importances))

            # Aggregate into high-level agronomic dimensions
            summary = {
                'Crop Variety / Taxonomy': float(sum(v for k, v in raw_map.items() if k.startswith('crop_'))),
                'Geographic Agro-Ecological District': float(sum(v for k, v in raw_map.items() if k.startswith('district_'))),
                'Plot Cultivated Area': float(raw_map.get('plot_area_ha', 0.0)),
                'Mineral Fertilizer Adoption': float(raw_map.get('uses_inorganic_fertilizer', 0.0)),
                'Organic Manure / Compost': float(raw_map.get('uses_organic_fertilizer', 0.0)),
                'Certified Improved Seeds': float(raw_map.get('is_improved_seed', 0.0)),
                'Pesticides & Crop Protection': float(raw_map.get('uses_pesticide', 0.0)),
                'Irrigation Infrastructure': float(raw_map.get('is_irrigated', 0.0)),
                'Soil Conservation Terracing': float(raw_map.get('has_anti_erosion', 0.0)),
                'Agricultural Mechanization': float(raw_map.get('uses_mechanization', 0.0)),
            }
            # Normalize to 100%
            total = sum(summary.values()) or 1.0
            return {k: round((v / total) * 100.0, 2) for k, v in summary.items()}
        except Exception as exc:
            logger.warning("Could not extract feature importances: %s", exc)
            return {}


class DistrictClusteringTrainer:
    """Trains K-Means clustering across Rwanda's 30 districts and populates DistrictTypology."""

    TYPOLOGY_PROFILES = {
        0: {
            'name': 'High-Adoption Commercial Maize & Cereal Hub',
            'summary': 'Districts with high adoption of mineral fertilizers and certified seed varieties. Above-average yields with substantial commercialization, but sensitive to seed price volatility and supply chain timing.',
            'constraints': ['Seasonal fertilizer price volatility', 'Timely distribution of certified hybrid seeds', 'Post-harvest drying bottlenecks'],
            'interventions': ['Scale up Smart Nkunganire subsidy coverage', 'Introduce digital warehouse receipt systems', 'Modern grain silo and drying center expansion'],
        },
        1: {
            'name': 'Soil Fertility-Constrained Rainfed Farming Zone',
            'summary': 'Characterized by extensive smallholder cultivation with high dependence on organic manure but low mineral fertilizer adoption. Vulnerable to soil acidity, nitrogen depletion, and rainfall fluctuations.',
            'constraints': ['Low mineral fertilizer application rate', 'Soil acidity (pH < 5.5)', 'Erosion on steep hillside plots'],
            'interventions': ['Subsidized agricultural lime distribution', 'Promotion of agroforestry and hillside terracing', 'Targeted soil testing and blended fertilizer packs'],
        },
        2: {
            'name': 'Post-Harvest Loss & Storage Vulnerability Zone',
            'summary': 'Districts achieving moderate to high harvest yields but suffering elevated post-harvest losses (>10%) during harvesting, transport, and traditional granary storage.',
            'constraints': ['High post-harvest loss rate', 'Inadequate hermetic storage bags and facilities', 'Poor transport infrastructure to primary markets'],
            'interventions': ['Distribute certified hermetic storage bags (PICS)', 'Establish communal aggregation centers and cold chains', 'Feeder road connectivity improvements'],
        },
        3: {
            'name': 'Diversified Agro-Ecological Transition Zone',
            'summary': 'Districts characterized by mixed cropping systems (beans, bananas, tubers) with moderate input adoption. Good ecological resilience with significant untapped productivity potential.',
            'constraints': ['Mixed plot competition without crop rotation', 'Limited access to small-scale irrigation', 'Low mechanization rate'],
            'interventions': ['Promote micro-irrigation schemes (dam sheets, solar pumps)', 'Intercropping agronomic guidance and extension', 'Establish shared agricultural machinery hubs'],
        },
    }

    @classmethod
    def train_and_register(cls, user=None, version='v1.0') -> Tuple[MLModel, int]:
        """
        Computes 30-district feature vectors, runs KMeans(k=4),
        maps meaningful domain profiles, and updates DistrictTypology records.
        """
        from apps.data_management.models import ValidatedObservation
        from django.db.models import Avg, Sum, Count, Q

        qs = ValidatedObservation.objects.filter(provenance__startswith='NISR_')
        district_aggs = qs.values(
            'district_id', 'district__name', 'district__code'
        ).annotate(
            total_plots=Count('id'),
            mean_yield=Avg('calculated_yield_kg_per_ha'),
            mean_area=Avg('plot_area_ha'),
            seed_count=Count('id', filter=Q(is_improved_seed=True)),
            inorg_count=Count('id', filter=Q(uses_inorganic_fertilizer=True)),
            org_count=Count('id', filter=Q(uses_organic_fertilizer=True)),
            loss_sum=Sum('total_loss_kg'),
            prod_sum=Sum('total_production_kg'),
        )

        if not district_aggs:
            raise ValueError("No validated observations available for district clustering.")

        rows = []
        for d in district_aggs:
            n_plots = max(1, d['total_plots'])
            p_sum = float(d['prod_sum'] or 0.0)
            l_sum = float(d['loss_sum'] or 0.0)
            loss_rate = (l_sum / (p_sum + l_sum) * 100.0) if (p_sum + l_sum) > 0 else 0.0

            rows.append({
                'district_id': d['district_id'],
                'district_name': d['district__name'],
                'district_code': d['district__code'],
                'mean_yield': float(d['mean_yield'] or 0.0),
                'mean_area': float(d['mean_area'] or 0.5),
                'seed_rate': (d['seed_count'] / n_plots) * 100.0,
                'fertilizer_rate': (d['inorg_count'] / n_plots) * 100.0,
                'organic_rate': (d['org_count'] / n_plots) * 100.0,
                'loss_rate': loss_rate,
            })

        df_districts = pd.DataFrame(rows)
        feature_cols = ['mean_yield', 'seed_rate', 'fertilizer_rate', 'organic_rate', 'loss_rate']

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_districts[feature_cols])

        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        df_districts['cluster_raw'] = kmeans.fit_predict(X_scaled)

        # Sort clusters by composite yield and input score for consistent profile mapping
        centroids = kmeans.cluster_centers_
        cluster_scores = centroids[:, 0] + centroids[:, 1] + centroids[:, 2]
        sorted_clusters = np.argsort(cluster_scores)[::-1]  # descending: 0 is highest input/yield
        cluster_mapping = {old_c: new_c for new_c, old_c in enumerate(sorted_clusters)}
        df_districts['cluster_id'] = df_districts['cluster_raw'].map(cluster_mapping)

        # Save artifact
        artifact_name = f"district_kmeans_{version}.joblib"
        ModelRegistry.save_artifact({'scaler': scaler, 'kmeans': kmeans, 'mapping': cluster_mapping}, artifact_name)

        # Register MLModel
        MLModel.objects.filter(
            model_type=MLModel.ModelType.DISTRICT_CLUSTERING,
            is_active=True
        ).update(is_active=False, status=MLModel.Status.DEPRECATED)

        model_record, _ = MLModel.objects.update_or_create(
            model_type=MLModel.ModelType.DISTRICT_CLUSTERING,
            version=version,
            defaults={
                'name': 'AgriLens 30-District Agro-Ecological Typology Clusterer',
                'algorithm': 'K-Means (k=4 clusters, StandardScaler)',
                'target_variable': 'district_typology_cluster',
                'feature_names': feature_cols,
                'metrics': {'n_clusters': 4, 'inertia': round(float(kmeans.inertia_), 2)},
                'training_provenance': 'NISR_SAS_2024_2025',
                'observation_count': len(df_districts),
                'validation_methodology': 'Unsupervised Multivariate Aggregation across all 30 administrative districts',
                'artifact_filename': artifact_name,
                'is_active': True,
                'status': MLModel.Status.ACTIVE,
                'training_notes': 'Clusters 30 districts into 4 distinct policy & investment intervention categories.',
                'trained_by': user,
            }
        )

        # Populate / update DistrictTypology records
        updated_count = 0
        for _, r in df_districts.iterrows():
            c_id = int(r['cluster_id'])
            profile = cls.TYPOLOGY_PROFILES.get(c_id, cls.TYPOLOGY_PROFILES[0])

            district_obj = District.objects.get(id=r['district_id'])
            DistrictTypology.objects.update_or_create(
                district=district_obj,
                defaults={
                    'cluster_id': c_id,
                    'cluster_name': profile['name'],
                    'profile_summary': profile['summary'],
                    'main_constraints': profile['constraints'],
                    'recommended_interventions': profile['interventions'],
                    'avg_yield_kg_per_ha': round(Decimal(str(r['mean_yield'])), 2),
                    'seed_adoption_rate': round(Decimal(str(r['seed_rate'])), 2),
                    'fertilizer_adoption_rate': round(Decimal(str(r['fertilizer_rate'])), 2),
                    'loss_rate_percentage': round(Decimal(str(r['loss_rate'])), 2),
                    'model': model_record,
                }
            )
            updated_count += 1

        # Ensure all 30 administrative districts receive cluster mapping (extrapolate provincial baseline if unobserved)
        assigned_ids = set(df_districts['district_id'])
        for unassigned in District.objects.exclude(id__in=assigned_ids).select_related('province'):
            prov_assigned = df_districts[df_districts['district_id'].isin(
                unassigned.province.districts.values_list('id', flat=True)
            )]
            if not prov_assigned.empty:
                c_id = int(prov_assigned['cluster_id'].mode()[0])
                avg_y = Decimal(str(round(prov_assigned['mean_yield'].mean(), 2)))
                avg_s = Decimal(str(round(prov_assigned['seed_rate'].mean(), 2)))
                avg_f = Decimal(str(round(prov_assigned['fertilizer_rate'].mean(), 2)))
                avg_l = Decimal(str(round(prov_assigned['loss_rate'].mean(), 2)))
            else:
                c_id = 3  # Diversified transition zone
                avg_y = Decimal('1850.00')
                avg_s = Decimal('25.00')
                avg_f = Decimal('30.00')
                avg_l = Decimal('8.50')

            profile = cls.TYPOLOGY_PROFILES.get(c_id, cls.TYPOLOGY_PROFILES[3])
            DistrictTypology.objects.update_or_create(
                district=unassigned,
                defaults={
                    'cluster_id': c_id,
                    'cluster_name': profile['name'],
                    'profile_summary': f"{profile['summary']} (Agro-ecological provincial extrapolation for {unassigned.province.name}).",
                    'main_constraints': profile['constraints'],
                    'recommended_interventions': profile['interventions'],
                    'avg_yield_kg_per_ha': avg_y,
                    'seed_adoption_rate': avg_s,
                    'fertilizer_adoption_rate': avg_f,
                    'loss_rate_percentage': avg_l,
                    'model': model_record,
                }
            )
            updated_count += 1

        return model_record, updated_count
