from django.contrib import admin

from .models import Page, PageFollower, PagePost


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "admin", "follower_count", "created_at"]
    list_filter = ["category", "created_at"]
    search_fields = ["name", "description"]


@admin.register(PageFollower)
class PageFollowerAdmin(admin.ModelAdmin):
    list_display = ["user", "page", "followed_at"]


@admin.register(PagePost)
class PagePostAdmin(admin.ModelAdmin):
    list_display = ["page", "author", "created_at", "content_preview"]

    def content_preview(self, obj):
        return obj.content[:80]
