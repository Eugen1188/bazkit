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

    canonical_name = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
    )

    is_recipe_ingredient = models.BooleanField(
        default=True,
        db_index=True,
    )

    recipe_exclusion_reason = models.CharField(
        max_length=150,
        blank=True,
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


class IngredientPriceReference(models.Model):
    BASIS_CHOICES = [
        ("kg", "Kilogramm"),
        ("unit", "Stück"),
    ]
    CONFIDENCE_CHOICES = [
        ("low", "Niedrig"),
        ("medium", "Mittel"),
        ("high", "Hoch"),
    ]

    canonical_name = models.CharField(max_length=150, db_index=True)
    category_tag = models.CharField(max_length=150)
    basis = models.CharField(max_length=10, choices=BASIS_CHOICES)
    median_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="EUR")
    region = models.CharField(max_length=10, default="DE")
    observation_count = models.PositiveIntegerField(default=0)
    location_count = models.PositiveIntegerField(default=0)
    newest_price_date = models.DateField(null=True, blank=True)
    confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES, default="low")
    source = models.CharField(max_length=40, default="open_prices_category")
    is_active = models.BooleanField(default=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["canonical_name", "category_tag", "basis", "region"],
                name="unique_ingredient_price_reference",
            )
        ]
        indexes = [
            models.Index(fields=["canonical_name", "is_active"], name="prod_price_name_active_idx"),
        ]

    def __str__(self):
        return f"{self.canonical_name}: {self.median_price} {self.currency}/{self.basis}"
