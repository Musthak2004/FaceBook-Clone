"""
Admin registration for groups models.
"""
from django.contrib import admin
from .models import Group, GroupMembership


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "admin", "member_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "admin__username")
    inlines = [GroupMembershipInline]

    def member_count(self, obj):
        return obj.memberships.count()


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "role", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("group__name", "user__username")
