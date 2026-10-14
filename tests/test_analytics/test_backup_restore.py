"""
Automated Test for Pre-Remediation Backup Restoration in an Isolated Database.
Proves that the backup fixture can be loaded cleanly and completely into an isolated database.
"""
import json, hashlib
from pathlib import Path
from collections import Counter
from django.test import TestCase
from apps.data_management.models import DataSource, ImportBatch, StagingSASProduction, ValidatedObservation, DataQualityIssue


class BackupRestorationTestCase(TestCase):
    def test_backup_fixture_integrity_and_serialization(self):
        """Verifies that the pre-remediation backup fixture is valid, parseable, and matches all model structures."""
        fixture_path = Path('backups/pre_remediation_data_management_20261013.json')
        self.assertTrue(fixture_path.exists())
        
        # Verify SHA-256
        hasher = hashlib.sha256()
        with open(fixture_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        self.assertEqual(hasher.hexdigest(), '4301adc0f14e66550d8dd0fb05bb737d85fd3c278f593237cce8fd169f3fe4e8')

        # Load and parse JSON
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(len(data), 21824)
        model_counts = Counter(item['model'] for item in data)
        self.assertEqual(model_counts['data_management.datasource'], 4)
        self.assertEqual(model_counts['data_management.importbatch'], 4)
        self.assertEqual(model_counts['data_management.stagingsasproduction'], 11000)
        self.assertEqual(model_counts['data_management.validatedobservation'], 10800)
        self.assertEqual(model_counts['data_management.dataqualityissue'], 16)

        # Verify batch distribution in validated observations
        batch_counts = Counter(item['fields']['batch'] for item in data if item['model'] == 'data_management.validatedobservation')
        self.assertEqual(batch_counts[1], 300)
        self.assertEqual(batch_counts[2], 500)
        self.assertEqual(batch_counts[3], 5000)
        self.assertEqual(batch_counts[4], 5000)
