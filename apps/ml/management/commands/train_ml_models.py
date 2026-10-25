"""
Django Management Command: train_ml_models
Executes feature extraction from PostgreSQL ValidatedObservation microdata,
trains survey-weighted crop yield regression, fits 30-district K-Means clustering,
and registers artifacts in MLModel and DistrictTypology.
"""
from django.core.management.base import BaseCommand
from apps.ml.services.training import YieldPredictionTrainer, DistrictClusteringTrainer


class Command(BaseCommand):
    help = "Train and register AgriLens Machine Learning models from official NISR microdata."

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-version',
            type=str,
            default='v1.0',
            help='Model semantic version identifier (default: v1.0)'
        )
        parser.add_argument(
            '--model-type',
            type=str,
            default='all',
            choices=['all', 'yield', 'clustering'],
            help='Select which model pipeline to train'
        )

    def handle(self, *args, **options):
        version = options['model_version']
        model_type = options['model_type']

        self.stdout.write(self.style.NOTICE("=" * 65))
        self.stdout.write(self.style.NOTICE("  AGRILENS MACHINE LEARNING TRAINING & REGISTRY PIPELINE"))
        self.stdout.write(self.style.NOTICE("=" * 65))

        if model_type in ('all', 'yield'):
            self.stdout.write(self.style.WARNING("\n1. Training Farm-Level Crop Yield Predictor..."))
            try:
                y_model, metrics = YieldPredictionTrainer.train_and_register(version=version)
                self.stdout.write(self.style.SUCCESS(f"   [OK] Trained Model: {y_model.name} ({y_model.version})"))
                self.stdout.write(f"   • Algorithm: {y_model.algorithm}")
                self.stdout.write(f"   • Training Observations: {y_model.observation_count:,} plots")
                self.stdout.write(f"   • R2 Score: {metrics.get('r2')} (Weighted: {metrics.get('weighted_r2')})")
                self.stdout.write(f"   • MAE: {metrics.get('mae')} kg/ha (Baseline: {metrics.get('baseline_mae')} kg/ha)")
                self.stdout.write(f"   • MAE Improvement vs Baseline: +{metrics.get('mae_improvement_pct')}%")
                self.stdout.write(f"   • Artifact: {y_model.artifact_filename}")
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"   [FAIL] Yield training error: {exc}"))
                raise

        if model_type in ('all', 'clustering'):
            self.stdout.write(self.style.WARNING("\n2. Training District Agro-Ecological Typology Clusterer..."))
            try:
                c_model, dist_count = DistrictClusteringTrainer.train_and_register(version=version)
                self.stdout.write(self.style.SUCCESS(f"   [OK] Trained Model: {c_model.name} ({c_model.version})"))
                self.stdout.write(f"   • Algorithm: {c_model.algorithm}")
                self.stdout.write(f"   • Districts Assigned: {dist_count} of 30 districts")
                self.stdout.write(f"   • Clusters: 4 distinct policy & investment typologies")
                self.stdout.write(f"   • Artifact: {c_model.artifact_filename}")
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"   [FAIL] District clustering error: {exc}"))
                raise

        self.stdout.write(self.style.NOTICE("\n" + "=" * 65))
        self.stdout.write(self.style.SUCCESS("  ALL REQUESTED MODELS TRAINED & REGISTERED SUCCESSFULLY"))
        self.stdout.write(self.style.NOTICE("=" * 65))
