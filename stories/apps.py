"""
App config for stories app.
Connects post_delete signal to clean up story images.
"""
from django.apps import AppConfig


class StoriesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stories"

    def ready(self):
        from django.db.models.signals import post_delete
        from .models import delete_story_image, Story
        post_delete.connect(delete_story_image, sender=Story)
