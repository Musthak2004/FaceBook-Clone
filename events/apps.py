"""
App config for events app.
Connects post_delete signal to clean up cover images.
"""
from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        from django.db.models.signals import post_delete
        from .models import delete_event_cover, Event
        post_delete.connect(delete_event_cover, sender=Event)
