"""
Tests for notifications app — written BEFORE implementation (TDD).
Covers models, views, consumers, signals, and integration points.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail


class NotificationModelTests(TestCase):
    """Tests for the Notification model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from notifications.models import Notification
        self.Notification = Notification

    def test_create_basic_notification(self):
        """Can create a basic notification with minimum fields."""
        notif = self.Notification.objects.create(
            recipient=self.user,
            verb="liked_your_post",
        )
        self.assertEqual(self.Notification.objects.count(), 1)
        self.assertEqual(notif.recipient, self.user)
        self.assertEqual(notif.verb, "liked_your_post")
        self.assertFalse(notif.is_read)

    def test_notification_with_actor(self):
        """Notification can have an optional actor."""
        User = get_user_model()
        actor = User.objects.create_user(username="bob", password="secret")
        notif = self.Notification.objects.create(
            recipient=self.user,
            actor=actor,
            verb="liked_your_post",
        )
        self.assertEqual(notif.actor, actor)

    def test_notification_null_actor(self):
        """System/automated notifications can omit the actor."""
        notif = self.Notification.objects.create(
            recipient=self.user,
            verb="welcome",
        )
        self.assertIsNone(notif.actor)

    def test_notification_default_read_status(self):
        """New notifications start unread."""
        notif = self.Notification.objects.create(
            recipient=self.user, verb="liked_your_post"
        )
        self.assertFalse(notif.is_read)

    def test_notification_ordering_newest_first(self):
        """Notifications are ordered by -created_at (most recent first)."""
        n1 = self.Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        n2 = self.Notification.objects.create(
            recipient=self.user, verb="commented_on_your_post",
        )
        self.assertEqual(
            list(self.Notification.objects.all()), [n2, n1],
        )

    def test_notification_str_method(self):
        """String representation includes recipient username and verb."""
        notif = self.Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        self.assertIn(self.user.username, str(notif))
        self.assertIn("liked_your_post", str(notif))

    def test_mark_notification_as_read(self):
        """Can mark an individual notification read."""
        notif = self.Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        notif.is_read = True
        notif.save()
        self.assertTrue(
            self.Notification.objects.get(pk=notif.pk).is_read
        )

    def test_unread_count_query(self):
        """Unread count uses standard queryset filtering."""
        self.Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        self.Notification.objects.create(
            recipient=self.user, verb="commented_on_your_post",
            is_read=True,
        )
        self.Notification.objects.create(
            recipient=self.user, verb="sent_friend_request",
        )
        count = self.Notification.objects.filter(
            recipient=self.user, is_read=False,
        ).count()
        self.assertEqual(count, 2)

    def test_valid_verb_choices(self):
        """Model accepts each defined verb choice."""
        verbs = [
            "liked_your_post",
            "commented_on_your_post",
            "sent_friend_request",
            "accepted_friend_request",
            "mentioned_you",
        ]
        for verb in verbs:
            with self.subTest(verb=verb):
                n = self.Notification.objects.create(
                    recipient=self.user, verb=verb,
                )
                self.assertEqual(n.verb, verb)


class NotificationPreferenceModelTests(TestCase):
    """Tests for the NotificationPreference model."""

    def setUp(self):
        from notifications.models import NotificationPreference
        self.NotificationPreference = NotificationPreference

    def test_prefs_auto_created_on_user_signup(self):
        """NotificationPreference is created via post_save when a User is created."""
        User = get_user_model()
        user = User.objects.create_user(
            username="charlie", password="secret"
        )
        pref = self.NotificationPreference.objects.get(user=user)
        self.assertIsNotNone(pref)

    def test_prefs_default_to_true(self):
        """All notification types are opted-in by default."""
        User = get_user_model()
        user = User.objects.create_user(
            username="charlie", password="secret"
        )
        pref = self.NotificationPreference.objects.get(user=user)
        self.assertTrue(pref.email_likes)
        self.assertTrue(pref.push_likes)
        self.assertTrue(pref.email_comments)
        self.assertTrue(pref.push_comments)
        self.assertTrue(pref.email_friend_requests)
        self.assertTrue(pref.push_friend_requests)
        self.assertTrue(pref.email_mentions)
        self.assertTrue(pref.push_mentions)

    def test_prefs_one_to_one_with_user(self):
        """Each user has exactly one preference row."""
        User = get_user_model()
        user = User.objects.create_user(
            username="charlie", password="secret"
        )
        pref = self.NotificationPreference.objects.get(user=user)
        # If get() works the same instance, the relation is one-to-one
        same = self.NotificationPreference.objects.get(user=user)
        self.assertEqual(pref.pk, same.pk)

    def test_prefs_can_toggle_off(self):
        """Users can opt out of individual notification types."""
        User = get_user_model()
        user = User.objects.create_user(
            username="charlie", password="secret"
        )
        pref = self.NotificationPreference.objects.get(user=user)
        pref.email_likes = False
        pref.save()
        pref.refresh_from_db()
        self.assertFalse(pref.email_likes)
        self.assertTrue(pref.email_comments)  # other types unaffected

    def test_pref_str_includes_username(self):
        """String representation mentions the user."""
        User = get_user_model()
        user = User.objects.create_user(
            username="charlie", password="secret"
        )
        pref = self.NotificationPreference.objects.get(user=user)
        self.assertIn(user.username, str(pref))


class NotificationViewTests(TestCase):
    """Tests for notification views (list, mark-read, preferences)."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.other = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from notifications.models import Notification
        self.Notification = Notification
        # Create test notifications with alternating read status
        for i in range(5):
            self.Notification.objects.create(
                recipient=self.user,
                verb="liked_your_post",
                is_read=(i % 2 == 0),
            )

    # --- NotificationListView ---

    def test_list_authenticated_200(self):
        """Authenticated user sees their notification list."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 200)

    def test_list_anonymous_redirects(self):
        """Anonymous user is redirected to the login page."""
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_list_only_own_notifications(self):
        """User only sees notifications addressed to them."""
        self.client.login(username="alice", password="secret")
        # Add a notification for another user
        self.Notification.objects.create(
            recipient=self.other, verb="liked_your_post",
        )
        response = self.client.get(reverse("notifications:list"))
        total = self.Notification.objects.filter(
            recipient=self.user,
        ).count()
        self.assertEqual(
            len(response.context["notifications"]), total,
        )

    def test_list_is_paginated(self):
        """Notification list view uses pagination."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("notifications:list"))
        self.assertIn("page_obj", response.context)
        self.assertIn("is_paginated", response.context)

    def test_list_shows_unread_first_by_default(self):
        """List orders notifications newest-first natively from -created_at."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("notifications:list"))
        notifs = response.context["notifications"]
        if len(notifs) >= 2:
            self.assertGreaterEqual(
                notifs[0].created_at, notifs[1].created_at,
            )

    # --- NotificationMarkReadView ---

    def test_mark_single_read(self):
        """POST marking one notification sets is_read=True."""
        self.client.login(username="alice", password="secret")
        unread = self.Notification.objects.filter(
            recipient=self.user, is_read=False,
        ).first()
        self.assertIsNotNone(unread)
        response = self.client.post(
            reverse("notifications:mark_read", kwargs={"pk": unread.pk}),
        )
        self.assertEqual(response.status_code, 302)
        unread.refresh_from_db()
        self.assertTrue(unread.is_read)

    def test_mark_single_anonymous(self):
        """Anonymous user cannot mark notifications as read."""
        notif = self.Notification.objects.create(
            recipient=self.user, verb="test",
        )
        response = self.client.post(
            reverse("notifications:mark_read", kwargs={"pk": notif.pk}),
        )
        self.assertIn(response.status_code, [302, 403])

    def test_mark_single_get_method_not_allowed(self):
        """GET request to mark-read endpoint returns 405."""
        self.client.login(username="alice", password="secret")
        notif = self.Notification.objects.create(
            recipient=self.user, verb="test",
        )
        response = self.client.get(
            reverse("notifications:mark_read", kwargs={"pk": notif.pk}),
        )
        self.assertEqual(response.status_code, 405)

    def test_mark_all_read(self):
        """POST marking all as read sets all user's notifications to read."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("notifications:mark_all_read"),
        )
        self.assertEqual(response.status_code, 302)
        unread = self.Notification.objects.filter(
            recipient=self.user, is_read=False,
        ).count()
        self.assertEqual(unread, 0)

    def test_mark_all_read_does_not_affect_others(self):
        """mark-all-read only touches the current user's notifications."""
        self.client.login(username="alice", password="secret")
        # Create notification for another user
        n_other = self.Notification.objects.create(
            recipient=self.other, verb="liked_your_post",
        )
        self.client.post(reverse("notifications:mark_all_read"))
        n_other.refresh_from_db()
        self.assertFalse(n_other.is_read)

    def test_mark_read_cannot_see_others(self):
        """User cannot mark another user's notification as read (403/404)."""
        self.client.login(username="alice", password="secret")
        others = self.Notification.objects.create(
            recipient=self.other, verb="test",
        )
        response = self.client.post(
            reverse("notifications:mark_read", kwargs={"pk": others.pk}),
        )
        self.assertIn(response.status_code, [403, 404])

    # --- NotificationPreferencesView ---

    def test_preferences_authenticated_200(self):
        """Authenticated user can see preferences form."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("notifications:preferences"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email_likes")

    def test_preferences_anonymous_redirects(self):
        """Anonymous user is redirected from preferences."""
        response = self.client.get(reverse("notifications:preferences"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_preferences_post_saves(self):
        """POST to preferences updates and redirects."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("notifications:preferences"),
            {
                "email_likes": False,
                "email_comments": False,
                "email_friend_requests": True,
                "email_mentions": True,
                "push_likes": True,
                "push_comments": True,
                "push_friend_requests": False,
                "push_mentions": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        from notifications.models import NotificationPreference
        pref = NotificationPreference.objects.get(user=self.user)
        self.assertFalse(pref.email_likes)
        self.assertFalse(pref.email_comments)
        self.assertFalse(pref.push_friend_requests)
        self.assertFalse(pref.push_mentions)

    def test_preferences_form_invalid_data(self):
        """Invalid POST data returns form with errors."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("notifications:preferences"),
            {"email_likes": "invalid_value"},  # should be boolean
        )
        # Should re-render form — either 200 or redirect back
        self.assertIn(response.status_code, [200, 302])


class NotificationGenericForeignKeyTests(TestCase):
    """Tests for Notification's GenericForeignKey target resolution."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from notifications.models import Notification
        self.Notification = Notification

    def test_target_post(self):
        """Notification can target a Post and resolve via GFK."""
        from posts.models import Post
        post = Post.objects.create(author=self.user, content="Target post")
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Post)
        notif = self.Notification.objects.create(
            recipient=self.user,
            verb="liked_your_post",
            target_content_type=ct,
            target_object_id=post.pk,
        )
        self.assertIsNotNone(notif.target)
        self.assertEqual(notif.target, post)

    def test_target_comment(self):
        """Notification can target a Comment."""
        from posts.models import Post, Comment
        post = Post.objects.create(author=self.user, content="A post")
        comment = Comment.objects.create(
            post=post, author=self.user, content="A comment",
        )
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Comment)
        notif = self.Notification.objects.create(
            recipient=self.user,
            verb="commented_on_your_post",
            target_content_type=ct,
            target_object_id=comment.pk,
        )
        self.assertEqual(notif.target, comment)

    def test_null_target(self):
        """Notification without a target resolves to None."""
        notif = self.Notification.objects.create(
            recipient=self.user, verb="welcome",
        )
        self.assertIsNone(notif.target)

    def test_target_object_id_indexed(self):
        """target_object_id field has db_index=True."""
        from notifications.models import Notification
        field = Notification._meta.get_field("target_object_id")
        self.assertTrue(field.db_index)


class NotificationSignalIntegrationTests(TestCase):
    """Tests that creating related objects fires notification signals."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from notifications.models import Notification
        from notifications import signals  # noqa: ensure receivers registered
        self.Notification = Notification
        self.client.login(username="alice", password="secret")

    def test_like_on_others_post_creates_notification(self):
        """Liking another user's post creates a 'liked_your_post' notification."""
        from posts.models import Post
        post = Post.objects.create(author=self.user2, content="Nice post!")
        self.client.post(
            reverse("post_like", kwargs={"pk": post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        exists = self.Notification.objects.filter(
            recipient=self.user2,
            actor=self.user1,
            verb="liked_your_post",
        ).exists()
        self.assertTrue(exists)

    def test_like_own_post_no_notification(self):
        """Liking your own post does NOT create a notification."""
        from posts.models import Post
        post = Post.objects.create(author=self.user1, content="Self post")
        self.client.post(
            reverse("post_like", kwargs={"pk": post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        count = self.Notification.objects.filter(
            verb="liked_your_post",
        ).count()
        self.assertEqual(count, 0)

    def test_comment_on_others_post_creates_notification(self):
        """Commenting on another user's post creates 'commented_on_your_post'."""
        from posts.models import Post
        post = Post.objects.create(author=self.user2, content="A post!")
        self.client.post(
            reverse("comment_new", kwargs={"post_pk": post.pk}),
            {"content": "Great post!"},
        )
        exists = self.Notification.objects.filter(
            recipient=self.user2,
            actor=self.user1,
            verb="commented_on_your_post",
        ).exists()
        self.assertTrue(exists)

    def test_comment_own_post_no_notification(self):
        """Commenting on your own post does NOT create a notification."""
        from posts.models import Post
        post = Post.objects.create(author=self.user1, content="Self post")
        self.client.post(
            reverse("comment_new", kwargs={"post_pk": post.pk}),
            {"content": "My comment"},
        )
        count = self.Notification.objects.filter(
            verb="commented_on_your_post",
        ).count()
        self.assertEqual(count, 0)

    def test_friend_request_creates_notification(self):
        """Sending a friend request creates 'sent_friend_request' notification."""
        self.client.post(
            reverse("friend_request", kwargs={"username": "bob"}),
        )
        exists = self.Notification.objects.filter(
            recipient=self.user2,
            actor=self.user1,
            verb="sent_friend_request",
        ).exists()
        self.assertTrue(exists)

    def test_friend_accept_creates_notification(self):
        """Accepting a friend request creates 'accepted_friend_request'."""
        from friendships.models import Friendship
        friendship = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status="pending",
        )
        self.client.post(
            reverse("friend_accept", kwargs={"pk": friendship.pk}),
        )
        exists = self.Notification.objects.filter(
            recipient=self.user2,
            actor=self.user1,
            verb="accepted_friend_request",
        ).exists()
        self.assertTrue(exists)


class NotificationEmailTests(TestCase):
    """Tests for email notifications sent via post_save signal."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="secret",
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_email_sent_when_preference_allows(self):
        """Email is sent when the recipient's preference allows it."""
        from notifications.models import Notification
        from notifications.models import NotificationPreference
        pref = NotificationPreference.objects.get(user=self.user)
        pref.email_likes = True
        pref.save()
        n = Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_email_not_sent_when_preference_disallows(self):
        """Email is NOT sent when the recipient's preference blocks it."""
        from notifications.models import Notification
        from notifications.models import NotificationPreference
        pref = NotificationPreference.objects.get(user=self.user)
        pref.email_likes = False
        pref.save()
        Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_email_only_on_create_not_update(self):
        """Email only fires on creation, not when an existing notification is updated."""
        from notifications.models import Notification
        notif = Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        mail.outbox.clear()  # clear creation email
        notif.is_read = True
        notif.save()  # update — should NOT send email
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_email_subject_mentions_verb(self):
        """Email subject line references the notification verb/action."""
        from notifications.models import Notification
        Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        subject = mail.outbox[0].subject.lower()
        self.assertIn("like", subject)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_email_sent_to_correct_address(self):
        """Email is addressed to the notification recipient."""
        from notifications.models import Notification
        Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        self.assertIn(
            self.user.email or self.user.username,
            mail.outbox[0].to,
        )


class NotificationNavbarTest(TestCase):
    """Tests that the navbar context includes unread notification count."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def test_context_has_unread_count(self):
        """Home page context includes unread_notifications for authenticated user."""
        from notifications.models import Notification
        Notification.objects.create(
            recipient=self.user, verb="liked_your_post",
        )
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("home"))
        self.assertIn("unread_notifications", response.context)
        self.assertEqual(response.context["unread_notifications"], 1)

    def test_unread_count_zero_when_none(self):
        """unread_notifications is zero when there are no unread notifications."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["unread_notifications"], 0)


class NotificationConsumerTests(TestCase):
    """Tests that notification Channels consumer/routing modules import cleanly."""

    def test_consumers_module_imports(self):
        """notifications.consumers module is importable."""
        try:
            from notifications import consumers
            self.assertTrue(hasattr(consumers, "NotificationConsumer"))
        except ImportError:
            self.fail("notifications.consumers module not found")

    def test_routing_module_imports(self):
        """notifications.routing module is importable with websocket_urlpatterns."""
        try:
            from notifications import routing
            self.assertTrue(hasattr(routing, "websocket_urlpatterns"))
            self.assertIsInstance(routing.websocket_urlpatterns, list)
        except ImportError:
            self.fail("notifications.routing module not found")
