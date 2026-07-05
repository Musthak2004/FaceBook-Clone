from django.contrib import admin

from .models import Attendee, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "creator",
        "date",
        "location",
        "attendee_count",
        "created_at",
    )
    search_fields = ("title",)
    list_filter = ("date",)


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "created_at")
    list_filter = ("status",)
