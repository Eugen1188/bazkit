from rest_framework import serializers

from .models import (
    Recipe,
    Ingredients
)


class IngredientsSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Ingredients

        fields = [
            "id",
            "name",
            "quantity",
            "unit"
        ]

        read_only_fields = [
            "id"
        ]


class RecipeSerializer(
    serializers.ModelSerializer
):
    ingredients = IngredientsSerializer(
        many=True,
        required=False
    )

    class Meta:
        model = Recipe

        fields = [
            "id",
            "name",
            "description",
            "servings",
            "preparation_time",
            "category",
            "instructions",
            "notes",
            "created_at",
            "updated_at",
            "ingredients"
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at"
        ]

    def create(
        self,
        validated_data
    ):
        ingredients_data = (
            validated_data.pop(
                "ingredients",
                []
            )
        )

        request = self.context[
            "request"
        ]

        recipe = Recipe.objects.create(
            user=request.user,
            **validated_data
        )

        for ingredient_data in ingredients_data:
            Ingredients.objects.create(
                recipe=recipe,
                **ingredient_data
            )

        return recipe

    def update(
        self,
        instance,
        validated_data
    ):
        ingredients_data = (
            validated_data.pop(
                "ingredients",
                None
            )
        )

        instance.name = validated_data.get(
            "name",
            instance.name
        )

        instance.description = (
            validated_data.get(
                "description",
                instance.description
            )
        )

        instance.servings = (
            validated_data.get(
                "servings",
                instance.servings
            )
        )

        instance.preparation_time = (
            validated_data.get(
                "preparation_time",
                instance.preparation_time
            )
        )

        instance.category = (
            validated_data.get(
                "category",
                instance.category
            )
        )

        instance.instructions = (
            validated_data.get(
                "instructions",
                instance.instructions
            )
        )

        instance.notes = (
            validated_data.get(
                "notes",
                instance.notes
            )
        )

        instance.save()

        if ingredients_data is not None:
            instance.ingredients.all().delete()

            for ingredient_data in ingredients_data:
                Ingredients.objects.create(
                    recipe=instance,
                    **ingredient_data
                )

        return instance