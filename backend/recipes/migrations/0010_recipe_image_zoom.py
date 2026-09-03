from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0009_recipe_image_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="image_zoom",
            field=models.PositiveSmallIntegerField(
                default=100,
                help_text="Zoom des Bildausschnitts in Prozent",
                validators=[MinValueValidator(100), MaxValueValidator(200)],
            ),
        ),
    ]
