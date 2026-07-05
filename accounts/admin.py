from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_private", "friend_count", "created_at")
    list_filter = ("is_private", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("-created_at",)
    fieldsets = UserAdmin.fieldsets + (
        (
            "Profile Info",
            {
                "fields": (
                    "profile_picture",
                    "cover_photo",
                    "bio",
                    "date_of_birth",
                    "education",
                    "work",
                    "location",
                    "website",
                    "is_private",
                ),
            },
        ),
    )
