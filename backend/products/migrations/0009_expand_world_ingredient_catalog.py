from decimal import Decimal

from django.db import migrations


NUTRIENT_FIELDS = (
    "calories_per_100g",
    "protein_per_100g",
    "carbohydrates_per_100g",
    "fat_per_100g",
    "fiber_per_100g",
)


def expand_ingredient_catalog(apps, schema_editor):
    from products.catalog import canonical_recipe_name, recipe_ingredient_status
    from products.curated_ingredient_data import CURATED_USDA_PRODUCTS
    from products.ingredient_catalog import aliases_for_product
    from products.nutrition_quality import apply_safe_zero_defaults

    Product = apps.get_model("products", "Product")
    ProductAlias = apps.get_model("products", "ProductAlias")

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

    ProductAlias.objects.all().delete()
    pending_products = []
    pending_aliases = []

    for product in Product.objects.all().iterator(chunk_size=500):
        canonical_name = canonical_recipe_name(
            product.name,
            product.source,
            product.external_id,
        )
        is_ingredient, reason = recipe_ingredient_status(
            product.name,
            product.category,
            product.source,
            product.external_id,
        )
        nutrients = apply_safe_zero_defaults(
            product.name,
            product.source,
            product.external_id,
            {field: getattr(product, field) for field in NUTRIENT_FIELDS},
        )
        product.canonical_name = canonical_name
        product.is_recipe_ingredient = is_ingredient
        product.recipe_exclusion_reason = reason
        for field in NUTRIENT_FIELDS:
            setattr(product, field, nutrients[field])
        pending_products.append(product)

        for alias, normalized, source in aliases_for_product(
            product.name,
            canonical_name,
            product.source,
            product.external_id,
        ):
            pending_aliases.append(ProductAlias(
                product_id=product.id,
                alias=alias,
                normalized_alias=normalized,
                source=source,
            ))

        if len(pending_products) >= 500:
            Product.objects.bulk_update(
                pending_products,
                [
                    "canonical_name",
                    "is_recipe_ingredient",
                    "recipe_exclusion_reason",
                    *NUTRIENT_FIELDS,
                ],
                batch_size=500,
            )
            pending_products.clear()
        if len(pending_aliases) >= 2000:
            ProductAlias.objects.bulk_create(
                pending_aliases,
                ignore_conflicts=True,
                batch_size=1000,
            )
            pending_aliases.clear()

    if pending_products:
        Product.objects.bulk_update(
            pending_products,
            [
                "canonical_name",
                "is_recipe_ingredient",
                "recipe_exclusion_reason",
                *NUTRIENT_FIELDS,
            ],
            batch_size=500,
        )
    if pending_aliases:
        ProductAlias.objects.bulk_create(
            pending_aliases,
            ignore_conflicts=True,
            batch_size=1000,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0008_rebuild_curated_ingredient_quality"),
    ]

    operations = [
        migrations.RunPython(expand_ingredient_catalog, migrations.RunPython.noop),
    ]
