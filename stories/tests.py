from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Story

User = get_user_model()


def get_test_image():
    """Return a small in-memory image file."""
    from PIL import Image

    buf = BytesIO()
    img = Image.new("RGB", (100, 100), "red")
    img.save(buf, "JPEG")
    buf.seek(0)
    return buf


class StoryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_story(self):
        story = Story.objects.create(
            user=self.user,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        self.assertEqual(story.user, self.user)
        self.assertFalse(story.is_expired)

    def test_story_str(self):
        story = Story.objects.create(
            user=self.user,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        self.assertIn(self.user.username, str(story))

    def test_active_stories_excludes_expired(self):
        Story.objects.create(
            user=self.user,
            expires_at=timezone.now() - timezone.timedelta(hours=1),
        )
        self.assertEqual(Story.active_stories().count(), 0)

    def test_story_expires_at_auto_set(self):
        story = Story.objects.create(user=self.user)
        self.assertIsNotNone(story.expires_at)
        self.assertGreater(story.expires_at, timezone.now())

    def test_is_expired_property(self):
        expired = Story.objects.create(
            user=self.user,
            expires_at=timezone.now() - timezone.timedelta(hours=1),
        )
        self.assertTrue(expired.is_expired)
        active = Story.objects.create(
            user=self.user,
            expires_at=timezone.now() + timezone.timedelta(hours=1),
        )
        self.assertFalse(active.is_expired)

    def test_stories_grouped_by_user(self):
        other = User.objects.create_user(username="other", password="testpass123")
        Story.objects.create(
            user=self.user,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        Story.objects.create(
            user=other,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        grouped = Story.stories_grouped_by_user()
        self.assertEqual(len(grouped), 2)
        self.assertIn(self.user, grouped)
        self.assertIn(other, grouped)


@override_settings(MEDIA_ROOT="/tmp/test-media")
class StoryViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_story_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("stories:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_story_list_empty(self):
        response = self.client.get(reverse("stories:list"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["stories"], [])

    def test_story_upload_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse("stories:upload"))
        self.assertNotEqual(response.status_code, 200)

    def test_story_upload_no_image(self):
        response = self.client.post(
            reverse("stories:upload"),
            {"caption": "Test"},
        )
        self.assertEqual(response.status_code, 400)

    def test_story_upload_success(self):
        img = get_test_image()
        response = self.client.post(
            reverse("stories:upload"),
            {"image": img, "caption": "My story"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("image_url", data)
        self.assertEqual(data["caption"], "My story")
        self.assertEqual(Story.objects.count(), 1)
