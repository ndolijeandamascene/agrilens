from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.template import Context, Template
from apps.accounts.menu_config import get_user_menu, MENU_CONFIG
from apps.accounts.context_processors import menu_context
from apps.accounts.templatetags.menu_tags import resolve_menu_url, is_menu_active, is_group_active, render_menu_icon
from apps.geography.models import Province, District

User = get_user_model()


class MenuConfigTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.province = Province.objects.create(name="Northern", code="01")
        self.district = District.objects.create(name="Musanze", code="0101", province=self.province)

    def test_admin_menu_has_administration_section(self):
        admin_menu = get_user_menu("ADMIN")
        section_ids = [group["id"] for group in admin_menu["sidebar"]]
        self.assertIn("admin", section_ids)
        self.assertIn("governance", section_ids)
        self.assertIn("reports", section_ids)

    def test_analyst_and_public_menu_lacks_admin_section(self):
        analyst_menu = get_user_menu("ANALYST")
        analyst_section_ids = [group["id"] for group in analyst_menu["sidebar"]]
        self.assertNotIn("admin", analyst_section_ids)

        public_menu = get_user_menu("PUBLIC")
        public_section_ids = [group["id"] for group in public_menu["sidebar"]]
        self.assertNotIn("admin", public_section_ids)
        self.assertNotIn("governance", public_section_ids)

    def test_legacy_roles_backward_compatibility(self):
        policy_menu = get_user_menu("POLICY_MAKER")
        national_menu = get_user_menu("NATIONAL_OFFICER")
        self.assertEqual(len(policy_menu["sidebar"]), len(national_menu["sidebar"]))

        extension_menu = get_user_menu("EXTENSION_OFFICER")
        district_menu = get_user_menu("DISTRICT_OFFICER")
        self.assertEqual(len(extension_menu["sidebar"]), len(district_menu["sidebar"]))

    def test_superuser_always_gets_admin_menu(self):
        superuser_menu = get_user_menu("PUBLIC", is_superuser=True)
        section_ids = [group["id"] for group in superuser_menu["sidebar"]]
        self.assertIn("admin", section_ids)

    def test_resolve_menu_url_tag(self):
        # Direct path
        self.assertEqual(resolve_menu_url("/api/"), "/api/")
        
        # Valid view name
        self.assertEqual(resolve_menu_url("dashboard:overview"), "/dashboard/")
        
        # View name with query parameter
        self.assertEqual(
            resolve_menu_url("data_management:manual_entry_list?status=pending"),
            "/data-management/manual/?status=pending"
        )
        
        # Invalid view fallback
        self.assertEqual(resolve_menu_url("invalid:non_existent_route"), "#")

    def test_is_menu_active_tag(self):
        req = self.factory.get("/dashboard/reports/national/")
        self.assertTrue(is_menu_active(req, "dashboard:reports_national"))
        self.assertFalse(is_menu_active(req, "dashboard:reports_district"))

        req_root = self.factory.get("/")
        self.assertTrue(is_menu_active(req_root, "dashboard:public_home"))
        self.assertFalse(is_menu_active(req_root, "dashboard:overview"))

    def test_menu_context_processor_for_anonymous_visitor(self):
        req = self.factory.get("/")
        req.user = None
        ctx = menu_context(req)
        self.assertIn("sidebar_menu", ctx)
        self.assertIsNone(ctx["user_geo_badge"])

    def test_menu_context_processor_for_district_officer(self):
        user = User.objects.create_user(
            username="dist_officer",
            email="dist@agrilens.rw",
            password="TestPassword123!",
            role=User.Role.DISTRICT_OFFICER,
        )
        user.assigned_districts.add(self.district)

        req = self.factory.get("/dashboard/")
        req.user = user
        ctx = menu_context(req)
        self.assertIn("sidebar_menu", ctx)
        self.assertIn("Musanze", ctx["user_geo_badge"])

    def test_sidebar_template_renders_dynamically(self):
        user = User.objects.create_superuser(
            username="super_test",
            email="super@agrilens.rw",
            password="SuperPassword123!",
        )
        req = self.factory.get("/dashboard/")
        req.user = user

        ctx_data = menu_context(req)
        ctx_data["user"] = user
        ctx_data["request"] = req

        template = Template("{% include 'includes/sidebar.html' %}")
        rendered = template.render(Context(ctx_data))

        self.assertIn("AgriLens", rendered)
        self.assertIn("Core Intelligence", rendered)
        self.assertIn("Administration", rendered)
        self.assertIn("Officers &amp; Roles", rendered)
