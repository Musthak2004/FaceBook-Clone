"""
Tests for stories app — written BEFORE implementation (TDD).
Covers models, views, auto-expiry, and cleanup.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


class StoryModelTests(TestCase):
    """Tests for the Story model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from stories.models import Story
        self.Story = Story

    def test_create_story(self):
        """Can create a story with a user."""
        story = self.Story.objects.create(
            user=self.user,
            caption="My first story",
        )
        self.assertEqual(self.Story.objects.count(), 1)
        self.assertEqual(story.user, self.user)
        self.assertEqual(story.caption, "My first story")

    def test_story_str(self):
        """String representation shows user and truncated caption."""
        story = self.Story.objects.create(
            user=self.user,
            caption="A wonderful day at the beach with friends",
        )
        self.assertIn(self.user.username, str(story))
        self.assertIn("wonderful", str(story))

    def test_story_expires_at_default(self):
        """Story has auto-set expires_at ~24h in the future."""
        story = self.Story.objects.create(
            user=self.user,
        )
        self.assertIsNotNone(story.expires_at)
        # Should be roughly 24 hours from now
        diff = story.expires_at - timezone.now()
        self.assertAlmostEqual(diff.total_seconds(), 86400, delta=60)

    def test_story_created_at(self):
        """Story has auto-set created_at."""
        story = self.Story.objects.create(user=self.user)
        self.assertIsNotNone(story.created_at)

    def test_active_stories_manager(self):
        """active_stories manager only returns non-expired stories."""
        # Create an active story
        self.Story.objects.create(user=self.user)
        # Create an expired story by setting expires_at in the past
        expired = self.Story.objects.create(user=self.user)
        expired.expires_at = timezone.now() - timedelta(hours=1)
        expired.save()

        active = self.Story.active_stories.all()
        self.assertEqual(active.count(), 1)

    def test_story_image_field(self):
        """Story has an image field."""
        story = self.Story(user=self.user)
        self.assertTrue(hasattr(story, "image"))
        # image is required — model validation ensures it's set


class CleanupStoriesCommandTests(TestCase):
    """Tests for the cleanup_stories management command."""

    def setUp(self):
        from stories.models import Story
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", password="secret"
        )
        # Create an expired story
        expired = Story.objects.create(user=user)
        expired.expires_at = timezone.now() - timezone.timedelta(hours=1)
        expired.save()
        # Create a non-expired story
        Story.objects.create(user=user)

    def test_cleanup_command(self):
        """Command deletes expired stories only."""
        from stories.models import Story
        self.assertEqual(Story.objects.count(), 2)

        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("cleanup_stories", stdout=out)
        output = out.getvalue()

        self.assertEqual(Story.objects.count(), 1)
        self.assertIn("Deleted 1", output)

    def test_cleanup_command_no_expired(self):
        """Command handles no expired stories gracefully."""
        from stories.models import Story
        Story.objects.all().delete()
        # All stories already deleted by previous test cleanup
        # Create only active stories
        from stories.models import Story as S
        User = get_user_model()
        user = User.objects.first()
        S.objects.create(user=user)

        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("cleanup_stories", stdout=out)
        output = out.getvalue()

        self.assertIn("No expired", output)


class StoryListViewTests(TestCase):
    """Tests for story list view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.friend = User.objects.create_user(
            username="bob", password="secret"
        )
        cls.non_friend = User.objects.create_user(
            username="charlie", password="secret"
        )

    def setUp(self):
        from stories.models import Story
        from friendships.models import Friendship
        self.Story = Story

        # Make bob a friend of alice
        Friendship.objects.create(
            from_user=self.user,
            to_user=self.friend,
            status="accepted",
        )
        # Also the reverse direction
        Friendship.objects.create(
            from_user=self.friend,
            to_user=self.user,
            status="accepted",
        )

        # Create stories
        Story.objects.create(user=self.friend, caption="Friend's story")
        Story.objects.create(
            user=self.non_friend, caption="Non-friend's story"
        )

    def test_list_authenticated(self):
        """Authenticated user sees friends' active stories."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("stories:list"))
        self.assertEqual(response.status_code, 200)

    def test_list_anonymous_redirect(self):
        """Anonymous user redirected to login."""
        response = self.client.get(reverse("stories:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_list_shows_only_friends_stories(self):
        """Story list only shows stories from friends."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("stories:list"))
        stories = response.context.get("stories", [])
        usernames = [s.user.username for s in stories]
        self.assertIn("bob", usernames)
        self.assertNotIn("charlie", usernames)


class StoryCreateViewTests(TestCase):
    """Tests for creating a story."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def test_create_view_authenticated(self):
        """Authenticated user sees creation form."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("stories:create"))
        self.assertEqual(response.status_code, 200)

    def test_create_view_anonymous_redirect(self):
        """Anonymous user redirected from create."""
        response = self.client.get(reverse("stories:create"))
        self.assertEqual(response.status_code, 302)

    def test_create_story(self):
        """POST creates a story with current user."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("stories:create"),
            {"caption": "Test story caption"},
        )
        self.assertEqual(response.status_code, 302)
        from stories.models import Story
        story = Story.objects.first()
        self.assertIsNotNone(story)
        self.assertEqual(story.user, self.user)
        self.assertEqual(story.caption, "Test story caption")


class StoryDetailViewTests(TestCase):
    """Tests for story detail/auto-advance view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.story_user = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from stories.models import Story
        self.story = Story.objects.create(
            user=self.story_user,
            caption="A story to view",
        )

    def test_detail_authenticated(self):
        """Authenticated user can view a story."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(
            reverse("stories:detail", kwargs={"pk": self.story.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A story to view")

    def test_detail_anonymous_redirect(self):
        """Anonymous user redirected from story detail."""
        response = self.client.get(
            reverse("stories:detail", kwargs={"pk": self.story.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_detail_shows_user_stories(self):
        """Detail shows all active stories for the story's user."""
        from stories.models import Story
        Story.objects.create(
            user=self.story_user,
            caption="Second story",
        )
        self.client.login(username="alice", password="secret")
        response = self.client.get(
            reverse("stories:detail", kwargs={"pk": self.story.pk}),
        )
        self.assertEqual(response.status_code, 200)
