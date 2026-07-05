"""WebSocket consumer for real-time chat messaging."""

import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """Per-conversation WebSocket consumer.

    Joins a channel group named ``chat_<conversation_id>`` so that all
    participants in a conversation receive each other's messages in real
    time.
    """

    async def connect(self):
        user = self.scope.get("user")
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages from the WebSocket client."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "typing":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_typing": data.get("is_typing", True),
                },
            )

    async def chat_message(self, event):
        """Relay a new chat message to the WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_message",
                    "id": event.get("id"),
                    "sender_id": event.get("sender_id"),
                    "sender_username": event.get("sender_username"),
                    "content": event.get("content"),
                    "created_at": event.get("created_at"),
                    "is_mine": event.get("sender_id") == self.user.id,
                }
            )
        )

    async def typing_indicator(self, event):
        """Relay a typing indicator to the WebSocket client."""
        # Only send to other users, not the typer themselves
        if event.get("user_id") != self.user.id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing",
                        "user_id": event.get("user_id"),
                        "username": event.get("username"),
                        "is_typing": event.get("is_typing", True),
                    }
                )
            )
