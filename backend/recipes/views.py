from rest_framework import generics
from rest_framework import status

from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser


from .models import Recipe

from .serializers import (
    RecipeSerializer,
    GenerateRecipeSerializer
)

from .ai_service import (
    generate_recipe_with_ai,
    RecipeGenerationError
)
from .storage import (
    RecipeImageError,
    delete_recipe_image_if_unused,
    upload_recipe_image,
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
                user=self.request.user,
                is_community_snapshot=False,
            )
            .prefetch_related(
                "ingredients__product"
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
                "ingredients__product"
            )
        )


    def perform_destroy(self, instance):

        image_key = instance.image_key
        super().perform_destroy(instance)
        delete_recipe_image_if_unused(image_key)


class RecipeImageAPIView(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_recipe(self, request, pk):
        return Recipe.objects.filter(user=request.user, pk=pk).first()

    def post(self, request, pk):
        recipe = self.get_recipe(request, pk)
        if recipe is None:
            return Response({"detail": "Rezept nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        uploaded_file = request.FILES.get("image")
        if uploaded_file is None:
            return Response({"image": "Bitte wähle ein Bild aus."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_key = upload_recipe_image(uploaded_file, request.user.id)
        except RecipeImageError as error:
            return Response({"image": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        old_key = recipe.image_key
        recipe.image_key = new_key
        recipe.save(update_fields=["image_key", "updated_at"])
        if old_key and old_key != new_key:
            delete_recipe_image_if_unused(old_key)

        return Response(RecipeSerializer(recipe, context={"request": request}).data)

    def delete(self, request, pk):
        recipe = self.get_recipe(request, pk)
        if recipe is None:
            return Response({"detail": "Rezept nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        old_key = recipe.image_key
        if old_key:
            recipe.image_key = ""
            recipe.save(update_fields=["image_key", "updated_at"])
            delete_recipe_image_if_unused(old_key)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateRecipeAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]


    def post(
        self,
        request
    ):

        serializer = GenerateRecipeSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )


        try:

            recipe = generate_recipe_with_ai(
                serializer.validated_data
            )

            return Response(
                recipe,
                status=status.HTTP_200_OK
            )


        except RecipeGenerationError as error:

            return Response(
                {
                    "detail": str(error),
                    "code": "recipe_generation_failed",
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
