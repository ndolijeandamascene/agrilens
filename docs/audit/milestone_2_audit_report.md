# AgriLens Milestone 2: Comprehensive Technical Audit Report

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Audit Scope:** Data Integrity, Statistical Validation, Security, and Production Readiness  
**Hackathon Track:** NISR 2026 Big Data Hackathon — Track 1: Agricultural Productivity  
**Audit Date:** October 2026  
**Auditor:** Senior Django Architect, PostgreSQL Engineer & Agricultural Statistician  
**Overall Status:** **Ready with Documented Limitations & Verified Findings**  

---

## 1. Executive Summary & Verification Baseline

This audit independently inspects, validates, and tests the actual implementation of AgriLens against all claims from Milestone 1, the Master Prompt requirements, and the NISR microdata reality.

### 1.1 Summary of Core Verified Facts
- **Configuration:** Centralized `config/settings.py` configured via `django-environ` reading `.env`. Automated test suite uses isolated in-memory SQLite and executes in **2.57 seconds** without network latency or production database pollution.
- **Authoritative Geography:** Verified in PostgreSQL: **5 Provinces**, **30 Districts** (official NISR 2-digit codes `11` to `57`), **416 Sectors**, **7 Agricultural Seasons** (2024A–2026A).
- **Priority Crops:** **10 Priority Crops** verified in PostgreSQL (Milestone 1 claimed 13; 3 were non-priority in the seed definition).
- **PostgreSQL Database Records:** Total **10,800 validated observation records** across 4 import batches (5,000 in SAS 2024A; 5,800 in SAS 2025A).
- **Testing:** 12 automated tests in `tests/test_apps/` and `tests/test_etl/` pass cleanly (`12 passed in 2.6s`).

---

## 2. Evidence-Based Audit Findings Table

| ID | Severity | Component | Finding | Evidence | Impact | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AUD-01** | **High** | ETL Pipeline (`import_sas_production.py`) | **Duplicate Records & Non-Idempotent Ingestion:** Re-running imports on the same file silently duplicates rows in `ValidatedObservation`. | 505 duplicate `source_record_id`s found in DB across Batches 1, 2, and 3 (`Rwa_raw_SeasonA2025_Production.sav`). | Inflates total observation count (5,800 vs. 5,000 unique rows) and skews unweighted indicators. | Add uniqueness constraint / deduplication logic checking `(provenance, season, source_record_id)` before insertion. |
| **AUD-02** | **High** | ETL Pipeline (`import_sas_production.py`) | **Omitted Practice Variables (Irrigation, Mechanization, Anti-Erosion):** Plot-level irrigation (`s4q14`/`s4q15`), mechanization (`s4q9`), and anti-erosion (`s4q3`) were not mapped during load, defaulting to `False`. | `Production.sav` contains columns `s4q14`, `s4q3`, `s4q9`, but lines 290–313 of `import_sas_production.py` omit them. | National irrigation and mechanization adoption rates calculate as `0.0%` in dynamic queries. | Update import command to map `s4q14` (2025) / `s4q15` (2024), `s4q3`, and `s4q9`. |
| **AUD-03** | **High** | Indicator Service (`apps/indicators/services.py`) | **Unweighted Yield in District Rankings:** `get_district_rankings()` calculates unweighted average yield: `Sum(Prod)/Sum(Area)` without applying `sampling_weight`. | Lines 129–142 of `apps/indicators/services.py` use `Sum('total_production_kg')` instead of weighted expression. | Inconsistent with `get_national_summary()`, which applies `sampling_weight`. Distorts ranking in strata with varying sampling fractions. | Standardize `get_district_rankings()` to compute survey-weighted average yield: $\frac{\sum (W \times P)}{\sum (W \times A)}$. |
| **AUD-04** | **High** | Indicator Service (`apps/indicators/services.py`) | **Crop Filter Ignored in YoY Comparison:** `get_year_over_year_comparison(crop_name=...)` does not pass `crop_name` to `get_national_summary()`. | Lines 196–197 of `apps/indicators/services.py` call `get_national_summary(year=...)` without `crop_name`. | Compares national all-crops aggregate yield between 2024 and 2025, but mislabels it as the growth rate for the specified crop (e.g. Maize). | Add `crop_name` filter parameter to `get_national_summary()` so crop-specific YoY growth is statistically authentic. |
| **AUD-05** | **Critical** | Security & Auth (`apps/data_management/views.py`) | **Missing Authentication & Role Enforcement:** Manual data entry and review endpoints allow anonymous users to submit and approve records. | Lines 93 & 171 of `views.py` use `get_default_user()` if unauthenticated; no `@login_required` or role checks. | Any unauthenticated web visitor can submit drafts, edit entries, and approve records as `admin_officer`. | Add `@login_required` and role-based permissions (`User.Role.ANALYST` or `ADMIN` required for review). |
| **AUD-06** | **Medium** | Settings (`config/settings.py`) | **Wildcard Allowed Hosts in Production Mode:** When `DEBUG = False`, `ALLOWED_HOSTS` defaults to `['*']`. | Line 33 of `config/settings.py`: `default=['localhost', ...] if DEBUG else ['*']`. | Increases host header poisoning risk if `.env` does not explicitly set `ALLOWED_HOSTS`. | Enforce strict `ALLOWED_HOSTS` in production without wildcard fallback. |
| **AUD-07** | **Medium** | Indicators & UI (`apps/indicators/services.py`) | **No Minimum Sample Threshold for Benchmark Selection:** Districts with as few as 1 plot can become the national #1 benchmark. | Line 126 of `services.py` ranks any district where `plot_count > 0`. | An unrepresentative micro-plot outlier could distort the national productivity gap analysis. | Enforce minimum threshold (e.g., $\ge 5$ plots) for a district to qualify as a benchmark. |
| **AUD-08** | **Verified** | Architecture & Models (`apps/data_management/models.py`) | **Strict Provenance Isolation Verified:** Manual entries remain strictly quarantined in `ManualObservation`. | Queries in `IndicatorService` filter by `provenance__startswith='NISR_'` by default. | Manual records cannot silently enter official NISR indicators without explicit user toggle. | Preserved. |
| **AUD-09** | **Verified** | Reference Geography (`apps/geography/models.py`) | **Official Administrative Hierarchy Verified:** 5 Provinces, 30 Districts, 416 Sectors match NISR gazetteer. | Query verified: 5 provinces, 30 districts (codes 11–57), 416 sectors linked properly. | High spatial integrity for maps, drill-downs, and forms. | Preserved. |
| **AUD-10** | **Verified** | Data Quality (`docs/data_quality_report.md`) | **Plausibility QA Outlier Flagging:** Outliers $> 60,000\text{ kg/ha}$ logged into `DataQualityIssue`. | 16 medium-severity QA outlier records logged in database. | Prevents biological impossibilities from going unnoticed. | Preserved. |

---

## 3. Data Integrity & Ingestion Reconciliation

### 3.1 Import Batches Detailed Breakdown
1. **Batch #1 (`Rwa_raw_SeasonA2025_Production.sav`):**
   - Rows Processed: 500 (Pilot limit)
   - Rows Accepted: 300 | Rejected: 200 (Initial strict filter before dynamic crop mapping)
   - Checksum: `2d8cac7ad6dbd5fbb59d3d92257f0d0cb748a313e2f5b5f8841da3671fb2b9d0`
2. **Batch #2 (`Rwa_raw_SeasonA2025_Production.sav`):**
   - Rows Processed: 500 (Pilot limit with full SPSS value label resolution)
   - Rows Accepted: 500 | Rejected: 0
   - Checksum: `2d8cac7ad6dbd5fbb59d3d92257f0d0cb748a313e2f5b5f8841da3671fb2b9d0`
3. **Batch #3 (`Rwa_raw_SeasonA2025_Production.sav`):**
   - Rows Processed: 5,000 (Extended limit)
   - Rows Accepted: 5,000 | Rejected: 0
   - Checksum: `2d8cac7ad6dbd5fbb59d3d92257f0d0cb748a313e2f5b5f8841da3671fb2b9d0`
4. **Batch #4 (`Rwa_raw_SeasonA2024_Production.sav`):**
   - Rows Processed: 5,000 (Extended limit)
   - Rows Accepted: 5,000 | Rejected: 0
   - Checksum: `23060865a98074d2b27bcfaef837016335123d47ad0e2cbe82baae82d1c68f70`

### 3.2 Reconciliation Status
- Total Rows Read: 11,000
- Staging Records Created: 11,000
- Validated Domain Records: 10,800
- **Duplicate Records in DB:** 505 rows (from overlapping Pilot Batch 2 and Extended Batch 3).
- **Unique Records in DB:** 10,295 unique observations across SAS 2024A and SAS 2025A.
- **Root Cause:** Absence of deduplication key check on `(provenance, season, source_record_id)` in `bulk_create`.
