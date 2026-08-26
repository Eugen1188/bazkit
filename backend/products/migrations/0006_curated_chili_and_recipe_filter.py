from decimal import Decimal

from django.db import migrations, models
from django.db.models import Q


def add_curated_chili_and_reclassify(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.update_or_create(
        source="usda",
        external_id="170497",
        defaults={
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
        },
    )
    Product.objects.filter(source="bls").filter(
        Q(external_id__istartswith="X") | Q(external_id__istartswith="Y")
    ).update(
        is_recipe_ingredient=False,
        recipe_exclusion_reason="BLS-Rezeptur oder zusammengesetzte Speise",
    )


def remove_curated_chili(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(
        source="usda",
        external_id="170497",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0005_recipe_catalog_and_price_references"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="source",
            field=models.CharField(
                blank=True,
                choices=[
                    ("bls", "Bundeslebensmittelschlüssel"),
                    ("open_food_facts", "Open Food Facts"),
                    ("usda", "USDA FoodData Central"),
                ],
                max_length=30,
                null=True,
            ),
        ),
        migrations.RunPython(add_curated_chili_and_reclassify, remove_curated_chili),
    ]
