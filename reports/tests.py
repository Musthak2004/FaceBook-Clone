"""Tests for the Reports app."""

import json

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from posts.models import Post
from .models import Report

User = get_user_model()


class ReportModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reporter", password="testpass123"
        )
        self.post = Post.objects.create(author=self.user, content="Reportable content")

    def test_create_report(self):
        report = Report.objects.create(
            reporter=self.user,
            content_object=self.post,
            reason="spam",
            description="This is spam",
        )
        self.assertEqual(report.reason, "spam")
        self.assertEqual(report.description, "This is spam")
        self.assertFalse(report.is_reviewed)
        self.assertFalse(report.resolved)

    def test_report_str(self):
        report = Report.objects.create(
            reporter=self.user,
            content_object=self.post,
            reason="harassment",
        )
        # ContentType __str__ uses "app_label | model_name" format, with em-dash separator
        actual = str(report)
        self.assertIn("reporter reported", actual)
        self.assertIn("harassment", actual)
        self.assertIn(str(self.post.id), actual)

    def test_report_all_reasons_valid(self):
        for reason, _ in Report.REASON_CHOICES:
            report = Report.objects.create(
                reporter=self.user,
                content_object=self.post,
                reason=reason,
            )
            self.assertEqual(report.reason, reason)


class ReportViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reporter", password="testpass123"
        )
        self.post = Post.objects.create(author=self.user, content="Post to report")

    def test_create_report_requires_login(self):
        response = self.client.post(
            reverse("reports:create"),
            {"content_type_id": 1, "object_id": 1, "reason": "spam"},
        )
        self.assertEqual(response.status_code, 302)

    def test_create_report_success(self):
        self.client.login(username="reporter", password="testpass123")
        ct = ContentType.objects.get_for_model(Post)
        response = self.client.post(
            reverse("reports:create"),
            data=json.dumps(
                {
                    "content_type_id": ct.id,
                    "object_id": self.post.id,
                    "reason": "spam",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(Report.objects.count(), 1)

    def test_create_report_via_model_name(self):
        self.client.login(username="reporter", password="testpass123")
        response = self.client.post(
            reverse("reports:create"),
            data=json.dumps(
                {
                    "model": "posts.post",
                    "object_id": self.post.id,
                    "reason": "harassment",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_create_report_missing_fields(self):
        self.client.login(username="reporter", password="testpass123")
        response = self.client.post(
            reverse("reports:create"),
            data=json.dumps(
                {
                    "reason": "spam",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_report_invalid_reason(self):
        self.client.login(username="reporter", password="testpass123")
        ct = ContentType.objects.get_for_model(Post)
        response = self.client.post(
            reverse("reports:create"),
            data=json.dumps(
                {
                    "content_type_id": ct.id,
                    "object_id": self.post.id,
                    "reason": "invalid_reason",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_report_invalid_json(self):
        self.client.login(username="reporter", password="testpass123")
        response = self.client.post(
            reverse("reports:create"),
            data="not valid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_report_invalid_content_type(self):
        self.client.login(username="reporter", password="testpass123")
        response = self.client.post(
            reverse("reports:create"),
            data=json.dumps(
                {
                    "model": "nonexistent.model",
                    "object_id": 1,
                    "reason": "spam",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
