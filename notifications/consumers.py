import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if user.is_anonymous:
            await self.close()
            return

        self.user_id = user.id
        self.group_name = f"notifications_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send unread count on connect
        unread_count = await self.get_unread_count()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "unread_count",
                    "count": unread_count,
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle messages from the WebSocket client."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "mark_read":
            notification_id = data.get("notification_id")
            if notification_id:
                await self.mark_notification_read(notification_id)
                unread_count = await self.get_unread_count()
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "unread_count",
                            "count": unread_count,
                        }
                    )
                )

        elif msg_type == "mark_all_read":
            await self.mark_all_notifications_read()
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "unread_count",
                        "count": 0,
                    }
                )
            )

    async def notification_message(self, event):
        """Send a notification to the WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification_id": event.get("notification_id"),
                    "notification_type": event.get("notification_type"),
                    "sender_username": event.get("sender_username"),
                    "sender_profile_picture": event.get("sender_profile_picture"),
                    "unread_count": event.get("unread_count", 0),
                    "message": event.get("message", ""),
                }
            )
        )

    async def unread_count_update(self, event):
        """Push an updated unread count."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "unread_count",
                    "count": event.get("count", 0),
                }
            )
        )

    @database_sync_to_async
    def get_unread_count(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.get(id=self.user_id)
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        Notification.objects.filter(
            id=notification_id, recipient_id=self.user_id
        ).update(is_read=True)

    @database_sync_to_async
    def mark_all_notifications_read(self):
        Notification.objects.filter(recipient_id=self.user_id, is_read=False).update(
            is_read=True
        )
