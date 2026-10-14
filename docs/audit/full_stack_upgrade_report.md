# AgriLens Full-Stack Upgrade Report — NISR Big Data Hackathon 2026 (Track 1)

**Platform:** AgriLens — See Agriculture Through Data  
**Scope:** Frontend, Backend, Analytics, Statistical Integrity, Security, and Production Polish  
**Audit Date:** October 2026  
**Status:** Completed & Validated (32/32 Automated Tests Passing)

---

## 1. Executive Summary

AgriLens has undergone an in-place full-stack upgrade to achieve production-grade quality for the 2026 NISR Big Data Hackathon (Track 1: Agricultural Productivity). 

All hardcoded mock statistics and client-side dictionaries have been replaced with dynamic connections to PostgreSQL microdata and validated Django/DRF endpoints. Statistical calculations now enforce a strict 3-way source selection policy (`official`, `manual`, and `combined`), ratio estimators $\sum(W \times P)/\sum(W \times A)$, and explicit minimum sample size thresholds. User authentication and role-based access control (RBAC) are actively enforced on all data-management operations, and placeholder domain apps (`agriculture`, `geography`, `markets`, `surveys`, `farmers`, `inputs`) have been completed with clean views, real records, and explanatory empty states.

---

## 2. Important Confirmed Issues Discovered & Resolved

| Component | Issue Identified | Resolution Implemented |
| :--- | :--- | :--- |
| **Frontend Map & Charts** | `static/js/dashboard.js` used a hardcoded dictionary (`DASH_DISTRICT_DATA`) for Leaflet mini-map choropleths. | Connected to `/indicators/api/districts/` and `/api/prices/`. Mini-map dynamically colors districts using live survey microdata; displays neutral state for unobserved districts. |
| **Productivity Gap Simulator** | `static/js/public_home.js` used a hardcoded dictionary (`CROP_DATA`) with fabricated metrics. | Connected to `/indicators/api/productivity-gap/`. Fetches live benchmark vs lagging comparisons; enforces minimum-sample thresholds. |
| **Statistical Fallback Policy** | `IndicatorService.get_productivity_gap()` silently fell back to single-observation districts (`min_plots=1`) when sample size was limited. | Implemented strict minimum sample policy. When fewer than 2 districts meet the threshold, returns a structured result with `is_sufficient_data: False` and clear justification. |
| **Manual Data Segregation** | `IndicatorService` queried `ValidatedObservation` with a loose provenance check, failing to incorporate approved records from `ManualObservation`. | Implemented a strict 3-way policy: `official` (survey-weighted NISR microdata), `manual` (unweighted approved entries), and `combined` (dual-source with separate provenance accounting). |
| **Security & Authentication** | Unsafe pattern in `data_management/views.py` (`get_default_user()`) automatically created an analyst account during requests without authentication. | Removed `get_default_user()`. Enforced `@login_required(login_url='accounts:login')` on creation, editing, and approval workflows. |
| **Query Parameter Validation** | Malformed parameters in indicators and dashboard views caused unhandled exceptions. | Added parameter sanitization (`_validate_common_params`) restricting years to `[2024, 2025]`, seasons to `['A', 'B', 'C']`, and sources to `['official', 'manual', 'combined']`. |
| **Placeholder Domain Modules** | `apps/agriculture/`, `apps/geography/`, `apps/markets/`, `apps/surveys/`, `apps/farmers/`, `apps/inputs/` had empty URL confs and views. | Built list/detail views, wired URL routes, and added templates displaying real crops, districts, price quotes, and explanatory empty states. |
| **Mobile Responsiveness** | Sidebar lacked responsive drawer styling on viewports $\le 992\text{px}$, pushing dashboard content downwards. | Added an off-canvas drawer layout in `main.css` with mobile toggle button and outside-click dismissal in `main.js`. |

---

## 3. Frontend Improvements Completed

1. **National Dashboard (`templates/dashboard/index.html` & `static/js/dashboard.js`):**
   - Survey Framework dropdown synchronized to real dataset choices (`SAS 2025 Season A` and `SAS 2024 Season A`).
   - Dynamic Leaflet choropleth map driven by `/indicators/api/districts/`.
   - Tooltips show weighted yield, irrigation rate, loss rate, and sampled plot counts per district.
   - Commodity market price chart wired to `/api/prices/` surveillance data.
   - Post-harvest loss donut chart reflects verified stage distributions.

2. **Public Landing Portal (`templates/home.html` & `static/js/public_home.js`):**
   - Interactive Productivity Gap Intelligence simulator wired to `/indicators/api/productivity-gap/?crop=...`.
   - Displays real benchmark vs lagging districts, yield gaps, and practice adoption rates.
   - Displays clear explanatory callouts when sample sizes are insufficient for reliable comparisons.

3. **Productivity Intelligence Dashboard (`templates/indicators/productivity_intelligence.html`):**
   - Added a 3-way Data Lineage selector: Official NISR Microdata (Strict), Approved Manual Only, and Combined Analysis.
   - Dynamic Active Source Scope alert banner showing provenance label, methodology note, and plot counts.
   - Informative sample threshold alert: *"Insufficient Data for a Reliable Benchmark Comparison"* when fewer than 2 qualifying districts meet the sample threshold.

4. **Shared Shell & Layout (`templates/base.html`, `sidebar.html`, `navbar.html`, `main.css`, `main.js`):**
   - Dynamic active route highlighting using `request.path`.
   - Top-navbar displays authenticated user name, role badge (`ADMIN`, `ANALYST`, etc.), profile link, and sign-out button.
   - Responsive off-canvas navigation drawer for tablet and mobile screens.

5. **Data Management & Review Workflows (`templates/data_management/`):**
   - Review and approval action buttons restricted to authorized reviewers (`is_reviewer`).
   - Non-reviewers and unauthenticated visitors see informative authorization notices instead of non-functional forms.

---

## 4. Backend Improvements Completed

1. **Statistical Indicator Services (`apps/indicators/services.py`):**
   - Survey-weighted ratio estimator: $\sum(W \times P) / \sum(W \times A)$.
   - Independent calculations for `_calculate_official_summary`, `_calculate_manual_summary`, and `_calculate_combined_summary`.
   - Multi-year comparison (`get_year_over_year_comparison`) verifies comparability between survey rounds and flags missing observations.

2. **Accounts Application (`apps/accounts/`):**
   - Implemented `LoginForm` and `UserProfileForm` in `forms.py`.
   - Implemented `login_view`, `logout_view`, and `profile_view` in `views.py`.
   - Registered `login/`, `logout/`, `profile/` routes in `urls.py`.
   - Created `templates/accounts/login.html` and `templates/accounts/profile.html`.

3. **Domain Applications Completed:**
   - **`apps/agriculture/`:** `crop_list` and `crop_detail` with category filtering and priority crop markers.
   - **`apps/geography/`:** `district_list` and `district_detail` grouping 30 districts and 416 sectors by province.
   - **`apps/markets/`:** `market_list` displaying commodity price quotes across Kimironko, Musanze, and Huye.
   - **`apps/surveys/`:** `survey_list` presenting SAS campaign methodology and cycle descriptions.
   - **`apps/farmers/`:** `farmer_list` presenting cooperatives and smallholder profiles.
   - **`apps/inputs/`:** `input_list` displaying Smart Nkunganire System subsidized prices and commercial benchmarks.

4. **API Quality & DRF Serializers (`apps/api/`):**
   - Replaced `fields = '__all__'` with explicit field declarations across all serializers.
   - Added descriptive nested attributes: `province_name`, `category_name`, `crop_name`, `market_name`, `district_name`.
   - Added filtering (`province`, `crop`, `market`, `priority`) and `select_related()` query optimizations.

---

## 5. Security & Data Integrity Improvements

1. **Server-Side Authorization (RBAC):**
   - Restricted manual entry review and approval to `ADMIN`, `ANALYST`, and `POLICY_MAKER` roles.
   - Restricted manual entry editing to the original creator or managers.
   - Enforced `@login_required` on all data-management mutations.
2. **Open-Redirect Protection:**
   - Sign-in redirect validated using `url_has_allowed_host_and_scheme`.
3. **Database Isolation Invariant:**
   - Test suite configured to run against in-memory SQLite (`:memory:`), ensuring zero modifications to the production PostgreSQL database.

---

## 6. Exact Files Modified & Created

### Modified Files (32)
- `apps/accounts/forms.py`
- `apps/accounts/urls.py`
- `apps/accounts/views.py`
- `apps/agriculture/urls.py`
- `apps/agriculture/views.py`
- `apps/api/serializers.py`
- `apps/api/views.py`
- `apps/dashboard/urls.py`
- `apps/dashboard/views.py`
- `apps/data_management/views.py`
- `apps/farmers/urls.py`
- `apps/farmers/views.py`
- `apps/geography/urls.py`
- `apps/geography/views.py`
- `apps/indicators/services.py`
- `apps/indicators/views.py`
- `apps/inputs/urls.py`
- `apps/inputs/views.py`
- `apps/markets/urls.py`
- `apps/markets/views.py`
- `apps/surveys/urls.py`
- `apps/surveys/views.py`
- `static/css/main.css`
- `static/js/dashboard.js`
- `static/js/main.js`
- `static/js/public_home.js`
- `templates/accounts/login.html`
- `templates/dashboard/index.html`
- `templates/data_management/manual_entry_detail.html`
- `templates/includes/navbar.html`
- `templates/includes/sidebar.html`
- `templates/indicators/productivity_intelligence.html`

### Newly Created Files (9)
- `templates/accounts/profile.html`
- `templates/agriculture/crop_list.html`
- `templates/agriculture/crop_detail.html`
- `templates/geography/district_list.html`
- `templates/geography/district_detail.html`
- `templates/markets/market_list.html`
- `templates/surveys/survey_list.html`
- `templates/farmers/farmer_list.html`
- `templates/inputs/input_list.html`
- `tests/test_apps/test_full_stack_upgrade.py`
- `docs/audit/full_stack_upgrade_report.md`

---

## 7. Automated Test Suite Execution Results

Ran complete automated test suite across all applications:

```text
Ran 32 tests in 17.055s

OK
Destroying test database for alias 'default'...
Found 32 test(s).
System check identified no issues (0 silenced).
```

### Key Tests Passing:
- `test_official_source_policy_excludes_manual_data` (OK)
- `test_manual_source_policy_only_aggregates_approved_manual_entries` (OK)
- `test_combined_source_policy_clearly_labels_dual_sources` (OK)
- `test_productivity_gap_enforces_strict_sample_size_without_silent_downgrade` (OK)
- `test_dashboard_view_handles_invalid_query_params_safely` (OK)
- `test_indicators_view_handles_invalid_query_params_safely` (OK)
- `test_unauthenticated_user_cannot_create_manual_entry` (OK)
- `test_unauthenticated_user_cannot_review_or_approve_manual_entry` (OK)
- `test_unauthorized_role_cannot_review_manual_entry` (OK)
- `test_authorized_analyst_can_approve_manual_entry` (OK)
- `test_agriculture_module_views` (OK)
- `test_geography_module_views` (OK)
- `test_markets_module_views` (OK)
- `test_surveys_farmers_inputs_modules` (OK)
- `test_indicators_json_apis` (OK)
- `test_drf_viewsets_serialization` (OK)
- All 16 legacy unit tests for indicator weighting, manual entry workflows, and ETL pipeline validation (OK)

---

## 8. Deployment & Demonstration Readiness

The platform is fully integrated, statistically grounded, and ready for presentation to NISR Big Data Hackathon judges:

- **Local Development / Demonstration Command:**
  ```powershell
  .\venv\Scripts\python.exe manage.py runserver
  ```
- **Automated Verification Command:**
  ```powershell
  .\venv\Scripts\python.exe manage.py test tests
  ```
- **Integrity Guarantee:** Zero hardcoded fallback numbers; every metric presented in the interface originates from verified survey microdata or authorized manual entries.
