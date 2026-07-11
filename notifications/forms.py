"""
Forms for the notifications app — preference management.
"""
from django import forms
from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    """Form for updating per-type notification preferences."""

    class Meta:
        model = NotificationPreference
        fields = [
            "email_likes",
            "email_comments",
            "email_friend_requests",
            "email_mentions",
            "push_likes",
            "push_comments",
            "push_friend_requests",
            "push_mentions",
        ]
        widgets = {
            field: forms.CheckboxInput(attrs={"class": "form-check-input"})
            for field in [
                "email_likes", "email_comments",
                "email_friend_requests", "email_mentions",
                "push_likes", "push_comments",
                "push_friend_requests", "push_mentions",
            ]
        }
        labels = {
            "email_likes": "Email — Likes",
            "email_comments": "Email — Comments",
            "email_friend_requests": "Email — Friend Requests",
            "email_mentions": "Email — Mentions",
            "push_likes": "In-App — Likes",
            "push_comments": "In-App — Comments",
            "push_friend_requests": "In-App — Friend Requests",
            "push_mentions": "In-App — Mentions",
        }
