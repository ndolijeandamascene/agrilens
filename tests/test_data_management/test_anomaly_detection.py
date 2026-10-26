"""
Tests for Microdata Multivariate Anomaly Detection Service
"""
import pytest
from apps.data_management.services.anomaly import MicrodataAnomalyDetector
from apps.data_management.models import ImportBatch, DataSource, StagingSASProduction, DataQualityIssue


@pytest.mark.django_db
class TestMicrodataAnomalyDetector:
    def test_score_normal_observation(self):
        # 0.5 ha, 1,500 kg -> 3,000 kg/ha (standard Maize yield in Rwanda)
        result = MicrodataAnomalyDetector.score_observation(
            plot_area_ha=0.5,
            total_production_kg=1500.0,
            calculated_yield_kg_per_ha=3000.0,
            total_loss_kg=50.0
        )
        assert result['is_hard_violation'] is False
        assert result['metrics']['calculated_yield_kg_per_ha'] == 3000.0
        assert len(result['reasons']) == 0 or result['anomaly_score'] > -0.2

    def test_score_impossible_agronomic_yield(self):
        # 0.1 ha, 20,000 kg -> 200,000 kg/ha (impossible biological anomaly)
        result = MicrodataAnomalyDetector.score_observation(
            plot_area_ha=0.1,
            total_production_kg=20000.0,
            calculated_yield_kg_per_ha=200000.0,
            total_loss_kg=0.0
        )
        assert result['is_anomaly'] is True
        assert result['is_hard_violation'] is True
        assert any("biological impossibility" in r.lower() for r in result['reasons'])

    def test_score_negative_production(self):
        result = MicrodataAnomalyDetector.score_observation(
            plot_area_ha=1.0,
            total_production_kg=-500.0,
            calculated_yield_kg_per_ha=-500.0
        )
        assert result['is_anomaly'] is True
        assert result['is_hard_violation'] is True
        assert any("negative harvest" in r.lower() for r in result['reasons'])

    def test_score_zero_area(self):
        result = MicrodataAnomalyDetector.score_observation(
            plot_area_ha=0.0,
            total_production_kg=100.0
        )
        assert result['is_anomaly'] is True
        assert result['is_hard_violation'] is True
        assert any("invalid cultivated plot area" in r.lower() for r in result['reasons'])

    def test_scan_staging_batch_creates_quality_issues(self):
        ds = DataSource.objects.create(
            name="Test SAS Data Source",
            source_type="TEST_SAS_SOURCE",
            data_kind=DataSource.DataKind.SURVEY,
            year=2025,
            season="A"
        )
        batch = ImportBatch.objects.create(
            source=ds,
            filename="test_sas.sav",
            total_rows=2
        )
        # Create normal staging row
        StagingSASProduction.objects.create(
            batch=batch,
            source_row_index=1,
            segment_id="SEG001",
            s2q4="Maize",
            s2q2_ha=0.5,
            s2q21=1200.0
        )
        # Create anomalous staging row (extreme yield: 0.01 ha with 5,000 kg = 500,000 kg/ha)
        StagingSASProduction.objects.create(
            batch=batch,
            source_row_index=2,
            segment_id="SEG002",
            s2q4="Maize",
            s2q2_ha=0.01,
            s2q21=5000.0
        )

        scan_res = MicrodataAnomalyDetector.scan_staging_batch(batch=batch, auto_flag_issues=True)

        assert scan_res['total_scanned'] == 2
        assert scan_res['anomalies_detected'] >= 1
        assert DataQualityIssue.objects.filter(batch=batch, issue_type="MULTIVARIATE_ANOMALY").exists()
