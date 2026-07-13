"""
Tests for posts app.
Follows Django for Beginners Ch 5/6 testing patterns.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Post, Like, Comment


class PostTests(TestCase):
    """Test post CRUD functionality."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@email.com",
            password="secret",
        )

    def _create_posts(self, count, author=None):
        """Helper to bulk-create posts."""
        author = author or self.user
        for i in range(count):
            Post.objects.create(author=author, content=f"Post {i} content")

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

    # ─── AJAX load-more API tests ───

    def test_post_feed_api_requires_login(self):
        """Unauthenticated requests to the AJAX endpoint should redirect."""
        response = self.client.get(reverse("post_feed_api") + "?offset=0")
        self.assertEqual(response.status_code, 302)

    def test_post_feed_api_returns_html(self):
        """Authenticated request returns JSON with rendered card HTML."""
        self.client.login(username="testuser", password="secret")
        Post.objects.create(author=self.user, content="API test post")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("next_offset", data)
        self.assertIn("has_more", data)
        self.assertIn("API test post", data["html"])

    def test_post_feed_api_pagination(self):
        """With more posts than BATCH_SIZE, has_more is true and next_offset advances."""
        self.client.login(username="testuser", password="secret")
        self._create_posts(12)
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = response.json()
        self.assertTrue(data["has_more"])
        self.assertEqual(data["next_offset"], 10)

    def test_post_feed_api_no_more(self):
        """When fewer posts than BATCH_SIZE remain, has_more is false."""
        self.client.login(username="testuser", password="secret")
        Post.objects.create(author=self.user, content="Only post")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = response.json()
        self.assertFalse(data["has_more"])

    # ─── Edge case: invalid / non-numeric offset ───

    def test_post_feed_api_invalid_offset(self):
        """Non-numeric offset returns 400 Bad Request."""
        self.client.login(username="testuser", password="secret")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=abc",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)

    # ─── Edge case: empty feed — no posts at all ───

    def test_post_feed_api_empty_feed(self):
        """With zero posts, API returns empty html and has_more=false."""
        self.client.login(username="testuser", password="secret")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["html"], "")
        self.assertFalse(data["has_more"])
        self.assertEqual(data["next_offset"], 0)

    # ─── Edge case: offset beyond all available posts ───

    def test_post_feed_api_offset_beyond_end(self):
        """Offset past the last post returns empty html and has_more=false."""
        self.client.login(username="testuser", password="secret")
        Post.objects.create(author=self.user, content="Only one")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=100",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["html"], "")
        self.assertFalse(data["has_more"])
        self.assertEqual(data["next_offset"], 100)

    # ─── Edge case: negative offset ───

    def test_post_feed_api_negative_offset(self):
        """Negative offset returns 400 Bad Request."""
        self.client.login(username="testuser", password="secret")
        self._create_posts(5)
        response = self.client.get(
            reverse("post_feed_api") + "?offset=-1",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)

    # ─── Edge case: exactly BATCH_SIZE posts → has_more=false ───

    def test_post_feed_api_exact_batch_size(self):
        """When total posts equal BATCH_SIZE exactly, has_more is false."""
        self.client.login(username="testuser", password="secret")
        self._create_posts(10)
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["has_more"])
        self.assertEqual(data["next_offset"], 10)

    # ─── Edge case: user with no friends only sees own posts ───

    def test_post_feed_api_no_friends(self):
        """User with no accepted friends sees only their own posts."""
        other = get_user_model().objects.create_user(
            username="other", password="secret",
        )
        Post.objects.create(author=other, content="Other's post")
        Post.objects.create(author=self.user, content="My post")
        self.client.login(username="testuser", password="secret")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("My post", data["html"])
        self.assertNotIn("Other's post", data["html"])

    # ─── Annotation-based like_count / comment_count ───

    def test_like_count_with_annotation(self):
        """like_count returns annotated value when _like_count is set."""
        post = Post.objects.create(author=self.user, content="Count test")
        Like.objects.create(user=self.user, post=post)
        post._like_count = 99  # Simulate annotation from query
        self.assertEqual(post.like_count, 99)

    def test_comment_count_with_annotation(self):
        """comment_count returns annotated value when _comment_count is set."""
        post = Post.objects.create(author=self.user, content="Comment count test")
        Comment.objects.create(post=post, author=self.user, content="A comment")
        post._comment_count = 42  # Simulate annotation from query
        self.assertEqual(post.comment_count, 42)
