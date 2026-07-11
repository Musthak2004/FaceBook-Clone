from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
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


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'bio', 'location', 'gender',
            'website', 'date_of_birth', 'profile_picture', 'cover_photo',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about yourself...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            'bio',
            Row(
                Column('location', css_class='col-md-6'),
                Column('gender', css_class='col-md-6'),
            ),
            Row(
                Column('website', css_class='col-md-6'),
                Column('date_of_birth', css_class='col-md-6'),
            ),
            Row(
                Column('profile_picture', css_class='col-md-6'),
                Column('cover_photo', css_class='col-md-6'),
            ),
            Submit('submit', 'Save Changes', css_class='btn-primary'),
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name')
