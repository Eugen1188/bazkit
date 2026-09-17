from django.urls import path

from lists.consumers import SavedListConsumer


websocket_urlpatterns = [
    path("ws/saved-lists/<int:list_id>/", SavedListConsumer.as_asgi()),
]
