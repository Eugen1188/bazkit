from django.urls import path

from .views import (
    RecipeListCreateAPIView,
    RecipeDetailAPIView,
    GenerateRecipeAPIView,
    AIRecipeUsageAPIView,
    RecipeImageAPIView,
)


urlpatterns = [

    path(
        "ai-usage/",
        AIRecipeUsageAPIView.as_view(),
        name="recipe-ai-usage",
    ),

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
    ),

    path(
        "<int:pk>/image/",
        RecipeImageAPIView.as_view(),
        name="recipe-image",
    ),

]
