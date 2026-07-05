"""Tests for the Dashboard app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from posts.models import Post
from dashboard.models import Report

User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="normaluser", password="testpass123"
        )
        self.staff_user = User.objects.create_user(
            username="staffuser", password="testpass123", is_staff=True
        )

    def test_dashboard_redirects_non_staff(self):
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_home"))
        self.assertRedirects(response, reverse("core:home"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:dashboard_home"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_home_staff(self):
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_dashboard_home_shows_counts(self):
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_home"))
        context = response.context
        self.assertIn("total_users", context)
        self.assertIn("total_posts", context)
        self.assertIn("total_comments", context)
        self.assertIn("pending_reports", context)

    def test_dashboard_user_management_staff(self):
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_users"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "normaluser")

    def test_dashboard_user_management_non_staff(self):
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_users"))
        self.assertRedirects(response, reverse("core:home"))

    def test_dashboard_post_moderation_staff(self):
        self.client.login(username="staffuser", password="testpass123")
        Post.objects.create(author=self.user, content="Test post for moderation")
        response = self.client.get(reverse("dashboard:dashboard_posts"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test post for moderation")

    def test_dashboard_post_moderation_non_staff(self):
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_posts"))
        self.assertRedirects(response, reverse("core:home"))

    def test_dashboard_report_management_staff(self):
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_reports"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_report_management_non_staff(self):
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.get(reverse("dashboard:dashboard_reports"))
        self.assertRedirects(response, reverse("core:home"))

    def test_resolve_report(self):
        self.client.login(username="staffuser", password="testpass123")
        post = Post.objects.create(author=self.user, content="Reported post")
        report = Report.objects.create(
            reported_by=self.user,
            post=post,
            reason="spam",
        )
        response = self.client.post(
            reverse("dashboard:resolve_report", kwargs={"pk": report.pk}),
        )
        self.assertRedirects(response, reverse("dashboard:dashboard_reports"))
        report.refresh_from_db()
        self.assertTrue(report.is_resolved)
        self.assertEqual(report.resolved_by, self.staff_user)
