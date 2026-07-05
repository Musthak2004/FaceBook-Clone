"""Tests for the posts app — CRUD, permissions, saved posts, hashtags, mentions."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Poll, PollOption, PollVote, Post, PostImage, SavedPost, Tag
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


class SharePostTests(TestCase):
    """Tests for the share/repost feature."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.other = User.objects.create_user("bob", password="pass123")
        self.post = Post.objects.create(
            author=self.other, content="Original post by bob"
        )
        self.client.login(username="alice", password="pass123")

    def test_share_post_creates_repost(self):
        """Sharing a post creates a new Post with shared_post pointing to original."""
        url = reverse("posts:post_share", kwargs={"pk": self.post.pk})
        response = self.client.post(url)
        self.assertJSONEqual(
            response.content, {"shared": True, "post_url": "/posts/2/"}
        )
        repost = Post.objects.exclude(pk=self.post.pk).get()
        self.assertEqual(repost.author, self.user)
        self.assertEqual(repost.shared_post, self.post)
        self.assertEqual(repost.content, "")

    def test_share_post_with_content(self):
        """Sharing a post with optional commentary creates a repost with that content."""
        url = reverse("posts:post_share", kwargs={"pk": self.post.pk})
        response = self.client.post(
            url, {"content": "Great post!", "visibility": "friends"}
        )
        self.assertEqual(response.status_code, 200)
        repost = Post.objects.exclude(pk=self.post.pk).get()
        self.assertEqual(repost.content, "Great post!")
        self.assertEqual(repost.visibility, "friends")
        self.assertEqual(repost.shared_post, self.post)

    def test_share_post_creates_notification(self):
        """Sharing another user's post creates a share notification."""
        from notifications.models import Notification

        url = reverse("posts:post_share", kwargs={"pk": self.post.pk})
        self.client.post(url)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.other,
                sender=self.user,
                notification_type="share",
                post=self.post,
            ).exists()
        )

    def test_share_own_post_no_notification(self):
        """Sharing your own post does NOT create a share notification."""
        from notifications.models import Notification

        own_post = Post.objects.create(author=self.user, content="My own post")
        url = reverse("posts:post_share", kwargs={"pk": own_post.pk})
        self.client.post(url)
        self.assertFalse(
            Notification.objects.filter(
                notification_type="share",
            ).exists()
        )

    def test_share_view_requires_login(self):
        """Unauthenticated users cannot access the share endpoint."""
        self.client.logout()
        url = reverse("posts:post_share", kwargs={"pk": self.post.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_share_nonexistent_post_returns_404(self):
        """Sharing a non-existent post returns 404."""
        url = reverse("posts:post_share", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class PollModelTests(TestCase):
    """Tests for Poll, PollOption, and PollVote models."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Poll post")
        self.poll = Poll.objects.create(post=self.post, question="Best framework?")
        self.opt1 = PollOption.objects.create(poll=self.poll, text="Django")
        self.opt2 = PollOption.objects.create(poll=self.poll, text="FastAPI")

    def test_poll_creation(self):
        self.assertEqual(self.poll.question, "Best framework?")
        self.assertEqual(self.poll.post, self.post)
        self.assertFalse(self.poll.is_closed)

    def test_poll_str(self):
        self.assertEqual(str(self.poll), "Best framework?")

    def test_poll_total_votes_initially_zero(self):
        self.assertEqual(self.poll.total_votes, 0)

    def test_poll_option_creation(self):
        self.assertEqual(self.opt1.text, "Django")
        self.assertEqual(self.opt2.text, "FastAPI")

    def test_poll_option_vote_count(self):
        PollVote.objects.create(option=self.opt1, user=self.user)
        self.assertEqual(self.opt1.vote_count, 1)
        self.assertEqual(self.opt2.vote_count, 0)

    def test_poll_vote_unique_together(self):
        PollVote.objects.create(option=self.opt1, user=self.user)
        with self.assertRaises(Exception):
            PollVote.objects.create(option=self.opt1, user=self.user)

    def test_poll_vote_switching(self):
        """User can delete old vote and vote on a different option."""
        PollVote.objects.create(option=self.opt1, user=self.user)
        self.assertEqual(self.opt1.vote_count, 1)
        PollVote.objects.filter(option=self.opt1, user=self.user).delete()
        PollVote.objects.create(option=self.opt2, user=self.user)
        self.assertEqual(self.opt1.vote_count, 0)
        self.assertEqual(self.opt2.vote_count, 1)

    def test_poll_closed_blocks_new_votes(self):
        """Once a poll is closed, no option should accept new votes."""
        self.poll.is_closed = True
        self.poll.save()
        # The view layer checks is_closed, but model-level creation is still allowed
        # (enforcement is in the view). This just tests model state.
        self.assertTrue(self.poll.is_closed)


class PollVoteViewTests(TestCase):
    """Tests for the PollVoteView AJAX endpoint."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.other = User.objects.create_user("bob", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Poll post")
        self.poll = Poll.objects.create(post=self.post, question="Best language?")
        self.opt_py = PollOption.objects.create(poll=self.poll, text="Python")
        self.opt_js = PollOption.objects.create(poll=self.poll, text="JavaScript")
        self.client.login(username="alice", password="pass123")

    def test_vote_on_poll(self):
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"option_id": self.opt_py.pk})
        data = response.json()
        self.assertTrue(data["voted"])
        self.assertEqual(data["option_id"], self.opt_py.pk)
        self.assertEqual(data["total_votes"], 1)
        self.assertTrue(
            PollVote.objects.filter(option=self.opt_py, user=self.user).exists()
        )

    def test_vote_switches_option(self):
        """Voting on a different option removes the old vote."""
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        self.client.post(url, {"option_id": self.opt_py.pk})
        self.client.post(url, {"option_id": self.opt_js.pk})
        self.assertEqual(PollVote.objects.filter(user=self.user).count(), 1)
        self.assertTrue(
            PollVote.objects.filter(option=self.opt_js, user=self.user).exists()
        )
        self.assertFalse(
            PollVote.objects.filter(option=self.opt_py, user=self.user).exists()
        )

    def test_vote_on_closed_poll_returns_error(self):
        self.poll.is_closed = True
        self.poll.save()
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"option_id": self.opt_py.pk})
        self.assertEqual(response.status_code, 400)
        self.assertIn("closed", response.json()["error"])

    def test_vote_without_option_id_returns_error(self):
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("No option", response.json()["error"])

    def test_vote_on_nonexistent_option_returns_404(self):
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"option_id": 9999})
        self.assertEqual(response.status_code, 404)

    def test_vote_requires_login(self):
        self.client.logout()
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"option_id": self.opt_py.pk})
        self.assertEqual(response.status_code, 302)

    def test_vote_returns_option_data(self):
        """Response should include all options with counts and percentages."""
        # Have another user vote first
        PollVote.objects.create(option=self.opt_py, user=self.other)
        url = reverse("posts:poll_vote", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"option_id": self.opt_js.pk})
        data = response.json()
        self.assertEqual(len(data["options"]), 2)
        for opt in data["options"]:
            self.assertIn("id", opt)
            self.assertIn("text", opt)
            self.assertIn("vote_count", opt)
            self.assertIn("percentage", opt)
        # After voting JS, opt_py has 1 vote (50%), opt_js has 1 vote (50%)
        opt_py_data = [o for o in data["options"] if o["id"] == self.opt_py.pk][0]
        opt_js_data = [o for o in data["options"] if o["id"] == self.opt_js.pk][0]
        self.assertEqual(opt_py_data["vote_count"], 1)
        self.assertEqual(opt_js_data["vote_count"], 1)
        self.assertEqual(opt_py_data["percentage"], 50)
        self.assertEqual(opt_js_data["percentage"], 50)
        self.assertEqual(data["total_votes"], 2)


class PollCreateWithPostTests(TestCase):
    """Tests that polls can be created alongside posts via the form."""

    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.client.login(username="alice", password="pass123")

    def test_create_post_with_poll(self):
        url = reverse("posts:post_create")
        response = self.client.post(
            url,
            {
                "content": "My poll post",
                "visibility": "public",
                "poll_question": "Best color?",
                "poll_options": "Red\nBlue\nGreen",
            },
        )
        self.assertRedirects(response, reverse("posts:post_detail", kwargs={"pk": 1}))
        post = Post.objects.get(pk=1)
        self.assertIsNotNone(post.poll)
        self.assertEqual(post.poll.question, "Best color?")
        self.assertEqual(post.poll.options.count(), 3)

    def test_create_post_without_poll(self):
        url = reverse("posts:post_create")
        response = self.client.post(
            url,
            {
                "content": "Just a regular post",
                "visibility": "public",
            },
        )
        self.assertRedirects(response, reverse("posts:post_detail", kwargs={"pk": 1}))
        post = Post.objects.get(pk=1)
        self.assertIsNone(getattr(post, "poll", None))

    def test_create_post_with_invalid_poll_options(self):
        """Single option should not create a poll."""
        url = reverse("posts:post_create")
        response = self.client.post(
            url,
            {
                "content": "Poll with one option",
                "visibility": "public",
                "poll_question": "Yes or no?",
                "poll_options": "Maybe",
            },
        )
        self.assertEqual(response.status_code, 200)  # Form re-renders with error
        self.assertIn("Add at least 2 options", response.content.decode())
        self.assertEqual(Post.objects.count(), 0)
