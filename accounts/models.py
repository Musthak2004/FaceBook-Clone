from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'username': self.username})

    def get_profile_picture_url(self):
        if hasattr(self, 'profile_picture') and self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default-avatar.svg'

    def get_cover_photo_url(self):
        if hasattr(self, 'cover_photo') and self.cover_photo:
            return self.cover_photo.url
        return '/static/images/default-cover.svg'
