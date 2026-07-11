from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import CustomUser


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254, required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_tag = True
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6 mb-0'),
                Column('last_name', css_class='col-md-6 mb-0'),
            ),
            'email',
            'username',
            'password1',
            'password2',
            Submit('submit', 'Sign Up', css_class='btn-primary w-100'),
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name')
