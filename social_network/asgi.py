"""
ASGI config for social_network project.

Exposes both the WSGI and ASGI applications.
Uses Django Channels for WebSocket support.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_network.settings")

django_asgi_app = get_asgi_application()

# Import here to ensure Django is fully initialized
from notifications import routing as notification_routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(notification_routing.websocket_urlpatterns)
        ),
    }
)
