# ETL Pipeline Reconciliation & Batch Accounting Report

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Audit Milestone:** Milestone 2  
**Database:** PostgreSQL (`agrilens` on port 5439)  

---

## 1. Batch Ledger & Checksum Accounting

| Batch ID | Source File | Survey / Season | SHA-256 Checksum (First 16 chars) | Total Rows Read | Rows Accepted | Rows Rejected | Outlier Flags | Batch Status | Ingestion Start Timestamp |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | `Rwa_raw_SeasonA2025_Production.sav` | SAS 2025 Season A | `2d8cac7ad6dbd5fb` | 500 (Pilot) | 300 | 200 | 0 | `PARTIAL` | 2026-10-13 09:12 UTC |
| **#2** | `Rwa_raw_SeasonA2025_Production.sav` | SAS 2025 Season A | `2d8cac7ad6dbd5fb` | 500 (Pilot) | 500 | 0 | 4 | `SUCCESS` | 2026-10-13 09:35 UTC |
| **#3** | `Rwa_raw_SeasonA2025_Production.sav` | SAS 2025 Season A | `2d8cac7ad6dbd5fb` | 5,000 (Extended) | 5,000 | 0 | 5 | `SUCCESS` | 2026-10-13 10:25 UTC |
| **#4** | `Rwa_raw_SeasonA2024_Production.sav` | SAS 2024 Season A | `23060865a98074d2` | 5,000 (Extended) | 5,000 | 0 | 7 | `SUCCESS` | 2026-10-13 10:27 UTC |

---

## 2. Row Reconciliation & Duplication Analysis

### 2.1 Accounting Equation
$$\text{Total Staging Rows in DB} = 500 (\text{Batch 1}) + 500 (\text{Batch 2}) + 5,000 (\text{Batch 3}) + 5,000 (\text{Batch 4}) = \mathbf{11,000}$$
$$\text{Total Validated Rows in DB} = 300 (\text{Batch 1}) + 500 (\text{Batch 2}) + 5,000 (\text{Batch 3}) + 5,000 (\text{Batch 4}) = \mathbf{10,800}$$

### 2.2 Reconciled Observation Status
- **Unique Records:** **10,295** observations
- **Overlapping / Duplicate Records:** **505** observations
- **Breakdown by Provenance:**
  - `NISR_SAS_2024` (Season 2024A): Exactly **5,000** records (100% unique, zero duplicates).
  - `NISR_SAS_2025` (Season 2025A): **5,800** records (5,295 unique, 505 duplicated across Pilot Batch 2 and Extended Batch 3).

### 2.3 Detailed Duplicate Investigation
- **Evidence:** Query on `ValidatedObservation.objects.values('source_record_id').annotate(c=Count('id')).filter(c__gt=1)` yielded 505 duplicate keys.
- **Cause:**
  In `apps/data_management/management/commands/import_sas_production.py`:
  ```python
  source_record_id = f"{seg_id}_{plot_no}_{crop_name}_{idx}"
  ```
  Because Batch 2 read rows 0–499 and Batch 3 read rows 0–4,999 of the same file, index rows 0–499 were generated with identical `source_record_id`s. The `bulk_create` call lacked `ignore_conflicts=True` or an upsert/deduplication check against existing records in that season.
- **Impact:**
  - The duplicate rows belong to the same survey year and season (`2025A`).
  - While they represent authentic survey microdata, having the same 500 plots counted twice in Batch 2 and Batch 3 inflates the sample denominator by 500 rows.

---

## 3. Recommended Remediation & Idempotency Strategy

1. **Idempotent Ingestion Check:**
   Update `import_sas_production.py` to check for existing records matching `(provenance, season, source_record_id)` before insertion.
   If re-importing an existing file/season:
   - Option A: Skip already-imported records.
   - Option B: Atomically purge previous batches for that exact file/season before re-ingestion.
2. **Database Constraint:**
   Add a unique constraint on `ValidatedObservation`:
   ```python
   class Meta:
       constraints = [
           models.UniqueConstraint(
               fields=['provenance', 'season', 'source_record_id'],
               name='unique_observation_per_source'
           )
       ]
   ```
3. **Controlled Deduplication Approval:**
   In accordance with Critical Rule 7 & 8 ("Do not delete, truncate, reset, or overwrite existing data without approval"), no rows will be deleted from PostgreSQL without formal user authorization.
