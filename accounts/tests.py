"""Tests for accounts app — profile, last_seen, online status."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class OnlineStatusTests(TestCase):
    """Tests for the is_online property and last_seen behavior."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")

    def test_is_online_false_when_no_last_seen(self):
        self.assertFalse(self.user.is_online)

    def test_is_online_true_when_recent(self):
        self.user.last_seen = timezone.now()
        self.assertTrue(self.user.is_online)

    def test_is_online_false_when_old(self):
        self.user.last_seen = timezone.now() - timedelta(minutes=10)
        self.assertFalse(self.user.is_online)

    def test_is_online_edge_case_4_minutes(self):
        self.user.last_seen = timezone.now() - timedelta(minutes=4)
        self.assertTrue(self.user.is_online)

    def test_last_seen_display_just_now(self):
        self.user.last_seen = timezone.now() - timedelta(seconds=30)
        self.assertEqual(self.user.last_seen_display, "Just now")

    def test_last_seen_display_minutes_ago(self):
        self.user.last_seen = timezone.now() - timedelta(minutes=3)
        self.assertEqual(self.user.last_seen_display, "3m ago")

    def test_last_seen_display_hours_ago(self):
        self.user.last_seen = timezone.now() - timedelta(hours=2)
        self.assertEqual(self.user.last_seen_display, "2h ago")

    def test_last_seen_display_older(self):
        self.user.last_seen = timezone.now() - timedelta(days=3)
        # Should show date like "Jul 02"
        self.assertIn(self.user.last_seen.strftime("%b"), self.user.last_seen_display)

    def test_heartbeat_returns_online_friends(self):
        """Heartbeat endpoint should return status ok."""
        self.client.login(username="alice", password="pass123")
        url = reverse("accounts:heartbeat")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["user_id"], self.user.id)

    def test_heartbeat_updates_last_seen(self):
        """POST to heartbeat should update last_seen."""
        self.client.login(username="alice", password="pass123")
        url = reverse("accounts:heartbeat")
        self.client.post(url)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_seen)
        now = timezone.now()
        diff = now - self.user.last_seen
        self.assertLess(diff, timedelta(seconds=10))  # Within last 10 seconds
