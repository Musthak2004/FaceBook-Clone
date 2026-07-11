"""
Admin registration for stories models.
"""
from django.contrib import admin
from .models import Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("user", "caption", "created_at", "expires_at", "is_expired")
    list_filter = ("created_at", "expires_at")
    search_fields = ("user__username", "caption")

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
