from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, DetailView, UpdateView

from .forms import SignUpForm, ProfileEditForm
from .models import CustomUser
from .utils import send_verification_email, verify_token


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            send_verification_email(self.request, self.object)
            messages.success(
                self.request,
                'Account created successfully! Check your email to verify your account.'
            )
        except Exception:
            messages.warning(
                self.request,
                'Account created, but we could not send a verification email. '
                'You may need to contact support.'
            )
        return response


class VerifyEmailView(TemplateView):
    template_name = 'registration/verification_failed.html'

    def get(self, request, *args, **kwargs):
        user = verify_token(kwargs['uidb64'], kwargs['token'])
        if user is None:
            return self.render_to_response({
                'error': 'Invalid or expired verification link.'
            })
        if user.is_email_verified:
            messages.info(request, 'Email already verified.')
        else:
            user.is_email_verified = True
            user.save()
            messages.success(request, 'Email verified! You can now log in.')
        return redirect('login')


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        context['is_own_profile'] = (self.request.user == profile_user)
        context['friends_count'] = 0  # Placeholder for Phase 3
        context['posts_count'] = 0    # Placeholder for Phase 4
        return context


class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'accounts/profile_edit.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        return self.get_object() == self.request.user

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.object.username})
