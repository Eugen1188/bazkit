from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0008_recipe_image_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="image_position_x",
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text="Horizontale Position des Bildausschnitts in Prozent",
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
        migrations.AddField(
            model_name="recipe",
            name="image_position_y",
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text="Vertikale Position des Bildausschnitts in Prozent",
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
    ]
