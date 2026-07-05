"""Tests for the Pages app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Page, PageFollower, PagePost

User = get_user_model()


class PageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pageadmin", password="testpass123"
        )

    def test_create_page(self):
        page = Page.objects.create(
            name="Test Page",
            description="A test page.",
            category="business",
            admin=self.user,
        )
        self.assertEqual(page.name, "Test Page")
        self.assertEqual(page.category, "business")
        self.assertEqual(page.admin, self.user)
        self.assertEqual(page.follower_count, 0)
        self.assertEqual(page.post_count, 0)

    def test_follow_page(self):
        page = Page.objects.create(name="Test Page", admin=self.user)
        follower = User.objects.create_user(username="follower", password="testpass123")
        PageFollower.objects.create(user=follower, page=page)
        self.assertEqual(page.follower_count, 1)

    def test_page_post(self):
        page = Page.objects.create(name="Test Page", admin=self.user)
        post = PagePost.objects.create(
            page=page, author=self.user, content="Hello followers!"
        )
        self.assertEqual(page.post_count, 1)
        self.assertEqual(str(post), "pageadmin on Test Page: Hello followers!")


class PageViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.page = Page.objects.create(
            name="Test Page", description="Desc", admin=self.user
        )

    def test_page_list_requires_login(self):
        response = self.client.get(reverse("pages:list"))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('pages:list')}")

    def test_page_list_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("pages:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Page")

    def test_page_detail(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("pages:detail", kwargs={"pk": self.page.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Page")

    def test_create_page(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("pages:create"),
            {"name": "New Page", "description": "Brand new", "category": "other"},
        )
        self.assertRedirects(response, reverse("pages:list"))
        self.assertTrue(Page.objects.filter(name="New Page").exists())

    def test_follow_page(self):
        self.client.login(username="testuser", password="testpass123")
        other = User.objects.create_user(username="other", password="testpass123")
        page = Page.objects.create(name="Other Page", admin=other)
        response = self.client.post(reverse("pages:follow", kwargs={"pk": page.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_following"])
        self.assertEqual(data["follower_count"], 1)

    def test_unfollow_page(self):
        self.client.login(username="testuser", password="testpass123")
        other = User.objects.create_user(username="other", password="testpass123")
        page = Page.objects.create(name="Other Page", admin=other)
        PageFollower.objects.create(user=self.user, page=page)
        response = self.client.post(reverse("pages:follow", kwargs={"pk": page.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_following"])
        self.assertEqual(data["follower_count"], 0)

    def test_admin_cannot_follow_own_page(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("pages:follow", kwargs={"pk": self.page.pk})
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("admin", response.json()["error"])

    def test_page_post_admin_only(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("pages:post", kwargs={"pk": self.page.pk}),
            {"content": "Hello followers!"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["created"])
        self.assertEqual(PagePost.objects.count(), 1)

    def test_page_post_non_admin_forbidden(self):
        User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="other", password="testpass123")
        response = self.client.post(
            reverse("pages:post", kwargs={"pk": self.page.pk}),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 403)
