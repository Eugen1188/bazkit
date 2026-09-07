from django.utils import timezone
from rest_framework import serializers

from .categories import shopping_category
from .models import (
    SavedList,
    SavedListInvitation,
    SavedListItem,
    ShoppingList,
    ShoppingListItem,
)


PRICE_FIELDS = [
    "estimated_price", "price_source", "price_currency", "price_date",
    "price_store", "price_sample_count", "price_min", "price_max",
    "package_price", "package_quantity", "package_unit",
]


def estimated_total(obj):
    prices = [item.estimated_price for item in obj.items.all() if item.estimated_price is not None]
    return round(sum(prices), 2) if prices else None


def display_name(user):
    return user.get_full_name().strip() or user.email or user.username


def access_role(obj, user):
    if not user or not getattr(user, "is_authenticated", False):
        return None
    if obj.user_id == user.id:
        return "owner"
    memberships = getattr(obj, "_prefetched_objects_cache", {}).get("memberships")
    if memberships is not None:
        membership = next((entry for entry in memberships if entry.user_id == user.id), None)
    else:
        membership = obj.memberships.filter(user=user).first()
    return membership.role if membership else None


class SavedListAccessMixin:
    def request_user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_access_role(self, obj):
        return access_role(obj, self.request_user())

    def get_can_edit(self, obj):
        return self.get_access_role(obj) in {"owner", "editor"}

    def get_is_owner(self, obj):
        return self.get_access_role(obj) == "owner"

    def get_owner_name(self, obj):
        return display_name(obj.user)

    def get_member_count(self, obj):
        return obj.memberships.count() + 1

    def get_checked_count(self, obj):
        annotated = getattr(obj, "checked_count", None)
        return annotated if annotated is not None else obj.items.filter(is_checked=True).count()


class SavedListItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source="product.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    checked_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SavedListItem
        fields = [
            "id", "product", "product_name", "name", "quantity", "unit",
            "note", "is_checked", "created_by_name", "checked_by_name",
            "checked_at", "updated_at", *PRICE_FIELDS,
        ]
        read_only_fields = [
            "id", "created_by_name", "checked_by_name", "checked_at", "updated_at",
        ]

    def get_created_by_name(self, obj):
        return display_name(obj.created_by) if obj.created_by else ""

    def get_checked_by_name(self, obj):
        return display_name(obj.checked_by) if obj.checked_by else ""

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        name = attrs.get("name", getattr(self.instance, "name", "")).strip()
        if not product and not name:
            raise serializers.ValidationError("Produkt oder Name muss angegeben werden.")
        if product:
            attrs["name"] = product.name
        elif "name" in attrs:
            attrs["name"] = name
        if attrs.get("estimated_price") is not None and attrs["estimated_price"] < 0:
            raise serializers.ValidationError({"estimated_price": "Der Preis darf nicht negativ sein."})
        return attrs


class SavedListSerializer(SavedListAccessMixin, serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    checked_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    estimated_total = serializers.SerializerMethodField()
    access_role = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    items = SavedListItemSerializer(many=True, required=False)

    class Meta:
        model = SavedList
        fields = [
            "id", "title", "created_at", "updated_at", "item_count",
            "checked_count", "member_count", "estimated_total", "access_role",
            "can_edit", "is_owner", "owner_name", "items",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "item_count", "checked_count",
            "member_count", "access_role", "can_edit", "is_owner", "owner_name",
        ]

    def get_item_count(self, obj):
        return obj.items.count()

    def get_estimated_total(self, obj):
        return estimated_total(obj)

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context["request"]
        saved_list = SavedList.objects.create(user=request.user, **validated_data)
        for item_data in items_data:
            item_data.pop("id", None)
            is_checked = item_data.get("is_checked", False)
            SavedListItem.objects.create(
                saved_list=saved_list,
                created_by=request.user,
                checked_by=request.user if is_checked else None,
                checked_at=timezone.now() if is_checked else None,
                **item_data,
            )
        return saved_list

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        request = self.context["request"]
        instance.title = validated_data.get("title", instance.title)
        instance.save()
        if items_data is None:
            return instance

        existing_items = {item.id: item for item in instance.items.all()}
        received_ids = []
        for item_data in items_data:
            item_id = item_data.pop("id", None)
            if item_id is not None and item_id in existing_items:
                item = existing_items[item_id]
                for field in ["name", "quantity", "unit", "product", "note", *PRICE_FIELDS]:
                    if field in item_data:
                        setattr(item, field, item_data[field])
                if "is_checked" in item_data and item.is_checked != item_data["is_checked"]:
                    item.is_checked = item_data["is_checked"]
                    item.checked_by = request.user if item.is_checked else None
                    item.checked_at = timezone.now() if item.is_checked else None
                item.save()
                received_ids.append(item.id)
            else:
                is_checked = item_data.get("is_checked", False)
                new_item = SavedListItem.objects.create(
                    saved_list=instance,
                    created_by=request.user,
                    checked_by=request.user if is_checked else None,
                    checked_at=timezone.now() if is_checked else None,
                    **item_data,
                )
                received_ids.append(new_item.id)
        instance.items.exclude(id__in=received_ids).delete()
        return instance


class SavedListSummarySerializer(SavedListAccessMixin, serializers.ModelSerializer):
    item_count = serializers.IntegerField(read_only=True)
    checked_count = serializers.IntegerField(read_only=True)
    member_count = serializers.SerializerMethodField()
    access_role = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = SavedList
        fields = [
            "id", "title", "created_at", "updated_at", "item_count",
            "checked_count", "member_count", "access_role", "can_edit",
            "is_owner", "owner_name",
        ]


class SavedListDetailSerializer(SavedListAccessMixin, serializers.ModelSerializer):
    items = SavedListItemSerializer(many=True, read_only=True)
    estimated_total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    checked_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    access_role = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = SavedList
        fields = [
            "id", "title", "created_at", "updated_at", "item_count",
            "checked_count", "member_count", "estimated_total", "access_role",
            "can_edit", "is_owner", "owner_name", "items",
        ]

    def get_estimated_total(self, obj):
        return estimated_total(obj)

    def get_item_count(self, obj):
        return obj.items.count()


class SavedListInvitationSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    invite_url = serializers.SerializerMethodField()

    class Meta:
        model = SavedListInvitation
        fields = [
            "id", "email", "role", "created_at", "expires_at", "status",
            "invite_url",
        ]

    def get_invite_url(self, obj):
        base_url = self.context.get("frontend_url", "").rstrip("/")
        return f"{base_url}/invite/{obj.token}"


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
    is_common_pantry = serializers.SerializerMethodField()

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
            "is_common_pantry",
            *PRICE_FIELDS,
        ]

    def category(self, obj):
        if not hasattr(obj, "_shopping_category"):
            obj._shopping_category = shopping_category(obj)
        return obj._shopping_category

    def get_shopping_category(self, obj):
        return self.category(obj)[0]

    def get_shopping_category_label(self, obj):
        return self.category(obj)[1]

    def get_shopping_category_order(self, obj):
        return self.category(obj)[2]

    def get_is_common_pantry(self, obj):
        return bool(obj.product and obj.product.is_common_pantry)

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
        return sum(1 for item in obj.items.all() if item.is_checked)

    def get_estimated_total(self, obj):
        return estimated_total(obj)
