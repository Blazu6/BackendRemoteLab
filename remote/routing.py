from django.urls import path
from .consumers import GuacamoleConsumer

websocket_urlpatterns = [
    path("ws/guacamole/", GuacamoleConsumer.as_asgi()),
]
