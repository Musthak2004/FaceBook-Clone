from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    poll_question = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Ask a question...",
            }
        ),
        label="Poll question",
    )
    poll_options = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-input",
                "rows": 3,
                "placeholder": "One option per line",
            }
        ),
        label="Poll options",
        help_text="Enter each option on a new line (min 2, max 10).",
    )

    class Meta:
        model = Post
        fields = ("content", "visibility", "is_draft")
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "What's on your mind?",
                    "class": "form-input post-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content"].label = ""
        for field_name in self.fields:
            if field_name != "content":
                self.fields[field_name].widget.attrs.update({"class": "form-input"})

    def clean_poll_options(self):
        options_raw = self.cleaned_data.get("poll_options", "").strip()
        if not options_raw:
            return ""
        lines = [line.strip() for line in options_raw.split("\n") if line.strip()]
        if len(lines) < 2:
            raise forms.ValidationError("Add at least 2 options.")
        if len(lines) > 10:
            raise forms.ValidationError("Maximum 10 options allowed.")
        return "\n".join(lines)
