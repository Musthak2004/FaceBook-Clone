from django.contrib import admin

from .models import Group, GroupMembership, GroupPost


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "admin", "member_count", "created_at")
    search_fields = ("name",)


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "role", "joined_at")
    list_filter = ("role",)


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ("author", "group", "created_at")
