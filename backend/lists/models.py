from django.conf import settings
from django.db import models
from products.models import Product


class SavedList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_lists"
    )
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class SavedListItem(models.Model):
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
    name = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    
    def __str__(self):
        return self.name


# class ShoppingList(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="shopping_lists"
#     )
#     title = models.CharField(max_length=100, default="Meine Einkaufsliste")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.title


# class ShoppingListItem(models.Model):
#     shopping_list = models.ForeignKey(
#         ShoppingList,
#         on_delete=models.CASCADE,
#         related_name="items"
#     )
#     product = models.ForeignKey(
#         Product,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     name = models.CharField(max_length=100, blank=True)
#     quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
#     unit = models.CharField(max_length=30, blank=True)
#     is_checked = models.BooleanField(default=False)

#     def __str__(self):
#         return self.name