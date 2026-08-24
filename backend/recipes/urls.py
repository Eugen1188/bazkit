from django.urls import path

from .views import (
    RecipeListCreateAPIView,
    RecipeDetailAPIView,
    GenerateRecipeAPIView
)


urlpatterns = [

    path(
        "",
        RecipeListCreateAPIView.as_view(),
        name="recipe-list-create"
    ),

    path(
        "generate/",
        GenerateRecipeAPIView.as_view(),
        name="recipe-generate"
    ),

    path(
        "<int:pk>/",
        RecipeDetailAPIView.as_view(),
        name="recipe-detail"
    )

]