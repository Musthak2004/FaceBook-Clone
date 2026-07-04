from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/<str:username>/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<str:username>/friends/', views.FriendListView.as_view(), name='friend_list'),
    path('settings/account/', views.AccountSettingsView.as_view(), name='account_settings'),
    path('settings/privacy/', views.PrivacySettingsView.as_view(), name='privacy_settings'),
    path('settings/security/', views.SecuritySettingsView.as_view(), name='security_settings'),
]
