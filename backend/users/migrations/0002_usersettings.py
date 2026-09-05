from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "shopping_default_sorting",
                    models.CharField(
                        choices=[
                            ("category", "Nach Kategorie"),
                            ("alphabetical", "Alphabetisch"),
                            ("created", "Zuletzt hinzugefügt"),
                        ],
                        default="category",
                        max_length=20,
                    ),
                ),
                (
                    "shopping_default_unit",
                    models.CharField(
                        choices=[
                            ("Stück", "Stück"),
                            ("g", "Gramm"),
                            ("kg", "Kilogramm"),
                            ("ml", "Milliliter"),
                            ("Liter", "Liter"),
                            ("Packung", "Packung"),
                        ],
                        default="Stück",
                        max_length=20,
                    ),
                ),
                ("shopping_move_completed_to_bottom", models.BooleanField(default=True)),
                ("recipe_default_portions", models.PositiveSmallIntegerField(default=2)),
                ("dietary_preferences", models.JSONField(blank=True, default=list)),
                ("favorite_cuisines", models.JSONField(blank=True, default=list)),
                (
                    "appearance",
                    models.CharField(
                        choices=[
                            ("light", "Hell"),
                            ("dark", "Dunkel"),
                            ("system", "System"),
                        ],
                        default="system",
                        max_length=10,
                    ),
                ),
                (
                    "accent_color",
                    models.CharField(
                        choices=[
                            ("green", "Grün"),
                            ("blue", "Blau"),
                            ("orange", "Orange"),
                            ("red", "Rot"),
                        ],
                        default="green",
                        max_length=10,
                    ),
                ),
                ("notification_shopping_reminders", models.BooleanField(default=True)),
                ("notification_shared_lists", models.BooleanField(default=True)),
                ("notification_product_updates", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="settings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
