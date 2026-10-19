"""
Tests for Data & API Public Portal and Developer Endpoints (Milestone 5 Design).
Validates HTTP responses, public accessibility, dynamic counts, API v1 routing,
and template fidelity matching the official design mockup.
"""
from django.test import TestCase, Client
from django.urls import reverse
from apps.agriculture.models import Crop, CropCategory, AgriculturalSeason
from apps.geography.models import Province, District


class DataApiPageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create categories and priority crops
        cls.category_cereal = CropCategory.objects.create(name="Cereals", description="Grain crops")
        cls.category_legume = CropCategory.objects.create(name="Legumes", description="Pulse crops")

        cls.season_2025_a = AgriculturalSeason.objects.create(
            year=2025,
            season="A",
            start_date="2024-09-01",
            end_date="2025-02-28"
        )

        cls.province = Province.objects.create(name="Kigali City", code="KGL")
        cls.district1 = District.objects.create(name="Nyarugenge", code="01", province=cls.province)
        cls.district2 = District.objects.create(name="Gasabo", code="02", province=cls.province)

        # 10 priority crops
        priority_names = [
            "Maize", "Marshland Rice", "Climbing Beans", "Bush Beans", "Soyabean",
            "Irish Potato", "Cassava", "Cooking Banana", "Coffee", "Tea"
        ]
        for name in priority_names:
            Crop.objects.create(
                name=name,
                category=cls.category_cereal,
                is_priority_crop=True
            )

        # 2 non-priority crops
        Crop.objects.create(name="Wheat", category=cls.category_cereal, is_priority_crop=False)
        Crop.objects.create(name="Sorghum", category=cls.category_cereal, is_priority_crop=False)

    def setUp(self):
        self.client = Client()

    def test_data_api_public_page_status_and_content(self):
        """Verify the public Data & API page is accessible without authentication and renders all sections."""
        response = self.client.get('/data-api/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/data_api.html')
        self.assertTemplateUsed(response, 'public_base.html')

        # Check Page Title & Hero
        self.assertContains(response, "Data &amp; API")
        self.assertContains(response, "Open data, tools and resources for developers and researchers.")
        self.assertContains(response, "&lt;/&gt;")

        # Check Left Card: Available Data
        self.assertContains(response, "Available Data")
        self.assertContains(response, "Agricultural Statistics")
        self.assertContains(response, "Crop production, area, yield and more.")
        self.assertContains(response, "Geographic Data")
        self.assertContains(response, "Districts, provinces and administrative boundaries.")
        self.assertContains(response, "Market Data")
        self.assertContains(response, "Commodity prices and market information.")
        self.assertContains(response, "Survey Data")
        self.assertContains(response, "SAS, AHS and other agricultural surveys.")
        self.assertContains(response, "Explore Data")

        # Check Right Card: Developer API
        self.assertContains(response, "Developer API")
        self.assertContains(response, "Integrate agricultural data into your applications using our RESTful API.")
        self.assertContains(response, "Real-time and historical data")
        self.assertContains(response, "Standard JSON format")
        self.assertContains(response, "Authentication required")
        self.assertContains(response, "Rate limits apply")
        self.assertContains(response, "View API Documentation")

        # Check Live Code Snippet Box
        self.assertContains(response, "/api/v1/crops/?season=2024-2025")
        self.assertContains(response, '"count":')
        self.assertContains(response, '"results":')

    def test_data_api_named_url_resolution(self):
        """Verify reverse('dashboard:data_api') resolves to '/data-api/'."""
        url = reverse('dashboard:data_api')
        self.assertEqual(url, '/data-api/')

    def test_api_v1_crops_season_filter(self):
        """Verify /api/v1/crops/?season=2024-2025 returns 10 priority crops."""
        response = self.client.get('/api/v1/crops/?season=2024-2025')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('count'), 10)
        self.assertEqual(len(data.get('results', [])), 10)
        crop_names = [c['name'] for c in data['results']]
        self.assertIn('Maize', crop_names)
        self.assertNotIn('Wheat', crop_names)

    def test_api_v1_and_api_root_districts_parity(self):
        """Verify /api/districts/ and /api/v1/districts/ both return district data."""
        r_root = self.client.get('/api/districts/')
        r_v1 = self.client.get('/api/v1/districts/')
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_v1.status_code, 200)
        self.assertEqual(r_root.json()['count'], 2)
        self.assertEqual(r_v1.json()['count'], 2)

    def test_api_docs_endpoints(self):
        """Verify /data-api/docs/ and /api/docs/ return 200 OK."""
        r1 = self.client.get('/data-api/docs/')
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.get('/api/docs/')
        self.assertEqual(r2.status_code, 200)
