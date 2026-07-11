"""
Tests for pages app.
Follows Django for Beginners Ch 10 SimpleTestCase pattern.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class HomePageTests(TestCase):
    """Test homepage functionality."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser",
            password="secret",
        )

    def test_homepage_requires_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_homepage_logged_in(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
