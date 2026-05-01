"""
ASGI config for control_asistencia project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application

import asistencia.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control_asistencia.settings')

django_asgi_app = get_asgi_application()
django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            asistencia.routing.websocket_urlpatterns
        )
    ),
})
