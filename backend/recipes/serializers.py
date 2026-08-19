from rest_framework import serializers

from .models import (
    Recipe,
    Ingredients,
)

from products.models import Product


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


    def sync_product(
        self,
        ingredient_data
    ):
        name = (
            ingredient_data
            .get(
                "name",
                ""
            )
            .strip()
        )

        unit = (
            ingredient_data
            .get(
                "unit",
                ""
            )
            .strip()
        )


        if not name:
            return


        product = (
            Product.objects
            .filter(
                name__iexact=name
            )
            .first()
        )


        if not product:
            Product.objects.create(
                name=name,
                default_unit=unit
            )

            return


        if (
            not product.default_unit
            and
            unit
        ):
            product.default_unit = unit

            product.save(
                update_fields=[
                    "default_unit"
                ]
            )


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

            self.sync_product(
                ingredient_data
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


        instance.name = (
            validated_data.get(
                "name",
                instance.name
            )
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

                self.sync_product(
                    ingredient_data
                )


        return instance


class GenerateRecipeSerializer(
    serializers.Serializer
):
    idea = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    available_ingredients = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            max_length=1000
        )
    )

    avoid_ingredients = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            max_length=500
        )
    )

    diet = serializers.ChoiceField(
        choices=[
            "none",
            "vegetarian",
            "vegan",
            "high_protein",
            "low_carb"
        ],
        default="none"
    )

    servings = serializers.IntegerField(
        min_value=1,
        max_value=20,
        default=2
    )

    max_time = serializers.IntegerField(
        min_value=5,
        max_value=240,
        default=30
    )

    category = serializers.ChoiceField(
        choices=[
            "breakfast",
            "lunch",
            "dinner",
            "snack",
            "dessert",
            "other"
        ],
        default="dinner"
    )

    def validate(
        self,
        attrs
    ):
        idea = attrs.get(
            "idea",
            ""
        ).strip()

        available_ingredients = attrs.get(
            "available_ingredients",
            ""
        ).strip()

        if (
            not idea
            and
            not available_ingredients
        ):
            raise serializers.ValidationError(
                {
                    "detail":
                        "Gib entweder eine Rezeptidee "
                        "oder vorhandene Zutaten an."
                }
            )

        return attrs