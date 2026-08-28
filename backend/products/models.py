from django.db import models

from .shopping_taxonomy import SHOPPING_CATEGORY_CHOICES


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
        (
            "usda",
            "USDA FoodData Central"
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

    shopping_category = models.CharField(
        max_length=30,
        choices=SHOPPING_CATEGORY_CHOICES,
        default="other",
        db_index=True,
    )

    is_common_pantry = models.BooleanField(
        default=False,
        db_index=True,
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

    @property
    def has_complete_nutrition(self):
        return all(
            getattr(self, field) is not None
            for field in (
                "calories_per_100g",
                "protein_per_100g",
                "carbohydrates_per_100g",
                "fat_per_100g",
                "fiber_per_100g",
            )
        )


class ProductAlias(models.Model):
    SOURCE_CHOICES = [
        ("derived", "Automatisch abgeleitet"),
        ("curated", "Redaktionell gepflegt"),
        ("imported", "Importiert"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    alias = models.CharField(max_length=150)
    normalized_alias = models.CharField(max_length=150, db_index=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="derived")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "normalized_alias"],
                name="unique_product_normalized_alias",
            )
        ]
        indexes = [
            models.Index(fields=["normalized_alias", "product"], name="prod_alias_lookup_idx"),
        ]
        ordering = ["alias"]

    def __str__(self):
        return f"{self.alias} → {self.product}"

    def save(self, *args, **kwargs):
        from .ingredient_catalog import normalize_alias

        self.normalized_alias = normalize_alias(self.alias)
        super().save(*args, **kwargs)


class IngredientSearchMetric(models.Model):
    CONTEXT_CHOICES = [
        ("recipe_create", "Rezept erstellen"),
        ("recipe_edit", "Rezept bearbeiten"),
        ("shopping_list", "Einkaufsliste"),
        ("saved_list", "Gespeicherte Liste"),
    ]
    REVIEW_STATUS_CHOICES = [
        ("open", "Offen"),
        ("resolved", "Gelöst"),
        ("ignored", "Ignoriert"),
    ]

    normalized_query = models.CharField(max_length=100)
    display_query = models.CharField(max_length=100)
    context = models.CharField(max_length=30, choices=CONTEXT_CHOICES)
    search_count = models.PositiveIntegerField(default=0)
    zero_result_count = models.PositiveIntegerField(default=0)
    selection_count = models.PositiveIntegerField(default=0)
    last_result_count = models.PositiveSmallIntegerField(default=0)
    last_selected_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    last_selected_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ingredient_search_metrics",
    )
    selection_counts = models.JSONField(default=dict, blank=True)
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default="open",
        db_index=True,
    )
    review_note = models.CharField(max_length=250, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["normalized_query", "context"],
                name="unique_ingredient_search_metric",
            )
        ]
        indexes = [
            models.Index(
                fields=["review_status", "-zero_result_count"],
                name="ingredient_search_gap_idx",
            ),
        ]
        ordering = ["-zero_result_count", "-search_count", "normalized_query"]

    def __str__(self):
        return f"{self.display_query} ({self.context})"


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
