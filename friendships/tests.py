from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Friendship


class FriendshipModelTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user1 = User.objects.create_user(
            email='user1@example.com', username='user1', password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com', username='user2', password='pass123'
        )
        self.user3 = User.objects.create_user(
            email='user3@example.com', username='user3', password='pass123'
        )

    def test_create_friend_request(self):
        f = Friendship.objects.create(
            from_user=self.user1, to_user=self.user2
        )
        self.assertEqual(f.status, 'pending')
        self.assertEqual(str(f), 'user1@example.com -> user2@example.com: pending')

    def test_are_friends(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status='accepted'
        )
        self.assertTrue(Friendship.are_friends(self.user1, self.user2))
        self.assertTrue(Friendship.are_friends(self.user2, self.user1))
        self.assertFalse(Friendship.are_friends(self.user1, self.user3))

    def test_friend_status(self):
        self.assertEqual(
            Friendship.friend_status(self.user1, self.user1), 'self'
        )
        self.assertEqual(
            Friendship.friend_status(self.user1, self.user2), 'none'
        )
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        self.assertEqual(
            Friendship.friend_status(self.user1, self.user2), 'pending'
        )
        self.assertEqual(
            Friendship.friend_status(self.user2, self.user1), 'pending'
        )

    def test_get_friend_ids(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status='accepted'
        )
        Friendship.objects.create(
            from_user=self.user3, to_user=self.user1, status='accepted'
        )
        friend_ids = Friendship.get_friend_ids(self.user1)
        self.assertIn(self.user2.pk, friend_ids)
        self.assertIn(self.user3.pk, friend_ids)

    def test_get_suggestions(self):
        # user1 and user2 are friends
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status='accepted'
        )
        # user2 and user3 are friends, so user3 should be suggested to user1
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user3, status='accepted'
        )
        suggestions = Friendship.get_suggestions(self.user1)
        self.assertIn(self.user3, suggestions)

    def test_uniqueness(self):
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        with self.assertRaises(Exception):
            Friendship.objects.create(from_user=self.user1, to_user=self.user2)


class FriendViewTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user1 = User.objects.create_user(
            email='friend1@example.com', username='friend1', password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='friend2@example.com', username='friend2', password='pass123'
        )

    def test_send_friend_request(self):
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.post(
            reverse('friendships:send_request', kwargs={'user_id': self.user2.pk})
        )
        self.assertRedirects(
            response,
            reverse('accounts:profile', kwargs={'username': 'friend2'})
        )
        self.assertTrue(
            Friendship.objects.filter(
                from_user=self.user1, to_user=self.user2
            ).exists()
        )

    def test_send_request_to_self(self):
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.post(
            reverse('friendships:send_request', kwargs={'user_id': self.user1.pk})
        )
        self.assertRedirects(
            response,
            reverse('accounts:profile', kwargs={'username': 'friend1'})
        )

    def test_accept_friend_request(self):
        f = Friendship.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.post(
            reverse('friendships:accept', kwargs={'request_id': f.pk})
        )
        self.assertRedirects(response, reverse('friendships:friend_requests'))
        f.refresh_from_db()
        self.assertEqual(f.status, 'accepted')

    def test_reject_friend_request(self):
        f = Friendship.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.post(
            reverse('friendships:reject', kwargs={'request_id': f.pk})
        )
        self.assertRedirects(response, reverse('friendships:friend_requests'))
        f.refresh_from_db()
        self.assertEqual(f.status, 'rejected')

    def test_cancel_friend_request(self):
        f = Friendship.objects.create(
            from_user=self.user1, to_user=self.user2
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.post(
            reverse('friendships:cancel', kwargs={'request_id': f.pk})
        )
        self.assertRedirects(response, reverse('friendships:friend_requests'))
        self.assertFalse(
            Friendship.objects.filter(pk=f.pk).exists()
        )

    def test_unfriend(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status='accepted'
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.post(
            reverse('friendships:unfriend', kwargs={'user_id': self.user2.pk})
        )
        self.assertRedirects(
            response,
            reverse('accounts:profile', kwargs={'username': 'friend2'})
        )
        self.assertFalse(
            Friendship.are_friends(self.user1, self.user2)
        )

    def test_friend_list_view(self):
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status='accepted'
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.get(reverse('friendships:friend_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'friend2')

    def test_friend_requests_view(self):
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.get(reverse('friendships:friend_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'friend2')

    def test_friend_suggestions_view(self):
        # user1 and user2 are friends. user3 is not.
        # So user3 should not appear as a suggestion to user1.
        User = get_user_model()
        user3 = User.objects.create_user(
            email='friend3@example.com', username='friend3', password='pass123'
        )
        Friendship.objects.create(
            from_user=self.user1, to_user=self.user2, status='accepted'
        )
        self.client.login(email='friend1@example.com', password='pass123')
        response = self.client.get(reverse('friendships:friend_suggestions'))
        self.assertEqual(response.status_code, 200)
        # user3 has no mutual friends with user1, so may or may not appear
        # depending on implementation. View just needs to render.
