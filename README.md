# AgriLens

> **See Agriculture Through Data.**

AgriLens is a data-driven agricultural intelligence and decision-support platform developed for the **2026 NISR Big Data Hackathon – Track 1: Agricultural Productivity**.

The platform uses official NISR agricultural data and other authorized open/public datasets to identify agricultural productivity gaps, analyze agricultural practices and risks, and provide practical insights through interactive maps, dashboards, analytics, and intelligent alerts.

---

# 1. Hackathon Context

AgriLens is designed specifically for:

**NISR 2026 Big Data Hackathon – Track 1: Agricultural Productivity**

### Track Challenge

> Use data to develop innovative solutions that address real agricultural challenges facing Rwanda.

The solution may address areas including:

* Small-scale irrigation
* Soil conservation and fertility management
* Post-harvest collection and storage
* Agricultural productivity
* Processing and value addition
* Export market opportunities

The solution must be informed by NISR data and may use other open/public datasets related to:

* Agriculture
* Food security
* Climate
* Markets
* Geography
* Other relevant public information

AgriLens should demonstrate practical value for:

* Farmers
* Agricultural planners
* Policymakers
* Government institutions
* Development partners

---

# 2. Project Vision

Rwanda produces large amounts of agricultural data, but raw data alone does not provide an easy way to understand where agricultural challenges exist and where opportunities may be available.

AgriLens transforms agricultural data into understandable intelligence.

The platform should help answer questions such as:

* Where is agricultural productivity low?
* Which crops perform better in different areas?
* Where are irrigation opportunities?
* Where are post-harvest losses high?
* How widely are improved seeds being used?
* Where is fertilizer being used?
* Where is agricultural mechanization occurring?
* Which areas have significant productivity gaps?
* Where are processing and value-addition opportunities?
* Which agricultural products show market opportunities?

---

# 3. Core Concept

AgriLens follows this architecture:

```text
                    NISR DATA
                       |
                       v
              Data Ingestion
                       |
                       v
          Cleaning & Validation
                       |
                       v
              Data Processing
                       |
                       v
             PostgreSQL Database
                       |
                       v
            Agricultural Analytics
                       |
          +------------+------------+
          |            |            |
          v            v            v
     Productivity    Risk        Market
     Intelligence  Analysis   Intelligence
          |            |            |
          +------------+------------+
                       |
                       v
                 AgriLens
                  Platform
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
      Maps         Dashboard       Smart Insights
```

---

# 4. Main Objective

Build a professional agricultural intelligence platform that converts official agricultural datasets into:

* Agricultural indicators
* Geographic insights
* Productivity comparisons
* Productivity gap analysis
* Agricultural risk analysis
* Market intelligence
* Interactive visualizations
* Practical decision-support information

The project must prioritize **data accuracy and methodological correctness over visual appearance**.

---

# 5. Signature Feature: Productivity Gap Intelligence

The primary innovative feature of AgriLens should be **Productivity Gap Intelligence**.

The system compares agricultural productivity between:

* Provinces
* Districts
* Crops
* Agricultural seasons
* Years

Example:

```text
MAIZE PRODUCTIVITY

District A
Yield: 4,200 kg/ha

District B
Yield: 2,700 kg/ha

Observed productivity gap: 35.7%
```

The system can then display available contextual indicators:

```text
District A
-------------------------
Irrigation        32%
Improved seed     71%
Fertilizer        64%
Mechanization     28%
Loss rate          7%

District B
-------------------------
Irrigation        14%
Improved seed     49%
Fertilizer        41%
Mechanization     11%
Loss rate         16%
```

The system must **not automatically claim causation**.

Use terms such as:

* Observed difference
* Associated indicator
* Potential factor
* Area for investigation

unless a statistically appropriate causal methodology has been implemented.

---

# 6. Main Platform Modules

## 6.1 Overview Dashboard

The main dashboard should display:

* Total production
* Average yield
* Agricultural area
* Post-harvest loss rate
* Irrigation adoption
* Improved seed adoption
* Fertilizer adoption
* Mechanization
* Quantity sold
* Processing rate

Filters:

```text
Year
Season
Province
District
Crop
```

---

## 6.2 Productivity Intelligence

Analyze:

* Production
* Yield
* Cultivated area
* Productivity trends
* Crop comparisons
* District comparisons
* Province comparisons
* Productivity gaps

Charts:

* Bar charts
* Line charts
* Ranking tables
* Geographic maps

---

## 6.3 Crop Intelligence

Each crop should have a dedicated analysis page.

Example:

```text
Crop: Maize

Production
Yield
Cultivated Area
Average Selling Price
Sales Rate
Storage Rate
Processing Rate
Loss Rate

Agricultural Practices
- Irrigation
- Fertilizer
- Improved Seeds
- Mechanization
- Soil Conservation

Geographic Distribution

Historical Trend
```

Only display indicators that can actually be calculated from available data.

---

# 7. Agricultural Practices

Analyze adoption and distribution of:

### Irrigation

* Irrigation adoption
* Irrigation technique
* Water source
* Irrigated area

### Soil Conservation

* Erosion level
* Anti-erosion practices
* Land consolidation
* Related practices

### Fertilizer

* Organic fertilizer
* Inorganic fertilizer
* Fertilizer type
* Quantity
* Cost
* Adoption

### Seeds

* Improved seed adoption
* Seed source
* Seed quantity
* Seed cost

### Mechanization

* Ox plough
* Tractor
* Other machinery
* Mechanization adoption

---

# 8. Post-Harvest Intelligence

Analyze:

* Total crop losses
* Harvesting losses
* Transport losses
* Storage losses
* Processing losses
* Packaging losses
* Sales losses
* Storage
* Processing

Core indicator:

```text
loss_rate_pct =
total_crop_loss_kg / production_kg * 100
```

The system should identify areas and crops with relatively high observed losses.

---

# 9. Market Intelligence

Analyze available:

* Quantity sold
* Selling price
* Market type
* Storage
* Processing
* Value addition

Possible features:

```text
Crop Market Overview
Price Analysis
Sales Analysis
Processing Opportunities
Storage Analysis
Market Comparison
```

If sufficient authorized data becomes available, AgriLens may include an **Export Opportunity Explorer**.

Do not create artificial export recommendations.

---

# 10. Rwanda Agricultural Map

Use an interactive Rwanda map.

Users should be able to navigate:

```text
Rwanda
   |
   +-- Province
          |
          +-- District
                  |
                  +-- Sector
```

A selected district should display:

* Production
* Yield
* Main crops
* Irrigation
* Fertilizer
* Improved seeds
* Mechanization
* Soil conservation
* Post-harvest losses
* Market indicators

Use **Leaflet** for map visualization.

Use **PostGIS** when spatial database functionality is required.

---

# 11. Smart Insights

AgriLens should generate understandable data-driven insights.

Example:

```text
Insight

The selected district has a lower maize yield than the
national/reference average.

The district also shows a lower observed irrigation
adoption rate and a higher post-harvest loss rate.

These indicators may help identify areas for further
agricultural investigation.
```

Insights must be generated from actual data.

Never generate fake statistics.

Never invent a conclusion when the data does not support it.

---

# 12. Data Sources

Primary source:

## NISR Seasonal Agricultural Survey

Priority:

```text
SAS 2025
SAS 2024
SAS 2023
```

Supporting source:

```text
Agriculture Household Survey 2024
```

Other public datasets may be integrated where useful, especially:

* Climate
* Rainfall
* Satellite/open geospatial data
* Agricultural market data
* Public geographic boundaries

All external datasets must be documented.

---

# 13. NISR Data Rules

NISR data is the foundation of AgriLens.

The development team must:

1. Use authorized datasets.
2. Preserve source information.
3. Keep dataset lineage.
4. Validate variables before importing.
5. Never invent NISR variables.
6. Never fabricate missing values.
7. Never hard-code NISR statistics.
8. Document transformations.
9. Document assumptions.
10. Keep source data separate from processed data.

If a variable name is uncertain, inspect the actual dataset or official metadata before implementing it.

---

# 14. Data Pipeline

The ETL pipeline should be:

```text
Official NISR Dataset
        |
        v
     Extract
        |
        v
      Validate
        |
        v
      Clean
        |
        v
    Transform
        |
        v
     Normalize
        |
        v
      Load
        |
        v
   PostgreSQL
        |
        v
   Indicators
        |
        v
   Dashboard
```

Repository structure:

```text
etl/
├── extract/
├── transform/
├── validation/
└── load/
```

---

# 15. Data Storage

Use:

```text
data/
├── raw/
├── interim/
├── processed/
└── reference/
```

### raw/

Original datasets.

Never modify these files.

### interim/

Cleaned intermediate files.

### processed/

Normalized data prepared for database loading.

### reference/

Reference data:

* Province codes
* District codes
* Sector codes
* Crop codes
* Other lookup tables

Do not commit restricted or confidential datasets to GitHub.

---

# 16. Database

Use:

**PostgreSQL**

Use PostGIS where spatial analysis is required.

Core tables:

```text
provinces
districts
sectors

survey_periods
data_sources
source_variables

crops
farmers
households
plots

production_records

seed_records
fertilizer_records
pesticide_records

irrigation_records
soil_conservation_records
mechanization_records

postharvest_loss_records
market_records
production_use_records

land_tenure_records
extension_records
agricultural_tool_records
sustainable_agriculture_records

productivity_indicators
risk_indicators
```

---

# 17. Core Production Record

Conceptually, production data should support:

```text
year
season

province
district
sector

segment
farmer
plot
crop

plot_area_sqm
plot_area_ha

production_kg
harvested_quantity_kg

quantity_sold_kg
stored_quantity_kg
processed_quantity_kg

selling_price_rwf_per_kg

improved_seed_used

organic_fertilizer_used
inorganic_fertilizer_used
pesticide_used
micronutrient_used

irrigated
irrigation_technique

erosion_level
anti_erosion

mechanized
ox_plough_used
tractor_used

total_loss_kg
harvesting_loss_kg
transport_loss_kg
storage_loss_kg
processing_loss_kg
packaging_loss_kg
sales_loss_kg

survey_weight
```

The exact NISR variable-to-database mapping must always be validated against the actual source files.

---

# 18. Important Indicators

## Yield

```text
yield_kg_per_ha =
production_kg / plot_area_ha
```

## Production Growth

```text
production_growth_pct =
(current_production - previous_production)
/
previous_production
* 100
```

## Yield Growth

```text
yield_growth_pct =
(current_yield - previous_yield)
/
previous_yield
* 100
```

## Loss Rate

```text
loss_rate_pct =
total_crop_loss_kg
/
production_kg
* 100
```

## Sales Rate

```text
sales_rate_pct =
quantity_sold_kg
/
production_kg
* 100
```

## Storage Rate

```text
storage_rate_pct =
stored_quantity_kg
/
production_kg
* 100
```

## Processing Rate

```text
processed_rate_pct =
processed_quantity_kg
/
production_kg
* 100
```

For survey-level statistics, use appropriate NISR survey weights when required.

---

# 19. Survey Weights

The analytics layer must support weighted calculations.

Examples:

```text
weighted_sum()
weighted_mean()
weighted_percentage()
```

Do not automatically use simple averages for estimates where survey weights are required.

Every weighted indicator should document:

* Weight variable
* Numerator
* Denominator
* Eligibility criteria
* Aggregation level

---

# 20. Technology Stack

## Backend

```text
Python
Django
Django REST Framework
PostgreSQL
PostGIS
```

## Frontend

```text
Django Templates
Tailwind CSS
Alpine.js
Chart.js
Leaflet
```

Do **not** introduce React unless explicitly requested.

The project should remain primarily Django server-rendered.

## Data Science

```text
Pandas
NumPy
Scikit-learn
```

## Background Processing

```text
Celery
Redis
```

---

# 21. Django Applications

Use modular Django applications:

```text
apps/
├── accounts/
├── agriculture/
├── api/
├── dashboard/
├── farmers/
├── geography/
├── indicators/
├── inputs/
├── markets/
└── surveys/
```

### accounts

Authentication, roles and permissions.

### agriculture

Crops, plots, production and agricultural practices.

### farmers

Farmers and households.

### geography

Province, district, sector and spatial information.

### inputs

Seeds, fertilizer, pesticides and micronutrients.

### markets

Sales, prices, markets, storage and processing.

### surveys

Survey metadata and data lineage.

### indicators

Agricultural calculations and analytical indicators.

### dashboard

User-facing dashboard and visualization.

### api

REST API.

---

# 22. API

Use Django REST Framework.

Initial endpoints:

```text
/api/v1/overview/
/api/v1/productivity/
/api/v1/crops/
/api/v1/crops/<id>/
/api/v1/provinces/
/api/v1/districts/
/api/v1/districts/<id>/productivity/
/api/v1/irrigation/
/api/v1/fertilizer/
/api/v1/mechanization/
/api/v1/postharvest-loss/
/api/v1/markets/
/api/v1/trends/
/api/v1/insights/
```

Support filters:

```text
?year=2025
?season=A
?province=01
?district=0101
?crop=maize
```

---

# 23. Data Lineage

Every dataset must be traceable.

Store:

```text
data_source
survey_year
season
file_name
import_date
variable_name
database_field
mapping_version
```

Example:

```text
NISR SAS 2025
      |
      v
Source Variable
      |
      v
Database Field
      |
      v
Indicator
      |
      v
Dashboard Visualization
```

A developer should be able to determine where an important dashboard statistic came from.

---

# 24. Repository Structure

The repository should follow approximately:

```text
agrilens/
│
├── .github/
│   └── workflows/
│
├── apps/
│   ├── accounts/
│   ├── agriculture/
│   ├── api/
│   ├── dashboard/
│   ├── farmers/
│   ├── geography/
│   ├── indicators/
│   ├── inputs/
│   ├── markets/
│   └── surveys/
│
├── analytics/
│   └── notebooks/
│
├── config/
│   └── settings/
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── reference/
│
├── etl/
│   ├── extract/
│   ├── transform/
│   ├── validation/
│   └── load/
│
├── scripts/
├── static/
├── templates/
├── tests/
│
├── requirements.txt
│
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

---

# 25. Security and Git Rules

Never commit:

```text
.env
*.sqlite3
__pycache__/
*.pyc
data/raw/
database dumps
passwords
API keys
private credentials
```

Use:

```text
.env.example
```

for configuration examples.

Do not expose personal or confidential survey information.

---

# 26. User Interface

The design should be:

* Modern
* Professional
* Clean
* Responsive
* Data-focused
* Easy to understand

Use a consistent visual language throughout the platform.

Primary interface:

```text
AgriLens
See Agriculture Through Data.
```

The dashboard should prioritize:

1. Important numbers
2. Rwanda map
3. Trends
4. Comparisons
5. Agricultural practices
6. Post-harvest losses
7. Market intelligence
8. Smart insights

Avoid unnecessary animations and visual clutter.

---

# 27. Innovation Requirements

AgriLens should go beyond a basic dashboard.

The system should progressively support:

### Productivity Gap Detection

Automatically identify significant observed productivity differences.

### Smart Alerts

Example:

```text
High Loss Alert

The selected district has a post-harvest
loss rate above the selected reference level.
```

### Geographic Intelligence

Show agricultural indicators spatially.

### Trend Detection

Identify changes across years and seasons.

### Multi-factor Analysis

Allow users to compare productivity with:

* Irrigation
* Fertilizer
* Seeds
* Mechanization
* Soil conservation
* Post-harvest losses

### Optional Predictive Analytics

Where sufficient historical data exists, explore:

* Yield prediction
* Production forecasting
* Risk identification

Any prediction must clearly show that it is a model output, not an official NISR statistic.

---

# 28. Impact

AgriLens should demonstrate tangible practical impact.

## Farmers

Potentially provide information about:

* Productivity
* Agricultural practices
* Local agricultural conditions
* Post-harvest challenges
* Market information

## Agricultural Planners

Support:

* Geographic prioritization
* Productivity analysis
* Irrigation planning
* Agricultural program monitoring
* Post-harvest interventions

## Policymakers

Support:

* Evidence-based planning
* Agricultural policy analysis
* Resource prioritization
* Monitoring agricultural trends

## Development Partners

Support:

* Identifying areas requiring intervention
* Monitoring agricultural indicators
* Understanding regional differences

---

# 29. Hackathon Evaluation Alignment

AgriLens must explicitly address all five evaluation criteria.

## 1. Problem Understanding & Relevance — 20 points

Clearly demonstrate a real agricultural productivity challenge and explain how the solution aligns with Rwanda's development priorities.

## 2. Data Use & Methodology — 20 points

Demonstrate:

* NISR data usage
* Data preprocessing
* Statistical methodology
* Survey weighting where required
* Analytical methods
* Data lineage

## 3. Tech Innovation — 20 points

Demonstrate:

* Geospatial analysis
* Productivity-gap intelligence
* Smart alerts
* Advanced analytics
* Optional predictive modeling

## 4. Usability & Design — 20 points

Provide:

* Simple navigation
* Interactive maps
* Clear charts
* Useful filters
* Responsive design
* Understandable insights

## 5. Tangible Impact — 20 points

Demonstrate practical applications for:

* Farmers
* Agricultural planners
* Policymakers
* Government
* Development partners

---

# 30. Development Phases

## Phase 1 — Foundation

Build:

* Django project
* PostgreSQL
* Environment configuration
* Authentication
* Base UI
* Geography models
* Survey metadata

## Phase 2 — NISR Data Infrastructure

Build:

* Dataset ingestion
* ETL framework
* Validation
* Data lineage
* NISR 2025 import

## Phase 3 — Agricultural Database

Build:

* Farmers
* Plots
* Crops
* Production
* Agricultural practices
* Inputs
* Markets
* Losses

## Phase 4 — Analytics

Build:

* Yield
* Production
* Growth
* Productivity gaps
* Irrigation
* Fertilizer
* Seeds
* Mechanization
* Soil conservation
* Post-harvest losses
* Market indicators

## Phase 5 — Dashboard

Build:

* Overview
* Rwanda map
* Crop intelligence
* District intelligence
* Productivity comparison
* Agricultural practices
* Market intelligence

## Phase 6 — Smart Intelligence

Build:

* Smart insights
* Alerts
* Productivity-gap detection
* Multi-factor analysis
* Optional predictive models

## Phase 7 — API

Build:

* REST API
* Filtering
* Aggregation
* Dashboard endpoints

## Phase 8 — Testing and Deployment

Complete:

* Unit tests
* ETL tests
* API tests
* UI testing
* Security review
* Performance optimization
* Production deployment

---

# 31. AI Developer Rules

This repository will be developed with assistance from AI coding tools.

The AI developer must follow these rules:

### Rule 1

Understand the existing code before modifying it.

### Rule 2

Do not create duplicate models, services, utilities, or business logic.

### Rule 3

Follow the existing architecture.

### Rule 4

Do not introduce React.

### Rule 5

Do not invent NISR variables.

### Rule 6

Inspect actual NISR datasets before implementing mappings.

### Rule 7

Never fabricate statistics.

### Rule 8

Never silently replace missing data with invented values.

### Rule 9

Write tests for important calculations.

### Rule 10

Use efficient database queries.

Avoid N+1 queries.

Use:

```python
select_related()
prefetch_related()
```

where appropriate.

### Rule 11

Keep ETL logic separate from Django views.

### Rule 12

Keep analytical calculations separate from templates.

### Rule 13

Document statistical assumptions.

### Rule 14

Protect sensitive information.

### Rule 15

Do not commit confidential datasets or credentials.

### Rule 16

Do not break existing functionality when adding features.

### Rule 17

Prefer simple, maintainable solutions over unnecessary complexity.

### Rule 18

If source data is insufficient for a requested feature, do not fabricate a solution. Clearly identify what data is required.

---

# 32. Definition of Done

A feature is complete only when:

* It works with real data.
* It follows the project architecture.
* Database migrations work.
* Tests pass.
* Validation exists where required.
* Errors are handled.
* The UI is responsive.
* No fake data is used.
* Important calculations are tested.
* Data source information is traceable.
* Existing functionality still works.

---

# 33. Initial MVP

The first working version should focus on:

```text
NISR SAS 2025
      |
      +-- Production
      +-- Agricultural Practices
      +-- Fertilizer/Pesticide
      +-- Screening
      |
      v
AgriLens Database
      |
      +-- Yield
      +-- Production
      +-- Irrigation
      +-- Fertilizer
      +-- Improved Seeds
      +-- Mechanization
      +-- Soil Conservation
      +-- Post-Harvest Losses
      |
      v
AgriLens Dashboard
      |
      +-- Rwanda Map
      +-- Productivity Analysis
      +-- Crop Analysis
      +-- District Comparison
      +-- Productivity Gap
      +-- Smart Insights
```

SAS 2024, SAS 2023, AHS 2024, and additional public datasets should be integrated progressively after the core SAS 2025 pipeline is stable.

---

# 34. Final Product Definition

AgriLens is **not simply a dashboard**.

It is an:

> **Agricultural Intelligence and Decision-Support Platform**

that transforms Rwanda's agricultural data into:

```text
DATA
  ↓
KNOWLEDGE
  ↓
INSIGHT
  ↓
DECISION SUPPORT
```

The final product should demonstrate that official agricultural data can be transformed into a practical technology solution that helps users understand agricultural productivity challenges and identify potential opportunities across Rwanda.

**Project Name:** AgriLens

**Tagline:** See Agriculture Through Data.

**Repository:** `agrilens`
