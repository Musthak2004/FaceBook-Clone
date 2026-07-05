from django import forms

from .models import Page


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = [
            "name",
            "description",
            "category",
            "profile_picture",
            "cover",
            "website",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
