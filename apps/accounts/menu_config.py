"""
AgriLens Modular Menu Configuration.
Declarative, role-aware, and decoupled navigation architecture for Rwanda's National Agricultural Intelligence Platform.

Provides a centralized single source of truth for:
- Menu hierarchy and section identifiers
- Reusable modular menu blocks
- Explicit institutional role visibility rules
- Named route resolutions and parameter handling
- Immutability guarantees via deep copying
"""
import copy


# ==============================================================================
# REUSABLE MODULAR MENU BLOCKS
# ==============================================================================

CORE_INTELLIGENCE_MENU = {
    "id": "core",
    "name": "Core Intelligence",
    "icon": "core",
    "description": "Macro-level agricultural productivity and public portal",
    "roles": ["*"],  # Accessible to all users including public
    "submenu": [
        {
            "id": "core_dashboard",
            "name": "National Dashboard",
            "url": "dashboard:overview",
            "icon": "dashboard",
            "description": "Macro KPIs, seasonal trends, and national aggregations",
        },
        {
            "id": "core_public_map",
            "name": "Public Portal & Map",
            "url": "dashboard:public_home",
            "icon": "public",
            "description": "Geospatial Rwanda crop map and public statistics",
        },
    ],
}

PRODUCTIVITY_MENU = {
    "id": "productivity",
    "name": "Productivity & Gap",
    "icon": "productivity",
    "description": "Actual vs. potential yield gap analytics and district rankings",
    "roles": ["*"],
    "submenu": [
        {
            "id": "yield_gap",
            "name": "Yield Gap Intelligence",
            "url": "indicators:productivity",
            "icon": "trending",
            "description": "Crop yield gap indexes, potential yields, and district comparisons",
        },
    ],
}

AGRICULTURAL_INSIGHTS_MENU = {
    "id": "insights",
    "name": "Agricultural Insights",
    "icon": "insights",
    "description": "Evidence-based patterns, data stories, and review queue",
    "roles": ["*"],
    "submenu": [
        {
            "id": "insights_public",
            "name": "Data Stories",
            "url": "insights:public_list",
            "icon": "stories",
            "description": "Published agricultural intelligence and data stories",
        },
        {
            "id": "insights_dashboard",
            "name": "Insights Command",
            "url": "insights:internal_dashboard",
            "icon": "dashboard",
            "description": "Internal insights management dashboard and metrics",
        },
        {
            "id": "insights_review",
            "name": "Review Queue",
            "url": "insights:internal_review_queue",
            "icon": "review",
            "description": "Verify and approve generated agricultural insights",
        },
        {
            "id": "insights_all",
            "name": "All Insights",
            "url": "insights:internal_list",
            "icon": "registry",
            "description": "Searchable repository of all generated and published insights",
        },
    ],
}

AGRICULTURAL_INSIGHTS_MENU_PUBLIC = {
    "id": "insights",
    "name": "Agricultural Insights",
    "icon": "insights",
    "description": "Published agricultural intelligence and data stories",
    "roles": ["PUBLIC"],
    "submenu": [
        {
            "id": "insights_public",
            "name": "Data Stories",
            "url": "insights:public_list",
            "icon": "stories",
            "description": "Published agricultural intelligence and data stories",
        },
    ],
}

REPORTS_MENU_FULL = {
    "id": "reports",
    "name": "Reports & Bulletins",
    "icon": "reports",
    "description": "Official national and district-level seasonal bulletins",
    "roles": ["ADMIN", "NISR_DATA_MANAGER", "ANALYST", "NATIONAL_OFFICER", "REVIEWER", "POLICY_MAKER", "RESEARCHER", "PUBLIC"],
    "submenu": [
        {
            "id": "reports_national",
            "name": "National Report",
            "url": "dashboard:reports_national",
            "icon": "report_national",
            "description": "Seasonal agricultural survey summary and crop production totals",
        },
        {
            "id": "reports_district",
            "name": "District Dossier",
            "url": "dashboard:reports_district",
            "icon": "report_district",
            "description": "District-specific yield matrix, crop profiles, and performance dossiers",
        },
    ],
}

REPORTS_MENU_DISTRICT_ONLY = {
    "id": "reports",
    "name": "Reports & Bulletins",
    "icon": "reports",
    "description": "Local district performance dossiers",
    "roles": ["DISTRICT_OFFICER", "EXTENSION_OFFICER"],
    "submenu": [
        {
            "id": "reports_district",
            "name": "District Dossier",
            "url": "dashboard:reports_district",
            "icon": "report_district",
            "description": "Scoped district agricultural performance and crop breakdown",
        },
    ],
}

DECISION_SUPPORT_MENU = {
    "id": "decision_support",
    "name": "Decision & Impact",
    "icon": "decision",
    "description": "Evidence-driven recommendations, institutional action plans, and impact tracking",
    "roles": ["ADMIN", "NISR_DATA_MANAGER", "ANALYST", "NATIONAL_OFFICER", "DISTRICT_OFFICER", "REVIEWER", "POLICY_MAKER", "RESEARCHER"],
    "submenu": [
        {
            "id": "decision_hub",
            "name": "Decision Hub",
            "url": "decision_support:hub",
            "icon": "hub",
            "description": "Stakeholder intelligence across Government, Banks, Insurers, and Agribusiness",
        },
        {
            "id": "decision_recommendations",
            "name": "Recommendations",
            "url": "decision_support:recommendation_list",
            "icon": "recommendations",
            "description": "Verified evidence-backed recommendations and review queue",
        },
        {
            "id": "decision_impact",
            "name": "Impact Tracking",
            "url": "decision_support:impact_dashboard",
            "icon": "impact",
            "description": "Track 1: Institutional action plans and seasonal yield monitoring",
        },
    ],
}

AGRICULTURAL_DOMAINS_MENU = {
    "id": "domains",
    "name": "Agricultural Domains",
    "icon": "domains",
    "description": "Published agricultural datasets, geographies, markets, and APIs",
    "roles": ["*"],
    "submenu": [
        {
            "id": "domain_crops",
            "name": "Crops & Seasons",
            "url": "agriculture:crop_list",
            "icon": "crops",
            "description": "National crop catalog, varieties, and seasonal cycles",
        },
        {
            "id": "domain_districts",
            "name": "Districts & Mapping",
            "url": "geography:district_list",
            "icon": "districts",
            "description": "Provinces, 30 districts, and administrative boundaries",
        },
        {
            "id": "domain_surveys",
            "name": "Seasonal Surveys",
            "url": "surveys:survey_list",
            "icon": "surveys",
            "description": "Seasonal Agricultural Survey (SAS) waves and sampling methodology",
        },
        {
            "id": "domain_farmers",
            "name": "Farmers & Cooperatives",
            "url": "farmers:farmer_list",
            "icon": "farmers",
            "description": "Smallholder registries, farming typologies, and cooperatives",
        },
        {
            "id": "domain_inputs",
            "name": "Inputs & Subsidies",
            "url": "inputs:input_list",
            "icon": "inputs",
            "description": "Fertilizers, improved seeds, and mechanization programs",
        },
        {
            "id": "domain_markets",
            "name": "Commodity Markets",
            "url": "markets:market_list",
            "icon": "markets",
            "description": "Wholesale and retail agricultural commodity prices",
        },
    ],
}

# ------------------------------------------------------------------------------
# PUBLIC SPECIFIC MODULAR MENU BLOCKS (Recommended Public Architecture)
# ------------------------------------------------------------------------------

CORE_INTELLIGENCE_MENU_PUBLIC = {
    "id": "core",
    "name": "Core Intelligence",
    "icon": "core",
    "description": "Macro-level agricultural productivity and public portal",
    "roles": ["PUBLIC"],
    "submenu": [
        {
            "id": "core_home",
            "name": "Home",
            "url": "dashboard:public_home",
            "icon": "public",
            "description": "AgriLens public landing portal and national overview",
        },
        {
            "id": "core_dashboard",
            "name": "National Dashboard",
            "url": "dashboard:overview",
            "icon": "dashboard",
            "description": "Macro KPIs, seasonal trends, and national aggregations",
        },
        {
            "id": "core_public_map",
            "name": "Agricultural Map",
            "url": "geography:district_list",
            "icon": "districts",
            "description": "Geospatial Rwanda agricultural map and district boundaries",
        },
    ],
}

PRODUCTIVITY_MENU_PUBLIC = {
    "id": "productivity",
    "name": "Productivity & Yield Gaps",
    "icon": "productivity",
    "description": "Actual vs. potential yield gap analytics and district rankings",
    "roles": ["PUBLIC"],
    "submenu": [
        {
            "id": "yield_gap",
            "name": "Productivity & Yield Gaps",
            "url": "indicators:productivity",
            "icon": "trending",
            "description": "Crop yield gap indexes, potential yields, and district comparisons",
        },
    ],
}

REPORTS_MENU_PUBLIC = {
    "id": "reports",
    "name": "Reports & Bulletins",
    "icon": "reports",
    "description": "Published reports only",
    "roles": ["PUBLIC"],
    "submenu": [
        {
            "id": "reports_national",
            "name": "National Report",
            "url": "dashboard:reports_national",
            "icon": "report_national",
            "description": "Published national bulletins and seasonal survey summaries",
        },
    ],
}

AGRICULTURAL_DOMAINS_MENU_PUBLIC = {
    "id": "domains",
    "name": "Agricultural Domains",
    "icon": "domains",
    "description": "Public agricultural datasets, open APIs, and published market data",
    "roles": ["PUBLIC"],
    "submenu": [
        {
            "id": "domain_crops",
            "name": "Crops & Seasons",
            "url": "agriculture:crop_list",
            "icon": "crops",
            "description": "Public crop information, varieties, and seasonal cycles",
        },
        {
            "id": "domain_surveys",
            "name": "Seasonal Surveys",
            "url": "surveys:survey_list",
            "icon": "surveys",
            "description": "Published survey information and SAS methodology",
        },
        {
            "id": "domain_markets",
            "name": "Commodity Markets",
            "url": "markets:market_list",
            "icon": "markets",
            "description": "Published market data and wholesale/retail prices",
        },
    ],
}

DATA_GOVERNANCE_MENU_FULL = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "description": "Complete data ingestion, manual submission, and lineage management",
    "roles": ["ADMIN", "NISR_DATA_MANAGER"],
    "submenu": [
        {
            "id": "gov_hub",
            "name": "Data Lineage Hub",
            "url": "data_management:hub",
            "icon": "lineage",
            "description": "ETL batches, staging tables, and provenance tracking",
        },
        {
            "id": "gov_registry",
            "name": "Manual Registry",
            "url": "data_management:manual_entry_list",
            "icon": "registry",
            "description": "Field observation audit log and verification queue",
        },
        {
            "id": "gov_submit",
            "name": "Submit Observation",
            "url": "data_management:manual_entry_create",
            "icon": "submit",
            "description": "Field survey entry form for ad-hoc crop and harvest data",
        },
    ],
}

DATA_GOVERNANCE_MENU_ANALYST = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "description": "Analytical data lineage and observational audit records",
    "roles": ["ANALYST", "RESEARCHER"],
    "submenu": [
        {
            "id": "gov_hub",
            "name": "Data Lineage Hub",
            "url": "data_management:hub",
            "icon": "lineage",
            "description": "Read-only inspection of ETL batches and provenance",
        },
        {
            "id": "gov_registry",
            "name": "Manual Registry",
            "url": "data_management:manual_entry_list",
            "icon": "registry",
            "description": "Field observation records and validation statuses",
        },
    ],
}

DATA_GOVERNANCE_MENU_ENTRY = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "description": "Field observation entry and localized status tracking",
    "roles": ["DATA_ENTRY_OFFICER", "DISTRICT_OFFICER", "EXTENSION_OFFICER"],
    "submenu": [
        {
            "id": "gov_registry",
            "name": "Manual Registry",
            "url": "data_management:manual_entry_list",
            "icon": "registry",
            "description": "Field observation submission history",
        },
        {
            "id": "gov_submit",
            "name": "Submit Observation",
            "url": "data_management:manual_entry_create",
            "icon": "submit",
            "description": "Enter new ad-hoc agricultural field observation",
        },
    ],
}

DATA_GOVERNANCE_MENU_REVIEWER = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "description": "Observation review and validation workflows",
    "roles": ["REVIEWER"],
    "submenu": [
        {
            "id": "gov_review_queue",
            "name": "Review Queue",
            "url": "data_management:manual_entry_list?status=SUBMITTED",
            "icon": "review",
            "description": "Pending field observations awaiting verification and approval",
        },
        {
            "id": "gov_registry",
            "name": "All Field Registry",
            "url": "data_management:manual_entry_list",
            "icon": "registry",
            "description": "Complete registry of approved, returned, and submitted observations",
        },
    ],
}

ADMINISTRATION_MENU = {
    "id": "admin",
    "name": "Administration",
    "icon": "security",
    "badge": "SYSADMIN",
    "description": "Institutional user management, role assignments, and security audit logs",
    "roles": ["ADMIN"],
    "submenu": [
        {
            "id": "admin_users",
            "name": "Officers & Roles",
            "url": "accounts:user_list",
            "icon": "users",
            "description": "User registry, role delegations, and district assignments",
        },
        {
            "id": "admin_register",
            "name": "Register Officer",
            "url": "accounts:user_create",
            "icon": "user_create",
            "description": "Provision new officer account with single-use password token",
        },
        {
            "id": "admin_audit_log",
            "name": "Security Audit Trail",
            "url": "accounts:audit_log_list",
            "icon": "audit_log",
            "description": "Tamper-evident log of logins, role updates, and approvals",
        },
    ],
}


# ==============================================================================
# CENTRAL ROLE-TO-MENU MAPPING REGISTRY
# ==============================================================================

MENU_CONFIG = {
    # 1. System Administrator (Full system clearance)
    "ADMIN": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_FULL,
            ADMINISTRATION_MENU,
        ]
    },

    # 2. NISR Data Manager (Lineage, batch ingestion, observations, no user admin)
    "NISR_DATA_MANAGER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_FULL,
        ]
    },

    # 3. Agricultural Data Analyst (Intelligence, reports, lineage, field registry read)
    "ANALYST": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ANALYST,
        ]
    },

    # 4. National Officer / MINAGRI (National macro intelligence, reports, domains)
    "NATIONAL_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },

    # 5. District Agriculture Officer (District dossier, domains, localized submission)
    "DISTRICT_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_DISTRICT_ONLY,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ENTRY,
        ]
    },

    # 6. Data Entry Officer (Essential intelligence, domains, observation entry)
    "DATA_ENTRY_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            DATA_GOVERNANCE_MENU_ENTRY,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },

    # 7. Reviewer / Approver (Review validation queue, registry, reports)
    "REVIEWER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            DATA_GOVERNANCE_MENU_REVIEWER,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },

    # Legacy Role Mappings (100% Backward Compatibility)
    "POLICY_MAKER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },
    "EXTENSION_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_DISTRICT_ONLY,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ENTRY,
        ]
    },
    "RESEARCHER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            AGRICULTURAL_INSIGHTS_MENU,
            DECISION_SUPPORT_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ANALYST,
        ]
    },

    # Public / Anonymous Visitor (Published dashboards, maps, reports, and public datasets only)
    "PUBLIC": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU_PUBLIC,
            PRODUCTIVITY_MENU_PUBLIC,
            AGRICULTURAL_INSIGHTS_MENU_PUBLIC,
            REPORTS_MENU_PUBLIC,
            AGRICULTURAL_DOMAINS_MENU_PUBLIC,
        ]
    },
}


def get_user_menu(role=None, is_superuser=False):
    """
    Returns an isolated, deep copy of the sidebar menu configuration for the given user role.

    Guarantees:
    - Superusers always receive the full ADMIN configuration.
    - Anonymous (None) or unknown roles fall back safely to 'PUBLIC'.
    - Immutability: Modifications to the returned dictionary do NOT mutate shared global configuration blocks.
    """
    if is_superuser:
        raw_menu = MENU_CONFIG.get("ADMIN", {})
    elif not role:
        raw_menu = MENU_CONFIG.get("PUBLIC", {})
    else:
        raw_menu = MENU_CONFIG.get(role, MENU_CONFIG.get("PUBLIC", {}))

    return copy.deepcopy(raw_menu)
