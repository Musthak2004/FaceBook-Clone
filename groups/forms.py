"""
Forms for the groups app.
"""
from django import forms
from .models import Group


class GroupCreateForm(forms.ModelForm):
    """Form for creating a new group."""

    class Meta:
        model = Group
        fields = ("name", "description", "cover")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Group name",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Describe your group...",
            }),
            "cover": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
        }
