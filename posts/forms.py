"""
Forms for posts and comments.
Follows Django for Beginners Ch 6 and Ch 15 form patterns.
"""
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Form for creating/editing a post."""

    class Meta:
        model = Post
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "What's on your mind?",
                }
            ),
        }


class CommentForm(forms.ModelForm):
    """Form for adding a comment. Follows Ch 15 CommentForm pattern."""

    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Write a comment...",
                }
            ),
        }
