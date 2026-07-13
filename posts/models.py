"""
Post, Like, and Comment models for Facebook Clone.
Uses patterns from Django for Beginners Ch 5, 13, and 15.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse


class Post(models.Model):
    """A user's post — the core Facebook content unit."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    content = models.TextField(max_length=5000, blank=True)
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.username}'s post ({self.created_at.date()})"

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"pk": self.pk})

    @property
    def like_count(self):
        if hasattr(self, '_like_count'):
            return self._like_count
        return self.likes.count()

    @property
    def comment_count(self):
        if hasattr(self, '_comment_count'):
            return self._comment_count
        return self.comments.count()

    @property
    def has_images(self):
        return self.images.exists()


class PostImage(models.Model):
    """Images attached to a post."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="post_images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for post {self.post_id}"


class Like(models.Model):
    """A like/reaction on a post."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} likes post {self.post_id}"


class Comment(models.Model):
    """A comment on a post. Follows Ch 15 pattern."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"pk": self.post.pk})
