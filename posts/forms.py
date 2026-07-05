from django import forms

from .models import Post


class PostForm(forms.ModelForm):
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
