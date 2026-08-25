from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from products.models import Product
from .models import Ingredients, Recipe


class IngredientsSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), allow_null=False, required=True)

    class Meta:
        model = Ingredients
        fields = ["id", "product", "name", "quantity", "unit"]
        read_only_fields = ["id", "name"]

    def validate(self, attrs):
        product = attrs.get("product")
        if product is None:
            raise serializers.ValidationError({"product": "Bitte ein Produkt aus den Vorschlägen auswählen."})
        attrs["name"] = product.name
        return attrs


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsSerializer(many=True, required=True)
    estimated_price_per_serving = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "name", "description", "servings", "preparation_time", "category",
            "instructions", "notes", "calories", "protein", "carbohydrates", "fat", "fiber",
            "estimated_price", "estimated_price_per_serving", "created_at", "updated_at", "ingredients",
        ]
        read_only_fields = ["id", "estimated_price_per_serving", "created_at", "updated_at"]

    def get_estimated_price_per_serving(self, obj):
        if obj.estimated_price is None or not obj.servings:
            return None
        return round(obj.estimated_price / Decimal(obj.servings), 2)

    def validate(self, attrs):
        for field in ("calories", "protein", "carbohydrates", "fat", "fiber", "estimated_price"):
            value = attrs.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: "Der Wert darf nicht negativ sein."})
        ingredients = attrs.get("ingredients")
        if ingredients is not None and not ingredients:
            raise serializers.ValidationError({"ingredients": "Mindestens eine Zutat ist erforderlich."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(user=self.context["request"].user, **validated_data)
        Ingredients.objects.bulk_create([Ingredients(recipe=recipe, **item) for item in ingredients])
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if ingredients is not None:
            instance.ingredients.all().delete()
            Ingredients.objects.bulk_create([Ingredients(recipe=instance, **item) for item in ingredients])
        return instance
