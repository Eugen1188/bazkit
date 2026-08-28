from decimal import Decimal

from django.db import migrations


NUTRIENT_FIELDS = (
    "calories_per_100g",
    "protein_per_100g",
    "carbohydrates_per_100g",
    "fat_per_100g",
    "fiber_per_100g",
)


def rebuild_catalog(apps, schema_editor):
    from products.catalog import canonical_recipe_name, recipe_ingredient_status
    from products.ingredient_catalog import aliases_for_product
    from products.nutrition_quality import apply_safe_zero_defaults

    Product = apps.get_model("products", "Product")
    ProductAlias = apps.get_model("products", "ProductAlias")
    Product.objects.update_or_create(
        source="usda",
        external_id="171328",
        defaults={
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
                    "canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason",
                    *NUTRIENT_FIELDS,
                ],
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
                "canonical_name", "is_recipe_ingredient", "recipe_exclusion_reason",
                *NUTRIENT_FIELDS,
            ],
        )
    if pending_aliases:
        ProductAlias.objects.bulk_create(
            pending_aliases,
            ignore_conflicts=True,
            batch_size=1000,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0007_product_aliases"),
    ]

    operations = [
        migrations.RunPython(rebuild_catalog, migrations.RunPython.noop),
    ]
