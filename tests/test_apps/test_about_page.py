"""
Tests for About AgriLens Public Page (Milestone 6 Design).
Verifies route resolution, HTTP 200 OK, public accessibility, template structure,
and exact copy matching the institutional mission, vision, values, and agricultural overview.
"""
from django.test import TestCase, Client
from django.urls import reverse


class AboutPageTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_page_status_and_templates(self):
        """Verify the About page loads with HTTP 200 and uses the proper template hierarchy."""
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/about.html')
        self.assertTemplateUsed(response, 'public_base.html')

    def test_about_page_named_reverse(self):
        """Verify named route 'dashboard:about' resolves to '/about/'."""
        self.assertEqual(reverse('dashboard:about'), '/about/')

    def test_about_hero_content(self):
        """Verify hero title, subtitle, and visual badge are rendered."""
        response = self.client.get('/about/')
        self.assertContains(response, "About AgriLens")
        self.assertContains(response, "Data-driven agriculture for a better tomorrow.")

    def test_about_pillars_mission_vision_values(self):
        """Verify left card pillars: Mission, Vision, and Core Values."""
        response = self.client.get('/about/')
        
        # Mission
        self.assertContains(response, "Our Mission")
        self.assertContains(
            response,
            "To provide reliable, accessible and actionable agricultural data that supports evidence-based decisions"
        )
        self.assertContains(response, "productive, resilient and sustainable Rwanda.")

        # Vision
        self.assertContains(response, "Our Vision")
        self.assertContains(
            response,
            "A future where data empowers farmers, communities and institutions to achieve food security and inclusive economic growth."
        )

        # Values
        self.assertContains(response, "Our Values")
        self.assertContains(response, "Integrity")
        self.assertContains(response, "Innovation")
        self.assertContains(response, "Collaboration")
        self.assertContains(response, "Impact")

    def test_about_rwanda_agriculture_overview(self):
        """Verify right card: Rwanda Agriculture overview, farmer photograph, and CTA button."""
        response = self.client.get('/about/')
        self.assertContains(response, "Rwanda Agriculture")
        self.assertContains(
            response,
            "Rwanda's agriculture is the backbone of our economy, supporting millions of households and driving rural development."
        )

        self.assertContains(response, "AgriLens brings together data, technology and people")
        self.assertContains(response, "Explore the Map")
        self.assertContains(response, "/geography/")
        self.assertContains(response, "about_rwanda_farmers.jpg")

    def test_navbar_active_state_on_about_page(self):
        """Verify that the navbar highlights the About link when visiting /about/."""
        response = self.client.get('/about/')
        self.assertContains(response, 'class="public-nav-link active"')
