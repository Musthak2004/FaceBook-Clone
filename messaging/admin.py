"""
Admin registration for messaging models.
"""
from django.contrib import admin
from .models import Conversation, Message, MessageReadReceipt


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")
    filter_horizontal = ("participants",)
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "conversation_id", "created_at", "preview")
    list_filter = ("created_at",)
    search_fields = ("sender__username", "content")

    def preview(self, obj):
        return obj.content[:50] if obj.content else "[file]"


@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "read_at")
    list_filter = ("read_at",)
