<div align="center">

# 🌾 AgriLens

### *See Agriculture Through Data.*

**Official Agricultural Intelligence & Decision-Support Platform for Rwanda**  
Developed for the **2026 NISR Big Data Hackathon – Track 1: Agricultural Productivity**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-092E20.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791.svg)](https://www.postgresql.org/)
[![AgriLens AI](https://img.shields.io/badge/AgriLens%20AI-Neural%20Assistant-059669.svg)](https://agrilens.ndoli.dev)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Alpine.js](https://img.shields.io/badge/Frontend-Alpine.js%20%7C%20Vanilla%20CSS-77C1D2.svg)](https://alpinejs.dev/)
[![Video Walkthrough](https://img.shields.io/badge/🎬%20Demo-Video%20Walkthrough-E11D48.svg)](https://drive.google.com/file/d/1ifLBSVwtlDGiR3tZiCt9HYd0bp2pXBz4/view?usp=sharing)
[![Automated Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

---

### 🚀 Live Hackathon Submission & Evaluation

| **Platform Resource** | **Direct Link / Credentials** | **Role / Notes** |
| :--- | :--- | :--- |
| 🌐 **Live Web Application** | **[https://agrilens.ndoli.dev](https://agrilens.ndoli.dev)** | Public Portal & Staff Management |
| 🎬 **Video Demonstration** | **[Watch Video Walkthrough (Google Drive Stream)](https://drive.google.com/file/d/1ifLBSVwtlDGiR3tZiCt9HYd0bp2pXBz4/view?usp=sharing)** | Instant video preview (stream without download) |
| 👤 **Evaluator Credentials** | Username: `admin` &bull; Password: `AgriLens2026!` | System Administrator (Full Superuser) |

*Full platform access enabled for the hackathon evaluation jury and reviewers.*

> 🔐 **Environment Configuration (`.env`):** To get the authorized `.env` configuration file, send a request to **[ndolijeandamascene@gmail.com](mailto:ndolijeandamascene@gmail.com)** or via WhatsApp message to **[+250 789 312 765](https://wa.me/250789312765)**.

---

[Live Demo](https://agrilens.ndoli.dev) •
[Video Walkthrough](https://drive.google.com/file/d/1ifLBSVwtlDGiR3tZiCt9HYd0bp2pXBz4/view?usp=sharing) •
[Key Capabilities](#-key-capabilities) •
[Architecture](#-system-architecture) •
[Quickstart](#-quickstart--installation) •
[Roles & RBAC](#-user-roles--access-control) •
[API Reference](#-api-endpoints) •
[Testing](#-testing--quality-assurance) •
[Data Governance](#-data-governance--scientific-integrity) •
[Usage Policy](#️-intellectual-property-license--usage-policy)

</div>

---

## 📖 Executive Summary

Rwanda generates rich agricultural datasets through the **National Institute of Statistics of Rwanda (NISR)**, notably the **Seasonal Agricultural Survey (SAS)** and **Agricultural Household Survey (AHS)**. However, raw survey microdata alone does not readily highlight where localized productivity bottlenecks exist, which farming practices drive yield variance, or where targeted policy interventions will yield maximum impact.

**AgriLens** bridges the gap between raw statistical data and operational agricultural governance. Built specifically for **Track 1: Agricultural Productivity**, AgriLens transforms official microdata into actionable intelligence through:
- **Interactive Geospatial Analytics** spanning all 5 Provinces and 30 Districts of Rwanda.
- **Productivity Gap Intelligence** contrasting yield disparities alongside correlated input adoption rates without claiming unproven causal links.
- **Predictive Machine Learning** (Random Forest yield modeling, K-Means district clustering, and what-if input policy simulations).
- **AgriLens AI Assistant**: An in-process neural and grounded conversational assistant powered by local quantized weights, answering over 23,833 NISR Seasonal Agricultural Survey records with role-based data clearance.
- **Maker-Checker Data Governance** for official survey microdata ETL and validated field observations.
- **Daily Commodity Market Surveillance** covering 30 districts with price dispersion analysis.
- **Automated Multi-Channel Communication** delivering timely alerts, reports, and administrative notices to agricultural stakeholders.

---

## 🌟 Key Capabilities

### 1. Executive Intelligence Dashboard & Geospatial Visualizations
- **6 Core Productivity KPIs**: Live weighted calculations for Total Production, Average Yield (kg/ha), Cultivated Area, Post-Harvest Loss Rate, Irrigation Adoption, and Mineral Fertilizer Usage.
- **Interactive District Choropleth Map**: Lightweight SVG and GeoJSON boundary rendering covering all 30 districts with instant metric filtering (Crop, Season, Province).
- **Provincial Disparity Benchmarks**: Radar and bar visualizations comparing Eastern, Western, Northern, Southern, and Kigali performance against national baselines.

### 2. Signature Feature: Productivity Gap Intelligence (Track 1)
- **Granular Yield Contrast Engine**: Compare any two districts, seasons, or crops to quantify observed productivity deficits (e.g., *Maize yield: Nyagatare 4,100 kg/ha vs. Gatsibo 2,850 kg/ha — 30.5% gap*).
- **Associative Indicator Breakdown**: Simultaneously contrasts 5 critical agronomic factors:
  - Irrigation adoption rate
  - Improved seed usage
  - Inorganic/Organic fertilizer application
  - Agricultural mechanization
  - Post-harvest storage losses
- **Strict Methodological Discipline**: Enforces non-causal language (*"associated indicator"*, *"observed difference"*) to uphold statistical integrity until controlled causal studies are conducted.

### 3. Machine Learning & Policy Simulation Engine
- **Yield Inference API (`/api/v1/ml/predict-yield/`)**: Trained `RandomForestRegressor` incorporating historical rainfall, soil pH, fertilizer intensity, seed type, and topography.
- **What-If Agronomic Policy Simulator (`/api/v1/ml/simulate-scenario/`)**: Allows agronomists and policymakers to simulate the expected yield delta from increasing irrigation, fertilizer subsidies, or seed quality by $X\%$.
- **District Typology Clustering (`/api/v1/ml/district-clusters/`)**: Unsupervised `K-Means` clustering categorizing Rwanda's 30 districts into distinct agro-ecological typologies (High Yield / High Input, Untapped Potential, Climate Vulnerable).
- **Seasonal Harvest & Price Forecasting (`/api/v1/ml/forecast/`, `/api/v1/ml/price-forecast/`)**: Predictive forecasting models for forthcoming harvest tonnage and wholesale market price trends.
- **Explainability & Model Transparency (`/api/v1/ml/explainability/`, `/api/v1/ml/models/`)**: Detailed feature importance weights, performance metrics (R², RMSE, MAE), and model version registry.
- **Automated Re-training Pipeline (`/api/v1/ml/train/` / `python manage.py train_ml_models`)**: Automated retraining pipeline refreshing models with newly verified survey cycles.

### 4. AgriLens AI: Grounded Intelligence & Conversational Assistant
- **100% In-Process Neural Engine**: High-performance local neural model operating directly in-process via C++ memory mapping (`llama-cpp-python`). Zero external daemons, zero third-party cloud API costs, and zero private data egress.
- **Dual Grounding & Zero Hallucination**: Every empirical question executes deterministic read-only aggregations across 23,833 NISR Seasonal Agricultural Survey records first. Official numbers (yield, production, adoption rate, post-harvest loss) are presented with complete statistical lineage and sample size ($n$), enriched by contextual agronomic analysis.
- **Conversational Agronomic Expertise**: Expert conversational guidance answering practical questions on Rwandan crop varieties, seasonal planting calendars (Season A/B/C), soil liming & NPK balance, and pest control.
- **Role-Aware Context Clearance (RBAC)**: Automatically tailors responses based on the caller's authorization level:
  - *Public Visitors / Citizens*: Access published national aggregates, market prices, and actionable farming guidance. Sensitive unapproved field drafts and data collector telemetry remain protected.
  - *Institutional Officers (District Agronomists, Analysts, Administrators)*: Unlock tactical district intelligence, vulnerability scores (AVI), and policy workflows.
- **Public Floating Chatbot Widget**: Interactive slide-up conversational widget accessible across all public pages (`/`, `/reports/`, `/data-api/`, `/about/`) with quick-action suggestions and complete API synchronization.
- **Dedicated ChatGPT-Style Intelligence Console (`/assistant/`)**: Full-screen conversation stream with dynamic leaderboard visualizations, KPI tiles, adoption progress meters, text-to-speech audio, and transparent ORM lineage drawers.

### 5. Agricultural Data Management & Maker-Checker QA Hub
- **3-Tier Data Architecture**:
  1. *Raw Ingestion Layer*: Preserves original NISR SPSS/SAV survey records with checksums and provenance tags.
  2. *Normalized Operational Store*: Relational database mapping parcels, households, seasons, and crops to authoritative geographic codes.
  3. *Aggregated Analytical Lineage*: Pre-aggregated indicator tables powering instant sub-second dashboards.
- **Maker-Checker Field Observation Workflow**: Multi-stage validation lifecycle (`Draft` ➔ `Submitted` ➔ `Approved` / `Needs Correction` / `Rejected`) with full immutable audit logs.
- **Automated SAS Importer**: Custom ETL pipeline leveraging `pyreadstat` to ingest official SAS microdata with automated survey sampling weight calculation.

### 6. Commodity Markets & Daily Price Surveillance
- **Wholesale & Retail Price Monitoring**: Real-time price tracking across 30 district markets for essential staple food crops (Maize, Beans, Irish Potato, Rice, Cassava).
- **5-Stage Publication Workflow**: `Collect` ➔ `Validate` ➔ `Review` ➔ `Approve` ➔ `Publish`.
- **Market Dispersion & Corridors**: Highlights supply bottlenecks and inter-district price arbitrage margins.

### 7. Decision Support & Strategic Agronomic Policies
- **Prescriptive Intervention Triggers**: Automated recommendation rules covering:
  - Small-scale irrigation expansion in drought-prone Eastern lowlands.
  - Soil acidity liming & NPK balance in Northern and Southern volcanic highlands.
  - Post-harvest hermetic storage and drying infrastructure to curb storage losses.
- **Actionable Policy Dossiers**: Quantified investment priorities and target beneficiary estimates per sector.

### 8. Internal Report Center & Automated Schedules
- **On-Demand Exports**: Clean PDF briefings and structured CSV data extracts for researchers and government planners.
- **Automated Background Dispatch**: Background cron task (`run_scheduled_reports`) that compiles and delivers recurring intelligence briefs.

### 9. Institutional Notifications & Communication Center
- **In-App Notification Hub & Dropdown Drawer (`/notifications/`)**: Real-time dropdown drawer with unread counter badges, instant mark-as-read, unread toggle, and direct navigation links to relevant platform records.
- **Asynchronous Email Worker (`apps.notifications.tasks`)**: Non-blocking background worker daemon with `transaction.on_commit` hooks, ensuring zero request lag, idempotency, and dual HTML/plain-text responsive email templates.
- **Platform Administrative Announcements (`/notifications/admin/`)**: Platform-wide broadcasts with customizable priority banners (`Normal`, `High`, `Critical`), target role filtering, and email delivery audit log with retry triggers.
- **User Preference Matrix (`/notifications/preferences/`)**: Granular multi-channel toggles allowing users to subscribe/unsubscribe from specific notification types (Data Approvals, Commodity Prices, System Alerts, Security).
- **Workflow-Triggered Communications**: Automatic alerts dispatched when field observations are submitted, approved, or rejected; when price anomalies occur; when scheduled reports are generated; and during user account provisioning.

### 10. Enterprise Authentication, RBAC & Security
- **Institutional Access Tiers**: 7 role tiers enforcing strict role-based access control.
- **Geographic Data Scoping**: Restricts regional agronomists and officers to their assigned Province, District, or Sector.
- **Tokenized User Provisioning**: Secure, single-use tokenized setup links emailed to newly created users.
- **Self-Service Password Management**: Secure Change Password with active session preservation and multi-step Forgot Password recovery.

---

## 🏗 System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                             OFFICIAL DATA SOURCES                           │
│     NISR SAS (Seasonal Agricultural Survey)  •  AHS  •  MINAGRI  •  RAB     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                ETL PIPELINE                                 │
│  pyreadstat Ingestion  •  Geographic Code Validation  •  Sampling Weights   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          3-TIER POSTGRESQL STORE                            │
│  ┌───────────────────────┐ ┌─────────────────────────┐ ┌──────────────────┐ │
│  │ Tier 1: Raw Microdata │ │ Tier 2: Normalized DB   │ │ Tier 3: Insights │ │
│  └───────────────────────┘ └─────────────────────────┘ └──────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                   ┌───────────────────┴───────────────────┐
                   ▼                                       ▼
┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
│      ANALYTICS & ML ENGINE          │ │     WORKFLOW & SECURITY ENGINE      │
│  • RandomForest Yield Predictor     │ │  • 7-Tier Institutional RBAC        │
│  • K-Means District Clustering      │ │  • Maker-Checker Verification       │
│  • What-If Policy Simulation        │ │  • Geographic Scoping Isolation     │
│  • Productivity Gap Analysis        │ │  • Async Notifications & Broadcasts │
└──────────────────┬──────────────────┘ └──────────────────┬──────────────────┘
                   │                                       │
                   └───────────────────┬───────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGRILENS PRESENTATION LAYER                          │
│   Responsive Django Templates  •  Vanilla CSS Design Tokens  •  Alpine.js   │
│   Interactive SVG / GeoJSON Maps  •  RESTful APIs  •  PDF & CSV Reports     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Technology Stack

| Layer | Technologies | Rationale & Specifications |
| :--- | :--- | :--- |
| **Backend Framework** | **Django 5.2 (Python 3.11+)** | High-security, enterprise-ready web platform with ORM, built-in auth, and transactional integrity. |
| **API Layer** | **Django REST Framework (DRF)** | Clean RESTful endpoints for ML inference, notifications, and indicators. |
| **Neural AI & Assistant** | **AgriLens AI (`llama-cpp-python`)** | In-process neural reasoning engine memory-mapped via C++, grounded in 23,833 NISR survey observations. |
| **Database** | **PostgreSQL / PostGIS** | ACID compliance, robust spatial support, and scalable relational querying. |
| **Machine Learning** | **Scikit-Learn, NumPy, Pandas** | `RandomForestRegressor` for yield inference; `KMeans` for agro-ecological district clustering. |
| **ETL & Data Science** | **pyreadstat, openpyxl** | Ingestion of official NISR SPSS/SAV microdata dictionaries and weights. |
| **Frontend UI** | **Vanilla CSS + Alpine.js** | Ultra-fast, zero-build asset pipeline with modern dark/light styling and reactive components. |
| **Geospatial** | **GeoJSON & Custom SVG** | High-performance district choropleths with zero external map library latency. |
| **Task Dispatch** | **Async Threads / Celery Ready** | Non-blocking email dispatch and scheduled report execution. |
| **Reporting** | **ReportLab & CSV** | Automated PDF briefing generation and structured data exports. |
| **Testing** | **pytest, pytest-django** | Comprehensive automated test suite spanning unit, workflow, and security tests. |

---

## 📁 Repository Structure

```text
agrilens/
├── apps/
│   ├── accounts/             # Custom User model, RBAC, single-use token activation, security
│   ├── agriculture/          # Crops, seasons, parcels, and production statistics
│   ├── api/                  # Public and authenticated REST endpoints
│   ├── assistant/            # AgriLens AI conversational assistant, grounded parser, and role prompt builder
│   ├── dashboard/            # National overview, executive KPIs, map views, scheduled reports
│   ├── data_management/      # 3-tier SAS ingestion, maker-checker manual observations, audit log
│   ├── decision_support/     # Policy recommendation engine and actionable agronomic dossiers
│   ├── geography/            # 5 Provinces, 30 Districts, 416 Sectors hierarchy & GeoJSON
│   ├── indicators/           # Productivity gap intelligence and comparative analytics
│   ├── markets/              # Daily commodity market prices and 5-stage publication workflow
│   ├── ml/                   # ML inference (Random Forest), clustering (K-Means), simulation
│   └── notifications/        # In-app alerts, user preferences, broadcast announcements, async email
├── config/                   # Root Django configuration, settings, URL routing, WSGI/ASGI
├── data/                     # Authoritative geographic GeoJSON and administrative hierarchy
├── etl/                      # Standalone microdata extraction and transformation scripts
├── scripts/                  # Seeding utilities (geography, dev bootstrap, audit reconciliation)
├── static/                   # Global CSS design tokens, icons, and client-side JavaScript
├── templates/                # Server-rendered HTML templates styled with Alpine.js & CSS
├── tests/                    # Pytest automated test suites covering all platform modules
├── manage.py                 # Django command-line utility
└── requirements.txt          # Unified Python dependencies
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- **Python 3.11+** installed
- **PostgreSQL 14+** installed and running
- **Git**

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/ndolijeandamascene/agrilens.git
cd agrilens

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment configuration:

```bash
# Windows:
copy .env.example .env
# Linux / macOS:
cp .env.example .env
```

> **Note:** To obtain the complete pre-configured `.env` file (including database credentials and API secrets), contact **[ndolijeandamascene@gmail.com](mailto:ndolijeandamascene@gmail.com)** or send a WhatsApp message to **[+250 789 312 765](https://wa.me/250789312765)**.

Edit `.env` to configure your PostgreSQL credentials:

```ini
DEBUG=True
SECRET_KEY=your-secure-secret-key-agrilens-2026
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/agrilens_db
TIME_ZONE=Africa/Kigali
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Seed Authoritative Rwanda Geography

Seeds the official NISR administrative hierarchy (5 Provinces, 30 Districts, 416 Sectors, Seasons, and Crops):

```bash
python scripts/seed_geography.py
```

### 6. Initialize Surveillance & Train ML Models

Seed market surveillance datasets and train the yield prediction and district clustering models:

```bash
# Seed commodity market prices
python manage.py seed_market_surveillance

# Train yield prediction & district clustering models
python manage.py train_ml_models
```

### 7. (Optional) Ingest Official NISR SAS Microdata

Ingest official SPSS/SAV microdata packages:

```bash
# Ingest SAS 2025 Season A
python manage.py import_sas_production --file "Datasets/SAS 2025 catalog and data dictionary/Season A/Rwa_raw_SeasonA2025_Production.sav" --year 2025 --season A --limit 5000

# Ingest SAS 2024 Season A
python manage.py import_sas_production --file "Datasets/SAS 2024 catalog and data dictionary/Season A/Rwa_raw_SeasonA2024_Production.sav" --year 2024 --season A --limit 5000
```

### 8. Create Superuser & Run Development Server

```bash
# Create an administrator
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

Open your browser and navigate to **`http://127.0.0.1:8000/`**.

---

## 👥 User Roles & Access Control

AgriLens implements 7 institutional role tiers with geographic scoping to enforce data sovereignty and administrative accountability:

| Institutional Role | Code | Scope | Primary Permissions & Responsibilities |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `ADMIN` | Global | Full system access, user management, audit logs, and broadcast announcements. |
| **NISR Data Manager** | `NISR_DATA_MANAGER` | National | SAS ETL ingestion, survey batch approval, methodology configuration, and report publishing. |
| **Agricultural Data Analyst** | `ANALYST` | National | Indicator analytics, ML policy simulations, gap analysis, and draft report authoring. |
| **National Agriculture Officer** | `NATIONAL_OFFICER` | National | Read access to all provincial data, decision support dashboards, and strategic reports. |
| **District Agriculture Officer** | `DISTRICT_OFFICER` | District-scoped | Data review for assigned districts, validation of submitted field observations, market price checks. |
| **Data Entry Officer** | `DATA_ENTRY_OFFICER` | Sector-scoped | Manual entry of field survey observations (`Draft` ➔ `Submitted`), local market price collection. |
| **Reviewer / Approver** | `REVIEWER` | Scoped | QA gatekeeper authorized to review, approve, or reject pending manual data submissions. |

---

## 🌐 Primary Navigation & URL Endpoints

### Web Portals

| Route | View Name | Description |
| :--- | :--- | :--- |
| `/` | `dashboard:home` | Executive Landing Page with live Rwanda map, Track 1 overview, and key KPIs. |
| `/dashboard/` | `dashboard:executive` | National Agricultural Executive Dashboard with multi-metric filters. |
| `/indicators/productivity/` | `indicators:productivity` | Productivity Gap Intelligence engine and district ranking tables. |
| `/data-management/` | `data_management:hub` | Data Ingestion Registry, ETL batches, QA queues, and audit trails. |
| `/data-management/entries/create/` | `data_management:entry_create` | Cascading Manual Observation form (`Province ➔ District ➔ Sector`). |
| `/markets/` | `markets:dashboard` | Daily Commodity Market surveillance, price dispersion, and 5-stage publishing. |
| `/decision-support/` | `decision_support:index` | Agronomic policy recommendation dossiers and prioritized interventions. |
| `/reports/` | `dashboard:report_center` | Internal Report Center for on-demand PDF and CSV export generation. |
| `/assistant/` | `assistant:index` | Fullscreen ChatGPT-style conversational assistant with KPI tiles, ranking leaderboards, and ORM lineage. |
| Floating Widget | Included on Public Pages | Interactive slide-up AI assistant available on all public pages (`/`, `/reports/`, `/data-api/`, `/about/`). |
| `/notifications/` | `notifications:notification_center` | In-app notification center, unread alerts, and activity feed. |
| `/notifications/preferences/` | `notifications:preferences` | User multi-channel notification settings & frequency matrix. |
| `/notifications/admin/` | `notifications:admin_announcements` | System-wide broadcasts, announcement manager, and email delivery logs. |
| `/accounts/login/` | `accounts:login` | Secure institutional login portal with password recovery and token activation. |

---

## 🔌 API Endpoints

### AgriLens AI Assistant APIs

```http
POST /api/v1/assistant/query/
Content-Type: application/json

{
  "query": "What is the average Irish Potato yield in Musanze?"
}
```

```json
{
  "status": "SUCCESS",
  "intent": "YIELD",
  "synthesized_by": "AgriLens AI (Neural Engine)",
  "user_role": "Public Agricultural Stakeholder / Citizen",
  "user_clearance": "PUBLIC_AGGREGATES_ONLY",
  "sample_count": 5,
  "provenance": "NISR 2025A Microdata",
  "dashboard_link": "/indicators/productivity/?crop=Irish Potato&district=Musanze",
  "answer": "The survey-weighted average yield for Irish Potato in Musanze District (2025A) is 9.50 t/ha (9,500 kg/ha), based on 5 validated field survey plots covering 6.0 hectares.\n\n**AgriLens AI Analysis**:\nMusanze benefits from highly fertile volcanic soils and consistent rainfall, enabling superior Irish potato productivity compared to the national average. Continued focus on certified disease-free seed tubers and proper storage ventilation will help sustain these observed yield levels.",
  "orm_query": "ValidatedObservation.objects.filter(crop__name__icontains='Irish Potato', district__name__iexact='Musanze').aggregate(avg_yield=Avg('calculated_yield_kg_per_ha'), plots=Count('id'))"
}
```

- **`POST /api/v1/assistant/query/`**: Natural language query interface supporting empirical productivity queries, input adoption rates, district rankings, market surveillance, and general agricultural guidance. Enforces role-based clearance boundaries.

### Machine Learning APIs

```http
POST /api/v1/ml/predict-yield/
Content-Type: application/json

{
  "district": "Nyagatare",
  "crop": "Maize",
  "season": "A",
  "irrigation_adoption": 0.45,
  "fertilizer_adoption": 0.70,
  "improved_seed_adoption": 0.85,
  "mechanization_rate": 0.30
}
```

```json
{
  "status": "success",
  "predicted_yield_kg_per_ha": 4350.2,
  "confidence_interval_95": [4120.0, 4580.4],
  "benchmark_district_average": 3150.0,
  "expected_yield_delta_percent": "+38.1%"
}
```

- **`POST /api/v1/ml/predict-yield/`**: Predicts crop yield (kg/ha) based on district inputs, soil factors, and practices.
- **`POST /api/v1/ml/simulate-scenario/`**: Simulates the yield impact of input subsidy or irrigation expansion policy scenarios.
- **`GET /api/v1/ml/district-clusters/`**: Returns agro-ecological district clusters based on yield and input adoption.
- **`GET /api/v1/ml/forecast/`**: Harvest volume forecasting for upcoming seasons.
- **`GET /api/v1/ml/price-forecast/`**: Predictive wholesale commodity price projections.
- **`GET /api/v1/ml/explainability/`**: Returns feature importance weights for transparent model interpretability.
- **`GET /api/v1/ml/models/`**: Returns trained model registry, evaluation metrics (R², RMSE, MAE), and training timestamps.
- **`POST /api/v1/ml/train/`**: Triggers ML model retraining on verified data (Admin/Staff only).

### Notification & Communication APIs

- **`GET /api/v1/notifications/`**: List user notifications (with optional `unread_only=true` filter).
- **`GET /api/v1/notifications/unread_count/`**: Returns badge count of unread notifications.
- **`POST /api/v1/notifications/{id}/mark-read/`**: Mark individual notification as read.
- **`POST /api/v1/notifications/{id}/mark-unread/`**: Mark individual notification as unread.
- **`POST /api/v1/notifications/{id}/dismiss/`**: Dismiss/archive notification.
- **`POST /api/v1/notifications/mark-all-read/`**: Mark all user notifications as read.
- **`GET /api/v1/notifications/preferences/`**: View and update email/in-app notification preferences.

---

## 🧪 Testing & Quality Assurance

AgriLens is verified by an extensive automated test suite covering unit calculations, workflow state machines, role permissions, and REST APIs:

```bash
# Run the complete test suite
.\venv\Scripts\python.exe -m pytest -v

# Run specific functional test suites:
# 1. Notifications & Background Dispatch
.\venv\Scripts\python.exe -m pytest tests/test_apps/test_notifications.py -v

# 2. RBAC, Tokenized Activation & Security
.\venv\Scripts\python.exe -m pytest tests/test_apps/test_rbac_and_user_management.py -v

# 3. Maker-Checker Data Entry Workflow
.\venv\Scripts\python.exe -m pytest tests/test_apps/test_manual_entry_workflow.py -v

# 4. Commodity Market Surveillance
.\venv\Scripts\python.exe -m pytest tests/test_apps/test_commodity_prices.py -v

# 5. Machine Learning & Predictors
.\venv\Scripts\python.exe -m pytest tests/test_ml/ -v
```

---

## 🔒 Data Governance & Scientific Integrity

### 1. Data Provenance & Lineage
Every agricultural metric in AgriLens maintains an immutable audit trail linking it to its source dataset (e.g., `SAS 2025 Season A`, `SAS 2024 Season A`, or manual field observations), including the collector ID, verification timestamp, and validation status.

### 2. Survey Sampling Weighting
All aggregated district and provincial yields are computed using official NISR household and parcel survey weights ($W_i$) to prevent sample distribution bias:
$$\bar{Y} = \frac{\sum (W_i \times P_i)}{\sum (W_i \times A_i)}$$
where $P_i$ represents weighted harvest production (kg) and $A_i$ represents parcel area (ha).

### 3. Non-Causal Reporting Framework
In adherence to statistical best practices, AgriLens explicitly distinguishes **correlation** from **causation**. Yield differences observed between districts with differing input adoption rates are classified as *"associated indicators"* and *"observed disparities"*. Causal claims are prohibited unless backed by randomized control trials (RCT) or econometric instrumental variable models.

---

## 📜 Acknowledgments & Data Attribution

- **National Institute of Statistics of Rwanda (NISR)**: Authoritative Seasonal Agricultural Survey (SAS) microdata, sampling frames, and administrative boundary standards.
- **Ministry of Agriculture and Animal Resources (MINAGRI)**: Strategic agricultural priorities, PSTA-4 guidelines, and crop value-chain standards.
- **Rwanda Agriculture and Animal Resources Development Board (RAB)**: Agro-ecological extension guidelines and input adoption benchmarks.

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

---

<div align="center">
  <sub>Developed with pride for the <b>2026 NISR Big Data Hackathon</b> • Kigali, Rwanda 🇷🇼</sub>
</div>
