"""
Custom User Model for Facebook Clone.
Follows Django for Beginners Ch 8 pattern: AbstractUser-based custom user model.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class CustomUser(AbstractUser):
    """Custom user model with profile fields."""
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Tell us about yourself",
    )
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    avatar = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        help_text="Profile picture",
    )
    cover_photo = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        help_text="Cover photo",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    friends = models.ManyToManyField(
        "self",
        through="friendships.Friendship",
        symmetrical=False,
        related_name="friends_set",
    )

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("profile", kwargs={"username": self.username})

    @property
    def post_count(self):
        return self.posts.count()

    @property
    def friend_count(self):
        return self.friends.count()

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "/static/images/default-avatar.svg"

    @property
    def cover_photo_url(self):
        if self.cover_photo:
            return self.cover_photo.url
        return "/static/images/default-cover.svg"
