from django.urls import re_path

from .consumers import AccesoConsumer

websocket_urlpatterns = [
    re_path(r'ws/accesos/$', AccesoConsumer.as_asgi()),
]
