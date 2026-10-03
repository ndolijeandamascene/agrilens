# AgriLens &bull; Rwanda Agricultural Intelligence Platform

AgriLens is a data-driven full-stack platform built with Django that harnesses agricultural datasets to analyze productivity, identify challenges, and deliver actionable insights for farming and agricultural decision-making across Rwanda.

---

## 🌾 Platform Architecture & Directory Structure

```text
agrilens/
├── README.md                  # Project overview, documentation & guides
├── manage.py                  # Django CLI entrypoint
├── requirements/              # Split dependency specifications
│   ├── base.txt               # Core framework & data science libraries
│   ├── dev.txt                # Testing & developer tooling
│   └── prod.txt               # Production WSGI & monitoring
├── config/                    # Project-level configuration & settings
│   ├── __init__.py
│   ├── asgi.py                # ASGI asynchronous server interface
│   ├── wsgi.py                # WSGI production server gateway
│   ├── urls.py                # Central URL routing
│   └── settings/              # Environment-tiered settings
│       ├── __init__.py
│       ├── base.py            # Common configuration & app registry
│       ├── dev.py             # Development settings (SQLite, Debug)
│       ├── prod.py            # Production settings (PostgreSQL, Security)
│       └── test.py            # Automated testing configurations
├── apps/                      # Modular domain applications
│   ├── accounts/              # User identity & role-based access control
│   ├── geography/             # Rwanda admin hierarchy (5 Provinces, 30 Districts, Sectors)
│   ├── agriculture/           # Crops, seasonal cycles (Season A, B, C), farming systems
│   ├── farmers/               # Farmer profiles, cooperatives, household plots
│   ├── surveys/               # Seasonal Agricultural Surveys (SAS) data intake
│   ├── inputs/                # Fertilizers, seeds, subsidy program tracking
│   ├── markets/               # Commodity price monitoring across market hubs
│   ├── indicators/            # Yield/ha, productivity metrics, policy KPIs
│   ├── dashboard/             # Visual dashboards, heatmaps & aggregated summaries
│   └── api/                   # RESTful API endpoints for external clients & frontend
├── etl/                       # Data Pipeline (Extract, Transform, Validate, Load)
│   ├── extract/               # Extractors for SAS dumps, market prices, weather data
│   ├── transform/             # Cleaners, unit normalizers, and aggregators
│   ├── validation/            # Schema validation and agronomic sanity checks
│   └── load/                  # Loaders for relational models and data warehouses
├── analytics/                 # Analytical & Modeling Core
│   ├── productivity.py        # Yield gap models & input-yield correlations
│   ├── forecasting.py         # Seasonal production estimates & forecasting
│   ├── spatial.py             # Geospatial & district choropleth analytics
│   └── reporting.py           # Automated digest generation & seasonal bulletins
├── data/                      # Structured Data Repository
│   ├── raw/                   # Immutable raw data files (ODK, SAS dumps, e-Soko)
│   ├── interim/               # Intermediate cleaned/transformed datasets
│   ├── processed/             # Final analytical datasets and geo layers
│   └── reference/             # Rwanda administrative boundaries, crop taxonomy
├── templates/                 # Server-rendered Django HTML templates
│   ├── base.html              # Base layout with navigation and design system
│   ├── includes/              # Partials (navbar, sidebar, footer)
│   ├── dashboard/             # Dashboard views
│   ├── agriculture/           # Crop and seasonal views
│   ├── surveys/               # Survey management screens
│   ├── markets/               # Market price boards
│   └── accounts/              # Authentication & profile views
├── static/                    # Static Web Assets
│   ├── css/                   # Stylesheets & CSS design tokens
│   ├── js/                    # Client JavaScript & visualization hooks
│   └── images/                # Logos, icons, and graphic assets
├── tests/                     # Test Suite
│   ├── conftest.py            # Pytest fixtures and test setup
│   ├── test_apps/             # Unit tests for domain apps
│   ├── test_etl/              # Pipeline verification tests
│   └── test_analytics/        # Mathematical & analytical tests
├── scripts/                   # Management & Bootstrap Automation
│   ├── seed_geography.py      # Seeds Rwanda's 5 provinces and 30 districts
│   ├── run_etl.py             # Triggers end-to-end data pipeline
│   └── setup_dev.py           # Bootstrap developer workspace
└── .github/
    └── workflows/
        └── ci.yml             # GitHub Actions continuous integration pipeline
```

---

## 🇷🇼 Rwanda Agricultural Context

AgriLens is built to reflect Rwanda's agricultural ecosystem:
- **Administrative Hierarchy**: 5 Provinces (Kigali City, Northern, Southern, Eastern, Western), 30 Districts, 416 Sectors, and thousands of Cells and Villages.
- **Agricultural Seasons**:
  - **Season A**: September to February (Major season for cereals and legumes).
  - **Season B**: March to June (Main harvest season).
  - **Season C**: July to September (Marshlands & irrigated farming, predominantly vegetables and Irish potatoes).
- **Core Priority Crops**: Maize, Beans, Irish Potato, Rice, Cassava, Banana, Coffee, and Tea.
- **Data Integration**: Seasonal Agricultural Surveys (SAS), market commodity prices from major trade hubs, input distribution (subsidized fertilizers and improved seeds), and agro-climatic indicators.

---

## 🚀 Getting Started

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # On Windows
# source venv/bin/activate  # On Linux/macOS

# Install development dependencies
pip install -r requirements/dev.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

### 3. Initialize Database & Seed Geography
```bash
python manage.py migrate
python scripts/seed_geography.py
```

### 4. Run Development Server
```bash
python manage.py runserver
```

Access the dashboard at `http://127.0.0.1:8000/`.
