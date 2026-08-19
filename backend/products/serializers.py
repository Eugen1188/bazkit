from rest_framework import serializers

from .models import Product


class ProductSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Product

        fields = [
            "id",
            "name",
            "category",
            "default_unit",
        ]

        read_only_fields = [
            "id",
        ]