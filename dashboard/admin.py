from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reported_by", "post", "comment", "is_resolved", "created_at")
    list_filter = ("is_resolved", "created_at")
    search_fields = ("reason", "reported_by__username")
