"""
Admin for posts, likes, comments.
Follows Ch 15 admin inline pattern.
"""
from django.contrib import admin
from .models import Post, PostImage, Like, Comment


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline, CommentInline]
    list_display = ["author", "content_preview", "created_at", "like_count"]
    list_filter = ["created_at"]

    def content_preview(self, obj):
        return obj.content[:75] + "..." if len(obj.content) > 75 else obj.content
    content_preview.short_description = "Content"


admin.site.register(Post, PostAdmin)
admin.site.register(PostImage)
admin.site.register(Like)
admin.site.register(Comment)
