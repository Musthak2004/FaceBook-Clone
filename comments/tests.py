"""Tests for the comments app — model, AJAX views, permissions."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Comment
from posts.models import Post

User = get_user_model()


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Test post")

    def test_create_comment(self):
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="Nice!"
        )
        self.assertEqual(comment.content[:50], "Nice!")
        self.assertIsNone(comment.parent)

    def test_create_reply(self):
        parent = Comment.objects.create(
            post=self.post, author=self.user, content="Parent"
        )
        reply = Comment.objects.create(
            post=self.post, author=self.user, content="Reply", parent=parent
        )
        self.assertEqual(reply.parent, parent)
        self.assertIn(reply, parent.replies.all())

    def test_comment_str(self):
        c = Comment.objects.create(
            post=self.post, author=self.user, content="Testing 123"
        )
        self.assertIn("Testing", str(c))

    def test_comment_ordering(self):
        c1 = Comment.objects.create(post=self.post, author=self.user, content="First")
        c2 = Comment.objects.create(post=self.post, author=self.user, content="Second")
        comments = Comment.objects.filter(post=self.post)
        self.assertEqual(comments[0], c1)
        self.assertEqual(comments[1], c2)


class CommentViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass123")
        self.other = User.objects.create_user("bob", password="pass123")
        self.post = Post.objects.create(author=self.user, content="Test post")
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, content="My comment"
        )
        self.client.login(username="alice", password="pass123")

    def test_comment_delete_by_author(self):
        url = reverse("comments:comment_delete", kwargs={"pk": self.comment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"deleted": True})
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_comment_delete_by_non_author_returns_403(self):
        self.client.logout()
        self.client.login(username="bob", password="pass123")
        url = reverse("comments:comment_delete", kwargs={"pk": self.comment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_comment_edit_by_author(self):
        url = reverse("comments:comment_edit", kwargs={"pk": self.comment.pk})
        response = self.client.post(url, {"content": "Edited!"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["edited"])
        self.assertEqual(data["content"], "Edited!")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Edited!")

    def test_comment_edit_by_non_author_returns_403(self):
        self.client.logout()
        self.client.login(username="bob", password="pass123")
        url = reverse("comments:comment_edit", kwargs={"pk": self.comment.pk})
        response = self.client.post(url, {"content": "Hacked!"})
        self.assertEqual(response.status_code, 403)
