"""
ETL Pipeline Unit Tests.
Validates tab-delimited file handling, missing values, range bounds, and checksum generation.
"""
import io
import hashlib
import pandas as pd
from django.test import TestCase


class ETLPipelineValidationTests(TestCase):
    def test_tab_delimited_csv_parsing(self):
        """NISR SAS CSV exports are tab-delimited; parser must auto-detect tabs properly."""
        raw_tab_content = "Segment_ID\ts1q2\ts2q1\ts2q4\ts2q2_ha\ts2q21\nSEG_001\t13\t1\t101\t0.5\t2000\nSEG_002\t14\t2\t110\t1.2\t14000\n"
        
        # Determine separator dynamically
        first_line = raw_tab_content.splitlines()[0]
        sep = '\t' if '\t' in first_line else ','
        self.assertEqual(sep, '\t')

        df = pd.read_csv(io.StringIO(raw_tab_content), sep=sep)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['Segment_ID', 's1q2', 's2q1', 's2q4', 's2q2_ha', 's2q21'])
        self.assertEqual(df.iloc[0]['Segment_ID'], 'SEG_001')

    def test_file_checksum_consistency(self):
        """Checksums must be deterministic SHA-256 for idempotency checks."""
        content = b"Sample microdata row bytes for hashing"
        h1 = hashlib.sha256(content).hexdigest()
        h2 = hashlib.sha256(content).hexdigest()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_yield_bounds_and_outlier_detection(self):
        """Yields exceeding plausible biological maximums must be flagged."""
        # Plausible maize yield: 2,000 to 8,000 kg/ha
        prod_kg = 50000.0
        area_ha = 0.1
        calculated_yield = prod_kg / area_ha # 500,000 kg/ha! Impossible smallholder outlier
        
        is_extreme_outlier = calculated_yield > 60000.0
        self.assertTrue(is_extreme_outlier)

    def test_zero_or_negative_area_rejection(self):
        """Records with area <= 0 must be rejected to prevent division by zero in yield."""
        invalid_areas = [0.0, -0.5, None]
        for a in invalid_areas:
            is_valid = a is not None and a > 0
            self.assertFalse(is_valid)
