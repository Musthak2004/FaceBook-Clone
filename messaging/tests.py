"""Tests for the Messaging app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Conversation, Message

User = get_user_model()


class MessagingModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="alice", password="testpass123")
        self.user2 = User.objects.create_user(username="bob", password="testpass123")
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_conversation_created(self):
        self.assertEqual(Conversation.objects.count(), 1)

    def test_conversation_str(self):
        self.assertEqual(str(self.conversation), f"Conversation {self.conversation.id}")

    def test_conversation_participants(self):
        participants = list(self.conversation.participants.all())
        self.assertIn(self.user1, participants)
        self.assertIn(self.user2, participants)

    def test_conversation_other_user(self):
        self.assertEqual(self.conversation.other_user(self.user1), self.user2)

    def test_conversation_last_message_empty(self):
        self.assertIsNone(self.conversation.last_message)

    def test_conversation_last_message_with_messages(self):
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello!",
        )
        self.assertEqual(self.conversation.last_message.content, "Hello!")

    def test_message_created(self):
        msg = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello Bob!",
        )
        self.assertEqual(msg.content, "Hello Bob!")
        self.assertFalse(msg.is_read)
        self.assertEqual(msg.conversation, self.conversation)

    def test_message_str(self):
        msg = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello!",
        )
        expected = f"{self.user1.username}: {msg.content[:30]}"
        self.assertEqual(str(msg), expected)

    def test_message_ordering(self):
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="First",
        )
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content="Second",
        )
        messages = list(Message.objects.all())
        self.assertEqual(messages[0].content, "First")
        self.assertEqual(messages[1].content, "Second")


class MessagingViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="alice", password="testpass123")
        self.user2 = User.objects.create_user(username="bob", password="testpass123")
        self.user3 = User.objects.create_user(
            username="charlie", password="testpass123"
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_conversation_list_requires_login(self):
        response = self.client.get(reverse("messaging:conversation_list"))
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('messaging:conversation_list')}",
        )

    def test_conversation_list_logged_in(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(reverse("messaging:conversation_list"))
        self.assertEqual(response.status_code, 200)

    def test_conversation_list_empty_for_no_conversations(self):
        self.client.login(username="charlie", password="testpass123")
        response = self.client.get(reverse("messaging:conversation_list"))
        self.assertEqual(response.status_code, 200)

    def test_new_conversation_creates(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(
            reverse(
                "messaging:new_conversation",
                kwargs={"username": "charlie"},
            )
        )
        new_conv = Conversation.objects.filter(participants=self.user1).filter(
            participants=self.user3
        )
        self.assertTrue(new_conv.exists())
        self.assertRedirects(
            response,
            reverse(
                "messaging:conversation_detail",
                kwargs={"pk": new_conv.first().pk},
            ),
        )

    def test_new_conversation_reuses_existing(self):
        self.client.login(username="alice", password="testpass123")
        self.client.get(
            reverse("messaging:new_conversation", kwargs={"username": "bob"}),
        )
        response = self.client.get(
            reverse("messaging:new_conversation", kwargs={"username": "bob"}),
        )
        self.assertRedirects(
            response,
            reverse(
                "messaging:conversation_detail",
                kwargs={"pk": self.conversation.pk},
            ),
        )
        self.assertEqual(Conversation.objects.count(), 1)

    def test_new_conversation_self_redirects(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(
            reverse(
                "messaging:new_conversation",
                kwargs={"username": "alice"},
            )
        )
        self.assertRedirects(response, reverse("messaging:conversation_list"))

    def test_conversation_detail_requires_login(self):
        response = self.client.get(
            reverse(
                "messaging:conversation_detail",
                kwargs={"pk": self.conversation.pk},
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_conversation_detail_shows_messages(self):
        self.client.login(username="alice", password="testpass123")
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hey Bob!",
        )
        response = self.client.get(
            reverse(
                "messaging:conversation_detail",
                kwargs={"pk": self.conversation.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hey Bob!")

    def test_conversation_detail_non_participant_blocked(self):
        self.client.login(username="charlie", password="testpass123")
        response = self.client.get(
            reverse(
                "messaging:conversation_detail",
                kwargs={"pk": self.conversation.pk},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_conversation_detail_marks_messages_read(self):
        self.client.login(username="bob", password="testpass123")
        msg = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Unread message",
        )
        self.client.get(
            reverse(
                "messaging:conversation_detail",
                kwargs={"pk": self.conversation.pk},
            )
        )
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_send_message_post(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.post(
            reverse(
                "messaging:send_message",
                kwargs={"pk": self.conversation.pk},
            ),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["sent"])

    def test_send_message_empty_content(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.post(
            reverse(
                "messaging:send_message",
                kwargs={"pk": self.conversation.pk},
            ),
            {"content": ""},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_send_message_non_participant_blocked(self):
        self.client.login(username="charlie", password="testpass123")
        response = self.client.post(
            reverse(
                "messaging:send_message",
                kwargs={"pk": self.conversation.pk},
            ),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 404)

    def test_send_message_get_not_allowed(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(
            reverse(
                "messaging:send_message",
                kwargs={"pk": self.conversation.pk},
            )
        )
        self.assertEqual(response.status_code, 405)
