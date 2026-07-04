from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='covers/', blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    date_of_birth = models.DateField(null=True, blank=True)
    education = models.CharField(max_length=255, blank=True)
    work = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    is_private = models.BooleanField(default=False)
    friends = models.ManyToManyField(
        'self',
        through='friendships.Friendship',
        symmetrical=False,
        related_name='friend_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('profile', kwargs={'username': self.username})

    @property
    def friend_count(self):
        from friendships.models import Friendship
        return Friendship.objects.filter(
            models.Q(from_user=self) | models.Q(to_user=self),
            status='accepted'
        ).count()

    @property
    def post_count(self):
        return self.posts.filter(is_draft=False).count()
