"""
Django Channels consumer for per-conversation real-time messaging.
Supports message sending, typing indicators, and presence.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for a single conversation room."""

    async def connect(self):
        """Authenticate user and join the conversation room."""
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        # Verify user is a participant
        if not await self._is_participant():
            await self.close()
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Leave the conversation room on disconnect."""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            await self._handle_send_message(data)
        elif action == "typing":
            await self._handle_typing(data)

    async def _handle_send_message(self, data):
        """Save a new message and broadcast it to the room."""
        content = data.get("content", "").strip()
        if not content:
            return

        message = await self._save_message(content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message.id,
                "sender_id": self.user.id,
                "sender_username": self.user.username,
                "sender_avatar": self.user.avatar_url,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            },
        )

    async def _handle_typing(self, data):
        """Broadcast typing indicator to the room (not back to sender)."""
        is_typing = data.get("is_typing", False)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": self.user.id,
                "username": self.user.username,
                "is_typing": is_typing,
            },
        )

    async def chat_message(self, event):
        """Forward a chat message to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "message_id": event["message_id"],
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "sender_avatar": event["sender_avatar"],
            "content": event["content"],
            "created_at": event["created_at"],
        }))

    async def typing_indicator(self, event):
        """Forward a typing indicator to the WebSocket client."""
        # Don't send typing indicator back to the user who initiated it
        if event["user_id"] == self.user.id:
            return

        await self.send(text_data=json.dumps({
            "type": "typing",
            "user_id": event["user_id"],
            "username": event["username"],
            "is_typing": event["is_typing"],
        }))

    @database_sync_to_async
    def _is_participant(self):
        """Check if the current user is a participant in the conversation."""
        from .models import Conversation
        try:
            conv = Conversation.objects.get(pk=self.conversation_id)
            return self.user in conv.participants.all()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def _save_message(self, content):
        """Persist a message to the database."""
        from .models import Conversation, Message
        conv = Conversation.objects.get(pk=self.conversation_id)
        return Message.objects.create(
            conversation=conv,
            sender=self.user,
            content=content,
        )
