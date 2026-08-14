from django.urls import path

from .views import (
    SavedListListCreateAPIView,
    SavedListDetailAPIView
)

urlpatterns = [
    path(
        "saved-lists/",
        SavedListListCreateAPIView.as_view(),
        name="saved-list-list-create"
    ),

    path(
        "saved-lists/<int:pk>/",
        SavedListDetailAPIView.as_view(),
        name="saved-list-detail"
    ),
]