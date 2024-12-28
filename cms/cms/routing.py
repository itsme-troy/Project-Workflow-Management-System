from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/project_ideas/', consumers.ProjectIdeasConsumer.as_asgi()),
]