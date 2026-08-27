from django.conf import settings
from django.db import models
from products.models import Product


class PriceSnapshotMixin(models.Model):
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

    class Meta:
        abstract = True


class SavedList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_lists"
    )

    title = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_community_snapshot = models.BooleanField(
        default=False,
        db_index=True,
    )

    def __str__(self):
        return self.title


class SavedListItem(PriceSnapshotMixin):
    saved_list = models.ForeignKey(
        SavedList,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=100,
        blank=True
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

    note = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        return self.name


class ShoppingList(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_list"
    )

    title = models.CharField(
        max_length=100,
        default="Meine Einkaufsliste"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title


class ShoppingListItem(PriceSnapshotMixin):
    shopping_list = models.ForeignKey(
        ShoppingList,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=100,
        blank=True
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

    note = models.CharField(
        max_length=255,
        blank=True
    )

    is_checked = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name
