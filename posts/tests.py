"""
Tests for posts app.
Follows Django for Beginners Ch 5/6 testing patterns.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Post, Like, Comment
from friendships.models import Friendship


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

    # ─── LikeToggleView ───

    def test_like_toggle_ajax_like(self):
        """AJAX POST to like endpoint creates a like and returns JSON with liked=true."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Like me")
        response = self.client.post(
            reverse("post_like", kwargs={"pk": post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["liked"])
        self.assertEqual(data["like_count"], 1)
        self.assertEqual(Like.objects.count(), 1)

    def test_like_toggle_ajax_unlike(self):
        """AJAX POST to unlike endpoint deletes the like and returns liked=false."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Unlike me")
        Like.objects.create(user=self.user, post=post)
        response = self.client.post(
            reverse("post_like", kwargs={"pk": post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["liked"])
        self.assertEqual(data["like_count"], 0)
        self.assertEqual(Like.objects.count(), 0)

    def test_like_toggle_redirect_like(self):
        """Non-AJAX POST to like endpoint redirects to post detail."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Redirect like")
        response = self.client.post(
            reverse("post_like", kwargs={"pk": post.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, post.get_absolute_url())

    def test_like_toggle_redirect_unlike(self):
        """Non-AJAX POST to unlike endpoint redirects to post detail."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Redirect unlike")
        Like.objects.create(user=self.user, post=post)
        response = self.client.post(
            reverse("post_like", kwargs={"pk": post.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, post.get_absolute_url())

    def test_like_toggle_nonexistent_post(self):
        """POST to like a non-existent post returns 404."""
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("post_like", kwargs={"pk": 99999}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)

    # ─── CommentCreateView ───

    def test_comment_create(self):
        """POST to comment creation creates a comment and redirects."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Comment target")
        response = self.client.post(
            reverse("comment_new", kwargs={"post_pk": post.pk}),
            {"content": "Nice post!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.content, "Nice post!")
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, post)

    def test_comment_create_nonexistent_post(self):
        """Comment on non-existent post returns 404."""
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("comment_new", kwargs={"post_pk": 99999}),
            {"content": "Hello"},
        )
        self.assertEqual(response.status_code, 404)

    # ─── CommentDeleteView ───

    def test_comment_delete_by_author(self):
        """Comment author can delete their own comment."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Post")
        comment = Comment.objects.create(
            post=post, author=self.user, content="My comment",
        )
        response = self.client.post(
            reverse("comment_delete", kwargs={"pk": comment.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_delete_by_non_author(self):
        """Non-author cannot delete a comment — returns 403."""
        other = get_user_model().objects.create_user(
            username="other", password="secret",
        )
        post = Post.objects.create(author=self.user, content="Post")
        comment = Comment.objects.create(
            post=post, author=other, content="Their comment",
        )
        self.client.login(username="testuser", password="secret")
        response = self.client.post(
            reverse("comment_delete", kwargs={"pk": comment.pk}),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 1)

    # ─── PostUpdateView ───

    def test_post_update_by_author(self):
        """Author can edit their own post."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Original content")
        response = self.client.post(
            reverse("post_edit", kwargs={"pk": post.pk}),
            {"content": "Updated content"},
        )
        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated content")

    def test_post_update_by_non_author(self):
        """Non-author cannot edit another user's post — returns 403."""
        other = get_user_model().objects.create_user(
            username="other", password="secret",
        )
        post = Post.objects.create(author=other, content="Other's post")
        self.client.login(username="testuser", password="secret")
        response = self.client.get(
            reverse("post_edit", kwargs={"pk": post.pk}),
        )
        self.assertEqual(response.status_code, 403)

    # ─── PostFeedAPIView with friend relationships (positive path) ───

    def test_post_feed_api_with_friends(self):
        """User sees friend's posts when bidirectional accepted friendship exists."""
        self.client.login(username="testuser", password="secret")
        friend = get_user_model().objects.create_user(
            username="friend", password="secret",
        )
        Friendship.objects.create(
            from_user=self.user, to_user=friend, status="accepted",
        )
        Friendship.objects.create(
            from_user=friend, to_user=self.user, status="accepted",
        )
        Post.objects.create(author=friend, content="Friend's post")
        Post.objects.create(author=self.user, content="My post")
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Friend&#x27;s post", data["html"])
        self.assertIn("My post", data["html"])

    # ─── PostFeedAPIView user_likes context ───

    def test_post_feed_api_user_likes_in_html(self):
        """When user has liked a post, rendered HTML shows btn-primary not btn-outline-secondary."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Liked post")
        Like.objects.create(user=self.user, post=post)
        response = self.client.get(
            reverse("post_feed_api") + "?offset=0",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("btn-primary", data["html"])

    # ─── PostDetailView context ───

    def test_post_detail_liked_context(self):
        """Post detail shows user_liked=True when user has liked the post."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Detail liked")
        Like.objects.create(user=self.user, post=post)
        response = self.client.get(
            reverse("post_detail", kwargs={"pk": post.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_liked"])

    def test_post_detail_unliked_context(self):
        """Post detail shows user_liked=False when user has not liked the post."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Detail unliked")
        response = self.client.get(
            reverse("post_detail", kwargs={"pk": post.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user_liked"])

    def test_post_detail_comment_form_in_context(self):
        """Post detail includes comment_form in context."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="Detail with form")
        response = self.client.get(
            reverse("post_detail", kwargs={"pk": post.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("comment_form", response.context)

    # ─── PostListView context ───

    def test_post_list_has_post_form(self):
        """Post list includes post_form in context."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="List post")
        response = self.client.get(reverse("post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("post_form", response.context)

    def test_post_list_user_likes_context(self):
        """Post list includes user_likes set in context."""
        self.client.login(username="testuser", password="secret")
        post = Post.objects.create(author=self.user, content="List like check")
        Like.objects.create(user=self.user, post=post)
        response = self.client.get(reverse("post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_likes", response.context)
        self.assertIn(post.pk, response.context["user_likes"])
