"""
Forms for messaging: new conversation, send message.
"""
from django import forms
from django.contrib.auth import get_user_model
from .models import Conversation, Message


class MessageForm(forms.ModelForm):
    """Form for sending a message in a conversation."""

    class Meta:
        model = Message
        fields = ("content", "image")
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Type a message...",
                }
            ),
        }


class ConversationCreateForm(forms.ModelForm):
    """Form for creating a new conversation with participants."""

    participants = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select participants",
    )

    class Meta:
        model = Conversation
        fields = ("participants",)
