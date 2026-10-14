"""
Comprehensive Automated Test Suite for AgriLens Modular Menu Configuration,
Role-Aware Navigation, Template Tags, Context Processors, and UI Components.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.template import Context, Template
from apps.accounts.menu_config import get_user_menu, MENU_CONFIG
from apps.accounts.context_processors import menu_context
from apps.accounts.templatetags.menu_tags import (
    resolve_menu_url,
    is_menu_active,
    is_group_active,
    render_menu_icon,
)
from apps.geography.models import Province, District
from apps.data_management.models import ManualObservation
from apps.agriculture.models import AgriculturalSeason, Crop

User = get_user_model()


class MenuConfigModuleTestCase(TestCase):
    """Tests the Python declarative menu configuration and immutability guarantees."""

    def test_get_user_menu_immutability(self):
        """Mutating the returned menu dictionary must NOT modify global MENU_CONFIG."""
        menu1 = get_user_menu("ADMIN")
        menu1["sidebar"].clear()
        menu1["sidebar"].append({"id": "tampered", "name": "Tampered"})

        # Subsequent call must be completely unaffected
        menu2 = get_user_menu("ADMIN")
        section_ids = [group["id"] for group in menu2["sidebar"]]
        self.assertIn("admin", section_ids)
        self.assertIn("core", section_ids)
        self.assertNotIn("tampered", section_ids)

    def test_anonymous_and_unknown_roles_fallback_safely(self):
        """None and unknown role strings safely fall back to PUBLIC configuration."""
        anon_menu = get_user_menu(None)
        self.assertIn("core", [g["id"] for g in anon_menu["sidebar"]])
        self.assertNotIn("admin", [g["id"] for g in anon_menu["sidebar"]])
        self.assertNotIn("governance", [g["id"] for g in anon_menu["sidebar"]])

        unknown_menu = get_user_menu("UNKNOWN_CUSTOM_ROLE")
        self.assertEqual(len(unknown_menu["sidebar"]), len(anon_menu["sidebar"]))

    def test_superuser_always_gets_admin_menu(self):
        """Superuser flag unconditionally grants ADMIN navigation clearance."""
        su_menu = get_user_menu("PUBLIC", is_superuser=True)
        section_ids = [g["id"] for g in su_menu["sidebar"]]
        self.assertIn("admin", section_ids)
        self.assertIn("governance", section_ids)

    def test_role_navigation_allocations(self):
        """Verifies explicit section allocation across all 7 institutional roles."""
        # 1. ADMIN
        admin_ids = [g["id"] for g in get_user_menu("ADMIN")["sidebar"]]
        self.assertIn("admin", admin_ids)
        self.assertIn("governance", admin_ids)
        self.assertIn("reports", admin_ids)

        # 2. NISR_DATA_MANAGER
        nisr_ids = [g["id"] for g in get_user_menu("NISR_DATA_MANAGER")["sidebar"]]
        self.assertNotIn("admin", nisr_ids)
        self.assertIn("governance", nisr_ids)
        self.assertIn("reports", nisr_ids)

        # 3. ANALYST
        analyst_ids = [g["id"] for g in get_user_menu("ANALYST")["sidebar"]]
        self.assertNotIn("admin", analyst_ids)
        self.assertIn("governance", analyst_ids)

        # 4. NATIONAL_OFFICER
        nat_ids = [g["id"] for g in get_user_menu("NATIONAL_OFFICER")["sidebar"]]
        self.assertNotIn("admin", nat_ids)
        self.assertNotIn("governance", nat_ids)
        self.assertIn("reports", nat_ids)

        # 5. DISTRICT_OFFICER
        dist_ids = [g["id"] for g in get_user_menu("DISTRICT_OFFICER")["sidebar"]]
        self.assertIn("governance", dist_ids)
        self.assertIn("reports", dist_ids)

        # 6. DATA_ENTRY_OFFICER
        entry_ids = [g["id"] for g in get_user_menu("DATA_ENTRY_OFFICER")["sidebar"]]
        self.assertIn("governance", entry_ids)
        self.assertNotIn("reports", entry_ids)

        # 7. REVIEWER
        reviewer_ids = [g["id"] for g in get_user_menu("REVIEWER")["sidebar"]]
        self.assertIn("governance", reviewer_ids)
        self.assertIn("reports", reviewer_ids)

    def test_legacy_roles_backward_compatibility(self):
        """Legacy roles map cleanly with 100% backward compatibility."""
        policy_ids = [g["id"] for g in get_user_menu("POLICY_MAKER")["sidebar"]]
        self.assertIn("core", policy_ids)
        self.assertIn("reports", policy_ids)

        ext_ids = [g["id"] for g in get_user_menu("EXTENSION_OFFICER")["sidebar"]]
        self.assertIn("governance", ext_ids)

        research_ids = [g["id"] for g in get_user_menu("RESEARCHER")["sidebar"]]
        self.assertIn("governance", research_ids)


class MenuTagsTestCase(TestCase):
    """Tests the safe template tags in apps/accounts/templatetags/menu_tags.py."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_resolve_menu_url_handling(self):
        # Direct URL
        self.assertEqual(resolve_menu_url("/api/"), "/api/")

        # Named view
        self.assertEqual(resolve_menu_url("dashboard:overview"), "/dashboard/")

        # Named view with canonical query parameters
        self.assertEqual(
            resolve_menu_url("data_management:manual_entry_list?status=SUBMITTED"),
            "/data-management/manual/?status=SUBMITTED"
        )

        # Invalid route fallback
        self.assertEqual(resolve_menu_url("non_existent:route_xyz"), "#")
        self.assertEqual(resolve_menu_url(""), "#")

    def test_is_menu_active_matching(self):
        # Exact root match
        req_root = self.factory.get("/")
        self.assertTrue(is_menu_active(req_root, "dashboard:public_home"))
        self.assertFalse(is_menu_active(req_root, "dashboard:overview"))

        # Sub-path match
        req_nat = self.factory.get("/dashboard/reports/national/")
        self.assertTrue(is_menu_active(req_nat, "dashboard:reports_national"))
        self.assertFalse(is_menu_active(req_nat, "dashboard:reports_district"))

    def test_is_group_active(self):
        req = self.factory.get("/dashboard/reports/national/")
        group = {
            "id": "reports",
            "submenu": [
                {"name": "National Report", "url": "dashboard:reports_national"},
                {"name": "District Dossier", "url": "dashboard:reports_district"},
            ]
        }
        self.assertTrue(is_group_active(req, group))

        other_group = {
            "id": "admin",
            "submenu": [
                {"name": "Users", "url": "accounts:user_list"}
            ]
        }
        self.assertFalse(is_group_active(req, other_group))

    def test_render_menu_icon(self):
        svg = render_menu_icon("dashboard")
        self.assertIn("<svg", svg)
        self.assertIn('viewBox="0 0 24 24"', svg)

        svg_classed = render_menu_icon("dashboard", extra_class="w-5 h-5")
        self.assertIn('class="w-5 h-5"', svg_classed)


class ContextProcessorAndTemplateTestCase(TestCase):
    """Tests the menu_context processor and dynamic sidebar, navbar, and footer rendering."""

    def setUp(self):
        self.factory = RequestFactory()
        self.province = Province.objects.create(name="Northern", code="01")
        self.district = District.objects.create(name="Musanze", code="0101", province=self.province)

    def test_menu_context_for_anonymous_visitor(self):
        req = self.factory.get("/dashboard/reports/national/")
        req.user = None
        ctx = menu_context(req)

        self.assertIn("sidebar_menu", ctx)
        self.assertIsNone(ctx["user_geo_badge"])
        self.assertEqual(ctx["pending_reviews_count"], 0)
        self.assertGreaterEqual(len(ctx["breadcrumbs"]), 2)
        self.assertEqual(ctx["breadcrumbs"][0]["label"], "AgriLens")

    def test_menu_context_for_district_officer(self):
        user = User.objects.create_user(
            username="agronomist_musanze",
            email="agro@musanze.gov.rw",
            password="SecurePassword123!",
            role=User.Role.DISTRICT_OFFICER,
        )
        user.assigned_districts.add(self.district)

        req = self.factory.get("/dashboard/")
        req.user = user
        ctx = menu_context(req)

        self.assertIn("Musanze", ctx["user_geo_badge"])

    def test_sidebar_and_navbar_render_dynamically(self):
        admin = User.objects.create_superuser(
            username="admin_test",
            email="admin@agrilens.rw",
            password="AdminPassword123!",
        )
        req = self.factory.get("/dashboard/reports/national/")
        req.user = admin

        ctx_data = menu_context(req)
        ctx_data["user"] = admin
        ctx_data["request"] = req

        # 1. Test Sidebar rendering
        sidebar_tpl = Template("{% include 'includes/sidebar.html' %}")
        rendered_sidebar = sidebar_tpl.render(Context(ctx_data))

        self.assertIn("AgriLens", rendered_sidebar)
        self.assertIn("Core Intelligence", rendered_sidebar)
        self.assertIn("Administration", rendered_sidebar)
        self.assertIn("Officers &amp; Roles", rendered_sidebar)
        self.assertIn("aria-label=\"AgriLens Primary Navigation\"", rendered_sidebar)

        # 2. Test Navbar rendering
        navbar_tpl = Template("{% include 'includes/navbar.html' %}")
        rendered_navbar = navbar_tpl.render(Context(ctx_data))

        self.assertIn("National Dashboard", rendered_navbar)
        self.assertIn("Ctrl K", rendered_navbar)
        self.assertIn("nav-breadcrumbs", rendered_navbar)

        # 3. Test Footer rendering
        footer_tpl = Template("{% include 'includes/footer.html' %}")
        rendered_footer = footer_tpl.render(Context(ctx_data))

        self.assertIn("AgriLens Rwanda", rendered_footer)
        self.assertIn("National Institute of Statistics of Rwanda", rendered_footer)

    def test_recommended_public_menu_architecture(self):
        """Validates the exact recommended public menu hierarchy and privacy exclusions."""
        pub_menu = get_user_menu("PUBLIC")
        sidebar = pub_menu["sidebar"]
        
        # Verify sections present
        section_ids = [g["id"] for g in sidebar]
        self.assertIn("core", section_ids)
        self.assertIn("productivity", section_ids)
        self.assertIn("reports", section_ids)
        self.assertIn("domains", section_ids)
        self.assertNotIn("governance", section_ids)
        self.assertNotIn("admin", section_ids)

        # Collect all submenu items for public
        all_subitems = []
        for g in sidebar:
            all_subitems.extend(g.get("submenu", []))
        
        sub_names = [item["name"] for item in all_subitems]
        self.assertIn("Home", sub_names)
        self.assertIn("National Dashboard", sub_names)
        self.assertIn("Agricultural Map", sub_names)
        self.assertIn("Productivity & Yield Gaps", sub_names)
        self.assertIn("National Report", sub_names)
        self.assertIn("Crops & Seasons", sub_names)
        self.assertIn("Seasonal Surveys", sub_names)
        self.assertIn("Commodity Markets", sub_names)
        self.assertIn("Developer API", sub_names)

        # Verify privacy exclusions: farmer registries, subsidies, district dossiers are NOT in public
        self.assertNotIn("Farmers & Cooperatives", sub_names)
        self.assertNotIn("Inputs & Subsidies", sub_names)
        self.assertNotIn("District Dossier", sub_names)

    def test_public_landing_navbar_rendering(self):
        """Tests that the public landing header displays the recommended public menu and officer sign in."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        self.assertIn("AgriLens", content)
        self.assertIn("See Agriculture Through Data.", content)
        self.assertIn("public-role-pill", content)
        self.assertIn("Public", content)
        self.assertIn("National Dashboard", content)
        self.assertIn("Agricultural Map", content)
        self.assertIn("Productivity &amp; Yield Gaps", content)
        self.assertIn("Reports &amp; Bulletins", content)
        self.assertIn("Crops &amp; Seasons", content)
        self.assertIn("Seasonal Surveys", content)
        self.assertIn("Commodity Markets", content)
        self.assertIn("Developer API", content)
        self.assertIn("Officer Sign In", content)
        self.assertIn("/accounts/login/", content)
