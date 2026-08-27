from django.conf import settings
from django.db import models

from recipes.models import Recipe


class WeeklyPlanEntry(models.Model):
    MEAL_TYPE_CHOICES = [
        ("breakfast", "Frühstück"),
        ("lunch", "Mittagessen"),
        ("dinner", "Abendessen"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weekly_plan_entries",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="weekly_plan_entries",
    )
    date = models.DateField(db_index=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    servings = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "meal_type", "created_at", "id"]
        indexes = [
            models.Index(
                fields=["user", "date"],
                name="planner_user_date_idx",
            )
        ]

    def __str__(self):
        return f"{self.date} · {self.get_meal_type_display()} · {self.recipe.name}"
