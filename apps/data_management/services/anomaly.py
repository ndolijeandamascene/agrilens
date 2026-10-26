"""
AgriLens Multivariate Microdata Anomaly Detection Service.
Uses an unsupervised Isolation Forest trained on official microdata to detect
multivariate outliers, extreme agricultural misreporting, and potential enumerator errors.
"""
import logging
import math
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from apps.data_management.models import (
    ImportBatch,
    StagingSASProduction,
    ValidatedObservation,
    DataQualityIssue,
)

logger = logging.getLogger(__name__)


class MicrodataAnomalyDetector:
    """
    Unsupervised multivariate agricultural anomaly detection service.
    Detects irregular correlations between cultivated area, production, yield, and losses.
    """

    FEATURE_COLS = ['log_area', 'log_prod', 'yield_val', 'loss_rate']
    DEFAULT_CONTAMINATION = 0.015

    _model_cache: Optional[Tuple[IsolationForest, RobustScaler]] = None

    @classmethod
    def get_or_train_detector(cls, force_retrain: bool = False) -> Tuple[IsolationForest, RobustScaler]:
        """
        Retrieves in-memory fitted model or trains a new IsolationForest on verified microdata.
        """
        if cls._model_cache is not None and not force_retrain:
            return cls._model_cache

        qs = ValidatedObservation.objects.filter(
            provenance__startswith='NISR_',
            plot_area_ha__gt=0.001,
            total_production_kg__gte=0.0
        ).values('plot_area_ha', 'total_production_kg', 'calculated_yield_kg_per_ha', 'total_loss_kg')

        records = []
        for r in qs[:15000]:
            try:
                area = float(r['plot_area_ha'])
                prod = float(r['total_production_kg'])
                yield_v = float(r['calculated_yield_kg_per_ha'] or (prod / area if area > 0 else 0.0))
                loss = float(r['total_loss_kg'] or 0.0)
                tot = prod + loss
                loss_rate = (loss / tot * 100.0) if tot > 0 else 0.0

                # Log-transforms stabilize extreme agricultural skew
                log_area = math.log(max(area, 0.0001))
                log_prod = math.log(max(prod, 0.01) + 1.0)

                records.append([log_area, log_prod, yield_v, loss_rate])
            except (ValueError, TypeError, ZeroDivisionError):
                continue

        if len(records) < 50:
            # Fallback synthetic reference bounds if database is completely empty
            X = np.array([
                [math.log(0.2), math.log(500), 2500.0, 5.0],
                [math.log(0.5), math.log(1200), 2400.0, 8.0],
                [math.log(1.0), math.log(2500), 2500.0, 10.0],
                [math.log(2.0), math.log(5000), 2500.0, 6.0],
            ])
        else:
            X = np.array(records)

        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

        iso = IsolationForest(
            n_estimators=100,
            contamination=cls.DEFAULT_CONTAMINATION,
            random_state=42,
            n_jobs=-1
        )
        iso.fit(X_scaled)

        cls._model_cache = (iso, scaler)
        return cls._model_cache

    @classmethod
    def score_observation(
        cls,
        plot_area_ha: float,
        total_production_kg: float,
        calculated_yield_kg_per_ha: Optional[float] = None,
        total_loss_kg: float = 0.0,
        crop_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scores a single agricultural plot record for multivariate plausibility.
        Returns anomaly decision, anomaly score (lower is more anomalous), and flags.
        """
        flags = []
        is_hard_anomaly = False

        area = float(plot_area_ha or 0.0)
        prod = float(total_production_kg or 0.0)
        loss = float(total_loss_kg or 0.0)

        if calculated_yield_kg_per_ha is not None:
            yield_val = float(calculated_yield_kg_per_ha)
        else:
            yield_val = (prod / area) if area > 0 else 0.0

        tot = prod + loss
        loss_rate = (loss / tot * 100.0) if tot > 0 else 0.0

        # Deterministic domain sanity checks (hard agricultural rules)
        if area <= 0:
            flags.append("Invalid cultivated plot area (must be > 0 ha).")
            is_hard_anomaly = True
        elif area > 100.0:
            flags.append(f"Unusually large smallholder plot area ({area:.2f} ha > 100 ha).")
            is_hard_anomaly = True

        if prod < 0:
            flags.append("Negative harvest production is logically impossible.")
            is_hard_anomaly = True

        if yield_val > 60000.0:
            flags.append(f"Biological impossibility: yield {yield_val:,.1f} kg/ha exceeds agronomic ceiling (60 t/ha).")
            is_hard_anomaly = True
        elif yield_val < 10.0 and prod > 0:
            flags.append(f"Severe sub-baseline yield ({yield_val:.1f} kg/ha).")

        if loss_rate > 90.0:
            flags.append(f"Extreme post-harvest loss rate ({loss_rate:.1f}%).")

        # Isolation Forest multivariate scoring
        iso, scaler = cls.get_or_train_detector()

        log_area = math.log(max(area, 0.0001))
        log_prod = math.log(max(prod, 0.01) + 1.0)
        features = np.array([[log_area, log_prod, yield_val, loss_rate]])

        try:
            feat_scaled = scaler.transform(features)
            raw_score = float(iso.decision_function(feat_scaled)[0])
            pred_label = int(iso.predict(feat_scaled)[0])  # -1 for anomaly, +1 for normal
            is_ml_anomaly = (pred_label == -1) or (raw_score < -0.15)
        except Exception as exc:
            logger.warning("Anomaly inference error: %s", exc)
            raw_score = 0.0
            is_ml_anomaly = False

        if is_ml_anomaly and not flags:
            flags.append(
                f"Multivariate outlier (score {raw_score:.3f}): unusual combination of area ({area} ha), "
                f"production ({prod} kg), and yield ({yield_val:.1f} kg/ha)."
            )

        is_anomaly = is_hard_anomaly or is_ml_anomaly

        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': round(raw_score, 4),
            'is_hard_violation': is_hard_anomaly,
            'is_ml_outlier': is_ml_anomaly,
            'reasons': flags,
            'metrics': {
                'plot_area_ha': area,
                'total_production_kg': prod,
                'calculated_yield_kg_per_ha': yield_val,
                'loss_rate_percentage': round(loss_rate, 2),
            }
        }

    @classmethod
    def scan_staging_batch(
        cls,
        batch: ImportBatch,
        auto_flag_issues: bool = True,
        max_records: int = 1000
    ) -> Dict[str, Any]:
        """
        Audits all records in StagingSASProduction for a given ImportBatch.
        Automatically logs DataQualityIssue rows for detected outliers.
        """
        staging_qs = StagingSASProduction.objects.filter(batch=batch)
        total_scanned = staging_qs.count()

        if total_scanned == 0:
            return {
                'batch_id': batch.id,
                'total_scanned': 0,
                'anomalies_detected': 0,
                'anomaly_rate_pct': 0.0,
                'flagged_records': []
            }

        flagged = []
        created_issues = 0

        for record in staging_qs[:max_records]:
            # s2q2_ha is plot area in hectares, fallback to s2q2 (sqm) / 10000
            area = float(record.s2q2_ha or 0.0)
            if area <= 0 and record.s2q2:
                area = float(record.s2q2) / 10000.0

            prod = float(record.s2q21 or 0.0)
            loss_total = sum(filter(None, [
                record.loss_harvest_kg,
                record.loss_transport_kg,
                record.loss_storage_kg,
                record.loss_processing_kg,
                record.loss_sales_kg,
            ]))

            res = cls.score_observation(
                plot_area_ha=area,
                total_production_kg=prod,
                total_loss_kg=loss_total,
                crop_name=record.s2q4
            )

            if res['is_anomaly']:
                rec_id = f"Segment {record.segment_id} / Plot {record.s2q4}"
                reasons_text = "; ".join(res['reasons'])
                flagged.append({
                    'staging_id': record.id,
                    'segment_id': record.segment_id,
                    'crop_code': record.s2q4,
                    'anomaly_score': res['anomaly_score'],
                    'reasons': res['reasons'],
                })

                if auto_flag_issues:
                    severity = (
                        DataQualityIssue.Severity.CRITICAL
                        if res['is_hard_violation']
                        else DataQualityIssue.Severity.HIGH
                    )
                    DataQualityIssue.objects.create(
                        batch=batch,
                        dataset_name=batch.source.name if batch.source else "SAS Import Batch",
                        variable_name="s2q8_area_s2q21_prod",
                        record_reference=rec_id[:120],
                        issue_type="MULTIVARIATE_ANOMALY",
                        severity=severity,
                        description=f"Isolation Forest flagged observation: {reasons_text}",
                        recommended_action="Review enumerator questionnaire for data entry typographical errors or plot mismeasurement.",
                        is_resolved=False,
                    )
                    created_issues += 1

        rate = (len(flagged) / min(total_scanned, max_records)) * 100.0 if total_scanned > 0 else 0.0

        return {
            'batch_id': batch.id,
            'total_scanned': min(total_scanned, max_records),
            'total_available': total_scanned,
            'anomalies_detected': len(flagged),
            'anomaly_rate_pct': round(rate, 2),
            'issues_logged_to_db': created_issues,
            'flagged_records': flagged[:25],
        }
