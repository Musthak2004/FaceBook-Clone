"""Forms for the Groups app."""

from django import forms

from .models import Group


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ("name", "description", "cover")

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if (
            Group.objects.filter(name__iexact=name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("A group with this name already exists.")
        return name
