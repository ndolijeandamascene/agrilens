"""
AgriLens Modular Menu Configuration.
Inspired by declarative role-based navigation architecture (decoupling menu structure from template markup).
Provides single source of truth for institutional roles, submenus, and access rules.
"""

# ==============================================================================
# REUSABLE MENU BLOCKS
# ==============================================================================

CORE_INTELLIGENCE_MENU = {
    "id": "core",
    "name": "Core Intelligence",
    "icon": "core",
    "submenu": [
        {"name": "National Dashboard", "url": "dashboard:overview", "icon": "dashboard"},
        {"name": "Public Portal & Map", "url": "dashboard:public_home", "icon": "public"},
    ],
}

PRODUCTIVITY_MENU = {
    "id": "productivity",
    "name": "Productivity & Gap",
    "icon": "productivity",
    "submenu": [
        {"name": "Yield Gap Intelligence", "url": "indicators:productivity", "icon": "trending"},
    ],
}

REPORTS_MENU_FULL = {
    "id": "reports",
    "name": "Reports & Bulletins",
    "icon": "reports",
    "submenu": [
        {"name": "National Report", "url": "dashboard:reports_national", "icon": "report_national"},
        {"name": "District Dossier", "url": "dashboard:reports_district", "icon": "report_district"},
    ],
}

REPORTS_MENU_DISTRICT = {
    "id": "reports",
    "name": "Reports & Bulletins",
    "icon": "reports",
    "submenu": [
        {"name": "District Dossier", "url": "dashboard:reports_district", "icon": "report_district"},
    ],
}

AGRICULTURAL_DOMAINS_MENU = {
    "id": "domains",
    "name": "Agricultural Domains",
    "icon": "domains",
    "submenu": [
        {"name": "Crops & Seasons", "url": "agriculture:crop_list", "icon": "crops"},
        {"name": "Districts & Mapping", "url": "geography:district_list", "icon": "districts"},
        {"name": "Seasonal Surveys", "url": "surveys:survey_list", "icon": "surveys"},
        {"name": "Farmers & Coops", "url": "farmers:farmer_list", "icon": "farmers"},
        {"name": "Inputs & Subsidies", "url": "inputs:input_list", "icon": "inputs"},
        {"name": "Commodity Markets", "url": "markets:market_list", "icon": "markets"},
        {"name": "Developer Data API", "url": "/api/", "icon": "api"},
    ],
}

DATA_GOVERNANCE_MENU_FULL = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "submenu": [
        {"name": "Data Lineage Hub", "url": "data_management:hub", "icon": "lineage"},
        {"name": "Manual Registry", "url": "data_management:manual_entry_list", "icon": "registry"},
        {"name": "Submit Observation", "url": "data_management:manual_entry_create", "icon": "submit"},
    ],
}

DATA_GOVERNANCE_MENU_ANALYST = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "submenu": [
        {"name": "Data Lineage Hub", "url": "data_management:hub", "icon": "lineage"},
        {"name": "Manual Registry", "url": "data_management:manual_entry_list", "icon": "registry"},
    ],
}

DATA_GOVERNANCE_MENU_ENTRY = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "submenu": [
        {"name": "Manual Registry", "url": "data_management:manual_entry_list", "icon": "registry"},
        {"name": "Submit Observation", "url": "data_management:manual_entry_create", "icon": "submit"},
    ],
}

DATA_GOVERNANCE_MENU_REVIEWER = {
    "id": "governance",
    "name": "Data Governance",
    "icon": "governance",
    "submenu": [
        {"name": "Review Queue", "url": "data_management:manual_entry_list?status=pending", "icon": "review"},
        {"name": "All Field Registry", "url": "data_management:manual_entry_list", "icon": "registry"},
    ],
}

ADMINISTRATION_MENU = {
    "id": "admin",
    "name": "Administration",
    "icon": "security",
    "badge": "SYSADMIN",
    "submenu": [
        {"name": "Officers & Roles", "url": "accounts:user_list", "icon": "users"},
        {"name": "Register Officer", "url": "accounts:user_create", "icon": "user_create"},
        {"name": "Security Audit Trail", "url": "accounts:audit_log_list", "icon": "audit_log"},
    ],
}

# ==============================================================================
# ROLE-TO-MENU MAPPING REGISTRY
# ==============================================================================

MENU_CONFIG = {
    # 1. System Administrator
    "ADMIN": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_FULL,
            ADMINISTRATION_MENU,
        ]
    },
    # 2. NISR Data Manager
    "NISR_DATA_MANAGER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_FULL,
        ]
    },
    # 3. Agricultural Data Analyst
    "ANALYST": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ANALYST,
        ]
    },
    # 4. National Officer (MINAGRI)
    "NATIONAL_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },
    # 5. District Agriculture Officer
    "DISTRICT_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_DISTRICT,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ENTRY,
        ]
    },
    # 6. Data Entry Officer
    "DATA_ENTRY_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            DATA_GOVERNANCE_MENU_ENTRY,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },
    # 7. Reviewer / Approver
    "REVIEWER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
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
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },
    "EXTENSION_OFFICER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_DISTRICT,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ENTRY,
        ]
    },
    "RESEARCHER": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
            DATA_GOVERNANCE_MENU_ANALYST,
        ]
    },
    # Public / Anonymous Visitor
    "PUBLIC": {
        "sidebar": [
            CORE_INTELLIGENCE_MENU,
            PRODUCTIVITY_MENU,
            REPORTS_MENU_FULL,
            AGRICULTURAL_DOMAINS_MENU,
        ]
    },
}


def get_user_menu(role=None, is_superuser=False):
    """
    Returns the sidebar menu configuration for the given user role.
    Superusers automatically receive the ADMIN configuration.
    Falls back to 'PUBLIC' for unauthenticated or unassigned users.
    """
    if is_superuser:
        return MENU_CONFIG.get("ADMIN", {})
    if not role:
        return MENU_CONFIG.get("PUBLIC", {})
    return MENU_CONFIG.get(role, MENU_CONFIG.get("PUBLIC", {}))
