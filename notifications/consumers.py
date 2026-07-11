"""
Django Channels consumer for real-time notification delivery.
Sends unread count updates to authenticated WebSocket clients.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that pushes notification counts to a user."""

    async def connect(self):
        """Accept connection only for authenticated users."""
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user = self.scope["user"]
        self.group_name = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

        # Send initial unread count on connect
        unread_count = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "count": unread_count,
        }))

    async def disconnect(self, close_code):
        """Leave the notification group on disconnect."""
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def notification_update(self, event):
        """Receive a notification-update event from the channel layer and forward it."""
        await self.send(text_data=json.dumps({
            "type": event.get("type", "unread_count"),
            "count": event.get("count", 0),
        }))

    @database_sync_to_async
    def _get_unread_count(self):
        """Return the number of unread notifications for the current user."""
        from .models import Notification
        return Notification.objects.filter(
            recipient=self.user, is_read=False,
        ).count()
