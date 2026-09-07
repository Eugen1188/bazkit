from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone
from products.models import Product


def saved_list_invitation_expiry():
    return timezone.now() + timedelta(days=7)


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

    updated_at = models.DateTimeField(
        auto_now=True
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

    is_checked = models.BooleanField(
        default=False
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_saved_list_items",
    )

    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_saved_list_items",
    )

    checked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class SavedListMembership(models.Model):
    EDITOR = "editor"
    VIEWER = "viewer"
    ROLE_CHOICES = [
        (EDITOR, "Kann bearbeiten"),
        (VIEWER, "Kann ansehen"),
    ]

    saved_list = models.ForeignKey(
        SavedList,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_saved_lists",
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=EDITOR,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("saved_list", "user"),
                name="unique_saved_list_member",
            )
        ]

    def __str__(self):
        return f"{self.user} in {self.saved_list} ({self.role})"


class SavedListInvitation(models.Model):
    ROLE_CHOICES = SavedListMembership.ROLE_CHOICES

    saved_list = models.ForeignKey(
        SavedList,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_saved_list_invitations",
    )
    email = models.EmailField(blank=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=SavedListMembership.EDITOR,
    )
    token = models.UUIDField(
        default=uuid4,
        unique=True,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=saved_list_invitation_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    @property
    def status(self):
        if self.revoked_at:
            return "revoked"
        if self.accepted_at:
            return "accepted"
        if self.expires_at <= timezone.now():
            return "expired"
        return "pending"

    def __str__(self):
        recipient = self.email or "Einladungslink"
        return f"{recipient}: {self.saved_list}"


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
