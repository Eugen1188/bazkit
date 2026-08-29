from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0007_recipe_is_community_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="image_key",
            field=models.CharField(
                blank=True,
                help_text="Objektschlüssel des optimierten Rezeptbildes in Cloudflare R2",
                max_length=500,
            ),
        ),
    ]
