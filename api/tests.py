"""Tests for the REST API app, including drf-spectacular schema."""

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from posts.models import Post
from comments.models import Comment
from messaging.models import Conversation, Message

User = get_user_model()


class APISchemaTests(APITestCase):
    """Verify drf-spectacular schema and Swagger UI endpoints work."""

    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="testpass123")
        self.client = APIClient()

    def test_schema_requires_no_auth(self):
        """Schema endpoint should be publicly accessible."""
        response = self.client.get(reverse("schema"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_schema_valid_openapi(self):
        """Schema should be valid OpenAPI JSON."""
        response = self.client.get(reverse("schema"), HTTP_ACCEPT="application/json")
        import json

        data = json.loads(response.content)
        self.assertIn("openapi", data)
        self.assertIn("paths", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_ui_accessible(self):
        """Swagger UI page should render."""
        response = self.client.get(reverse("swagger-ui"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_redoc_ui_accessible(self):
        """ReDoc page should render."""
        response = self.client.get(reverse("redoc"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="testpass123")
        self.other = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.client = APIClient()
        self.client.login(username="apiuser", password="testpass123")

    def test_list_users(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_user_detail(self):
        response = self.client.get(f"/api/users/{self.user.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "apiuser")

    def test_user_detail_other(self):
        response = self.client.get(f"/api/users/{self.other.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_blocked(self):
        self.client.logout()
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PostAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="postuser", password="testpass123"
        )
        self.client = APIClient()
        self.client.login(username="postuser", password="testpass123")

    def test_create_post(self):
        response = self.client.post(
            "/api/posts/", {"content": "API post!", "visibility": "public"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(response.data["author"]["username"], "postuser")

    def test_list_posts(self):
        Post.objects.create(author=self.user, content="Test post", visibility="public")
        response = self.client.get("/api/posts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_update_own_post(self):
        post = Post.objects.create(author=self.user, content="Original")
        response = self.client.patch(f"/api/posts/{post.pk}/", {"content": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated")

    def test_delete_own_post(self):
        post = Post.objects.create(author=self.user, content="Delete me")
        response = self.client.delete(f"/api/posts/{post.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_update_others_post(self):
        other = User.objects.create_user(username="other", password="testpass123")
        post = Post.objects.create(author=other, content="Other's post")
        response = self.client.patch(f"/api/posts/{post.pk}/", {"content": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CommentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="commentuser", password="testpass123"
        )
        self.client = APIClient()
        self.client.login(username="commentuser", password="testpass123")
        self.post = Post.objects.create(author=self.user, content="Post with comments")

    def test_create_comment(self):
        response = self.client.post(
            "/api/comments/",
            {"post": self.post.pk, "content": "Nice post!"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_list_comments(self):
        Comment.objects.create(author=self.user, post=self.post, content="First!")
        response = self.client.get("/api/comments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConversationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="msguser", password="testpass123")
        self.other = User.objects.create_user(
            username="othermsg", password="testpass123"
        )
        self.client = APIClient()
        self.client.login(username="msguser", password="testpass123")
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user, self.other)
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Hello!",
        )

    def test_list_conversations(self):
        response = self.client.get("/api/conversations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_messages(self):
        response = self.client.get(
            f"/api/messages/?conversation={self.conversation.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_access_others_conversation(self):
        self.client.logout()
        User.objects.create_user(username="stranger", password="testpass123")
        self.client.login(username="stranger", password="testpass123")
        response = self.client.get(
            f"/api/messages/?conversation={self.conversation.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)
