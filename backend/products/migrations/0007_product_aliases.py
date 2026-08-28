from django.db import migrations, models
import django.db.models.deletion


def populate_aliases(apps, schema_editor):
    from products.catalog import canonical_recipe_name
    from products.ingredient_catalog import aliases_for_product

    Product = apps.get_model("products", "Product")
    ProductAlias = apps.get_model("products", "ProductAlias")
    pending_products = []
    pending_aliases = []

    for product in Product.objects.all().iterator(chunk_size=500):
        canonical_name = canonical_recipe_name(
            product.name,
            product.source,
            product.external_id,
        )
        if product.canonical_name != canonical_name:
            product.canonical_name = canonical_name
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
            Product.objects.bulk_update(pending_products, ["canonical_name"])
            pending_products.clear()
        if len(pending_aliases) >= 2000:
            ProductAlias.objects.bulk_create(
                pending_aliases,
                ignore_conflicts=True,
                batch_size=1000,
            )
            pending_aliases.clear()

    if pending_products:
        Product.objects.bulk_update(pending_products, ["canonical_name"])
    if pending_aliases:
        ProductAlias.objects.bulk_create(
            pending_aliases,
            ignore_conflicts=True,
            batch_size=1000,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0006_curated_chili_and_recipe_filter"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alias", models.CharField(max_length=150)),
                ("normalized_alias", models.CharField(db_index=True, max_length=150)),
                ("source", models.CharField(choices=[("derived", "Automatisch abgeleitet"), ("curated", "Redaktionell gepflegt"), ("imported", "Importiert")], default="derived", max_length=20)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="aliases", to="products.product")),
            ],
            options={
                "ordering": ["alias"],
                "indexes": [models.Index(fields=["normalized_alias", "product"], name="prod_alias_lookup_idx")],
                "constraints": [models.UniqueConstraint(fields=("product", "normalized_alias"), name="unique_product_normalized_alias")],
            },
        ),
        migrations.RunPython(populate_aliases, migrations.RunPython.noop),
    ]
