from rest_framework import serializers

from .catalog import (
    liquid_density_grams_per_ml,
    logical_available_units,
    product_unit_conversions,
    resolved_product_unit_name,
)
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    origin = serializers.SerializerMethodField()
    nutrition_complete = serializers.BooleanField(source="has_complete_nutrition", read_only=True)
    grams_per_unit = serializers.SerializerMethodField()
    grams_per_ml = serializers.SerializerMethodField()
    unit_conversions = serializers.SerializerMethodField()
    available_units = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "canonical_name", "is_recipe_ingredient",
            "category", "shopping_category", "is_common_pantry",
            "brand", "source", "external_id",
            "default_unit", "package_quantity", "package_unit", "grams_per_unit", "grams_per_ml",
            "unit_conversions", "available_units", "calories_per_100g", "protein_per_100g",
            "carbohydrates_per_100g", "fat_per_100g", "fiber_per_100g",
            "nutrition_complete", "origin",
        ]
        read_only_fields = fields

    def get_origin(self, obj):
        if obj.source in {"bls", "open_food_facts", "usda"}:
            return obj.source
        return "local"

    def get_grams_per_unit(self, obj):
        conversion = next(
            (
                item for item in self._logical_conversions(obj)
                if item["unit"].casefold() == "stück"
            ),
            None,
        )
        value = conversion["grams_per_unit"] if conversion else None
        return str(value) if value is not None else None

    def get_grams_per_ml(self, obj):
        value = liquid_density_grams_per_ml(self._unit_name(obj))
        return str(value) if value is not None else None

    def get_unit_conversions(self, obj):
        return [
            {
                **conversion,
                "grams_per_unit": str(conversion["grams_per_unit"]),
            }
            for conversion in self._logical_conversions(obj)
        ]

    def get_available_units(self, obj):
        conversions = self._logical_conversions(obj)
        return logical_available_units(
            obj.default_unit,
            obj.package_unit,
            obj.shopping_category,
            conversions,
            self._unit_name(obj),
        )

    @staticmethod
    def _logical_conversions(obj):
        return product_unit_conversions(
            obj.name,
            obj.canonical_name,
            obj.package_quantity,
            obj.package_unit,
            obj.source,
            obj.external_id,
        )

    @staticmethod
    def _unit_name(obj):
        return resolved_product_unit_name(
            obj.name,
            obj.canonical_name,
            obj.source,
            obj.external_id,
        )
