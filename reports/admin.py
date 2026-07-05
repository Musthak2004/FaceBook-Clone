from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "reporter",
        "content_type",
        "object_id",
        "reason",
        "is_reviewed",
        "created_at",
    )
    list_filter = ("reason", "is_reviewed", "resolved")
    search_fields = ("reporter__username", "description")
