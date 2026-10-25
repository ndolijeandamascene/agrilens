# AgriLens Data Assessment & Initial Architecture Report

**Project:** AgriLens • National Agricultural Productivity Intelligence Platform  
**Hackathon:** NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity  
**Date:** October 2026  
**Status:** Initial Assessment Completed (Stage 1 / Phase One Deliverable)  

---

## 1. Executive Summary

AgriLens is an evidence-based decision-support platform designed to transform official National Institute of Statistics of Rwanda (NISR) agricultural datasets into empirical productivity indicators, interactive district-level maps, yield gap calculations, and agricultural practice analyses.

This document represents the **Mandatory Phase One Assessment**. It establishes the baseline state of the project codebase, catalogs the available datasets, verifies infrastructure reachability, highlights critical data risks, and lays out the step-by-step implementation sequence.

---

## 2. Existing Project Architecture

### 2.1 Backend & Web Framework
* **Python Runtime:** Python 3.14.7 (Active in `venv/`, backward compatible with CI target Python 3.11/3.12).
* **Web Framework:** Django 5.2.17 (`django-environ`, `djangorestframework`, `corsheaders`, `whitenoise`).
* **Settings Architecture:** Unified [`config/settings.py`](../config/settings.py) dynamically loaded via [`.env`](../.env), with automatic PostgreSQL connection parsing and local SQLite fallback.
* **Database Driver:** `psycopg2-binary 2.9.13` (PostgreSQL connectivity verified).
* **Data Processing Libraries:** `pandas 3.0.6`, `numpy 2.5.3`, `scikit-learn 1.9.1`, `openpyxl 3.1.5`, `pyreadstat 1.3.6`, `shapely 2.1.2`, `geopandas 1.2.0`.
* **Asynchronous Engine:** Celery 5.6.3 + Redis 8.1.0 configured for heavy survey ETL jobs.

### 2.2 Existing Applications (`apps/`)
* [`apps.accounts`](../apps/accounts/models.py): Custom `User` model with role tiers (`ADMIN`, `ANALYST`, `POLICY_MAKER`, `EXTENSION_OFFICER`, `RESEARCHER`).
* [`apps.geography`](../apps/geography/models.py): Administrative boundary models (`Province`, `District`, `Sector`).
* [`apps.agriculture`](../apps/agriculture/models.py): Domain models for `CropCategory`, `Crop`, and `AgriculturalSeason` (Season A, B, C).
* [`apps.indicators`](../apps/indicators/models.py): Aggregated metrics: `ProductivityMetric` (`avg_yield_kg_per_ha`, `total_production_mt`, `post_harvest_loss_percentage`).
* [`apps.markets`](../apps/markets/models.py): `MarketLocation` and `CommodityPrice` models for retail and wholesale market tracking.
* [`apps.surveys`](../apps/surveys/models.py): Survey campaign tracking and field submission models (`SurveyCampaign`, `FarmSurveySubmission`).
* [`apps.farmers`](../apps/farmers/models.py): `Cooperative` and `Farmer` demographic records.
* [`apps.inputs`](../apps/inputs/models.py): `InputCategory` and `AgriculturalInput` tracking.
* [`apps.dashboard`](../apps/dashboard/views.py): Web controllers for the public portal (`/`) and internal national indicator dashboard (`/dashboard/`).
* [`apps.api`](../apps/api/views.py): DRF read-only viewsets for provinces, districts, crops, and market prices.

### 2.3 Frontend & Spatial Architecture
* **Design Philosophy:** Pure HTML5 + Vanilla CSS + Vanilla JS (No React or Node-based build complexity).
* **Geographic Layer:** Leaflet.js with official 30-district polygon geometries loaded from [`static/data/rwanda_districts.geojson`](../static/data/rwanda_districts.geojson).
* **Hierarchy Reference:** Authoritative administrative tree (30 Districts, 416 Sectors, Cells, Villages) in [`static/data/rwanda_hierarchy.json`](../static/data/rwanda_hierarchy.json).
* **Color System:** Official NISR Brand palette (Pantone Royal Blue `#005CAB`, Cyan `#00AEEF`, Green `#46962B`, Yellow `#F3EA00`).

---

## 3. Database Infrastructure Status

* **Engine:** PostgreSQL 16+ on dedicated remote host.
* **Connectivity Verification:**
  - Tested using `psycopg2` via `DATABASE_URL=postgres://postgres:agrilens123!@62.171.182.99:5439/agrilens?sslmode=disable`.
  - **Status:** **CONNECTED (Success, 0 errors)**.
  - **Schema State:** The remote database is currently clean (`public` schema contains 0 tables).
* **Security & Credential Safety:**
  - Database credentials are strictly isolated inside `.env` (which is excluded from Git via `.gitignore`).
  - `.env.example` provides sanitized placeholders.
* **Migration Status:**
  - Initial Django schema migrations have not yet been run against PostgreSQL.
  - Custom domain apps (`apps.accounts`, `apps.geography`, etc.) are ready for initial migration generation.

---

## 4. Available Data Resources & Inventory Summary

A total of **86 official data files** across 3 major NISR survey frameworks have been discovered and profiled in [`data/reference/dataset_inventory.csv`](../data/reference/dataset_inventory.csv):

| Survey Collection | Covered Periods | Available Formats | Disk Size | Modules Included |
| :--- | :--- | :--- | :---: | :--- |
| **AHS 2024** | 2024 Agriculture Year | Stata (`.dta`) | ~170 MB | 14 sections: Demographics, Land Tenure, Crop Production, Inputs, Livestock, Credit, Sustainable Ag |
| **SAS 2024** | Season A, B, C | CSV (tab-sep), DTA, SAV | ~340 MB | 4 core modules per season: Screening, Production, Ag Practices, Fertilizer/Pesticides |
| **SAS 2025** | Season A, B, C | CSV (tab-sep), DTA, SAV | ~1.15 GB | 4 core modules per season: Screening, Production, Ag Practices, Fertilizer/Pesticides |
| **Geography** | Current Admin Standard | GeoJSON, JSON | ~670 KB | 30 District polygons (`rwanda_districts.geojson`), 416 Sectors + Cells + Villages hierarchy |

---

## 5. Critical Findings & Technical Risks

### Risk 1: CSV Delimiter Pitfall (Tab-Separated vs Comma)
* **Finding:** All `.csv` files in the NISR SAS 2024 and SAS 2025 catalogs are actually **tab-delimited (`\t`)**, not comma-separated.
* **Impact:** Default `pd.read_csv(filepath)` calls fail or mangle columns unless explicit `sep='\t'` is specified.
* **Mitigation:** The ETL extractor must use automated delimiter detection or explicit tab delimiters.

### Risk 2: Stata Non-UTF-8 Character Encodings
* **Finding:** Multiple Stata files (e.g., `AHS2024_Section1_HOUSEHOLD MEMBERS CHARACTERISTICS.dta` and `Section6_EXTENSION SERVICES...`) contain French accent characters that fail strict UTF-8 decoding.
* **Impact:** Crashes with `'utf-8' codec can't decode byte 0xf4`.
* **Mitigation:** The reader must specify `encoding='latin1'` / `encoding='WINDOWS-1252'` for legacy Stata files.

### Risk 3: SAS Season C 2024 Naming Anomaly
* **Finding:** In `Datasets/SAS 2024 catalog and data dictionary/Season C/`, the CSV file for fertilizer is mislabeled as `Rwa_raw_fertilizer_pesticideB2024.csv`, while its `.dta` and `.sav` siblings are correctly named `...C2024`.
* **Mitigation:** The ETL batch registry must verify internal header metadata rather than blindly parsing file basenames.

### Risk 4: Disparate Sampling Frames (SAS vs AHS)
* **Finding:** SAS observational units are **Segments (`Segment_ID`) $\rightarrow$ Tracts $\rightarrow$ Plots (`s2q1`) $\rightarrow$ Crops**. AHS observational units are **Households (`hhid`) $\rightarrow$ Persons (`pid`) $\rightarrow$ Parcels $\rightarrow$ Crops**.
* **Impact:** Joining SAS and AHS into a single table would create statistically invalid chimeric records.
* **Mitigation:** SAS and AHS must be loaded into distinct schema tables and harmonized only at the aggregated indicator level.

### Risk 5: Provenance Dilution with Manual Data
* **Rule:** Manual entries must never be merged with official NISR survey microdata without explicit provenance flags (`NISR_SAS_2024`, `NISR_SAS_2025`, `NISR_AHS_2024`, `MANUAL_ENTRY`). Official statistics must filter out unapproved or non-official records by default.

---

## 6. Missing Resources & Gaps

1. **Independent PDF Questionnaires:**
   - Standalone PDF codebooks were not provided as separate PDF files in the directory; however, **authoritative variable labels and category value dictionaries are fully embedded within the SPSS (`.sav`) and Stata (`.dta`) file headers**. We can extract 100% of the variable definitions directly from the data files using `pyreadstat`.
2. **PostGIS Spatial Extension:**
   - The PostgreSQL instance currently does not have PostGIS enabled; however, polygon GeoJSON layers are handled efficiently on the frontend using Leaflet, with district and sector codes stored relationally in PostgreSQL.

---

## 7. Recommended Implementation Sequence

```text
[Stage 1: Assessment & Inventory] (COMPLETED)
  ├── docs/data_assessment.md
  ├── docs/dataset_inventory.md
  └── data/reference/dataset_inventory.csv
         │
         ▼
[Stage 2: Profiling & Variable Mapping]
  ├── Detailed variable dictionary extraction (pyreadstat)
  ├── docs/data_dictionary_mapping.md & docs/data_quality_report.md
  └── data/reference/variable_mapping.csv & data_quality_summary.csv
         │
         ▼
[Stage 3: PostgreSQL Schema & Provenance Architecture]
  ├── Design staging, validated, and harmonized analytical tables
  ├── docs/database_design.md
  └── Django models & initial PostgreSQL migrations
         │
         ▼
[Stage 4: Pilot Ingestion]
  ├── Ingest SAS 2025 Season A Production dataset
  └── Validate row count, identifiers, and staging integrity
         │
         ▼
[Stage 5: Full Ingestion Pipeline]
  ├── SAS 2024 (Seasons A, B, C)
  ├── SAS 2025 (Seasons A, B, C)
  ├── AHS 2024 core modules
  └── docs/sas_2024_2025_harmonization.md
         │
         ▼
[Stage 6: Manual Entry & Review Workflow]
  ├── Forms with dynamic dependent dropdowns (Province ➔ District ➔ Sector)
  ├── Draft ➔ Submitted ➔ Reviewed ➔ Approved status lifecycle
  └── Audit trail and provenance isolation
         │
         ▼
[Stage 7: Validated Analytics & Indicators]
  ├── Empirical yield, yield gaps, practice adoption, post-harvest losses
  └── Connect frontend simulator and Leaflet map to dynamic API
         │
         ▼
[Stage 8: Automated Verification & Test Suite]
  └── End-to-end tests for ETL, permissions, calculations, and UI
```

---

## ⚖️ Intellectual Property, License & Usage Policy

> ### ⚠️ STRICT RESTRICTED USE NOTICE
> **All Rights Reserved © 2026 AgriLens Development Team.**
>
> 1. **Non-Commercial & No Personal Profit:**  
>    No individual, entity, or third party is permitted to use, copy, reproduce, monetize, sub-license, or exploit any portion of this codebase, architecture, machine learning models, algorithms, or visual designs for commercial purposes, revenue generation, or personal financial profit under any circumstances.
>
> 2. **Public Hackathon Visibility Disclaimer:**  
>    Although this repository is publicly accessible solely for the purpose of evaluation, review, and judging during the **2026 NISR Big Data Hackathon (Track 1: Agricultural Productivity)**, public availability does **NOT** constitute an open-source license, public domain dedication, or waiver of intellectual property rights.
>
> 3. **Prohibition of Modifications & Derivative Works:**  
>    Any unauthorized modification, alteration, redistribution, fork, decompilation, reverse-engineering, or derivation of this codebase or its underlying assets is strictly prohibited.
>
> 4. **Exclusive Authorization for NISR:**  
>    Operational utilization, institutional adoption, data integration, and platform deployment are **exclusively and solely permitted for the National Institute of Statistics of Rwanda (NISR)** and its officially designated national agricultural partners.

