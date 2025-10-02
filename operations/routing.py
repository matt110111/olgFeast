from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/kitchen/(?P<station>\w+)/$', consumers.KitchenDisplayConsumer.as_asgi()),
]
