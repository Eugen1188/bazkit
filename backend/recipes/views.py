from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticated
)

from .models import Recipe

from .serializers import (
    RecipeSerializer
)


class RecipeListCreateAPIView(
    generics.ListCreateAPIView
):
    serializer_class = RecipeSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            Recipe.objects
            .filter(
                user=self.request.user
            )
            .prefetch_related(
                "ingredients"
            )
            .order_by(
                "-created_at"
            )
        )


class RecipeDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = RecipeSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            Recipe.objects
            .filter(
                user=self.request.user
            )
            .prefetch_related(
                "ingredients"
            )
        )