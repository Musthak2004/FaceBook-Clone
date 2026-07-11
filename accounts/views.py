"""
Account views: profile, edit profile, signup.
Follows Django for Beginners Ch 7-9 patterns with class-based views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, CreateView
from .forms import CustomUserCreationForm, ProfileEditForm
from .models import CustomUser
from posts.models import Post


class SignUpView(CreateView):
    """User registration. Follows Ch 7 SignUpView pattern."""
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class ProfileView(DetailView):
    """Display a user's profile with their posts."""
    model = CustomUser
    template_name = "accounts/profile.html"
    slug_field = "username"
    slug_url_kwarg = "username"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        context["posts"] = Post.objects.filter(
            author=profile_user, group__isnull=True,
        ).select_related("author").prefetch_related(
            "likes", "comments"
        ).order_by("-created_at")

        # Check for active stories
        from stories.models import Story
        context["has_active_stories"] = Story.active_stories.filter(
            user=profile_user,
        ).exists()

        # Friendship status for logged-in user viewing this profile
        if self.request.user.is_authenticated and self.request.user != profile_user:
            from friendships.models import Friendship
            friendship = Friendship.objects.filter(
                from_user=self.request.user,
                to_user=profile_user,
            ).first()
            if friendship:
                context["friendship_status"] = friendship.status
                context["friendship_id"] = friendship.id
            else:
                context["friendship_status"] = None
        elif self.request.user == profile_user:
            context["is_own_profile"] = True

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit own profile. Follows Ch 6 UpdateView pattern."""
    model = CustomUser
    form_class = ProfileEditForm
    template_name = "accounts/profile_edit.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("profile", kwargs={"username": self.request.user.username})
