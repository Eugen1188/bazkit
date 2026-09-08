from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0010_recipe_image_zoom"),
    ]

    operations = [
        migrations.AddField(
            model_name="ingredients",
            name="note",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
    ]
