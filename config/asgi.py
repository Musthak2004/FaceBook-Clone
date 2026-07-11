"""
ASGI config for Facebook Clone project.
Routes HTTP requests to Django's WSGI handler and WebSocket connections to Channels.
"""
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# Import app routings after get_asgi_application() so the app registry is ready
import notifications.routing  # noqa: E402
import messaging.routing  # noqa: E402

# Combine all WebSocket URL patterns into one router
websocket_patterns = (
    notifications.routing.websocket_urlpatterns
    + messaging.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_patterns),
    ),
})
