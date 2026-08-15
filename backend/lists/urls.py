from django.urls import path

from .views import (
    SavedListListCreateAPIView,
    SavedListDetailAPIView,
    SavedListItemDetailAPIView,
)

urlpatterns = [
    path(
        "saved-lists/",
        SavedListListCreateAPIView.as_view(),
        name="saved-list-list-create",
    ),

    path(
        "saved-lists/<int:pk>/",
        SavedListDetailAPIView.as_view(),
        name="saved-list-detail",
    ),

    path(
        "saved-lists/<int:list_id>/items/<int:item_id>/",
        SavedListItemDetailAPIView.as_view(),
        name="saved-list-item-detail",
    ),
]