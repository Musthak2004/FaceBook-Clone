"""
Main URL configuration.
Follows Django for Beginners pattern (Ch 2, 8, 10, 13).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("posts/", include("posts.urls")),
    path("friends/", include("friendships.urls")),
    path("notifications/", include("notifications.urls")),
    path("messages/", include("messaging.urls")),
    path("groups/", include("groups.urls")),
    path("events/", include("events.urls")),
    path("stories/", include("stories.urls")),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
