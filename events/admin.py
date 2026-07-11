"""
Admin registration for events models.
"""
from django.contrib import admin
from .models import Event, Attendee


class AttendeeInline(admin.TabularInline):
    model = Attendee
    extra = 1
    raw_id_fields = ("user",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "location", "creator", "attendee_count", "created_at")
    list_filter = ("date", "created_at")
    search_fields = ("title", "creator__username")
    inlines = [AttendeeInline]

    def attendee_count(self, obj):
        return obj.attendees.count()


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("event__title", "user__username")
