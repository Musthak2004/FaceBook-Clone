"""
Story forms.
"""
from django import forms
from .models import Story


class StoryForm(forms.ModelForm):
    """Form for creating a story."""

    class Meta:
        model = Story
        fields = ["image", "caption"]
        widgets = {
            "caption": forms.TextInput(
                attrs={"placeholder": "Add a caption..."}
            ),
        }
