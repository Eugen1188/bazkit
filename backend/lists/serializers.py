from rest_framework import serializers
from .models import SavedList, SavedListItem


class SavedListItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    class Meta:
        model = SavedListItem
        fields = [
            "id",
            "product",
            "product_name",
            "name",
            "quantity",
            "unit",
        ]

    def validate(self, attrs):
        product = attrs.get("product")
        name = attrs.get("name", "").strip()

        if not product and not name:
            raise serializers.ValidationError(
                "Either product or name must be provided."
            )

        return attrs


class SavedListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = SavedList
        fields = [
            "id",
            "title",
            "created_at",
            "item_count",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class SavedListDetailSerializer(serializers.ModelSerializer):
    items = SavedListItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = SavedList
        fields = [
            "id",
            "title",
            "created_at",
            "items",
        ]