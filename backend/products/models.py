from django.db import models


class Product(models.Model):

    SOURCE_CHOICES = [
        (
            "bls",
            "Bundeslebensmittelschlüssel"
        ),
        (
            "open_food_facts",
            "Open Food Facts"
        ),
    ]

    name = models.CharField(
        max_length=150
    )

    category = models.CharField(
        max_length=150,
        blank=True
    )

    brand = models.CharField(
        max_length=150,
        blank=True
    )

    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        null=True,
        blank=True
    )

    external_id = models.CharField(
        max_length=100,
        null=True,
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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source",
                    "external_id"
                ],
                name="unique_external_product"
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "name"
                ]
            ),
            models.Index(
                fields=[
                    "source",
                    "external_id"
                ]
            ),
        ]

    def __str__(self):
        return self.name