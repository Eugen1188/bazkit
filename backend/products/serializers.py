from rest_framework import serializers

from .catalog import average_unit_weight_grams
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    origin = serializers.SerializerMethodField()
    nutrition_complete = serializers.BooleanField(source="has_complete_nutrition", read_only=True)
    grams_per_unit = serializers.SerializerMethodField()
    unit_conversions = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "canonical_name", "is_recipe_ingredient",
            "category", "shopping_category", "is_common_pantry",
            "brand", "source", "external_id",
            "default_unit", "package_quantity", "package_unit", "grams_per_unit",
            "unit_conversions", "calories_per_100g", "protein_per_100g",
            "carbohydrates_per_100g", "fat_per_100g", "fiber_per_100g",
            "nutrition_complete", "origin",
        ]
        read_only_fields = fields

    def get_origin(self, obj):
        if obj.source in {"bls", "open_food_facts", "usda"}:
            return obj.source
        return "local"

    def get_grams_per_unit(self, obj):
        conversion = obj.unit_conversions.filter(
            unit__iexact="Stück", is_active=True
        ).exclude(confidence="estimated").first()
        value = conversion.grams_per_unit if conversion else None
        return str(value) if value is not None else None

    def get_unit_conversions(self, obj):
        return [
            {
                "unit": conversion.unit,
                "grams_per_unit": str(conversion.grams_per_unit),
                "source": conversion.source,
                "confidence": conversion.confidence,
            }
            for conversion in obj.unit_conversions.filter(is_active=True).exclude(
                confidence="estimated"
            )
        ]
