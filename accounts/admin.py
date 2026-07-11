"""
Admin configuration for CustomUser.
Follows Django for Beginners Ch 8 admin pattern.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    """Custom admin to display all profile fields."""
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "location",
        "is_staff",
    ]
    fieldsets = UserAdmin.fieldsets + (
        ("Profile Info", {"fields": ("bio", "location", "date_of_birth", "avatar", "cover_photo")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile Info", {"fields": ("bio", "location", "date_of_birth")}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
