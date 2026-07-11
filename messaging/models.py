"""
Conversation, Message, and MessageReadReceipt models for real-time messaging.
"""
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A conversation (DM or group) between multiple participants."""

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        names = self.participants.values_list("username", flat=True)[:3]
        suffix = " ..." if self.participants.count() > 3 else ""
        return ", ".join(names) + suffix

    @property
    def last_message(self):
        return self.messages.order_by("-created_at").first()


class Message(models.Model):
    """A single message within a conversation. No is_read field — use MessageReadReceipt."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_sent",
    )
    content = models.TextField(max_length=5000, blank=True)
    image = models.ImageField(
        upload_to="message_images/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        preview = self.content[:50] if self.content else "[file]"
        return f"{self.sender.username}: {preview}"


class MessageReadReceipt(models.Model):
    """Records that a user has read a message."""

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="read_receipts",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_read_receipts",
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")

    def __str__(self):
        return f"{self.user.username} read message {self.message_id}"
