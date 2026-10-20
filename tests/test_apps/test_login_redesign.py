from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User


class OfficerLoginRedesignTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "ValidPass123!"
        self.user = User.objects.create_user(
            username="officer_rwanda",
            email="officer@minagri.gov.rw",
            password=self.password,
            first_name="Jean",
            last_name="Mugabo",
            role=User.Role.ANALYST
        )

    def test_login_page_renders_successfully(self):
        """Verifies GET /accounts/login/ returns 200 with all reference mockup components."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Hero Brand & Headlines
        self.assertIn("AgriLens", content)
        self.assertIn("See Agriculture Through Data.", content)
        self.assertIn("Smarter Agriculture.", content)
        self.assertIn("A Prosperous", content)
        self.assertIn("Rwanda.", content)
        self.assertIn("highlight-rwanda", content)

        # 4 Core Value Pillars
        self.assertIn("Real Data", content)
        self.assertIn("From NISR &amp; MINAGRI", content)
        self.assertIn("Interactive Maps", content)
        self.assertIn("Explore Rwanda", content)
        self.assertIn("Actionable Insights", content)
        self.assertIn("For farmers, businesses &amp; policymakers", content)
        self.assertIn("Sustainable Future", content)
        self.assertIn("Better data. Better decisions.", content)

        # Footer Platform Badge
        self.assertIn("Rwanda Agricultural Intelligence Platform", content)
        self.assertIn("Powered by data. Driven by people.", content)

        # Right White Login Card
        self.assertIn("Officer Login", content)
        self.assertIn("Access your workspace and manage agricultural data, reports and analytics.", content)
        self.assertIn("Username or Email", content)
        self.assertIn("Password", content)
        self.assertIn("Remember me", content)
        self.assertIn("Forgot password?", content)
        self.assertIn("Sign In", content)
        self.assertIn("Login with SSO", content)
        self.assertIn("Not an officer?", content)
        self.assertIn("Visit public portal", content)

    def test_login_with_username_success(self):
        """Officers can sign in using their official username."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'officer_rwanda',
            'password': self.password
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_email_success(self):
        """Officers can sign in seamlessly using their email address."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'officer@minagri.gov.rw',
            'password': self.password
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_remember_me(self):
        """Remember me option sets 2-week session expiry."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'officer_rwanda',
            'password': self.password,
            'remember_me': 'on'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        # Session should be extended (> 1 day)
        self.assertGreater(self.client.session.get_expiry_age(), 86400)

    def test_login_invalid_credentials_error_message(self):
        """Invalid credentials provide clear, secure error notification."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'officer_rwanda',
            'password': 'WrongPassword999'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("Invalid username or password", content)

    def test_authenticated_user_redirected_to_dashboard(self):
        """Logged-in users visiting login page are redirected to dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard:overview'), response.url)
