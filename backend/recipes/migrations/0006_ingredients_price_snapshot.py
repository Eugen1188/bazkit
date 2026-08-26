from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("recipes", "0005_ingredients_product")]

    operations = [
        migrations.AddField(model_name="ingredients", name="estimated_price", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name="ingredients", name="price_source", field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name="ingredients", name="price_currency", field=models.CharField(default="EUR", max_length=3)),
        migrations.AddField(model_name="ingredients", name="price_date", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="ingredients", name="price_store", field=models.CharField(blank=True, max_length=150)),
        migrations.AddField(model_name="ingredients", name="price_sample_count", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name="ingredients", name="price_min", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name="ingredients", name="price_max", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name="ingredients", name="package_price", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name="ingredients", name="package_quantity", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name="ingredients", name="package_unit", field=models.CharField(blank=True, max_length=20)),
    ]
