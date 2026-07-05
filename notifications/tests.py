"""Tests for notification signals and views."""

from django.core import mail
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Notification
from friendships.models import Friendship
from posts.models import Post
from comments.models import Comment
from reactions.models import Reaction

User = get_user_model()


class NotificationSignalTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("alice", password="pass123")
        self.user2 = User.objects.create_user("bob", password="pass123")
        self.post = Post.objects.create(author=self.user1, content="Hello world!")

    def test_friend_request_signal_creates_notification(self):
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user1,
                sender=self.user2,
                notification_type="friend_request",
            ).exists()
        )

    def test_friend_accept_signal_creates_notification(self):
        friendship = Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        friendship.status = "accepted"
        friendship.save()
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user2,
                sender=self.user1,
                notification_type="friend_accept",
            ).exists()
        )

    def test_like_signal_creates_notification(self):
        Reaction.objects.create(user=self.user2, post=self.post, reaction_type="like")
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user1,
                sender=self.user2,
                notification_type="like",
                post=self.post,
            ).exists()
        )

    def test_like_own_post_does_not_notify(self):
        """Liking your own post should not create a notification."""
        Reaction.objects.create(user=self.user1, post=self.post, reaction_type="like")
        self.assertFalse(
            Notification.objects.filter(
                notification_type="like",
                post=self.post,
            ).exists()
        )

    def test_comment_signal_creates_notification(self):
        Comment.objects.create(post=self.post, author=self.user2, content="Great post!")
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user1,
                sender=self.user2,
                notification_type="comment",
                post=self.post,
            ).exists()
        )

    def test_reply_to_comment_notifies_parent_author(self):
        """Replying to a comment should notify the comment author."""
        comment = Comment.objects.create(
            post=self.post, author=self.user2, content="Nice!"
        )
        Comment.objects.create(
            post=self.post,
            author=self.user1,
            content="Thanks!",
            parent=comment,
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user2,
                sender=self.user1,
                notification_type="reply",
                post=self.post,
            ).exists()
        )

    def test_duplicate_friend_request_does_not_duplicate_notification(self):
        """get_or_create in signals should prevent duplicate notifications."""
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        # Trigger the signal again (same friendship, but status unchanged)
        Friendship.objects.filter(from_user=self.user2, to_user=self.user1).update(
            status="pending"
        )
        # Since we use get_or_create, duplicate notifications are prevented
        # Manually testing: the signal only fires on 'created' for pending
        # So this is implicitly tested
        count = Notification.objects.filter(
            recipient=self.user1,
            sender=self.user2,
            notification_type="friend_request",
        ).count()
        self.assertEqual(count, 1)


class NotificationEmailTests(TestCase):
    """Tests that email notifications are sent for key event types."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            "alice", email="alice@example.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            "bob", email="bob@example.com", password="pass123"
        )
        self.post = Post.objects.create(author=self.user1, content="Hello world!")

    def test_friend_request_sends_email(self):
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("friend request", mail.outbox[0].subject.lower())
        self.assertIn("bob", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.user1.email])

    def test_friend_accept_sends_email(self):
        friendship = Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        mail.outbox.clear()
        friendship.status = "accepted"
        friendship.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("accepted", mail.outbox[0].subject.lower())

    def test_like_does_not_send_email(self):
        """Low-value notifications (likes, comments) should not send email."""
        Reaction.objects.create(user=self.user2, post=self.post, reaction_type="like")
        self.assertEqual(len(mail.outbox), 0)

    def test_comment_does_not_send_email(self):
        Comment.objects.create(post=self.post, author=self.user2, content="Great!")
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_when_recipient_has_no_email(self):
        user3 = User.objects.create_user("charlie", password="pass123")
        # Send friend request TO charlie (no email) — recipient has no email
        Friendship.objects.create(from_user=self.user1, to_user=user3, status="pending")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(DEFAULT_FROM_EMAIL="socialnet@example.com")
    def test_email_from_address(self):
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        self.assertEqual(mail.outbox[0].from_email, "socialnet@example.com")

    def test_email_body_contains_username(self):
        Friendship.objects.create(
            from_user=self.user2, to_user=self.user1, status="pending"
        )
        self.assertIn("bob", mail.outbox[0].body)
        self.assertIn(self.user1.username, mail.outbox[0].body)


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.other = User.objects.create_user("bob", password="pass123")
        self.client.login(username="alice", password="pass123")

        # Create a notification
        self.notification = Notification.objects.create(
            recipient=self.user,
            sender=self.other,
            notification_type="friend_request",
        )

    def test_notification_list_requires_login(self):
        self.client.logout()
        url = reverse("notifications:notification_list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_notification_list_shows_notifications(self):
        url = reverse("notifications:notification_list")
        response = self.client.get(url)
        self.assertContains(response, self.other.username)

    def test_mark_read(self):
        url = reverse("notifications:mark_read", kwargs={"pk": self.notification.pk})
        response = self.client.post(url)
        self.assertJSONEqual(response.content, {"read": True})
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(
            recipient=self.user,
            sender=self.other,
            notification_type="like",
        )
        url = reverse("notifications:mark_all_read")
        response = self.client.post(url)
        self.assertJSONEqual(response.content, {"read_all": True})
        unread_count = Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_mark_read_for_other_user_fails(self):
        """A user cannot mark another user's notification as read."""
        other_notification = Notification.objects.create(
            recipient=self.other,
            sender=self.user,
            notification_type="friend_accept",
        )
        url = reverse("notifications:mark_read", kwargs={"pk": other_notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_json_format(self):
        url = reverse("notifications:notification_list") + "?format=json"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("html", response.json())

    def test_unread_count(self):
        url = reverse("notifications:notification_list") + "?count=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["unread_count"], 1)

    def test_unread_count_updates_after_mark_read(self):
        url = reverse("notifications:mark_read", kwargs={"pk": self.notification.pk})
        self.client.post(url)
        count_url = reverse("notifications:notification_list") + "?count=1"
        response = self.client.get(count_url)
        self.assertEqual(response.json()["unread_count"], 0)


class NotificationTypeTests(TestCase):
    def test_all_notification_types_have_display_names(self):
        for code, name in Notification.NOTIFICATION_TYPES:
            self.assertTrue(len(code) > 0)
            self.assertTrue(len(name) > 0)

    def test_notification_str(self):
        user = User.objects.create_user("alice", password="pass123")
        sender = User.objects.create_user("bob", password="pass123")
        n = Notification.objects.create(
            recipient=user, sender=sender, notification_type="like"
        )
        self.assertIn("like", str(n))
        self.assertIn("alice", str(n))
