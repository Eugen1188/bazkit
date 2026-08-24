from rest_framework import generics
from rest_framework import status

from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.response import Response

from rest_framework.views import APIView


from .models import Recipe

from .serializers import (
    RecipeSerializer,
    GenerateRecipeSerializer
)

from .ai_service import (
    generate_recipe_with_ai,
    RecipeGenerationError
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
                    "detail":
                        "Das Rezept konnte "
                        "nicht generiert werden.",

                    "error":
                        str(error)
                },
                status=status.HTTP_502_BAD_GATEWAY
            )