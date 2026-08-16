from django.conf import settings
from django.db import models


class Recipe(models.Model):
    CATEGORY_CHOICES = [
        ("breakfast", "Frühstück"),
        ("lunch", "Mittagessen"),
        ("dinner", "Abendessen"),
        ("snack", "Snack"),
        ("dessert", "Dessert"),
        ("other", "Sonstiges"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes"
    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    servings = models.PositiveIntegerField(
        default=2
    )

    preparation_time = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    instructions = models.TextField()

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients"
    )

    name = models.CharField(
        max_length=100
    )

    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    unit = models.CharField(
        max_length=30,
        blank=True
    )

    def __str__(self):
        return self.name