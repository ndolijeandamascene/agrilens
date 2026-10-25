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
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans

from apps.geography.models import District
from apps.ml.models import MLModel, DistrictTypology
from .features import FeatureExtractionPipeline
from .evaluation import ModelEvaluationService
from .registry import ModelRegistry

logger = logging.getLogger(__name__)


class YieldPredictionTrainer:
    """Trains and registers the farm-level crop yield regression pipeline."""

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

        # Persist artifact
        artifact_name = f"yield_randomforest_{version}.joblib"
        ModelRegistry.save_artifact(pipeline, artifact_name)

        # Deprecate previous active models of this type
        MLModel.objects.filter(
            model_type=MLModel.ModelType.YIELD_PREDICTION,
            is_active=True
        ).update(is_active=False, status=MLModel.Status.DEPRECATED)

        model_record, _ = MLModel.objects.update_or_create(
            model_type=MLModel.ModelType.YIELD_PREDICTION,
            version=version,
            defaults={
                'name': 'AgriLens Farm-Level Crop Yield Predictor',
                'algorithm': 'RandomForestRegressor (100 estimators, max_depth=14)',
                'target_variable': 'calculated_yield_kg_per_ha',
                'feature_names': feature_cols,
                'metrics': eval_metrics,
                'feature_importance': feature_importance_dict,
                'training_provenance': 'NISR_SAS_2024_2025',
                'observation_count': len(train_df),
                'validation_methodology': split_info['method'],
                'artifact_filename': artifact_name,
                'is_active': True,
                'status': MLModel.Status.ACTIVE,
                'training_notes': f"Trained on {len(train_df)} plots; tested on {len(test_df)} plots. R2: {eval_metrics['r2']}, MAE: {eval_metrics['mae']} kg/ha.",
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
