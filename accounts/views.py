from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    UpdateView,
    ListView,
    TemplateView,
)

from django_ratelimit.decorators import ratelimit

from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileEditForm
from .models import CustomUser
from friendships.models import Friendship


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST"), name="dispatch")
class RateLimitedLoginView(LoginView):
    """Login view with brute-force protection (5 POSTs/min per IP)."""

    def form_invalid(self, form):
        was_limited = getattr(self.request, "limited", False)
        if was_limited:
            from django.contrib import messages

            messages.error(
                self.request, "Too many login attempts. Please try again in a minute."
            )
        return super().form_invalid(form)


@method_decorator(ratelimit(key="ip", rate="3/m", method="POST"), name="dispatch")
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")

    def form_invalid(self, form):
        was_limited = getattr(self.request, "limited", False)
        if was_limited:
            from django.contrib import messages

            messages.error(
                self.request, "Too many signup attempts. Please try again in a minute."
            )
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Send verification email
        if self.object.email:
            from .utils import send_verification_email

            try:
                send_verification_email(self.request, self.object)
            except Exception:
                pass  # Email failure shouldn't block signup
        return response


class VerifyEmailView(TemplateView):
    """Verify email address using a signed token."""

    template_name = "accounts/verification_failed.html"

    def get(self, request, *args, **kwargs):
        token = self.kwargs.get("token")
        from .utils import verify_token

        user_id = verify_token(token)
        if user_id is None:
            return self.render_to_context(
                {"error": "The verification link is invalid or has expired."}
            )

        from .models import CustomUser

        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return self.render_to_context({"error": "User not found."})

        if user.is_email_verified:
            from django.shortcuts import redirect

            return redirect("core:home")

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        from django.shortcuts import render

        return render(request, "accounts/verification_done.html")


class ResendVerificationView(LoginRequiredMixin, View):
    """Resend verification email to the logged-in user."""

    def get(self, request):
        if request.user.is_email_verified:
            from django.contrib import messages

            messages.info(request, "Your email is already verified.")
        else:
            from .utils import send_verification_email

            try:
                send_verification_email(request, request.user)
                from django.contrib import messages

                messages.success(request, "Verification email sent. Check your inbox.")
            except Exception:
                from django.contrib import messages

                messages.error(
                    request, "Failed to send verification email. Try again later."
                )
        return redirect("accounts:account_settings")


class ProfileDetailView(DetailView):
    model = CustomUser
    template_name = "accounts/profile.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        context["posts"] = (
            profile_user.posts.filter(is_draft=False)
            .select_related("author")
            .prefetch_related("images")[:10]
        )
        if self.request.user.is_authenticated:
            status = Friendship.friend_status(self.request.user, profile_user)
            context["friendship_status"] = status
            context["is_own_profile"] = self.request.user == profile_user
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = "accounts/profile_edit.html"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            "accounts:profile", kwargs={"username": self.request.user.username}
        )


class FriendListView(LoginRequiredMixin, ListView):
    template_name = "accounts/friend_list.html"
    context_object_name = "friends"
    paginate_by = 20

    def get_queryset(self):
        username = self.kwargs.get("username")
        user = get_object_or_404(CustomUser, username=username)
        friend_ids = Friendship.get_friends(user)
        return CustomUser.objects.filter(id__in=friend_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = get_object_or_404(
            CustomUser, username=self.kwargs.get("username")
        )
        return context


class AccountSettingsView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = "accounts/account_settings.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("accounts:account_settings")


class PrivacySettingsView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    fields = ["is_private"]
    template_name = "accounts/privacy_settings.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("accounts:privacy_settings")


class SecuritySettingsView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/security_settings.html"


class HeartbeatView(LoginRequiredMixin, View):
    """AJAX endpoint for clients to signal activity. Returns online friends."""

    def post(self, request):
        CustomUser.objects.filter(pk=request.user.pk).update(last_seen=timezone.now())
        request.user.last_seen = timezone.now()

        # Return IDs of online friends (for UI badge updates)
        friend_ids = Friendship.get_friends(request.user)
        online_friends = (
            CustomUser.objects.filter(
                id__in=friend_ids,
                last_seen__gte=timezone.now() - timezone.timedelta(minutes=5),
            ).values_list("id", flat=True)
            if friend_ids
            else []
        )
        return JsonResponse(
            {
                "status": "ok",
                "user_id": request.user.id,
                "online_friends": list(online_friends),
            }
        )
