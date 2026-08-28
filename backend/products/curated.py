from decimal import Decimal

from .curated_ingredient_data import CURATED_USDA_PRODUCTS
from .models import Product


def ensure_curated_ingredients():
    """Create vetted cooking ingredients that are missing from BLS."""
    ingredients = (
        ("170497", {
            "name": "Chilischote",
            "canonical_name": "Chilischote",
            "category": "Gewürzgemüse · USDA FoodData Central 170497",
            "brand": "USDA FoodData Central",
            "default_unit": "Stück",
            "is_recipe_ingredient": True,
            "recipe_exclusion_reason": "",
            "calories_per_100g": Decimal("40.00"),
            "protein_per_100g": Decimal("2.00"),
            "carbohydrates_per_100g": Decimal("9.46"),
            "fat_per_100g": Decimal("0.20"),
            "fiber_per_100g": Decimal("1.50"),
        }),
        ("171328", {
            "name": "Oregano",
            "canonical_name": "Oregano",
            "category": "Gewürz · USDA FoodData Central 171328",
            "brand": "USDA FoodData Central",
            "default_unit": "g",
            "is_recipe_ingredient": True,
            "recipe_exclusion_reason": "",
            "calories_per_100g": Decimal("265.00"),
            "protein_per_100g": Decimal("9.00"),
            "carbohydrates_per_100g": Decimal("68.90"),
            "fat_per_100g": Decimal("4.28"),
            "fiber_per_100g": Decimal("42.50"),
        }),
    )
    for external_id, defaults in ingredients:
        Product.objects.update_or_create(
            source="usda",
            external_id=external_id,
            defaults=defaults,
        )

    for item in CURATED_USDA_PRODUCTS:
        external_id = item["external_id"]
        name = item["name"]
        Product.objects.update_or_create(
            source="usda",
            external_id=external_id,
            defaults={
                "name": name,
                "canonical_name": name,
                "category": (
                    f'{item["category"]} · USDA FoodData Central {external_id}'
                ),
                "brand": "USDA FoodData Central",
                "default_unit": item["default_unit"],
                "is_recipe_ingredient": True,
                "recipe_exclusion_reason": "",
                "calories_per_100g": Decimal(item["calories_per_100g"]),
                "protein_per_100g": Decimal(item["protein_per_100g"]),
                "carbohydrates_per_100g": Decimal(
                    item["carbohydrates_per_100g"]
                ),
                "fat_per_100g": Decimal(item["fat_per_100g"]),
                "fiber_per_100g": Decimal(item["fiber_per_100g"]),
            },
        )
