from decimal import Decimal

from django.db import migrations


CHOCOLATES = (
    ("167587", "Vollmilchschokolade", "535", "7.65", "59.4", "29.66", "3.4"),
    ("167571", "Weiße Schokolade", "539", "5.87", "59.24", "32.09", "0.2"),
    ("170271", "Zartbitterschokolade 45–59 %", "546", "4.88", "61.17", "31.28", "7"),
    ("170272", "Zartbitterschokolade 60–69 %", "579", "6.12", "52.42", "38.31", "8"),
    ("170273", "Zartbitterschokolade 70–85 %", "598", "7.79", "45.9", "42.63", "10.9"),
)


def add_verified_chocolates(apps, schema_editor):
    from products.ingredient_catalog import aliases_for_product
    from products.shopping_taxonomy import infer_product_taxonomy

    Product = apps.get_model("products", "Product")
    ProductAlias = apps.get_model("products", "ProductAlias")
    products = []

    for external_id, name, calories, protein, carbs, fat, fiber in CHOCOLATES:
        category = f"Schokolade · USDA FoodData Central {external_id}"
        shopping_category, is_common_pantry = infer_product_taxonomy(
            name,
            name,
            category,
            "usda",
            external_id,
        )
        product, _created = Product.objects.update_or_create(
            source="usda",
            external_id=external_id,
            defaults={
                "name": name,
                "canonical_name": name,
                "category": category,
                "shopping_category": shopping_category,
                "is_common_pantry": is_common_pantry,
                "brand": "USDA FoodData Central",
                "default_unit": "g",
                "is_recipe_ingredient": True,
                "recipe_exclusion_reason": "",
                "calories_per_100g": Decimal(calories),
                "protein_per_100g": Decimal(protein),
                "carbohydrates_per_100g": Decimal(carbs),
                "fat_per_100g": Decimal(fat),
                "fiber_per_100g": Decimal(fiber),
            },
        )
        products.append(product)

    ProductAlias.objects.filter(product_id__in=[product.id for product in products]).delete()
    aliases = []
    for product in products:
        for alias, normalized, source in aliases_for_product(
            product.name,
            product.canonical_name,
            product.source,
            product.external_id,
        ):
            aliases.append(ProductAlias(
                product_id=product.id,
                alias=alias,
                normalized_alias=normalized,
                source=source,
            ))
    ProductAlias.objects.bulk_create(aliases, ignore_conflicts=True, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0013_product_package_quantity_product_package_unit_and_more"),
    ]

    operations = [
        migrations.RunPython(
            add_verified_chocolates,
            migrations.RunPython.noop,
        ),
    ]
