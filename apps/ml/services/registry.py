"""
AgriLens Model Registry & Artifact Storage Service.
Provides thread-safe persistence, caching, and retrieval of trained model artifacts.
"""
import os
import logging
from pathlib import Path
import joblib
from django.conf import settings
from apps.ml.models import MLModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Thread-safe model registry managing artifact persistence and in-memory serving cache."""

    _model_cache = {}

    @classmethod
    def get_storage_dir(cls) -> Path:
        """Returns the configured model directory, ensuring it exists."""
        storage_dir = getattr(settings, 'ML_MODEL_DIR', settings.BASE_DIR / 'data' / 'models')
        os.makedirs(storage_dir, exist_ok=True)
        return Path(storage_dir)

    @classmethod
    def save_artifact(cls, artifact, filename: str) -> str:
        """Serializes a trained model pipeline to disk using joblib."""
        storage_dir = cls.get_storage_dir()
        dest_path = storage_dir / filename
        joblib.dump(artifact, dest_path, compress=3)
        logger.info("Saved ML model artifact to %s", dest_path)
        # Invalidate cache for this filename
        cls._model_cache.pop(filename, None)
        return filename

    @classmethod
    def load_artifact(cls, filename: str):
        """Loads a model artifact from disk with in-memory caching."""
        if not filename:
            return None
        if filename in cls._model_cache:
            return cls._model_cache[filename]

        storage_dir = cls.get_storage_dir()
        target_path = storage_dir / filename

        if not target_path.exists():
            logger.warning("Model artifact not found on disk: %s", target_path)
            return None

        try:
            artifact = joblib.load(target_path)
            cls._model_cache[filename] = artifact
            return artifact
        except Exception as exc:
            logger.error("Failed to load model artifact %s: %s", filename, exc)
            return None

    @classmethod
    def get_active_model_record(cls, model_type: str):
        """Retrieves active model metadata record from the database."""
        return MLModel.objects.filter(
            model_type=model_type,
            is_active=True,
            status=MLModel.Status.ACTIVE
        ).order_by('-created_at').first()

    @classmethod
    def get_active_pipeline(cls, model_type: str):
        """Retrieves active model record and its instantiated scikit-learn pipeline."""
        record = cls.get_active_model_record(model_type)
        if not record or not record.artifact_filename:
            return None, None
        pipeline = cls.load_artifact(record.artifact_filename)
        return record, pipeline

    @classmethod
    def save_model_artifact(cls, artifact, filename: str) -> str:
        """Alias for save_artifact."""
        cls.save_artifact(artifact, filename)
        return str(cls.get_storage_dir() / filename)

    @classmethod
    def load_model_artifact(cls, filename: str):
        """Alias for load_artifact."""
        return cls.load_artifact(filename)

    @classmethod
    def load_active_model(cls, model_type: str):
        """Alias for get_active_pipeline."""
        return cls.get_active_pipeline(model_type)

    @classmethod
    def register_model(cls, name, model_type, version, algorithm, features, target, metrics, artifact_filename, notes=""):
        """Registers a model metadata record in the database."""
        return MLModel.objects.create(
            name=name,
            model_type=model_type,
            version=version,
            algorithm=algorithm,
            feature_names=features,
            target_variable=target,
            metrics=metrics,
            artifact_filename=artifact_filename,
            status=MLModel.Status.TRAINED,
            is_active=False,
            training_notes=notes
        )

    @classmethod
    def clear_cache(cls):
        """Clears the in-memory artifact cache."""
        cls._model_cache.clear()

