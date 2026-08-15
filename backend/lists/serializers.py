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
            "note"
        ]

    def validate(self, attrs):
        product = attrs.get("product")

        # Bei einem Update kann name eventuell nicht erneut
        # im Request enthalten sein.
        name = attrs.get(
            "name",
            getattr(self.instance, "name", "")
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
            SavedListItem.objects.create(
                saved_list=saved_list,
                **item_data
            )

        return saved_list

    def update(self, instance, validated_data):
        items_data = validated_data.pop(
            "items",
            []
        )

        instance.title = validated_data.get(
            "title",
            instance.title
        )

        instance.save()

        instance.items.all().delete()

        for item_data in items_data:
            SavedListItem.objects.create(
                saved_list=instance,
                **item_data
            )

        return instance


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
            "items"
        ]