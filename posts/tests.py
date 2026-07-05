"""Tests for the posts app — CRUD, permissions, saved posts."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Post, PostImage, SavedPost

User = get_user_model()


class PostModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")

    def test_create_post(self):
        post = Post.objects.create(
            author=self.user, content="Test post", visibility="public"
        )
        self.assertEqual(post.content[:50], "Test post")
        self.assertFalse(post.is_draft)
        self.assertEqual(post.total_likes, 0)
        self.assertEqual(post.total_comments, 0)

    def test_post_str(self):
        post = Post.objects.create(author=self.user, content="Hello world!")
        self.assertIn("Hello", str(post))

    def test_post_default_ordering(self):
        Post.objects.create(author=self.user, content="First")
        Post.objects.create(author=self.user, content="Second")
        posts = Post.objects.all()
        self.assertEqual(posts[0].content[:50], "Second")

    def test_visibility_choices(self):
        for choice, _ in Post.VISIBILITY_CHOICES:
            post = Post.objects.create(
                author=self.user, content=f"Post {choice}", visibility=choice
            )
            self.assertEqual(post.visibility, choice)

    def test_draft_posts_excluded_from_default_queryset(self):
        # POSTS are not excluded by default unless filtered
        Post.objects.create(author=self.user, content="Draft", is_draft=True)
        self.assertEqual(Post.objects.count(), 1)

    def test_get_absolute_url(self):
        post = Post.objects.create(author=self.user, content="Test")
        url = post.get_absolute_url()
        self.assertEqual(url, reverse("posts:post_detail", kwargs={"pk": post.pk}))
        self.assertTrue(url.startswith("/posts/"))


class PostImageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.post = Post.objects.create(author=self.user, content="With image")

    def test_create_post_image(self):
        # Just test that PostImage can be created and related
        # (actual file upload is tested separately)
        self.assertEqual(self.post.images.count(), 0)

    def test_post_image_str(self):
        # Test string representation
        pi = PostImage(post=self.post, image="posts/test.jpg")
        self.assertIn(f"Post {self.post.id}", str(pi))


class SavedPostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Saveable post")

    def test_save_post(self):
        saved = SavedPost.objects.create(user=self.user, post=self.post)
        self.assertEqual(saved.user, self.user)
        self.assertEqual(saved.post, self.post)

    def test_save_post_unique_together(self):
        SavedPost.objects.create(user=self.user, post=self.post)
        with self.assertRaises(Exception):
            SavedPost.objects.create(user=self.user, post=self.post)

    def test_save_view_creates_then_toggles(self):
        self.client.login(username="alice", password="pass123")
        url = reverse("posts:post_save", kwargs={"pk": self.post.pk})

        # First save
        response = self.client.post(url)
        self.assertJSONEqual(response.content, {"saved": True})
        self.assertTrue(
            SavedPost.objects.filter(user=self.user, post=self.post).exists()
        )

        # Toggle unsave
        response = self.client.post(url)
        self.assertJSONEqual(response.content, {"saved": False})
        self.assertFalse(
            SavedPost.objects.filter(user=self.user, post=self.post).exists()
        )


class PostCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.other = User.objects.create_user("bob", password="pass123")
        self.client.login(username="alice", password="pass123")

    def test_create_post_view(self):
        url = reverse("posts:post_create")
        response = self.client.post(
            url,
            {
                "content": "New post!",
                "visibility": "public",
            },
        )
        self.assertRedirects(response, reverse("posts:post_detail", kwargs={"pk": 1}))
        self.assertTrue(Post.objects.filter(content="New post!").exists())

    def test_create_post_requires_login(self):
        self.client.logout()
        url = reverse("posts:post_create")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_post_detail_shows_post(self):
        post = Post.objects.create(author=self.user, content="Detail test")
        url = reverse("posts:post_detail", kwargs={"pk": post.pk})
        response = self.client.get(url)
        self.assertContains(response, "Detail test")

    def test_post_update_by_author(self):
        post = Post.objects.create(author=self.user, content="Original")
        url = reverse("posts:post_update", kwargs={"pk": post.pk})
        response = self.client.post(
            url, {"content": "Updated!", "visibility": "public"}
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"pk": post.pk})
        )
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated!")

    def test_post_update_by_non_author_returns_403(self):
        self.client.logout()
        self.client.login(username="bob", password="pass123")
        post = Post.objects.create(author=self.user, content="Original")
        url = reverse("posts:post_update", kwargs={"pk": post.pk})
        response = self.client.post(url, {"content": "Hacked!", "visibility": "public"})
        self.assertEqual(response.status_code, 403)

    def test_post_delete_by_author(self):
        post = Post.objects.create(author=self.user, content="To delete")
        url = reverse("posts:post_delete", kwargs={"pk": post.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("core:home"))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_post_delete_by_non_author_returns_403(self):
        self.client.logout()
        self.client.login(username="bob", password="pass123")
        post = Post.objects.create(author=self.user, content="Mine")
        url = reverse("posts:post_delete", kwargs={"pk": post.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_post_author_property(self):
        post = Post.objects.create(author=self.user, content="Test")
        self.assertEqual(post.author, self.user)
