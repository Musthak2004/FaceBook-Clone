from django.contrib import admin

from .models import Post, PostImage, SavedPost


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content', 'visibility', 'is_draft', 'created_at')
    list_filter = ('visibility', 'is_draft', 'created_at')
    search_fields = ('content', 'author__username')
    inlines = [PostImageInline]


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'uploaded_at')


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
