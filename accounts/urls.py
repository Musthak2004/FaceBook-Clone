"""
Account URL patterns.
Follows Django for Beginners Ch 7/9 URL patterns.
"""
from django.urls import path
from .views import SignUpView, ProfileView, ProfileEditView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("~<username>/", ProfileView.as_view(), name="profile"),
    path("~<username>/edit/", ProfileEditView.as_view(), name="profile_edit"),
]
