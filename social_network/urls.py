from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Local app URLs (before auth include to override login/signup)
    path("accounts/", include("accounts.urls")),
    # Auth URLs (built-in views from django.contrib.auth)
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
    path("posts/", include("posts.urls")),
    path("comments/", include("comments.urls")),
    path("reactions/", include("reactions.urls")),
    path("friends/", include("friendships.urls")),
    path("notifications/", include("notifications.urls")),
    path("messages/", include("messaging.urls")),
    path("search/", include("search.urls")),
    path("dashboard/", include("dashboard.urls")),
]

# Serve media files during development (per book's pattern)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
