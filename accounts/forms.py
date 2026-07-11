"""
Forms for CustomUser.
Follows Django for Beginners Ch 8/9 pattern.
"""
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users with extended fields."""

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
        )


class CustomUserChangeForm(UserChangeForm):
    """Form for changing user details."""

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "location",
            "date_of_birth",
            "avatar",
            "cover_photo",
        )


class ProfileEditForm(UserChangeForm):
    """Form for users to edit their own profile (password excluded)."""

    password = None  # Remove password field

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "bio",
            "location",
            "date_of_birth",
            "avatar",
            "cover_photo",
        )
