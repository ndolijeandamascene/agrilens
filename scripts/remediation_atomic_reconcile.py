"""
AgriLens Atomic Production Remediation Script.
Supports --dry-run (default) and --commit.
Executes Option A under strict transactional boundaries with exhaustive pre- and post-condition assertions.
"""
import os, sys, django
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.data_management.models import ImportBatch, StagingSASProduction, ValidatedObservation


class RemediationError(Exception):
    pass


def run_remediation(commit=False):
    print("=" * 70)
    print(f"AGRILENS PRODUCTION DATA REMEDIATION (Commit Mode: {commit})")
    print("=" * 70)

    with transaction.atomic():
        # --- 1. PRECONDITION VERIFICATION ---
        print("\n[Step 1/5] Verifying Preconditions...")
        b1_val_cnt = ValidatedObservation.objects.filter(batch_id=1).count()
        b2_val_cnt = ValidatedObservation.objects.filter(batch_id=2).count()
        b3_val_cnt = ValidatedObservation.objects.filter(batch_id=3).count()
        b4_val_cnt = ValidatedObservation.objects.filter(batch_id=4).count()

        b1_stg_cnt = StagingSASProduction.objects.filter(batch_id=1).count()
        b2_stg_cnt = StagingSASProduction.objects.filter(batch_id=2).count()
        b3_stg_cnt = StagingSASProduction.objects.filter(batch_id=3).count()
        b4_stg_cnt = StagingSASProduction.objects.filter(batch_id=4).count()

        print(f"  Validated observations: B1={b1_val_cnt}, B2={b2_val_cnt}, B3={b3_val_cnt}, B4={b4_val_cnt}")
        print(f"  Staging records:        B1={b1_stg_cnt}, B2={b2_stg_cnt}, B3={b3_stg_cnt}, B4={b4_stg_cnt}")

        if b1_val_cnt != 300:
            raise RemediationError(f"Precondition failed: Batch 1 has {b1_val_cnt} validated rows (expected 300).")
        if b2_val_cnt != 500:
            raise RemediationError(f"Precondition failed: Batch 2 has {b2_val_cnt} validated rows (expected 500).")
        if b3_val_cnt != 5000:
            raise RemediationError(f"Precondition failed: Batch 3 has {b3_val_cnt} validated rows (expected 5000).")
        if b4_val_cnt != 5000:
            raise RemediationError(f"Precondition failed: Batch 4 has {b4_val_cnt} validated rows (expected 5000).")
        if b1_stg_cnt != 500 or b2_stg_cnt != 500 or b3_stg_cnt != 5000 or b4_stg_cnt != 5000:
            raise RemediationError("Precondition failed: Staging counts do not match expected 500, 500, 5000, 5000.")

        # Verify redundancy against Batch 3
        b3_src_ids = set(ValidatedObservation.objects.filter(batch_id=3).values_list('source_record_id', flat=True))
        b1_src_ids = set(ValidatedObservation.objects.filter(batch_id=1).values_list('source_record_id', flat=True))
        b2_src_ids = set(ValidatedObservation.objects.filter(batch_id=2).values_list('source_record_id', flat=True))

        if not b1_src_ids.issubset(b3_src_ids):
            missing = len(b1_src_ids - b3_src_ids)
            raise RemediationError(f"Precondition failed: {missing} records in Batch 1 are NOT present in Batch 3.")
        if not b2_src_ids.issubset(b3_src_ids):
            missing = len(b2_src_ids - b3_src_ids)
            raise RemediationError(f"Precondition failed: {missing} records in Batch 2 are NOT present in Batch 3.")

        print("  All preconditions SATISFIED. 100% of Batches 1 & 2 are verified redundant in Batch 3.")

        # --- 2. DELETION OF REDUNDANT VALIDATED OBSERVATIONS ---
        print("\n[Step 2/5] Deleting Redundant Validated Observations...")
        val_del_count, val_del_details = ValidatedObservation.objects.filter(batch_id__in=[1, 2]).delete()
        print(f"  Deleted validated rows: {val_del_count} (Expected: 800)")
        if val_del_count != 800:
            raise RemediationError(f"Deletion mismatch: deleted {val_del_count} validated rows (expected 800).")

        # --- 3. DELETION OF REDUNDANT STAGING RECORDS ---
        print("\n[Step 3/5] Deleting Obsolete Pilot Staging Records...")
        stg_del_count, stg_del_details = StagingSASProduction.objects.filter(batch_id__in=[1, 2]).delete()
        print(f"  Deleted staging rows: {stg_del_count} (Expected: 1,000)")
        if stg_del_count != 1000:
            raise RemediationError(f"Deletion mismatch: deleted {stg_del_count} staging rows (expected 1000).")

        # --- 4. UPDATE IMPORT BATCH METADATA ---
        print("\n[Step 4/5] Updating ImportBatch Metadata...")
        ImportBatch.objects.filter(id=1).update(
            status=ImportBatch.Status.PARTIAL,
            rows_skipped=300,
            summary_notes="SUPERSEDED: Pilot batch records removed during Milestone 3 reconciliation. Authoritative data resides in Batch #3. Original import: 500 staged, 300 accepted, 200 rejected."
        )
        ImportBatch.objects.filter(id=2).update(
            status=ImportBatch.Status.PARTIAL,
            rows_skipped=500,
            summary_notes="SUPERSEDED: Pilot batch records removed during Milestone 3 reconciliation. Authoritative data resides in Batch #3. Original import: 500 staged, 500 accepted."
        )
        print("  Batch #1 and #2 marked as superseded using supported Status.PARTIAL and rows_skipped.")

        # --- 5. POST-CONDITION VERIFICATION ---
        print("\n[Step 5/5] Verifying Post-Remediation Database Integrity...")
        final_val_total = ValidatedObservation.objects.count()
        final_val_b3 = ValidatedObservation.objects.filter(batch_id=3).count()
        final_val_b4 = ValidatedObservation.objects.filter(batch_id=4).count()

        final_stg_total = StagingSASProduction.objects.count()
        final_stg_b3 = StagingSASProduction.objects.filter(batch_id=3).count()
        final_stg_b4 = StagingSASProduction.objects.filter(batch_id=4).count()

        print(f"  Final Validated Observations: Total={final_val_total} (B3={final_val_b3}, B4={final_val_b4})")
        print(f"  Final Staging Records:        Total={final_stg_total} (B3={final_stg_b3}, B4={final_stg_b4})")

        if final_val_total != 10000:
            raise RemediationError(f"Postcondition failed: Validated total is {final_val_total} (expected 10000).")
        if final_val_b3 != 5000 or final_val_b4 != 5000:
            raise RemediationError(f"Postcondition failed: B3={final_val_b3}, B4={final_val_b4} (expected 5000 each).")
        if final_stg_total != 10000:
            raise RemediationError(f"Postcondition failed: Staging total is {final_stg_total} (expected 10000).")

        # Uniqueness check
        distinct_val_keys = ValidatedObservation.objects.values('season_id', 'source_record_id').distinct().count()
        if distinct_val_keys != 10000:
            raise RemediationError(f"Postcondition failed: Distinct (season, source_record_id) is {distinct_val_keys} (expected 10000).")

        print("  All post-conditions SATISFIED: Database is 100% clean and reconciled.")

        if not commit:
            print("\n[DRY RUN] Aborting transaction (rollback). No changes written to database.")
            transaction.set_rollback(True)
        else:
            print("\n[COMMIT] Transaction committed successfully to database.")

    print("=" * 70)


if __name__ == '__main__':
    commit_flag = '--commit' in sys.argv
    run_remediation(commit=commit_flag)
