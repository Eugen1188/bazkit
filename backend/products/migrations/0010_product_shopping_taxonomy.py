from django.db import migrations, models


def populate_shopping_taxonomy(apps, schema_editor):
    from products.ingredient_catalog import aliases_for_product
    from products.shopping_taxonomy import infer_product_taxonomy

    Product = apps.get_model("products", "Product")
    ProductAlias = apps.get_model("products", "ProductAlias")
    pending_products = []

    for product in Product.objects.all().iterator(chunk_size=500):
        shopping_category, is_common_pantry = infer_product_taxonomy(
            product.name,
            product.canonical_name,
            product.category,
            product.source,
            product.external_id,
        )
        product.shopping_category = shopping_category
        product.is_common_pantry = is_common_pantry
        pending_products.append(product)
        if len(pending_products) >= 500:
            Product.objects.bulk_update(
                pending_products,
                ["shopping_category", "is_common_pantry"],
                batch_size=500,
            )
            pending_products.clear()

    if pending_products:
        Product.objects.bulk_update(
            pending_products,
            ["shopping_category", "is_common_pantry"],
            batch_size=500,
        )

    # Die Migration baut auch die redaktionellen Synonyme neu auf. Dadurch ist
    # z. B. "Gemüsezwiebel" sofort mit dem BLS-Datensatz der Speisezwiebel
    # verknüpft, ohne einen erneuten BLS-Import zu verlangen.
    ProductAlias.objects.all().delete()
    pending_aliases = []
    for product in Product.objects.all().iterator(chunk_size=500):
        for alias, normalized, source in aliases_for_product(
            product.name,
            product.canonical_name,
            product.source,
            product.external_id,
        ):
            pending_aliases.append(ProductAlias(
                product_id=product.id,
                alias=alias,
                normalized_alias=normalized,
                source=source,
            ))
        if len(pending_aliases) >= 2000:
            ProductAlias.objects.bulk_create(
                pending_aliases,
                ignore_conflicts=True,
                batch_size=1000,
            )
            pending_aliases.clear()

    if pending_aliases:
        ProductAlias.objects.bulk_create(
            pending_aliases,
            ignore_conflicts=True,
            batch_size=1000,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0009_expand_world_ingredient_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="shopping_category",
            field=models.CharField(
                choices=[
                    ("produce", "Obst & Gemüse"),
                    ("bakery", "Brot & Backwaren"),
                    ("meat_fish", "Fleisch & Fisch"),
                    ("dairy_eggs", "Milchprodukte & Eier"),
                    ("frozen", "Tiefkühl"),
                    ("pantry", "Vorrat & Gewürze"),
                    ("drinks", "Getränke"),
                    ("household", "Haushalt & Drogerie"),
                    ("other", "Sonstiges"),
                ],
                db_index=True,
                default="other",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_common_pantry",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.RunPython(
            populate_shopping_taxonomy,
            migrations.RunPython.noop,
        ),
    ]
