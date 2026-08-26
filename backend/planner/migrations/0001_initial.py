import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("recipes", "0006_ingredients_price_snapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyPlanEntry",
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
                ("date", models.DateField(db_index=True)),
                (
                    "meal_type",
                    models.CharField(
                        choices=[
                            ("breakfast", "Frühstück"),
                            ("lunch", "Mittagessen"),
                            ("dinner", "Abendessen"),
                        ],
                        max_length=20,
                    ),
                ),
                ("servings", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weekly_plan_entries",
                        to="recipes.recipe",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weekly_plan_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["date", "meal_type"],
                "indexes": [
                    models.Index(
                        fields=["user", "date"],
                        name="planner_user_date_idx",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "date", "meal_type"),
                        name="unique_weekly_plan_slot",
                    )
                ],
            },
        )
    ]

