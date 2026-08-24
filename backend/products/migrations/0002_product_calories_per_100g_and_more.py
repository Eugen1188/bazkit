from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "products",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="calories_per_100g",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name="product",
            name="carbohydrates_per_100g",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name="product",
            name="fat_per_100g",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name="product",
            name="fiber_per_100g",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name="product",
            name="protein_per_100g",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),
    ]