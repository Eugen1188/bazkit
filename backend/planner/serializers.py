from rest_framework import serializers

from recipes.models import Recipe
from recipes.storage import get_recipe_image_url

from .models import WeeklyPlanEntry


PLANNER_MEAL_TYPES = ("breakfast", "lunch", "dinner")


class WeeklyPlanGenerateSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    meal_types = serializers.ListField(
        child=serializers.ChoiceField(choices=PLANNER_MEAL_TYPES),
        allow_empty=False,
        default=list(PLANNER_MEAL_TYPES),
    )
    daily_calorie_target = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=500,
        max_value=6000,
    )
    daily_protein_target = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=10,
        max_value=400,
    )
    max_recipe_repeats = serializers.IntegerField(
        min_value=1,
        max_value=7,
        default=2,
    )
    servings = serializers.IntegerField(
        min_value=1,
        max_value=30,
        default=2,
    )
    overwrite = serializers.BooleanField(default=False)

    def validate_meal_types(self, value):
        # Keep the order stable while avoiding duplicate slots.
        return list(dict.fromkeys(value))


class PlannerRecipeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    ingredient_count = serializers.IntegerField(
        source="ingredients.count",
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "image_url",
            "image_position_x",
            "image_position_y",
            "image_zoom",
            "category",
            "servings",
            "calories",
            "protein",
            "carbohydrates",
            "fat",
            "fiber",
            "estimated_price",
            "ingredient_count",
        ]

    def get_image_url(self, obj):
        return get_recipe_image_url(obj.image_key)


class WeeklyPlanEntrySerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    recipe_detail = PlannerRecipeSerializer(source="recipe", read_only=True)
    servings = serializers.IntegerField(min_value=1, max_value=30, required=False)

    class Meta:
        model = WeeklyPlanEntry
        fields = [
            "id",
            "date",
            "meal_type",
            "servings",
            "recipe",
            "recipe_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "recipe_detail", "created_at", "updated_at"]

    def validate_recipe(self, recipe):
        request = self.context.get("request")
        if request is None or recipe.user_id != request.user.id:
            raise serializers.ValidationError(
                "Du kannst nur eigene Rezepte in deinen Wochenplan aufnehmen."
            )
        return recipe
