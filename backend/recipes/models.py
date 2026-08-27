from django.conf import settings
from django.db import models

from products.models import Product

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

    # ==========================================
    # NÄHRWERTE PRO PORTION
    # ==========================================

    calories = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Kilokalorien pro Portion"
    )

    protein = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Protein in Gramm pro Portion"
    )

    carbohydrates = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Kohlenhydrate in Gramm pro Portion"
    )

    fat = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fett in Gramm pro Portion"
    )

    fiber = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Ballaststoffe in Gramm pro Portion"
    )

    # ==========================================
    # PREIS
    # ==========================================

    estimated_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Geschätzter Gesamtpreis des Rezepts"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_community_snapshot = models.BooleanField(
        default=False,
        db_index=True,
    )

    def __str__(self):
        return self.name


class Ingredients(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
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

    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_source = models.CharField(max_length=30, blank=True)
    price_currency = models.CharField(max_length=3, default="EUR")
    price_date = models.DateField(null=True, blank=True)
    price_store = models.CharField(max_length=150, blank=True)
    price_sample_count = models.PositiveSmallIntegerField(default=0)
    price_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_unit = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name
