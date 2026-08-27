from rest_framework import serializers

from .models import (
    SavedList,
    SavedListItem,
    ShoppingList,
    ShoppingListItem
)
from .categories import shopping_category


PRICE_FIELDS = [
    "estimated_price", "price_source", "price_currency", "price_date",
    "price_store", "price_sample_count", "price_min", "price_max",
    "package_price", "package_quantity", "package_unit",
]


def estimated_total(obj):
    prices = [item.estimated_price for item in obj.items.all() if item.estimated_price is not None]
    return round(sum(prices), 2) if prices else None


class SavedListItemSerializer(
    serializers.ModelSerializer
):
    id = serializers.IntegerField(
        required=False
    )

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
            "note",
            *PRICE_FIELDS,
        ]

        read_only_fields = [
            "id",
            "created_at",
            "shopping_category",
            "shopping_category_label",
            "shopping_category_order",
        ]

    def validate(self, attrs):
        product = attrs.get(
            "product",
            getattr(
                self.instance,
                "product",
                None
            )
        )

        name = attrs.get(
            "name",
            getattr(
                self.instance,
                "name",
                ""
            )
        ).strip()

        if not product and not name:
            raise serializers.ValidationError(
                "Either product or name must be provided."
            )

        if product:
            attrs["name"] = product.name
        elif "name" in attrs:
            attrs["name"] = name

        if attrs.get("estimated_price") is not None and attrs["estimated_price"] < 0:
            raise serializers.ValidationError({"estimated_price": "Der Preis darf nicht negativ sein."})

        return attrs


class SavedListSerializer(
    serializers.ModelSerializer
):
    item_count = serializers.SerializerMethodField()
    estimated_total = serializers.SerializerMethodField()

    items = SavedListItemSerializer(
        many=True,
        required=False
    )

    class Meta:
        model = SavedList

        fields = [
            "id",
            "title",
            "created_at",
            "item_count",
            "estimated_total",
            "items"
        ]

        read_only_fields = [
            "id",
            "created_at",
            "item_count"
        ]

    def get_item_count(self, obj):
        return obj.items.count()

    def get_estimated_total(self, obj):
        return estimated_total(obj)

    def create(self, validated_data):
        items_data = validated_data.pop(
            "items",
            []
        )

        request = self.context["request"]

        saved_list = SavedList.objects.create(
            user=request.user,
            **validated_data
        )

        for item_data in items_data:
            item_data.pop(
                "id",
                None
            )

            SavedListItem.objects.create(
                saved_list=saved_list,
                **item_data
            )

        return saved_list

    def update(
        self,
        instance,
        validated_data
    ):
        items_data = validated_data.pop(
            "items",
            None
        )

        instance.title = validated_data.get(
            "title",
            instance.title
        )

        instance.save()

        if items_data is None:
            return instance

        existing_items = {
            item.id: item
            for item in instance.items.all()
        }

        received_ids = []

        for item_data in items_data:
            item_id = item_data.pop(
                "id",
                None
            )

            if (
                item_id is not None
                and item_id in existing_items
            ):
                item = existing_items[
                    item_id
                ]

                item.name = item_data.get(
                    "name",
                    item.name
                )

                item.quantity = item_data.get(
                    "quantity",
                    item.quantity
                )

                item.unit = item_data.get(
                    "unit",
                    item.unit
                )

                item.product = item_data.get(
                    "product",
                    item.product
                )

                for field in ["note", *PRICE_FIELDS]:
                    if field in item_data:
                        setattr(item, field, item_data[field])

                item.save()

                received_ids.append(
                    item.id
                )

            else:
                new_item = (
                    SavedListItem.objects.create(
                        saved_list=instance,
                        **item_data
                    )
                )

                received_ids.append(
                    new_item.id
                )

        instance.items.exclude(
            id__in=received_ids
        ).delete()

        return instance


class SavedListDetailSerializer(
    serializers.ModelSerializer
):
    items = SavedListItemSerializer(
        many=True,
        read_only=True
    )
    estimated_total = serializers.SerializerMethodField()

    class Meta:
        model = SavedList

        fields = [
            "id",
            "title",
            "created_at",
            "estimated_total",
            "items"
        ]

    def get_estimated_total(self, obj):
        return estimated_total(obj)


# ==========================================
# SHOPPING LIST
# ==========================================

class ShoppingListItemSerializer(
    serializers.ModelSerializer
):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    shopping_category = serializers.SerializerMethodField()
    shopping_category_label = serializers.SerializerMethodField()
    shopping_category_order = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingListItem

        fields = [
            "id",
            "product",
            "product_name",
            "name",
            "quantity",
            "unit",
            "note",
            "is_checked",
            "created_at",
            "shopping_category",
            "shopping_category_label",
            "shopping_category_order",
            *PRICE_FIELDS,
        ]

    def get_shopping_category(self, obj):
        return shopping_category(obj)[0]

    def get_shopping_category_label(self, obj):
        return shopping_category(obj)[1]

    def get_shopping_category_order(self, obj):
        return shopping_category(obj)[2]

    def validate(
        self,
        attrs
    ):
        product = attrs.get(
            "product",
            getattr(
                self.instance,
                "product",
                None
            )
        )

        name = attrs.get(
            "name",
            getattr(
                self.instance,
                "name",
                ""
            )
        ).strip()

        if (
            not product
            and
            not name
        ):
            raise serializers.ValidationError(
                "Produkt oder Name muss angegeben werden."
            )

        if product:
            attrs["name"] = product.name
        elif "name" in attrs:
            attrs["name"] = name

        if attrs.get("estimated_price") is not None and attrs["estimated_price"] < 0:
            raise serializers.ValidationError({"estimated_price": "Der Preis darf nicht negativ sein."})

        return attrs


class ShoppingListSerializer(
    serializers.ModelSerializer
):
    items = ShoppingListItemSerializer(
        many=True,
        read_only=True
    )

    item_count = serializers.SerializerMethodField()

    completed_count = serializers.SerializerMethodField()
    estimated_total = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingList

        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "item_count",
            "completed_count",
            "estimated_total",
            "items"
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "item_count",
            "completed_count",
            "items"
        ]

    def get_item_count(self, obj):
        return obj.items.count()

    def get_completed_count(self, obj):
        return obj.items.filter(
            is_checked=True
        ).count()

    def get_estimated_total(self, obj):
        return estimated_total(obj)
