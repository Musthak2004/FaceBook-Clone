"""Tests for the Search app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from posts.models import Post

User = get_user_model()


class SearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe", password="testpass123", bio="A software developer"
        )
        self.user2 = User.objects.create_user(
            username="janedoe", password="testpass123", bio="A designer"
        )

    def test_search_requires_login(self):
        response = self.client.get(reverse("search:search_results"))
        self.assertRedirects(
            response, f"/accounts/login/?next={reverse('search:search_results')}"
        )

    def test_search_without_query_returns_empty(self):
        self.client.login(username="johndoe", password="testpass123")
        response = self.client.get(reverse("search:search_results"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["results"]), 0)

    def test_search_users_by_username(self):
        self.client.login(username="johndoe", password="testpass123")
        response = self.client.get(
            reverse("search:search_results"), {"q": "jane", "type": "users"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "janedoe")

    def test_search_users_by_bio(self):
        self.client.login(username="johndoe", password="testpass123")
        response = self.client.get(
            reverse("search:search_results"), {"q": "developer", "type": "users"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "johndoe")

    def test_search_users_no_match(self):
        self.client.login(username="johndoe", password="testpass123")
        response = self.client.get(
            reverse("search:search_results"), {"q": "nonexistent", "type": "users"}
        )
        self.assertEqual(response.status_code, 200)

    def test_search_posts_by_content(self):
        self.client.login(username="johndoe", password="testpass123")
        Post.objects.create(
            author=self.user, content="Hello world this is a post", visibility="public"
        )
        response = self.client.get(
            reverse("search:search_results"), {"q": "Hello world", "type": "posts"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world")

    def test_search_posts_excludes_drafts(self):
        self.client.login(username="johndoe", password="testpass123")
        Post.objects.create(
            author=self.user,
            content="Draft content",
            visibility="public",
            is_draft=True,
        )
        response = self.client.get(
            reverse("search:search_results"), {"q": "Draft", "type": "posts"}
        )
        self.assertEqual(response.status_code, 200)

    def test_search_posts_private_not_shown_to_others(self):
        self.client.login(username="janedoe", password="testpass123")
        Post.objects.create(
            author=self.user,
            content="Private thoughts",
            visibility="only_me",
        )
        response = self.client.get(
            reverse("search:search_results"), {"q": "Private", "type": "posts"}
        )
        self.assertEqual(response.status_code, 200)

    def test_search_context_has_query_and_type(self):
        self.client.login(username="johndoe", password="testpass123")
        response = self.client.get(
            reverse("search:search_results"), {"q": "test", "type": "users"}
        )
        self.assertEqual(response.context["query"], "test")
        self.assertEqual(response.context["search_type"], "users")

    def test_search_exact_email(self):
        self.client.login(username="johndoe", password="testpass123")
        self.user.email = "john@example.com"
        self.user.save()
        response = self.client.get(
            reverse("search:search_results"), {"q": "john@example.com", "type": "users"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "johndoe")
