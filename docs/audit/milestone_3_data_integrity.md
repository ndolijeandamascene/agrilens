# AgriLens Milestone 3: Data Integrity, Survey Weights, and Agricultural Indicator Validation Report

**Project:** AgriLens — "See Agriculture Through Data"  
**Hackathon:** 2026 NISR Big Data Hackathon (Track 1: Agricultural Productivity)  
**Role:** Senior Agricultural Statistician, NISR Survey-Data Specialist, Django/PostgreSQL Data Engineer & ETL Integrity Auditor  
**Date:** October 2026  
**Status:** COMPLETE AUDIT REPORT (Read-Only Inspection Concluded; Awaiting User Approval for Data Remediation)

---

## 1. Executive Summary & Verification of Prior Claims

The preceding post-upgrade acceptance audit stated several claims regarding data volumes, survey weights, variable mappings, and test coverage. Milestone 3 verified these claims against empirical reality in PostgreSQL and the original NISR SPSS (`.sav`) microdata files:

```
+---------------------------------------------------------------------------------------------------------------------------+
| Prior Audit Claim               | Empirical Reality (Verified)                                  | Status                  |
+---------------------------------------------------------------------------------------------------------------------------+
| 10,800 validated observations   | Verified exactly: 10,800 rows across Batches 1, 2, 3, 4.       | CONFIRMED               |
| 5,000 in 2024A; 5,800 in 2025A  | Verified: Batch 4 = 5,000; Batches 1, 2, 3 = 5,800.           | CONFIRMED               |
| 500 duplicates across B1, B2, B3| In reality, 800 redundant rows exist (B1=300, B2=500 in B3).   | REFUSED / CORRECTED     |
| 35.2% have weight = 1.0         | Verified: exactly 3,799 / 10,800 (35.18%). All Stratum 90.     | EXPLAINED / CONFIRMED   |
| Missing/default weights         | 0% missing in raw files. 100% of 1.0 weights are genuine LSF.   | REFUTED / CLARIFIED     |
| Irrigation/mech/erosion unmapped| Variables exist in Section 4 of raw SPSS, but unextracted in DB| VERIFIED & MAPPED       |
| Test suite passes 32 tests      | 32/32 tests pass in 17.08s against isolated test database.     | CONFIRMED               |
+---------------------------------------------------------------------------------------------------------------------------+
```

---

## 2. Phase 1: Record & Batch Reconciliation

### 2.1 The Reconciliation Table

| Dataset | Batch ID | Source Filename | SHA-256 Checksum | Source Rows Available | Staged Rows | Validated Rows | Unique Natural Records | Duplicate Redundant Rows | Rejected Rows | Batch Status |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| **SAS 2025A** | 1 | `Rwa_raw_SeasonA2025_Production.sav` | `2d8cac7ad6...` | 34,369 | 500 | 300 | 0 *(in B3)* | 300 | 200 | Superseded |
| **SAS 2025A** | 2 | `Rwa_raw_SeasonA2025_Production.sav` | `2d8cac7ad6...` | 34,369 | 500 | 500 | 0 *(in B3)* | 500 | 0 | Superseded |
| **SAS 2025A** | 3 | `Rwa_raw_SeasonA2025_Production.sav` | `2d8cac7ad6...` | 34,369 | 5,000 | 5,000 | 4,999 | 0 | 0 | **Authoritative (2025A)** |
| **SAS 2024A** | 4 | `Rwa_raw_SeasonA2024_Production.sav` | `23060865a9...` | 39,330 | 5,000 | 5,000 | 5,000 | 0 | 0 | **Authoritative (2024A)** |
| **TOTAL** | — | — | — | **73,699** | **11,000** | **10,800** | **9,999** | **800** | **200** | — |

### 2.2 Proof of Redundancy
- Checksums of source files for Batches 1, 2, and 3 are bit-for-bit identical (`2d8cac7ad6dbce0a8309990520633b490f4db239fe24d86927bf3426743cb8d2`).
- 100% of validated records in Batch 1 (300/300) match records in Batch 3.
- 100% of validated records in Batch 2 (500/500) match records in Batch 3.
- Batch 3 represents the authoritative 5,000-observation record set for 2025A. Batch 4 represents the authoritative 5,000-observation record set for 2024A.
- Total redundant rows currently stored in PostgreSQL: **exactly 800 rows**.

---

## 3. Phase 2: Survey Weight Audit Findings

### 3.1 The Truth Behind the 35.2% Weights of 1.0
1. **Zero Missing Weights in Source Data:** Both `Rwa_raw_SeasonA2024_Production.sav` and `Rwa_raw_SeasonA2025_Production.sav` contain **zero NaN or missing values** in `plot_weight`.
2. **Stratum 90 Complete Census Enumeration:** In official NISR survey design, Stratum 90 (`s1q3 == 90.0`, Farmer Types 3.0 and 4.0) consists of **Large-Scale Farmers (LSF)**. These commercial operators are completely enumerated ($P = 1.0$), so their official survey expansion weight is **genuinely 1.0**.
3. **Head Slicing Concentration Bias:** Because raw survey files sort Large Scale Farmers first, slicing `df.head(5000)` captured 100% of Rwanda's Large Scale Farmers (1,556 in 2024A; 1,443 in 2025A), while capturing only ~10% of smallholders.
4. **Duplicate Multiplication:** Batches 1 and 2 duplicated 800 of these LSF records. $(1,556 + 1,443 + 800) / 10,800 = 35.18\% \approx 35.2\%$.
5. **Verdict:** Not a single weight of 1.0 was an artificial fallback or missing-data guess. However, the pilot dataset has **selection bias toward Large Scale Farmers**. Full survey ingestion will restore national proportions (~4% LSF).

---

## 4. Phase 3: Variable Mapping Audit Findings

### 4.1 Resolution of Unmapped Agricultural Practices
1. **Section 4 Verification:** Anti-erosion (`s4q3`), mechanization (`s4q9`), and irrigation (`s4q14`/`s4q15`) **do exist** directly in `Production.sav` as well as in `Agricultural_practice.sav`.
2. **Current Database Values:** All 10,800 rows in `ValidatedObservation` currently show `False` because the pilot ETL command was executed before Section 4 variable mappings were wired into `ValidatedObservation` bulk inserts.
3. **Survey Questionnaire Shift (Gotcha):**
   - **2024:** Plot-level irrigation is `s4q15` (*"Has this plot been irrigated during this agricultural season?"*).
   - **2025:** Plot-level irrigation shifted to `s4q14` (*"Has this plot been irrigated during this agricultural season?"*).
   - Year-aware ETL mapping is mandatory to prevent cross-season variable inversion.
4. **Actual Adoption in Raw Source Data:**
   - Anti-erosion (`s4q3`): **75.6%** (2024A), **70.3%** (2025A).
   - Irrigation (`s4q15`/`s4q14`): **15.2%** (2024A), **25.5%** (2025A).
   - Mechanization (`s4q9`): **3.0%** (2024A), **4.0%** (2025A).

---

## 5. Phase 4: Indicator Formula Validation & Duplicate Impact

### 5.1 Impact of Duplicate Imports on Intelligence Indicators

| Indicator (2025A) | Current (Batches 1, 2, 3) | Authoritative (Batch 3 Only) | Distortion / Error |
|---|---:|---:|---:|
| **Sample Size (plots)** | 5,800 | 5,000 | **+800 plots (+16.0%)** |
| **Total Production (MT)** | 434,620.21 MT | 344,825.32 MT | **+89,795 MT (+26.0%)** |
| **Total Cultivated Area (ha)** | 221,755.21 ha | 197,564.06 ha | **+24,191 ha (+12.2%)** |
| **Weighted Yield (All Crops)** | 1,959.91 kg/ha | 1,745.38 kg/ha | **+214.53 kg/ha (+12.3%)** |
| **Maize Weighted Yield** | 1,483.86 kg/ha | 1,192.97 kg/ha | **+290.89 kg/ha (+24.4%)** |
| **Maize YOY Growth (2024A to 2025A)** | **+15.1%** | **-7.5%** | **Trend reversed by +22.6pp!** |
| **Improved Seed Adoption** | 31.2% | 26.3% | **+4.9 pp** |
| **Inorganic Fertilizer Adoption** | 36.6% | 32.1% | **+4.5 pp** |
| **Post-Harvest Loss Rate** | 2.16% | 2.20% | -0.04 pp |

### 5.2 Indicator Methodology Classification

```
+---------------------------------------------------------------------------------------------------------+
| Indicator                   | Mathematical Formula                | Weighting Status | Representativeness |
+---------------------------------------------------------------------------------------------------------+
| Crop Yield (kg/ha)          | sum(W*P) / sum(W*A)                 | Survey-Weighted  | Valid sample ratio |
| Post-Harvest Loss Rate (%)  | sum(W*L) / (sum(W*P) + sum(W*L))    | Survey-Weighted  | Valid sample ratio |
| Practice Adoption Rates (%) | Count(Practice=True) / Total Plots  | Unweighted       | Sample plots only  |
| Productivity Gap (%)        | (Yield_lag - Yield_bench) / Yield_b | Survey-Weighted  | Conditional (min_N)|
| Year-on-Year Growth (%)     | (Yield_2025 - Yield_2024) / Y_2024  | Survey-Weighted  | Valid once cleaned |
+---------------------------------------------------------------------------------------------------------+
```

---

## 6. Phase 5: Future Duplicate Prevention & Safe Idempotency Strategy

### 6.1 Natural Key Formulation
Our empirical analysis of all 73,699 raw records proved that the combination:
`['Segment_ID', 's2q1', 's2q4']` (Segment ID, Plot Number, Crop Code) is **100.0% globally unique** across both full survey datasets with zero collisions.

Appending the arbitrary row index `_{idx}` to `source_record_id` was the root flaw that allowed duplicate imports across varying slice limits.

### 6.2 Safe Idempotency Architecture
1. **Deterministic Natural Key:**
   ```python
   source_record_id = f"SAS_{year}{season}_{segment_id}_P{plot_no}_C{crop_code}"
   ```
2. **Database Constraint:**
   Add a unique constraint to `ValidatedObservation`:
   ```python
   models.UniqueConstraint(
       fields=['season', 'source_record_id'], 
       name='unique_season_source_record'
   )
   ```
3. **Idempotent Ingestion Rule:**
   `ValidatedObservation.objects.bulk_create(..., ignore_conflicts=True)` or set-filtering against `existing_keys` using the deterministic natural key.

---

## 7. Deliverables Index

The following detailed audit reports have been compiled in `docs/audit/`:
1. [Duplicate Import Remediation Plan](file:///c:/Users/ndoli/Documents/WEBAPP/agrilens/docs/audit/duplicate_import_remediation_plan.md)
2. [Survey Weight Validation & Statistical Analysis](file:///c:/Users/ndoli/Documents/WEBAPP/agrilens/docs/audit/survey_weight_validation.md)
3. [Variable Mapping Validation & Source Data Audit](file:///c:/Users/ndoli/Documents/WEBAPP/agrilens/docs/audit/variable_mapping_validation.md)
4. [Agricultural Indicator Methodology & Formula Validation](file:///c:/Users/ndoli/Documents/WEBAPP/agrilens/docs/audit/indicator_methodology_validation.md)
5. [Milestone 3 Data Integrity Master Report](file:///c:/Users/ndoli/Documents/WEBAPP/agrilens/docs/audit/milestone_3_data_integrity.md)

---

## 8. Post-Remediation Execution & Production Verification

Following user authorization of Option A, the remediation script and database migration were executed in a controlled maintenance window on October 13, 2026:

1. **Atomic Transaction Execution:**
   `python scripts/remediation_atomic_reconcile.py --commit`
   - Preconditions verified: Batches 1 & 2 confirmed 100% redundant against Batch 3.
   - Deleted validated rows: Exactly 800 rows (`ValidatedObservation`).
   - Deleted staging rows: Exactly 1,000 rows (`StagingSASProduction`).
   - Batches 1 & 2 metadata updated: Status set to `PARTIAL`, marked superseded by Batch 3, `rows_skipped` set to 300 and 500 respectively.
   - Transaction committed successfully.
2. **Database Migration Applied:**
   `python manage.py migrate data_management`
   - Migration `0003_validatedobservation_unique_season_source_record` applied: **OK**.
   - PostgreSQL unique constraint `unique_season_source_record` successfully created on `ValidatedObservation (season_id, source_record_id)`.
3. **Database Constraint Verified:**
   - Attempted inserting an exact duplicate `(season, source_record_id)`.
   - PostgreSQL immediately aborted the insert with: `IntegrityError: duplicate key value violates unique constraint "unique_season_source_record"`.
4. **Final Database Counts:**
   - `ValidatedObservation`: Exactly **10,000 records** (Batch 3: 5,000; Batch 4: 5,000; Batches 1 & 2: 0).
   - `StagingSASProduction`: Exactly **10,000 records** (Batch 3: 5,000; Batch 4: 5,000; Batches 1 & 2: 0).
   - `ImportBatch`: Exactly **4 records** (Preserved; Batches 1 & 2 marked superseded).
5. **Recalculated Agricultural Indicators:**
   - 2025A Total Production: **344,825.32 MT** (corrected from 434,620.21 MT).
   - 2025A Cultivated Area: **197,564.06 ha** (corrected from 221,755.21 ha).
   - 2025A Weighted Yield: **1,745.38 kg/ha** (corrected from 1,959.91 kg/ha).
   - Maize Year-over-Year Growth (2024A to 2025A): **-7.5%** (corrected from distorted +15.1%).
   - Post-Harvest Loss Rate: **2.20%**.
   - Practice Availability: Explicit status badge *"Pending Re-import"* rendered for unmapped pilot variables.
6. **Automated Test Suite Verification:**
   - Complete project test suite: **41/41 tests passed** (`Ran 41 tests in 19.156s - OK`).
   - Zero test regressions or unexpected conflicts.
