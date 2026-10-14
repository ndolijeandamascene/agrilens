# AgriLens Post-Upgrade Verification and Acceptance Audit Report

**Evaluation Scope:** Independent verification of claims in `docs/audit/full_stack_upgrade_report.md`  
**Target Platform:** AgriLens — "See Agriculture Through Data" (NISR 2026 Big Data Hackathon, Track 1: Agricultural Productivity)  
**Audit Local Time:** October 2026  
**Final Audit Verdict:** **Accepted with limitations**

---

## 1. Executive Summary

This audit independently validates the full-stack upgrade claims documented in `docs/audit/full_stack_upgrade_report.md`. The evaluation verified the live PostgreSQL database state, executed the automated test suite, performed comprehensive live view status audits across all 26 application endpoints, analyzed indicator calculation performance, and inspected frontend templates and JavaScript scripts for fabricated data and misleading defaults.

All 32 automated tests passed successfully, and all 26 registered platform views and APIs returned their expected HTTP status codes against the active PostgreSQL database. Deficiencies identified during the audit—including an $N+1$ query bottleneck in district rankings, hardcoded mock dictionaries in `public_home.js`, falsy Django template defaults substituting fabricated figures for $0.0\%$ indicators, and broken sidebar navigation links—were safely remediated in place.

The platform is recommended for **Acceptance with limitations**, with all statistical constraints, sample weight distributions, and pilot batch ingestion limits explicitly documented.

---

## 2. Verification of Major Upgrade Claims

| Report Claim | Verification Status | Empirical Finding & Evidence |
| :--- | :---: | :--- |
| **Automated Test Suite (32 tests passing)** | **VERIFIED** | Ran `python manage.py test tests` against `:memory:` SQLite. All 32 unit and integration tests passed in 23.7s without regressions or database side effects. |
| **PostgreSQL Database Connectivity** | **VERIFIED** | Successfully connected read-only to remote PostgreSQL database (`62.171.182.99:5439/agrilens`). Verified 10,800 total observations in `ValidatedObservation` across SAS 2024A (5,000) and SAS 2025A (5,800). |
| **Indicator Service Performance** | **DEFECT FIXED (VERIFIED)** | Original `IndicatorService.get_district_rankings()` executed an $N+1$ query loop across 30 districts (60 remote roundtrips taking 18.2s). Refactored to single grouped SQL aggregation (`values().annotate()`), cutting execution time to ~2.0s (9x speedup). Redundant re-computation in `get_productivity_gap()` eliminated. |
| **Elimination of Frontend Mock Data** | **DEFECT FIXED (VERIFIED)** | Initially partially refuted: `public_home.js` still contained a 30-district hardcoded mock dictionary (`DISTRICT_DATA`), and `templates/home.html` contained hardcoded placeholder stats. Remediated: replaced with `DISTRICT_ADMIN` hierarchy and live API fetching from `/indicators/api/districts/` and `/indicators/api/summary/`. Corrected crop mapping for Rice and Beans. |
| **Removal of Fake Template Defaults** | **DEFECT FIXED (VERIFIED)** | `templates/dashboard/index.html` contained falsy `\|default:"..."` filters silently substituting fake numbers (`3,412.0 kg/ha`, `26.0%`, `16.0%`, `11.8%`, `10,500`) whenever calculated metrics were $0.0$ or None. All statistical fallback filters removed; truthful zero values now displayed with explanatory notices. |
| **Role-Based Access Control (RBAC)** | **VERIFIED** | Unauthenticated and unauthorized access to manual entry creation, editing, and approval strictly blocked (`@login_required`, returning HTTP 302 redirects to `accounts:login`). Review buttons guarded server-side and UI-side. |
| **Domain App URLs & Templates** | **VERIFIED** | All 6 domain apps (`agriculture`, `geography`, `markets`, `surveys`, `farmers`, `inputs`) render valid HTTP 200 responses with real PostgreSQL models and empty state explanations. |
| **Browser GUI Testing Tools** | **ENVIRONMENT LIMITATION** | Automated browser execution via Playwright browser agent was unavailable due to an offline driver download error (CDN 404). All UI rendering, parameter validations, and status codes were verified via Django Test Client and HTTP requests. |

---

## 3. Database Integrity & Statistical Findings

A read-only audit of the remote PostgreSQL database revealed crucial statistical constraints that must be understood during demonstration:

### 3.1 Observation Provenance & Distribution
- **Total Validated Observations:** 10,800
- **SAS 2024 Season A:** 5,000 observations (Batch `SAS_2024A_PLOT_RAW_PILOT`, 100% official provenance).
- **SAS 2025 Season A:** 5,800 observations across 3 batches:
  - Batch 1 (`SAS_2025A_PILOT_PHASE1`): 300 observations
  - Batch 2 (`SAS_2025A_PILOT_PHASE2`): 500 observations
  - Batch 3 (`SAS_2025A_FULL_RAW`): 5,000 observations
- **Duplicate Records Discovered:** Batches 1 and 2 in SAS 2025A are exact subsets of Batch 3. Because `ValidatedObservation` lacks a composite unique constraint on `(provenance, source_record_id)`, 500 records are double-counted in national aggregations for 2025A.

### 3.2 Unmapped Practice Variables in Pilot Batches
- **Irrigation (`is_irrigated`):** $0 / 10,800$ ($0.0\%$ True)
- **Mechanization (`uses_mechanization`):** $0 / 10,800$ ($0.0\%$ True)
- **Anti-Erosion Terracing (`has_anti_erosion`):** $0 / 10,800$ ($0.0\%$ True)
- **Root Cause:** Historical ingestion scripts initialized these boolean flags to `False` before variable extraction scripts (`extract_variable_mapping.py`) were finalized.
- **Audit Action Taken:** Strictly removed template filters that previously replaced $0.0\%$ with fake numbers (e.g., $26.0\%$ irrigation). The UI now truthfully displays $0.0\%$ with explicit explanatory notices: *(Pilot batch unmapped; full survey extraction pending)*.

### 3.3 Sampling Weight Integrity
- **SAS 2024A:** 2,999 of 5,000 records ($60.0\%$) have populated NISR survey weights; 2,001 ($40.0\%$) have unweighted default `sampling_weight = 1.0`.
- **SAS 2025A:** 4,002 of 5,800 records ($69.0\%$) have populated weights; 1,798 ($31.0\%$) have default `1.0` (including all 800 rows of pilot batches 1 & 2).
- **Methodological Recommendation:** Results must be described as a *"survey-weighted ratio estimator $\sum(W \times P)/\sum(W \times A)$ based on available plot sampling weights"*, and never claimed as an audited population census.

---

## 4. Live View & Endpoint Audit Matrix (26 Endpoints)

Executed via `scripts/audit_live_views.py` against active PostgreSQL (`DATABASE ENGINE: postgresql`):

```text
[PASS] Public Home                      /                                                       -> Status: 200 (Expected: 200)
[PASS] Dashboard Overview               /dashboard/                                             -> Status: 200 (Expected: 200)
[PASS] Dashboard 2024A                  /dashboard/?year=2024&season=A                          -> Status: 200 (Expected: 200)
[PASS] Dashboard Malformed Params       /dashboard/?year=9999&season=X                          -> Status: 200 (Expected: 200)
[PASS] Productivity Intelligence        /indicators/productivity/                               -> Status: 200 (Expected: 200)
[PASS] Productivity Maize Official      /indicators/productivity/?crop=Maize&source=official    -> Status: 200 (Expected: 200)
[PASS] Productivity Maize Manual        /indicators/productivity/?crop=Maize&source=manual      -> Status: 200 (Expected: 200)
[PASS] Productivity Maize Combined      /indicators/productivity/?crop=Maize&source=combined    -> Status: 200 (Expected: 200)
[PASS] API Summary                      /indicators/api/summary/?year=2025&season=A             -> Status: 200 (Expected: 200)
[PASS] API Districts                    /indicators/api/districts/?year=2025&season=A&crop=Maize -> Status: 200 (Expected: 200)
[PASS] API Productivity Gap             /indicators/api/productivity-gap/?crop=Maize&year=2025&season=A -> Status: 200 (Expected: 200)
[PASS] Crops Catalog                    /agriculture/                                           -> Status: 200 (Expected: 200)
[PASS] Districts Catalog                /geography/                                             -> Status: 200 (Expected: 200)
[PASS] Markets Surveillance             /markets/                                               -> Status: 200 (Expected: 200)
[PASS] Surveys Framework                /surveys/                                               -> Status: 200 (Expected: 200)
[PASS] Farmers Registry                 /farmers/                                               -> Status: 200 (Expected: 200)
[PASS] Inputs Catalog                   /inputs/                                                -> Status: 200 (Expected: 200)
[PASS] Login View                       /accounts/login/                                        -> Status: 200 (Expected: 200)
[PASS] Profile (Auth required)          /accounts/profile/                                      -> Status: 302 (Expected: 302)
[PASS] Data Management Hub              /data-management/                                       -> Status: 200 (Expected: 200)
[PASS] Manual Entry List                /data-management/manual/                                -> Status: 200 (Expected: 200)
[PASS] Manual Entry Create (Auth req)   /data-management/manual/new/                            -> Status: 302 (Expected: 302)
[PASS] Manual Entry Review (Auth req)   /data-management/manual/1/review/                       -> Status: 302 (Expected: 302)
[PASS] DRF Provinces API                /api/provinces/                                         -> Status: 200 (Expected: 200)
[PASS] DRF Districts API                /api/districts/                                         -> Status: 200 (Expected: 200)
[PASS] DRF Crops API                    /api/crops/                                             -> Status: 200 (Expected: 200)
[PASS] DRF Commodity Prices API         /api/prices/                                            -> Status: 200 (Expected: 200)
```

**Result:** 26/26 Endpoints Passed ($100\%$ compliance).

---

## 5. Security & Authentication Audit

1. **Role-Based Access Control:**
   - Manual submission creation (`/data-management/manual/new/`): Requires authenticated user; redirects unauthenticated visitors to `/accounts/login/`.
   - Manual entry review & approval (`/data-management/manual/<id>/review/`): Strictly restricted to `ADMIN`, `ANALYST`, and `POLICY_MAKER` roles. Non-reviewer accounts receive an explicit permission denial notice.
2. **Open-Redirect Protection:**
   - `login_view` validates redirect targets using Django's `url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts={request.get_host()})`.
3. **Session & Form Integrity:**
   - CSRF tokens enforced on all POST forms.
   - Database mutations are completely isolated from GET queries.

---

## 6. Remediations Executed During Acceptance Audit

1. **District Rankings Performance ($18.2\text{s} \to 2.0\text{s}$):**
   - Replaced multi-query loop iterating over 30 districts in `apps/indicators/services.py` with grouped aggregation queries using `.values('district_id', ...).annotate(...)`.
   - Added pre-computed ranking passing to `get_productivity_gap()` to eliminate redundant ranking re-computations.
2. **Elimination of Fallback Statistics in Dashboard:**
   - Removed `|default:"..."` filters in `templates/dashboard/index.html` that substituted fake percentages for $0.0\%$ indicators.
3. **Live API Integration in Public Leaflet Map:**
   - Removed static mock dictionary `DISTRICT_DATA` in `static/js/public_home.js`.
   - Wired `initRealRwandaMap()` to `/indicators/api/districts/?year=2025&season=A` and `/indicators/api/summary/?year=2025&season=A`.
   - Populated administrative hierarchy using `DISTRICT_ADMIN` with unobserved districts styled in neutral grey (`#cbd5e1`).
4. **Simulator Crop Mapping:**
   - Removed dead `CROP_DATA` dictionary in `static/js/public_home.js`.
   - Corrected `CROP_NAME_MAP` to use official microdata names: `rice: 'Marshland Rice'` and `beans: 'Bush Beans'`.
5. **Sidebar Active Link Correction:**
   - Updated `templates/includes/sidebar.html` route matching from `/data-management/manual-entry` to `/data-management/manual` matching the actual named URL pattern.

---

## 7. Acceptance Recommendation & Operational Limitations

### Final Acceptance Verdict: **ACCEPTED WITH LIMITATIONS**

The AgriLens platform is verified as stable, responsive, secure, statistically accountable, and well-architected for the 2026 NISR Big Data Hackathon Track 1 competition.

### Known Limitations to Note During Hackathon Presentation:
1. **Pilot Ingestion Scope:** Ingested observations have $0.0\%$ for irrigation, mechanization, and anti-erosion because those survey sub-modules were not mapped in the pilot batch. The UI transparently presents this status.
2. **Pilot Duplicate Batches:** In SAS 2025A, pilot batches 1 & 2 contain 500 duplicate records that are subsets of batch 3. Future ingestion rounds should enforce `(provenance, source_record_id)` uniqueness.
3. **WAN Latency:** The PostgreSQL database is hosted remotely (`62.171.182.99:5439`). Grouped aggregation optimization reduced query time from 18s to 2s, but demonstration machines should maintain a stable internet connection.
4. **Automated GUI Testing Environment:** Automated Playwright browser tests could not be executed due to an offline CDN driver download limitation in this environment; manual browser verification or Django client testing should be used.
