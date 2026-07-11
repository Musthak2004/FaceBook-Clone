"""
Group and GroupMembership models for public groups.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse


class Group(models.Model):
    """A public group with an admin and members."""

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000, blank=True)
    cover = models.ImageField(
        upload_to="group_covers/",
        blank=True,
        null=True,
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groups_administered",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("groups:detail", kwargs={"pk": self.pk})

    @property
    def members(self):
        """Return the queryset of users who are members of this group."""
        from django.contrib.auth import get_user_model
        return get_user_model().objects.filter(
            pk__in=self.memberships.values("user_id"),
        )

    def is_admin_user(self, user):
        return self.admin == user


class GroupMembership(models.Model):
    """Membership linking a user to a group with a role."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


# Auto-cleanup cover image on group delete via post_delete signal
def delete_group_cover(sender, instance, **kwargs):
    """Remove the cover image file from disk when group is deleted."""
    if instance.cover:
        instance.cover.delete(save=False)
