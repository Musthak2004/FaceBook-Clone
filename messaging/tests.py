"""
Tests for messaging app — written BEFORE implementation (TDD).
Covers models, views, consumers, read receipts, and typing indicators.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ConversationModelTests(TestCase):
    """Tests for the Conversation model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from messaging.models import Conversation
        self.Conversation = Conversation

    def test_create_conversation(self):
        """Can create a conversation with two participants."""
        conv = self.Conversation.objects.create()
        conv.participants.add(self.user1, self.user2)
        self.assertEqual(self.Conversation.objects.count(), 1)
        self.assertEqual(conv.participants.count(), 2)

    def test_conversation_str(self):
        """String representation shows participant usernames."""
        conv = self.Conversation.objects.create()
        conv.participants.add(self.user1, self.user2)
        self.assertIn("alice", str(conv))
        self.assertIn("bob", str(conv))

    def test_group_conversation(self):
        """Conversation supports 3+ participants."""
        User = get_user_model()
        user3 = User.objects.create_user(
            username="charlie", password="secret"
        )
        conv = self.Conversation.objects.create()
        conv.participants.add(self.user1, self.user2, user3)
        self.assertEqual(conv.participants.count(), 3)


class MessageModelTests(TestCase):
    """Tests for the Message model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from messaging.models import Conversation, Message
        self.Conversation = Conversation
        self.Message = Message
        self.conv = Conversation.objects.create()
        self.conv.participants.add(self.user1, self.user2)

    def test_create_message(self):
        """Can create a message in a conversation."""
        msg = self.Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content="Hello!",
        )
        self.assertEqual(self.Message.objects.count(), 1)
        self.assertEqual(msg.content, "Hello!")
        self.assertEqual(msg.sender, self.user1)

    def test_message_ordering(self):
        """Messages ordered by created_at (oldest first for chat)."""
        from django.utils import timezone
        import datetime
        msg1 = self.Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content="First",
        )
        msg2 = self.Message.objects.create(
            conversation=self.conv,
            sender=self.user2,
            content="Second",
        )
        msgs = list(self.Message.objects.filter(conversation=self.conv))
        self.assertEqual(msgs, [msg1, msg2])

    def test_message_no_is_read_field(self):
        """Message model does NOT have an is_read field (use MessageReadReceipt)."""
        self.assertFalse(hasattr(self.Message, "is_read"))

    def test_message_str(self):
        """String representation includes sender and preview."""
        msg = self.Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content="Hello there!",
        )
        self.assertIn("alice", str(msg))
        self.assertIn("Hello", str(msg))

    def test_message_with_image(self):
        """Message can have an optional image/file attachment."""
        msg = self.Message(
            conversation=self.conv,
            sender=self.user1,
            content="Check this out",
        )
        # image field exists and is optional
        self.assertTrue(hasattr(msg, "image") or hasattr(msg, "file"))
        self.assertEqual(msg.content, "Check this out")


class MessageReadReceiptModelTests(TestCase):
    """Tests for the MessageReadReceipt model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from messaging.models import Conversation, Message, MessageReadReceipt
        self.Conversation = Conversation
        self.Message = Message
        self.MessageReadReceipt = MessageReadReceipt
        self.conv = Conversation.objects.create()
        self.conv.participants.add(self.user1, self.user2)
        self.msg = self.Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content="Read me",
        )

    def test_create_read_receipt(self):
        """Can create a read receipt linking user to message."""
        receipt = self.MessageReadReceipt.objects.create(
            message=self.msg,
            user=self.user2,
        )
        self.assertEqual(self.MessageReadReceipt.objects.count(), 1)
        self.assertEqual(receipt.message, self.msg)
        self.assertEqual(receipt.user, self.user2)

    def test_read_receipt_has_read_at(self):
        """Read receipt records when it was read."""
        from django.utils import timezone
        receipt = self.MessageReadReceipt.objects.create(
            message=self.msg,
            user=self.user2,
        )
        self.assertIsNotNone(receipt.read_at)

    def test_read_receipt_unique_together(self):
        """Each user has at most one read receipt per message."""
        self.MessageReadReceipt.objects.create(
            message=self.msg, user=self.user2,
        )
        # Second creation should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.MessageReadReceipt.objects.create(
                message=self.msg, user=self.user2,
            )

    def test_message_read_by(self):
        """Can query which users have read a message."""
        self.MessageReadReceipt.objects.create(
            message=self.msg, user=self.user2,
        )
        readers = self.MessageReadReceipt.objects.filter(
            message=self.msg,
        ).values_list("user__username", flat=True)
        self.assertIn("bob", list(readers))
        self.assertNotIn("alice", list(readers))

    def test_unread_messages_for_user(self):
        """Can find messages not yet read by a user."""
        msg2 = self.Message.objects.create(
            conversation=self.conv,
            sender=self.user2,
            content="Reply",
        )
        self.MessageReadReceipt.objects.create(
            message=self.msg, user=self.user2,
        )
        # user2 has not read msg2 yet
        unread = self.Message.objects.filter(
            conversation=self.conv,
        ).exclude(
            sender=self.user2,
        ).exclude(
            pk__in=self.MessageReadReceipt.objects.filter(
                user=self.user2,
            ).values("message_id"),
        )
        self.assertEqual(unread.count(), 0)  # msg sent by user2, msg2 also by user2

        # For user1: msg2 is unread (not their own, no receipt)
        unread_for_user1 = self.Message.objects.filter(
            conversation=self.conv,
        ).exclude(
            sender=self.user1,
        ).exclude(
            pk__in=self.MessageReadReceipt.objects.filter(
                user=self.user1,
            ).values("message_id"),
        )
        self.assertEqual(unread_for_user1.count(), 1)


class ConversationListViewTests(TestCase):
    """Tests for the conversation list view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from messaging.models import Conversation, Message
        self.Conversation = Conversation
        self.Message = Message

    def test_list_authenticated(self):
        """Authenticated user sees their conversations."""
        conv = self.Conversation.objects.create()
        conv.participants.add(self.user1, self.user2)
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:list"))
        self.assertEqual(response.status_code, 200)

    def test_list_anonymous_redirect(self):
        """Anonymous user is redirected to login."""
        response = self.client.get(reverse("messaging:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_list_only_own_conversations(self):
        """User only sees conversations they participate in."""
        User = get_user_model()
        user3 = User.objects.create_user(
            username="charlie", password="secret"
        )
        conv1 = self.Conversation.objects.create()
        conv1.participants.add(self.user1, self.user2)
        conv2 = self.Conversation.objects.create()
        conv2.participants.add(self.user2, user3)
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:list"))
        self.assertIn("conversations", response.context)
        # alice should only see conv1
        self.assertEqual(len(response.context["conversations"]), 1)

    def test_list_ordered_by_most_recent_message(self):
        """Conversations are ordered by their most recent message."""
        conv1 = self.Conversation.objects.create()
        conv1.participants.add(self.user1, self.user2)
        conv2 = self.Conversation.objects.create()
        conv2.participants.add(self.user1, self.user2)
        self.Message.objects.create(
            conversation=conv2, sender=self.user1, content="Newer",
        )
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:list"))
        convs = response.context["conversations"]
        self.assertEqual(convs[0].pk, conv2.pk)  # newest first

    def test_list_shows_last_message_preview(self):
        """Conversation list shows the most recent message content."""
        self.Message.objects.create(
            conversation=self.Conversation.objects.create(),
            sender=self.user1,
            content="Last message preview",
        )
        self.Conversation.objects.first().participants.add(self.user1, self.user2)
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:list"))
        self.assertContains(response, "Last message preview")

    def test_list_shows_unread_count(self):
        """Conversation list shows unread message count."""
        conv = self.Conversation.objects.create()
        conv.participants.add(self.user1, self.user2)
        self.Message.objects.create(
            conversation=conv, sender=self.user2, content="Unread msg",
        )
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:list"))
        # Context should include unread counts
        self.assertIn("unread_counts", response.context)


class ConversationDetailViewTests(TestCase):
    """Tests for the conversation detail (chat) view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from messaging.models import Conversation, Message
        self.Conversation = Conversation
        self.Message = Message
        self.conv = self.Conversation.objects.create()
        self.conv.participants.add(self.user1, self.user2)
        # Add some messages
        for i in range(3):
            self.Message.objects.create(
                conversation=self.conv,
                sender=self.user1 if i % 2 == 0 else self.user2,
                content=f"Message {i}",
            )

    def test_detail_authenticated(self):
        """Authenticated participant sees conversation detail."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_anonymous_redirect(self):
        """Anonymous user is redirected from conversation detail."""
        response = self.client.get(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
        )
        self.assertEqual(response.status_code, 302)

    def test_detail_non_participant_denied(self):
        """Non-participant gets 403 or 404."""
        User = get_user_model()
        user3 = User.objects.create_user(
            username="charlie", password="secret"
        )
        self.client.login(username="charlie", password="secret")
        response = self.client.get(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
        )
        self.assertIn(response.status_code, [403, 404])

    def test_detail_has_message_form(self):
        """Conversation detail includes a message send form."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
        )
        self.assertIn("form", response.context)

    def test_detail_post_creates_message(self):
        """POST to conversation detail creates a new message."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
            {"content": "New message!"},
        )
        self.assertEqual(response.status_code, 302)
        msg_exists = self.Message.objects.filter(
            conversation=self.conv,
            sender=self.user1,
            content="New message!",
        ).exists()
        self.assertTrue(msg_exists)

    def test_detail_marks_messages_as_read(self):
        """Viewing conversation creates read receipts for unread messages."""
        from messaging.models import MessageReadReceipt
        self.client.login(username="alice", password="secret")
        self.client.get(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
        )
        # Messages sent by bob should now have read receipts from alice
        bob_msgs = self.Message.objects.filter(
            conversation=self.conv, sender=self.user2,
        )
        for msg in bob_msgs:
            self.assertTrue(
                MessageReadReceipt.objects.filter(
                    message=msg, user=self.user1,
                ).exists(),
                f"Message {msg.pk} should have read receipt from alice",
            )

    def test_detail_shows_messages(self):
        """Conversation detail renders message history."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(
            reverse("messaging:detail", kwargs={"pk": self.conv.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Message 0")
        self.assertContains(response, "Message 1")


class ConversationCreateViewTests(TestCase):
    """Tests for creating a new conversation."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def test_create_view_authenticated(self):
        """Authenticated user sees the new conversation form."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:create"))
        self.assertEqual(response.status_code, 200)

    def test_create_view_anonymous_redirect(self):
        """Anonymous user redirected from create conversation."""
        response = self.client.get(reverse("messaging:create"))
        self.assertEqual(response.status_code, 302)

    def test_create_conversation_with_participants(self):
        """POST creates conversation with selected participants."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("messaging:create"),
            {"participants": [self.user2.pk]},
        )
        self.assertEqual(response.status_code, 302)
        from messaging.models import Conversation
        conv = Conversation.objects.first()
        self.assertIsNotNone(conv)
        self.assertIn(self.user1, conv.participants.all())
        self.assertIn(self.user2, conv.participants.all())


class ConversationLeaveViewTests(TestCase):
    """Tests for leaving a conversation."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from messaging.models import Conversation
        self.Conversation = Conversation
        self.conv = self.Conversation.objects.create()
        self.conv.participants.add(self.user1, self.user2)

    def test_leave_conversation(self):
        """POST removes current user from participants."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("messaging:leave", kwargs={"pk": self.conv.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(
            self.user1, self.conv.participants.all(),
        )

    def test_leave_anonymous_redirect(self):
        """Anonymous user cannot leave conversations."""
        response = self.client.post(
            reverse("messaging:leave", kwargs={"pk": self.conv.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_leave_non_participant_denied(self):
        """Non-participant cannot leave a conversation (403/404)."""
        User = get_user_model()
        user3 = User.objects.create_user(
            username="charlie", password="secret"
        )
        self.client.login(username="charlie", password="secret")
        response = self.client.post(
            reverse("messaging:leave", kwargs={"pk": self.conv.pk}),
        )
        self.assertIn(response.status_code, [403, 404])


class MessagingConsumerTests(TestCase):
    """Tests for the messaging WebSocket consumer."""

    def test_consumer_imports(self):
        """Messaging consumer module is importable."""
        try:
            from messaging import consumers
            self.assertTrue(hasattr(consumers, "ChatConsumer"))
        except ImportError:
            self.fail("messaging.consumers module not found")

    def test_routing_imports(self):
        """Messaging routing module is importable."""
        try:
            from messaging import routing
            self.assertTrue(hasattr(routing, "websocket_urlpatterns"))
            self.assertIsInstance(routing.websocket_urlpatterns, list)
        except ImportError:
            self.fail("messaging.routing module not found")


class MessagingIntegrationTests(TestCase):
    """End-to-end integration tests for messaging."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def test_full_message_flow(self):
        """Complete flow: create conv → send messages → view → leave."""
        from messaging.models import Conversation, Message, MessageReadReceipt

        # Alice creates a conversation with Bob
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("messaging:create"),
            {"participants": [self.user2.pk]},
        )
        self.assertEqual(response.status_code, 302)
        conv = Conversation.objects.first()
        self.assertEqual(conv.participants.count(), 2)

        # Alice sends a message
        self.client.post(
            reverse("messaging:detail", kwargs={"pk": conv.pk}),
            {"content": "Hey Bob!"},
        )
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.content, "Hey Bob!")

        # Bob logs in and views the conversation
        self.client.logout()
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("messaging:detail", kwargs={"pk": conv.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hey Bob!")

        # Bob's view should have created a read receipt
        self.assertTrue(
            MessageReadReceipt.objects.filter(
                message=msg, user=self.user2,
            ).exists(),
        )

        # Bob sends a reply
        self.client.post(
            reverse("messaging:detail", kwargs={"pk": conv.pk}),
            {"content": "Hey Alice!"},
        )
        self.assertEqual(Message.objects.count(), 2)

        # Bob leaves the conversation
        response = self.client.post(
            reverse("messaging:leave", kwargs={"pk": conv.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user2, conv.participants.all())

    def test_conversation_list_shows_own_conversations(self):
        """User's conversation list only includes their conversations."""
        from messaging.models import Conversation
        conv = Conversation.objects.create()
        conv.participants.add(self.user1, self.user2)
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("messaging:list"))
        self.assertEqual(len(response.context["conversations"]), 1)
        self.client.logout()

        User = get_user_model()
        user3 = User.objects.create_user(
            username="charlie", password="secret"
        )
        self.client.login(username="charlie", password="secret")
        response = self.client.get(reverse("messaging:list"))
        self.assertEqual(len(response.context["conversations"]), 0)
