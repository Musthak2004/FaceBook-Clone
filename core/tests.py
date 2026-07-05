"""Tests for core app — home feed visibility, permissions."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post
from friendships.models import Friendship

User = get_user_model()


class HomeFeedVisibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.friend = User.objects.create_user("bob", password="pass123")
        self.stranger = User.objects.create_user("carol", password="pass123")

        # Make self.user and self.friend friends
        Friendship.objects.create(
            from_user=self.user, to_user=self.friend, status="accepted"
        )

        # Create posts with different visibilities
        self.public_post = Post.objects.create(
            author=self.stranger, content="Public post", visibility="public"
        )
        self.friend_post = Post.objects.create(
            author=self.friend, content="Friend post", visibility="friends"
        )
        self.own_post = Post.objects.create(
            author=self.user, content="My post", visibility="public"
        )
        self.only_me_post = Post.objects.create(
            author=self.friend, content="Private post", visibility="only_me"
        )

        self.client.login(username="alice", password="pass123")

    def test_feed_shows_own_posts(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "My post")

    def test_feed_shows_friend_public_posts(self):
        """Friend's 'public' posts should appear in feed."""
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Public post")

    def test_feed_shows_friend_only_posts(self):
        """Friend's 'friends only' posts should appear in feed."""
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Friend post")

    def test_feed_excludes_only_me_posts(self):
        """'only_me' posts from others should not appear."""
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "Private post")

    def test_feed_excludes_draft_posts(self):
        Post.objects.create(
            author=self.friend, content="Draft post", visibility="public", is_draft=True
        )
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "Draft post")

    def test_feed_requires_login(self):
        self.client.logout()
        url = reverse("core:home")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_feed_is_paginated(self):
        # Create 15 posts
        for i in range(15):
            Post.objects.create(
                author=self.user, content=f"Post {i}", visibility="public"
            )
        response = self.client.get(reverse("core:home"))
        self.assertIn("is_paginated", response.context)
        self.assertTrue(response.context["is_paginated"])

    def test_stranger_friend_only_posts_excluded(self):
        """Posts from non-friends with 'friends' visibility should not appear."""
        Post.objects.create(
            author=self.stranger, content="Stranger friends post", visibility="friends"
        )
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "Stranger friends post")

    def test_feed_ordered_by_recency(self):
        """Feed should show newest posts first (most recent is first)."""
        response = self.client.get(reverse("core:home"))
        post_list = list(response.context["posts"])
        dates = [p.created_at for p in post_list]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_friend_suggestions_shown(self):
        """Non-friend users should appear as suggestions."""
        response = self.client.get(reverse("core:home"))
        self.assertIn("friend_suggestions", response.context)

    def test_friend_suggestions_excludes_self_and_friends(self):
        response = self.client.get(reverse("core:home"))
        suggestions = response.context["friend_suggestions"]
        suggestion_ids = [u.id for u in suggestions]
        self.assertNotIn(self.user.id, suggestion_ids)
        self.assertNotIn(self.friend.id, suggestion_ids)

    def test_own_private_posts_visible_to_self(self):
        """User's own 'only_me' posts should be visible to them."""
        Post.objects.create(
            author=self.user, content="My private thought", visibility="only_me"
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "My private thought")
