from django.db import models


class Product(models.Model):
    name = models.CharField(
        max_length=100,
        db_index=True
    )

    category = models.CharField(
        max_length=100,
        blank=True
    )

    default_unit = models.CharField(
        max_length=30,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "name"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name"
                ],
                name="unique_product_name"
            )
        ]

    def __str__(self):
        return self.name