from django.db import migrations, models


def price_fields():
    return [
        ("estimated_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        ("price_source", models.CharField(blank=True, max_length=30)),
        ("price_currency", models.CharField(default="EUR", max_length=3)),
        ("price_date", models.DateField(blank=True, null=True)),
        ("price_store", models.CharField(blank=True, max_length=150)),
        ("price_sample_count", models.PositiveSmallIntegerField(default=0)),
        ("price_min", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        ("price_max", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        ("package_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        ("package_quantity", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        ("package_unit", models.CharField(blank=True, max_length=20)),
    ]


class Migration(migrations.Migration):
    dependencies = [("lists", "0004_shoppinglist_shoppinglistitem")]

    operations = [
        migrations.AddField(model_name=model, name=name, field=field)
        for model in ("savedlistitem", "shoppinglistitem")
        for name, field in price_fields()
    ]
