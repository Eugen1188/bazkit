from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    origin = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "canonical_name", "is_recipe_ingredient",
            "category", "brand", "source", "external_id",
            "default_unit", "calories_per_100g", "protein_per_100g",
            "carbohydrates_per_100g", "fat_per_100g", "fiber_per_100g",
            "origin",
        ]
        read_only_fields = fields

    def get_origin(self, obj):
        if obj.source in {"bls", "open_food_facts", "usda"}:
            return obj.source
        return "local"
