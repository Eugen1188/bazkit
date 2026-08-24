from django.db import models

class Product(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    category = models.CharField(
        max_length=100,
        blank=True
    )

    default_unit = models.CharField(
        max_length=30,
        blank=True
    )

    calories_per_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    protein_per_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    carbohydrates_per_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    fat_per_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    fiber_per_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name