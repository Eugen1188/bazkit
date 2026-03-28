from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import Recipe, Ingredients

class RecipeView(generics.ListCreateAPIView):
    serializer_class = Recipe
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user).prefetch_related('ingredients')

    def perform_create(self, serializer):
        serializer.save()


class RecipeDetailView(generics.RetrieveAPIView):
    serializer_class = Recipe
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user).prefetch_related('ingredients')
