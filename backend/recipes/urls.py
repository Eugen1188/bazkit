from django.urls import path

from .views import (
    RecipeListCreateAPIView,
    RecipeDetailAPIView
)


urlpatterns = [
    path(
        "",
        RecipeListCreateAPIView.as_view(),
        name="recipe-list-create"
    ),

    path(
        "<int:pk>/",
        RecipeDetailAPIView.as_view(),
        name="recipe-detail"
    ),
]