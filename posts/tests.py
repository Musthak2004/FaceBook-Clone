"""
Tests for posts app.
Follows Django for Beginners Ch 5/6 testing patterns.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Post


class PostTests(TestCase):
    """Test post CRUD functionality."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@email.com",
            password="secret",
        )

    def test_create_post(self):
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("post_new"),
            {"content": "This is a test post!"},
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().content, "This is a test post!")
        self.assertEqual(Post.objects.first().author, self.user)

    def test_post_list_view(self):
        self.client.login(username="testuser", password="secret")
        Post.objects.create(author=self.user, content="Test post")
        response = self.client.get(reverse("post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test post")

    def test_post_detail_view(self):
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Detail test")
        response = self.client.get(reverse("post_detail", kwargs={"pk": post.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail test")

    def test_post_delete(self):
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Delete me")
        response = self.client.post(
            reverse("post_delete", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 0)

    def test_cannot_delete_others_post(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="secret"
        )
        post = Post.objects.create(author=other_user, content="Not mine")
        self.client.login(username="testuser", password="secret")
        response = self.client.get(
            reverse("post_delete", kwargs={"pk": post.pk})
        )
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
