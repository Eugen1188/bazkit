from rest_framework.response import Response
from rest_framework import generics, status
from .serializers import SavedListSerializer, ShoppingListSerializer, AddRecipeToShoppingListSerializer, AddSavedListToShoppingListSerializer
from rest_framework.permissions import IsAuthenticated
from .models import SavedList, ShoppingList, ShoppingListItem
from recipes.models import Recipe
from rest_framework.views import APIView

class SavedListListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedList.objects.filter(user=self.request.user).prefetch_related('items')

    def perform_create(self, serializer):
        serializer.save()

class SavedListDetailView(generics.RetrieveAPIView):
    serializer_class = SavedListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedList.objects.filter(user=self.request.user).prefetch_related('items')
    
class ShoppingListListCreateView(generics.ListCreateAPIView):
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShoppingList.objects.filter(
            user=self.request.user
        ).prefetch_related('items')

    def perform_create(self, serializer):
        serializer.save()


class ShoppingListDetailView(generics.RetrieveAPIView):
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShoppingList.objects.filter(
            user=self.request.user
        ).prefetch_related('items')
    
class AddSavedListToShoppingListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, shopping_list_id):
        serializer = AddSavedListToShoppingListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        saved_list_id = serializer.validated_data['saved_list_id']

        shopping_list = ShoppingList.objects.get(
            id=shopping_list_id,
            user=request.user
        )

        saved_list = SavedList.objects.get(
            id=saved_list_id,
            user=request.user
        )

        for item in saved_list.items.all():
            ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                product=item.product,
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
            )

        return Response(
            {"detail": "Saved list wurde zur Shopping List hinzugefügt."},
            status=status.HTTP_201_CREATED
        )

class AddRecipeToShoppingListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, shopping_list_id):
        serializer = AddRecipeToShoppingListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe_id = serializer.validated_data['recipe_id']

        shopping_list = ShoppingList.objects.get(
            id=shopping_list_id,
            user=request.user
        )

        recipe = Recipe.objects.get(
            id=recipe_id,
            user=request.user
        )

        for ingredient in recipe.ingredients.all():
            ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                name=ingredient.name,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
                is_checked=False,
            )

        return Response(
            {"detail": "Rezept-Zutaten wurden zur Shopping List hinzugefügt."},
            status=status.HTTP_201_CREATED
        )