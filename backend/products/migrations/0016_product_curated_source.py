from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0015_product_catalog_review"),
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
                    ("curated", "Bazkit kuratierte Zutatenvariante"),
                ],
                max_length=30,
                null=True,
            ),
        ),
    ]
