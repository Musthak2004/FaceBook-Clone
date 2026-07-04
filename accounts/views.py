from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, ListView, TemplateView

from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileEditForm
from .models import CustomUser
from friendships.models import Friendship


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('login')


class ProfileDetailView(DetailView):
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        context['posts'] = profile_user.posts.filter(is_draft=False)[:10]
        if self.request.user.is_authenticated:
            status = Friendship.friend_status(self.request.user, profile_user)
            context['friendship_status'] = status
            context['is_own_profile'] = self.request.user == profile_user
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'accounts/profile_edit.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})


class FriendListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/friend_list.html'
    context_object_name = 'friends'
    paginate_by = 20

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(CustomUser, username=username)
        friend_ids = Friendship.get_friends(user)
        return CustomUser.objects.filter(id__in=friend_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = get_object_or_404(
            CustomUser, username=self.kwargs.get('username')
        )
        return context


class AccountSettingsView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/account_settings.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('accounts:account_settings')


class PrivacySettingsView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    fields = ['is_private']
    template_name = 'accounts/privacy_settings.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('accounts:privacy_settings')


class SecuritySettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/security_settings.html'
