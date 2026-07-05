"""Tests for the friendships app — state machine, CRUD, views."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Friendship

User = get_user_model()


class FriendshipModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("alice", password="pass123")
        self.user2 = User.objects.create_user("bob", password="pass123")
        self.user3 = User.objects.create_user("carol", password="pass123")

    def test_send_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="pending"
        )
        self.assertEqual(friendship.status, "pending")
        self.assertEqual(Friendship.friend_status(self.user1, self.user2), "pending")

    def test_accept_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="pending"
        )
        friendship.status = "accepted"
        friendship.save()

        self.assertTrue(Friendship.are_friends(self.user1, self.user2))
        self.assertTrue(Friendship.are_friends(self.user2, self.user1))

    def test_reject_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="pending"
        )
        friendship.status = "rejected"
        friendship.save()

        self.assertFalse(Friendship.are_friends(self.user1, self.user2))
        self.assertEqual(Friendship.friend_status(self.user1, self.user2), "rejected")

    def test_get_friends(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="accepted"
        )
        Friendship.objects.create(
            from_user=self.user3, to_user=self.user1, status="accepted"
        )

        friends = Friendship.get_friends(self.user1)
        self.assertIn(self.user2.id, friends)
        self.assertIn(self.user3.id, friends)
        self.assertEqual(len(friends), 2)

    def test_get_friends_excludes_non_accepted(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="pending"
        )
        Friendship.objects.create(
            from_user=self.user3, to_user=self.user1, status="rejected"
        )

        friends = Friendship.get_friends(self.user1)
        self.assertEqual(len(friends), 0)

    def test_are_friends_bidirectional(self):
        """Friendship is symmetric — direction doesn't matter."""
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="accepted"
        )
        self.assertTrue(Friendship.are_friends(self.user2, self.user1))

    def test_mutual_friends(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="accepted"
        )
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user3, status="accepted"
        )
        # user1 and user3 are not friends — user2 is mutual
        mutual = Friendship.get_mutual_friends(self.user1, self.user3)
        self.assertIn(self.user2.id, mutual)

    def test_friend_status_self(self):
        self.assertEqual(Friendship.friend_status(self.user1, self.user1), "self")

    def test_friend_status_none(self):
        self.assertEqual(Friendship.friend_status(self.user1, self.user2), "none")

    def test_unique_constraint(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="pending"
        )
        with self.assertRaises(Exception):
            Friendship.objects.create(
                from_user=self.user1, to_user=self.user2, status="pending"
            )

    def test_friend_count_property(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="accepted"
        )
        Friendship.objects.create(
            from_user=self.user3, to_user=self.user1, status="accepted"
        )
        self.assertEqual(self.user1.friend_count, 2)

    def test_block_prevents_friendship(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="blocked"
        )
        self.assertFalse(Friendship.are_friends(self.user1, self.user2))


class FriendshipViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("alice", password="pass123")
        self.user2 = User.objects.create_user("bob", password="pass123")
        self.client.login(username="alice", password="pass123")

    def test_send_friend_request_view(self):
        url = reverse("friendships:send_request", kwargs={"pk": self.user2.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"sent": True})
        self.assertTrue(
            Friendship.objects.filter(
                from_user=self.user1, to_user=self.user2, status="pending"
            ).exists()
        )

    def test_send_request_to_self_returns_error(self):
        url = reverse("friendships:send_request", kwargs={"pk": self.user1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"error": "Cannot send request to yourself"}
        )

    def test_accept_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        url = reverse("friendships:accept_request", kwargs={"pk": friendship.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"accepted": True})
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, "accepted")

    def test_reject_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        url = reverse("friendships:reject_request", kwargs={"pk": friendship.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"rejected": True})
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, "rejected")

    def test_remove_friend(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="accepted"
        )
        url = reverse("friendships:remove_friend", kwargs={"pk": self.user2.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"removed": True})
        self.assertFalse(Friendship.are_friends(self.user1, self.user2))

    def test_friend_request_list_requires_login(self):
        self.client.logout()
        url = reverse("friendships:friend_requests")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_pending_requests_appear_in_list(self):
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        url = reverse("friendships:friend_requests")
        response = self.client.get(url)
        self.assertContains(response, self.user2.username)

    def test_duplicate_request_returns_error(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="pending"
        )
        url = reverse("friendships:send_request", kwargs={"pk": self.user2.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_remove_non_friend_returns_error(self):
        url = reverse("friendships:remove_friend", kwargs={"pk": self.user2.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_accept_rejected_request(self):
        """Re-sending a friend request is blocked if a record exists in that direction."""
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status="rejected"
        )
        url = reverse("friendships:send_request", kwargs={"pk": self.user2.pk})
        response = self.client.post(url)
        # get_or_create returns existing (from_user, to_user) pair
        self.assertEqual(response.status_code, 400)
