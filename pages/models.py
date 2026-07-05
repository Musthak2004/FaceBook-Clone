"""Models for Pages/Community pages feature.

Facebook-style Pages — businesses, organizations, public figures that users
can follow (rather than "join" like Groups). Page admins post updates that
appear in their followers' feeds.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse


class Page(models.Model):
    """A public-facing page (business, organization, public figure)."""

    CATEGORY_CHOICES = [
        ("business", "Business"),
        ("organization", "Organization"),
        ("public_figure", "Public Figure"),
        ("entertainment", "Entertainment"),
        ("community", "Community"),
        ("education", "Education"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )
    profile_picture = models.ImageField(
        upload_to="pages/profile_pictures/", blank=True, null=True
    )
    cover = models.ImageField(upload_to="pages/covers/", blank=True, null=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="administered_pages",
    )
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("pages:detail", kwargs={"pk": self.pk})

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def post_count(self):
        return self.posts.count()


class PageFollower(models.Model):
    """Links a user to a page they follow."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followed_pages",
    )
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="followers")
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "page")
        ordering = ["-followed_at"]

    def __str__(self):
        return f"{self.user.username} follows {self.page.name}"


class PagePost(models.Model):
    """An update posted by a page admin to the page's followers."""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="page_posts",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.username} on {self.page.name}: {self.content[:50]}"
