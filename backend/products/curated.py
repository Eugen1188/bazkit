from decimal import Decimal

from .catalog import suggested_unit_for_product
from .curated_ingredient_data import CURATED_USDA_PRODUCTS
from .models import Product
from .shopping_taxonomy import infer_product_taxonomy


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
        defaults = defaults.copy()
        shopping_category, is_common_pantry = infer_product_taxonomy(
            defaults["name"],
            defaults["canonical_name"],
            defaults["category"],
            "usda",
            external_id,
        )
        defaults["shopping_category"] = shopping_category
        defaults["is_common_pantry"] = is_common_pantry
        defaults["default_unit"] = suggested_unit_for_product(
            defaults["name"],
            defaults["canonical_name"],
            shopping_category,
            defaults["default_unit"],
        )
        Product.objects.update_or_create(
            source="usda",
            external_id=external_id,
            defaults=defaults,
        )

    for item in CURATED_USDA_PRODUCTS:
        external_id = item["external_id"]
        name = item["name"]
        source_category = (
            f'{item["category"]} · USDA FoodData Central {external_id}'
        )
        shopping_category, is_common_pantry = infer_product_taxonomy(
            name,
            name,
            source_category,
            "usda",
            external_id,
        )
        Product.objects.update_or_create(
            source="usda",
            external_id=external_id,
            defaults={
                "name": name,
                "canonical_name": name,
                "category": source_category,
                "shopping_category": shopping_category,
                "is_common_pantry": is_common_pantry,
                "brand": "USDA FoodData Central",
                "default_unit": suggested_unit_for_product(
                    name,
                    name,
                    shopping_category,
                    item["default_unit"],
                ),
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

    # Eigenständige Kochbegriffe, für die die Referenzdatenbank nur einen
    # gemeinsamen Nährwertdatensatz führt. Sie bleiben als Zutaten getrennt,
    # damit z. B. helle und dunkle Sojasauce nicht wieder zu "Sojasauce"
    # zusammenfallen. Die Herkunft der Nährwertreferenz bleibt sichtbar.
    variants = (
        ("soy-sauce-light", "Helle Sojasauce", "bls", "R143000"),
        ("soy-sauce-dark", "Dunkle Sojasauce", "bls", "R143000"),
        ("paprika-sweet", "Paprikapulver edelsüß", "usda", "171329"),
        ("paprika-hot", "Paprikapulver rosenscharf", "usda", "171329"),
        ("sesame-oil-toasted", "Geröstetes Sesamöl", "usda", "171016"),
        ("white-wine-vinegar", "Weißweinessig", "bls", "R121000"),
        ("panko", "Panko", "bls", "B821000"),
        ("rice-basmati", "Basmatireis", "bls", "C352000"),
        ("rice-jasmine", "Jasminreis", "bls", "C352000"),
    )
    nutrient_fields = (
        "calories_per_100g",
        "protein_per_100g",
        "carbohydrates_per_100g",
        "fat_per_100g",
        "fiber_per_100g",
    )
    for external_id, name, reference_source, reference_external_id in variants:
        reference = Product.objects.filter(
            source=reference_source,
            external_id=reference_external_id,
        ).first()
        if reference is None or any(
            getattr(reference, field) is None for field in nutrient_fields
        ):
            continue
        source_label = "BLS" if reference_source == "bls" else "USDA FoodData Central"
        source_category = (
            f"Kuratierte Zutatenvariante · Nährwertreferenz {source_label} "
            f"{reference_external_id}"
        )
        shopping_category, is_common_pantry = infer_product_taxonomy(
            name,
            name,
            source_category,
            "curated",
            external_id,
        )
        defaults = {
            "name": name,
            "canonical_name": name,
            "category": source_category,
            "shopping_category": shopping_category,
            "is_common_pantry": is_common_pantry,
            "brand": f"Bazkit · {source_label}-Referenz",
            "default_unit": suggested_unit_for_product(
                name,
                name,
                shopping_category,
                reference.default_unit,
            ),
            "is_recipe_ingredient": True,
            "catalog_status": "approved",
            "catalog_review_note": (
                f"Eigenständige Kochzutat; Nährwerte basieren auf "
                f"{source_label} {reference_external_id}."
            ),
            "recipe_exclusion_reason": "",
        }
        defaults.update({
            field: getattr(reference, field)
            for field in nutrient_fields
        })
        Product.objects.update_or_create(
            source="curated",
            external_id=external_id,
            defaults=defaults,
        )
