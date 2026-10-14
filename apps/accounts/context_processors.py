"""
Global template context processors for AgriLens navigation, breadcrumbs, search, and user metadata.
"""
from .menu_config import get_user_menu


# Cached lightweight list of Rwanda's 30 districts for quick command jump palette
_RWANDA_DISTRICTS = [
    {"name": "Bugesera", "province": "Eastern"},
    {"name": "Burera", "province": "Northern"},
    {"name": "Gakenke", "province": "Northern"},
    {"name": "Gasabo", "province": "Kigali City"},
    {"name": "Gatsibo", "province": "Eastern"},
    {"name": "Gicumbi", "province": "Northern"},
    {"name": "Gisagara", "province": "Southern"},
    {"name": "Huye", "province": "Southern"},
    {"name": "Kamonyi", "province": "Southern"},
    {"name": "Karongi", "province": "Western"},
    {"name": "Kayonza", "province": "Eastern"},
    {"name": "Kicukiro", "province": "Kigali City"},
    {"name": "Kirehe", "province": "Eastern"},
    {"name": "Muhanga", "province": "Southern"},
    {"name": "Musanze", "province": "Northern"},
    {"name": "Ngoma", "province": "Eastern"},
    {"name": "Ngororero", "province": "Western"},
    {"name": "Nyabihu", "province": "Western"},
    {"name": "Nyagatare", "province": "Eastern"},
    {"name": "Nyamagabe", "province": "Southern"},
    {"name": "Nyamasheke", "province": "Western"},
    {"name": "Nyanza", "province": "Southern"},
    {"name": "Nyarugenge", "province": "Kigali City"},
    {"name": "Nyaruguru", "province": "Southern"},
    {"name": "Rubavu", "province": "Western"},
    {"name": "Ruhango", "province": "Southern"},
    {"name": "Rulindo", "province": "Northern"},
    {"name": "Rusizi", "province": "Western"},
    {"name": "Rutsiro", "province": "Western"},
    {"name": "Rwamagana", "province": "Eastern"},
]


def _build_breadcrumbs(request):
    """Constructs breadcrumb trail from request path."""
    crumbs = [{"label": "AgriLens", "url": "/"}]
    path = request.path.strip("/")
    if not path:
        return crumbs

    segments = path.split("/")
    accumulated = ""
    label_map = {
        "dashboard": "Dashboard",
        "reports": "Reports & Bulletins",
        "national": "National Report",
        "district": "District Dossier",
        "indicators": "Productivity & Gap",
        "productivity": "Yield Gap Intelligence",
        "agriculture": "Agricultural Domains",
        "crops": "Crops & Seasons",
        "geography": "Geographic Scope",
        "districts": "Districts & Mapping",
        "surveys": "Seasonal Surveys",
        "farmers": "Farmers & Coops",
        "inputs": "Inputs & Subsidies",
        "markets": "Commodity Markets",
        "data-management": "Data Governance",
        "manual": "Field Observation Registry",
        "new": "Submit Observation",
        "review": "Review Observation",
        "edit": "Edit",
        "accounts": "Security & Administration",
        "users": "Officers & Roles",
        "audit-log": "Security Audit Trail",
        "profile": "Officer Profile",
        "login": "Sign In",
    }

    for idx, seg in enumerate(segments):
        accumulated += f"/{seg}"
        label = label_map.get(seg, seg.replace("-", " ").replace("_", " ").title())
        is_last = (idx == len(segments) - 1)
        crumbs.append({
            "label": label,
            "url": accumulated if not is_last else None,
            "is_last": is_last,
        })
    return crumbs


def menu_context(request):
    """
    Injects dynamic role-based sidebar menu items, geographic assignment badges,
    pending review count, breadcrumbs, and command palette items into all templates.
    """
    breadcrumbs = _build_breadcrumbs(request)

    if getattr(request, "user", None) and request.user.is_authenticated:
        role = getattr(request.user, "role", "PUBLIC")
        is_super = getattr(request.user, "is_superuser", False)
        menu = get_user_menu(role, is_superuser=is_super)
        sidebar = list(menu.get("sidebar", []))

        # Compute geographic scope badge for UI header/footer
        geo_badge = None
        if hasattr(request.user, "is_district_officer") and request.user.is_district_officer:
            try:
                districts = list(request.user.assigned_districts.values_list("name", flat=True))
                if districts:
                    geo_badge = f"Districts: {', '.join(districts)}"
                else:
                    geo_badge = "District Scope: All Districts"
            except Exception:
                geo_badge = "District Scope"
        elif hasattr(request.user, "assigned_province") and request.user.assigned_province:
            geo_badge = f"Province: {request.user.assigned_province.name}"
        elif role in ["ADMIN", "NISR_DATA_MANAGER", "ANALYST", "NATIONAL_OFFICER"] or is_super:
            geo_badge = "National Jurisdiction"

        # Compute count of pending field submissions for officers with review clearance
        pending_reviews_count = 0
        if role in ["ADMIN", "REVIEWER", "NISR_DATA_MANAGER", "DISTRICT_OFFICER"] or is_super:
            try:
                from apps.data_management.models import ManualObservation
                pending_qs = ManualObservation.objects.filter(review_status=ManualObservation.ReviewStatus.SUBMITTED)
                if hasattr(request.user, "is_district_officer") and request.user.is_district_officer:
                    district_ids = request.user.get_authorized_district_ids()
                    if district_ids:
                        pending_qs = pending_qs.filter(district_id__in=district_ids)
                pending_reviews_count = pending_qs.count()
            except Exception:
                pending_reviews_count = 0

        return {
            "sidebar_menu": sidebar,
            "user_geo_badge": geo_badge,
            "pending_reviews_count": pending_reviews_count,
            "breadcrumbs": breadcrumbs,
            "command_palette_districts": _RWANDA_DISTRICTS,
        }

    # Public visitor fallback
    return {
        "sidebar_menu": get_user_menu("PUBLIC").get("sidebar", []),
        "user_geo_badge": None,
        "pending_reviews_count": 0,
        "breadcrumbs": breadcrumbs,
        "command_palette_districts": _RWANDA_DISTRICTS,
    }
