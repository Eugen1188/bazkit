from django.db import migrations


COOKING_WINE_CODES = (
    "P2A3000",
    "P210000",
    "P461000",
    "P431000",
)


def repair_cooking_wines(apps, schema_editor):
    from products.catalog import canonical_recipe_name, recipe_ingredient_status
    from products.ingredient_catalog import aliases_for_product
    from products.nutrition_quality import NUTRIENT_FIELDS, apply_safe_zero_defaults
    from products.shopping_taxonomy import infer_product_taxonomy

    Product = apps.get_model("products", "Product")
    ProductAlias = apps.get_model("products", "ProductAlias")
    pending = []

    for product in Product.objects.filter(source="bls").iterator(chunk_size=500):
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
        shopping_category, is_common_pantry = infer_product_taxonomy(
            product.name,
            canonical_name,
            product.category,
            product.source,
            product.external_id,
        )
        nutrients = apply_safe_zero_defaults(
            product.name,
            product.source,
            product.external_id,
            {
                field: getattr(product, field)
                for field in NUTRIENT_FIELDS
            },
        )

        product.canonical_name = canonical_name
        product.is_recipe_ingredient = is_ingredient
        product.recipe_exclusion_reason = reason
        product.shopping_category = shopping_category
        product.is_common_pantry = is_common_pantry
        if shopping_category == "drinks":
            product.default_unit = "ml"
        for field, value in nutrients.items():
            setattr(product, field, value)
        pending.append(product)

        if len(pending) >= 500:
            Product.objects.bulk_update(
                pending,
                [
                    "canonical_name",
                    "is_recipe_ingredient",
                    "recipe_exclusion_reason",
                    "shopping_category",
                    "is_common_pantry",
                    "default_unit",
                    *NUTRIENT_FIELDS,
                ],
                batch_size=500,
            )
            pending.clear()

    if pending:
        Product.objects.bulk_update(
            pending,
            [
                "canonical_name",
                "is_recipe_ingredient",
                "recipe_exclusion_reason",
                "shopping_category",
                "is_common_pantry",
                "default_unit",
                *NUTRIENT_FIELDS,
            ],
            batch_size=500,
        )

    wines = list(Product.objects.filter(
        source="bls",
        external_id__in=COOKING_WINE_CODES,
    ))
    ProductAlias.objects.filter(product_id__in=[wine.id for wine in wines]).delete()
    aliases = []
    for wine in wines:
        for alias, normalized, source in aliases_for_product(
            wine.name,
            wine.canonical_name,
            wine.source,
            wine.external_id,
        ):
            aliases.append(ProductAlias(
                product_id=wine.id,
                alias=alias,
                normalized_alias=normalized,
                source=source,
            ))
    ProductAlias.objects.bulk_create(aliases, ignore_conflicts=True, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0010_product_shopping_taxonomy"),
    ]

    operations = [
        migrations.RunPython(
            repair_cooking_wines,
            migrations.RunPython.noop,
        ),
    ]
