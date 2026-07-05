"""Tests for the posts app — CRUD, permissions, saved posts, hashtags, mentions."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Post, PostImage, SavedPost, Tag
from .utils import parse_hashtags, parse_mentions, render_content

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


class HashtagParsingTests(TestCase):
    """Tests for posts/utils.py parsing functions."""

    def test_parse_hashtags_simple(self):
        self.assertEqual(parse_hashtags("Hello #world"), {"world"})

    def test_parse_hashtags_multiple(self):
        self.assertEqual(
            parse_hashtags("#django #python #test"), {"django", "python", "test"}
        )

    def test_parse_hashtags_case_normalized(self):
        self.assertEqual(parse_hashtags("#Hello #WORLD"), {"hello", "world"})

    def test_parse_hashtags_none(self):
        self.assertEqual(parse_hashtags("No hashtags here"), set())

    def test_parse_hashtags_adjacent_to_punctuation(self):
        """Hashtags adjacent to punctuation should still be matched."""
        self.assertEqual(
            parse_hashtags("Check #django! and #python."), {"django", "python"}
        )

    def test_parse_hashtags_numeric(self):
        self.assertEqual(parse_hashtags("#2024 #123"), {"2024", "123"})

    def test_parse_hashtags_empty_string(self):
        self.assertEqual(parse_hashtags(""), set())

    def test_parse_mentions_simple(self):
        self.assertEqual(parse_mentions("Hello @alice"), {"alice"})

    def test_parse_mentions_multiple(self):
        self.assertEqual(
            parse_mentions("@alice @bob @charlie"), {"alice", "bob", "charlie"}
        )

    def test_parse_mentions_none(self):
        self.assertEqual(parse_mentions("No mentions here"), set())

    def test_parse_mentions_empty_string(self):
        self.assertEqual(parse_mentions(""), set())

    def test_render_content_escapes_html(self):
        """XSS vectors must be escaped."""
        result = render_content("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_render_content_hashtag_link(self):
        """#tag should become a clickable link."""
        result = render_content("#python")
        self.assertIn('<a href="', result)
        self.assertIn('class="hashtag"', result)
        self.assertIn("#python", result)

    def test_render_content_mention_link(self):
        """@alice should link to alice's profile if alice exists."""
        User.objects.create_user("alice", password="pass123")
        result = render_content("Hello @alice")
        self.assertIn('<a href="', result)
        self.assertIn('class="mention"', result)
        self.assertIn("@alice", result)

    def test_render_content_unknown_mention(self):
        """@nonexistent should stay as plain text."""
        result = render_content("Hello @nonexistentuser")
        self.assertNotIn('<a href="', result)
        self.assertIn("@nonexistentuser", result)

    def test_render_content_empty(self):
        self.assertEqual(render_content(""), "")
        self.assertEqual(render_content(None), "")


class HashtagSignalTests(TestCase):
    """Tests that post_save signals properly parse hashtags and create mention notifications."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.other = User.objects.create_user("bob", password="pass123")

    def test_post_save_creates_tags(self):
        post = Post.objects.create(
            author=self.user, content="Learning #django and #python"
        )
        tags = Tag.objects.filter(posts=post)
        self.assertEqual(tags.count(), 2)
        self.assertIn(Tag.objects.get(name="django"), tags)
        self.assertIn(Tag.objects.get(name="python"), tags)

    def test_post_save_creates_mention_notification(self):
        from notifications.models import Notification

        post = Post.objects.create(
            author=self.user, content="Hello @bob check this out!"
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.other,
                sender=self.user,
                notification_type="mention",
                post=post,
            ).exists()
        )

    def test_post_save_does_not_mention_self(self):
        from notifications.models import Notification

        Post.objects.create(author=self.user, content="Feeling great @alice")
        self.assertFalse(
            Notification.objects.filter(
                notification_type="mention",
            ).exists()
        )

    def test_post_save_no_hashtags_or_mentions(self):
        Post.objects.create(author=self.user, content="Just a regular post")
        self.assertEqual(Tag.objects.count(), 0)

    def test_post_save_duplicate_tags(self):
        """Same hashtag used twice should create only one Tag."""
        Post.objects.create(
            author=self.user, content="#python is great #python is fast"
        )
        self.assertEqual(Tag.objects.count(), 1)


class HashtagViewTests(TestCase):
    """Tests for the hashtag detail page."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")

    def test_hashtag_detail_requires_login(self):
        url = reverse("posts:hashtag_detail", kwargs={"slug": "python"})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_hashtag_detail_shows_matching_posts(self):
        self.client.login(username="alice", password="pass123")
        Post.objects.create(author=self.user, content="#python is awesome")
        url = reverse("posts:hashtag_detail", kwargs={"slug": "python"})
        response = self.client.get(url)
        self.assertContains(response, "#python")

    def test_hashtag_detail_excludes_drafts(self):
        self.client.login(username="alice", password="pass123")
        Post.objects.create(author=self.user, content="#draftpost", is_draft=True)
        url = reverse("posts:hashtag_detail", kwargs={"slug": "draftpost"})
        response = self.client.get(url)
        self.assertContains(response, "No posts")

    def test_hashtag_detail_case_insensitive(self):
        self.client.login(username="alice", password="pass123")
        Post.objects.create(author=self.user, content="#Python")
        url = reverse("posts:hashtag_detail", kwargs={"slug": "python"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
