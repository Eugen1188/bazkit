from rest_framework import serializers

from .models import (
    SavedList,
    SavedListItem,
    ShoppingList,
    ShoppingListItem,
    Product
)


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
            "note"
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

        return attrs


class SavedListSerializer(
    serializers.ModelSerializer
):
    item_count = serializers.SerializerMethodField()

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
            "items"
        ]

        read_only_fields = [
            "id",
            "created_at",
            "item_count"
        ]

    def get_item_count(self, obj):
        return obj.items.count()

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

                if "note" in item_data:
                    item.note = item_data[
                        "note"
                    ]

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

    class Meta:
        model = SavedList

        fields = [
            "id",
            "title",
            "created_at",
            "items"
        ]


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
            "created_at"
        ]

        read_only_fields = [
            "id",
            "created_at"
        ]


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

        return attrs


    def create(
        self,
        validated_data
    ):
        name = (
            validated_data
            .get(
                "name",
                ""
            )
            .strip()
        )

        unit = (
            validated_data
            .get(
                "unit",
                ""
            )
            .strip()
        )


        if (
            name
            and
            not validated_data.get(
                "product"
            )
        ):
            product = (
                Product.objects
                .filter(
                    name__iexact=name
                )
                .first()
            )


            if not product:
                product = Product.objects.create(
                    name=name,
                    default_unit=unit
                )


            elif (
                not product.default_unit
                and
                unit
            ):
                product.default_unit = unit

                product.save(
                    update_fields=[
                        "default_unit"
                    ]
                )


            validated_data[
                "product"
            ] = product


        return super().create(
            validated_data
        )


class ShoppingListSerializer(
    serializers.ModelSerializer
):
    items = ShoppingListItemSerializer(
        many=True,
        read_only=True
    )

    item_count = serializers.SerializerMethodField()

    completed_count = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingList

        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "item_count",
            "completed_count",
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