"""Tests for the reactions app — model, toggle behavior, views."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Reaction
from posts.models import Post

User = get_user_model()


class ReactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Test post")

    def test_create_reaction(self):
        reaction = Reaction.objects.create(
            user=self.user, post=self.post, reaction_type="like"
        )
        self.assertEqual(reaction.reaction_type, "like")
        self.assertEqual(self.post.total_likes, 1)

    def test_reaction_unique_together(self):
        Reaction.objects.create(user=self.user, post=self.post, reaction_type="like")
        with self.assertRaises(Exception):
            Reaction.objects.create(
                user=self.user, post=self.post, reaction_type="love"
            )

    def test_reaction_str(self):
        r = Reaction.objects.create(
            user=self.user, post=self.post, reaction_type="haha"
        )
        self.assertIn("alice", str(r))
        self.assertIn("haha", str(r))

    def test_all_reaction_types_valid(self):
        """All reaction types can be created (each on a separate post)."""
        for i, (reaction_type, _) in enumerate(Reaction.REACTION_CHOICES):
            post = Post.objects.create(author=self.user, content=f"Post {i}")
            Reaction.objects.create(
                user=self.user, post=post, reaction_type=reaction_type
            )
        self.assertEqual(Reaction.objects.count(), len(Reaction.REACTION_CHOICES))


class ReactionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Likeable post")
        self.client.login(username="alice", password="pass123")

    def test_like_view_creates_reaction(self):
        url = reverse("reactions:post_like", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"reaction_type": "like"})
        self.assertJSONEqual(
            response.content,
            {
                "liked": True,
                "total_likes": 1,
                "reaction_type": "like",
            },
        )
        self.assertTrue(
            Reaction.objects.filter(user=self.user, post=self.post).exists()
        )

    def test_like_view_toggles_off(self):
        Reaction.objects.create(user=self.user, post=self.post, reaction_type="like")
        url = reverse("reactions:post_like", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"reaction_type": "like"})
        self.assertJSONEqual(
            response.content,
            {
                "liked": False,
                "total_likes": 0,
            },
        )
        self.assertFalse(
            Reaction.objects.filter(user=self.user, post=self.post).exists()
        )

    def test_like_view_changes_reaction_type(self):
        original = Reaction.objects.create(
            user=self.user, post=self.post, reaction_type="like"
        )
        url = reverse("reactions:post_like", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"reaction_type": "love"})
        self.assertJSONEqual(
            response.content,
            {
                "liked": True,
                "total_likes": 1,
                "reaction_type": "love",
            },
        )
        original.refresh_from_db()
        self.assertEqual(original.reaction_type, "love")

    def test_like_requires_login(self):
        self.client.logout()
        url = reverse("reactions:post_like", kwargs={"pk": self.post.pk})
        response = self.client.post(url, {"reaction_type": "like"})
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_like_nonexistent_post_returns_404(self):
        url = reverse("reactions:post_like", kwargs={"pk": 9999})
        response = self.client.post(url, {"reaction_type": "like"})
        self.assertEqual(response.status_code, 404)
