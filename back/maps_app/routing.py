from django.urls import re_path
from . import consumers

websocket_urls = [
    re_path(r'ws/map/(?P<map_id>\d+)/$', consumers.MapConsumer.as_asgi()),
]
