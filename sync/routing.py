from django.urls import re_path
from sync import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_code>[A-Z0-9]+)/$', consumers.CerebroConsumer.as_asgi()),
]