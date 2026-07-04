from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth URLs (built-in views from django.contrib.auth)
    path('accounts/', include('django.contrib.auth.urls')),
    # Local app URLs
    path('accounts/', include('accounts.urls')),
    path('', include('core.urls')),
    path('posts/', include('posts.urls')),
    path('comments/', include('comments.urls')),
    path('reactions/', include('reactions.urls')),
    path('friends/', include('friendships.urls')),
    path('notifications/', include('notifications.urls')),
    path('messages/', include('messaging.urls')),
    path('search/', include('search.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Serve media files during development (per book's pattern)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
