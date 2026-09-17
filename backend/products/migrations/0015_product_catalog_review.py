from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0014_add_verified_chocolate_ingredients"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="catalog_status",
            field=models.CharField(
                choices=[
                    ("pending", "Prüfung ausstehend"),
                    ("approved", "Freigegeben"),
                    ("rejected", "Abgelehnt"),
                ],
                db_index=True,
                default="approved",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="catalog_review_note",
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
