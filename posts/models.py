from django.conf import settings
from django.db import models
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"

    def get_absolute_url(self):
        return reverse("posts:hashtag_detail", kwargs={"slug": self.name})


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("friends", "Friends Only"),
        ("only_me", "Only Me"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    content = models.TextField()
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY_CHOICES, default="public"
    )
    is_draft = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    shared_post = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="shares"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.content[:50]

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"pk": self.pk})

    @property
    def total_likes(self):
        return self.reactions.count()

    @property
    def total_comments(self):
        return self.comments.count()


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="posts/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Post {self.post.id}"


class Poll(models.Model):
    """A poll attached to a post (one poll per post)."""

    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="poll")
    question = models.CharField(max_length=255)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return PollVote.objects.filter(option__poll=self).count()


class PollOption(models.Model):
    """An option/choice within a poll."""

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

    @property
    def vote_count(self):
        return PollVote.objects.filter(option=self).count()

    @property
    def percentage(self, total=None):
        if total is None:
            total = self.poll.total_votes
        if total == 0:
            return 0
        return round(self.vote_count / total * 100)


class PollVote(models.Model):
    """A user's vote for a poll option."""

    option = models.ForeignKey(
        PollOption, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="poll_votes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("option", "user")

    def __str__(self):
        return f"{self.user} voted for {self.option}"


class SavedCollection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_collections",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user}'s collection: {self.name}"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("posts:collection_detail", kwargs={"pk": self.pk})


class SavedPost(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_posts"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saved_by")
    collection = models.ForeignKey(
        SavedCollection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="saved_posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} saved Post {self.post.id}"
