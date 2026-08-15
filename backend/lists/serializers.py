from rest_framework import serializers

from .models import (
    SavedList,
    SavedListItem
)


class SavedListItemSerializer(serializers.ModelSerializer):
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


class SavedListSerializer(serializers.ModelSerializer):
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

            # Vorhandenes Produkt aktualisieren
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

                # Notiz bleibt erhalten bzw. wird aktualisiert
                if "note" in item_data:
                    item.note = item_data.get(
                        "note",
                        item.note
                    )

                item.save()

                received_ids.append(
                    item.id
                )

            # Neues Produkt anlegen
            else:
                new_item = SavedListItem.objects.create(
                    saved_list=instance,
                    **item_data
                )

                received_ids.append(
                    new_item.id
                )

        # Nur Produkte löschen,
        # die auf der Edit-Seite wirklich entfernt wurden
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