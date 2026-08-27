from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipes", "0006_ingredients_price_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="is_community_snapshot",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
