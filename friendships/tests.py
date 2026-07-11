"""
Tests for friendships app.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Friendship


class FriendshipTests(TestCase):
    """Test friend request flow."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="user1", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="user2", password="secret"
        )

    def test_send_friend_request(self):
        self.client.login(username="user1", password="secret")
        response = self.client.post(
            reverse("friend_request", kwargs={"username": "user2"})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Friendship.objects.count(), 1)
        self.assertEqual(
            Friendship.objects.first().status, "pending"
        )

    def test_accept_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status="pending",
        )
        self.client.login(username="user2", password="secret")
        response = self.client.post(
            reverse("friend_accept", kwargs={"pk": friendship.pk})
        )
        self.assertEqual(response.status_code, 302)
        # Check friendship is accepted
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, "accepted")
        # Check reverse friendship was created
        self.assertTrue(
            Friendship.objects.filter(
                from_user=self.user2,
                to_user=self.user1,
                status="accepted",
            ).exists()
        )
