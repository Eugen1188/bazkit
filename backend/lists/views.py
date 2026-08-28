from django.db import transaction

from rest_framework import status

from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.response import Response

from rest_framework.views import APIView


from recipes.models import Recipe
from products.pricing import scaled_price


from .models import (
    SavedList,
    SavedListItem,
    ShoppingList,
    ShoppingListItem
)


from .serializers import (
    SavedListSerializer,
    SavedListDetailSerializer,
    SavedListItemSerializer,
    ShoppingListSerializer,
    ShoppingListItemSerializer
)


PRICE_SNAPSHOT_FIELDS = (
    "estimated_price", "price_source", "price_currency", "price_date",
    "price_store", "price_sample_count", "price_min", "price_max",
    "package_price", "package_quantity", "package_unit",
)


# ==========================================
# SAVED LISTS
# ==========================================


class SavedListListCreateAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):
        saved_lists = (
            SavedList.objects
            .filter(
                user=request.user,
                is_community_snapshot=False,
            )
            .prefetch_related(
                "items"
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = SavedListSerializer(
            saved_lists,
            many=True
        )

        return Response(
            serializer.data
        )


    def post(
        self,
        request
    ):
        serializer = SavedListSerializer(
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        saved_list = serializer.save()

        return Response(
            SavedListSerializer(
                saved_list
            ).data,
            status=status.HTTP_201_CREATED
        )


class SavedListDetailAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_object(
        self,
        request,
        pk
    ):
        return (
            SavedList.objects
            .filter(
                id=pk,
                user=request.user
            )
            .prefetch_related(
                "items"
            )
            .first()
        )


    def get(
        self,
        request,
        pk
    ):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = (
            SavedListDetailSerializer(
                saved_list
            )
        )

        return Response(
            serializer.data
        )


    def put(
        self,
        request,
        pk
    ):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SavedListSerializer(
            saved_list,
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_list = (
            serializer.save()
        )

        return Response(
            SavedListSerializer(
                updated_list
            ).data,
            status=status.HTTP_200_OK
        )


    def delete(
        self,
        request,
        pk
    ):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        saved_list.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SavedListItemDetailAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_object(
        self,
        request,
        list_id,
        item_id
    ):
        return (
            SavedListItem.objects
            .filter(
                id=item_id,
                saved_list_id=list_id,
                saved_list__user=request.user
            )
            .first()
        )


    def put(
        self,
        request,
        list_id,
        item_id
    ):
        item = self.get_object(
            request,
            list_id,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = (
            SavedListItemSerializer(
                item,
                data=request.data,
                partial=True
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    def delete(
        self,
        request,
        list_id,
        item_id
    ):
        item = self.get_object(
            request,
            list_id,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


# ==========================================
# SHOPPING LIST
# ==========================================


class ShoppingListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_shopping_list(
        self,
        request
    ):
        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )

        return shopping_list


    def get(
        self,
        request
    ):
        shopping_list = (
            self.get_shopping_list(
                request
            )
        )

        shopping_list = (
            ShoppingList.objects
            .prefetch_related(
                "items__product"
            )
            .get(
                id=shopping_list.id
            )
        )

        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data
        )


    def delete(
        self,
        request
    ):
        shopping_list = (
            self.get_shopping_list(
                request
            )
        )

        shopping_list.items.all().delete()

        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data,
            status=status.HTTP_200_OK
        )


class ShoppingListItemCreateAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def post(
        self,
        request
    ):
        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )

        serializer = (
            ShoppingListItemSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        item = serializer.save(
            shopping_list=
                shopping_list
        )

        return Response(
            ShoppingListItemSerializer(
                item
            ).data,
            status=status.HTTP_201_CREATED
        )


class ShoppingListItemDetailAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    def get_object(
        self,
        request,
        item_id
    ):
        return (
            ShoppingListItem.objects
            .filter(
                id=item_id,
                shopping_list__user=
                    request.user
            )
            .first()
        )


    def patch(
        self,
        request,
        item_id
    ):
        item = self.get_object(
            request,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = (
            ShoppingListItemSerializer(
                item,
                data=request.data,
                partial=True
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data
        )


    def delete(
        self,
        request,
        item_id
    ):
        item = self.get_object(
            request,
            item_id
        )

        if not item:
            return Response(
                {
                    "detail":
                        "Produkt nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class AddSavedListToShoppingListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    @transaction.atomic
    def post(
        self,
        request,
        saved_list_id
    ):
        saved_list = (
            SavedList.objects
            .filter(
                id=saved_list_id,
                user=request.user
            )
            .prefetch_related(
                "items"
            )
            .first()
        )

        if not saved_list:
            return Response(
                {
                    "detail":
                        "Gespeicherte Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )

        new_items = []

        for saved_item in (
            saved_list.items.all()
        ):
            new_items.append(
                ShoppingListItem(
                    shopping_list=
                        shopping_list,

                    product=
                        saved_item.product,

                    name=
                        (
                            saved_item.name
                            or
                            (
                                saved_item
                                .product.name
                                if
                                saved_item.product
                                else ""
                            )
                        ),

                    quantity=
                        saved_item.quantity,

                    unit=
                        saved_item.unit,

                    note=
                        saved_item.note,

                    is_checked=False,

                    **{
                        field: getattr(saved_item, field)
                        for field in PRICE_SNAPSHOT_FIELDS
                    }
                )
            )

        ShoppingListItem.objects.bulk_create(
            new_items
        )

        shopping_list = (
            ShoppingList.objects
            .prefetch_related(
                "items"
            )
            .get(
                id=shopping_list.id
            )
        )

        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data,
            status=status.HTTP_200_OK
        )


class AddRecipeToShoppingListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]


    @transaction.atomic
    def post(
        self,
        request,
        recipe_id
    ):
        recipe = (
            Recipe.objects
            .filter(
                id=recipe_id,
                user=request.user
            )
            .prefetch_related(
                "ingredients__product"
            )
            .first()
        )


        if not recipe:
            return Response(
                {
                    "detail":
                        "Rezept nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )


        shopping_list, _ = (
            ShoppingList.objects
            .get_or_create(
                user=request.user
            )
        )


        new_items = []

        included_pantry_ids = request.data.get("included_pantry_product_ids")
        if included_pantry_ids is not None:
            if not isinstance(included_pantry_ids, list):
                return Response(
                    {"detail": "Die ausgewählten Vorratszutaten sind ungültig."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                included_pantry_ids = {int(value) for value in included_pantry_ids}
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Die ausgewählten Vorratszutaten sind ungültig."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


        for ingredient in (
            recipe.ingredients.all()
        ):

            if (
                included_pantry_ids is not None
                and ingredient.product is not None
                and ingredient.product.is_common_pantry
                and ingredient.product_id not in included_pantry_ids
            ):
                continue

            price_data = {
                field: getattr(ingredient, field)
                for field in PRICE_SNAPSHOT_FIELDS
            }

            if ingredient.package_price is not None:
                price_data["estimated_price"] = scaled_price(
                    ingredient.package_price,
                    ingredient.package_quantity,
                    ingredient.package_unit,
                    ingredient.quantity,
                    ingredient.unit,
                    mode="purchase",
                )
                price_data["price_min"] = None
                price_data["price_max"] = None

            new_items.append(
                ShoppingListItem(
                    shopping_list=
                        shopping_list,

                    product=
                        ingredient.product,

                    name=
                        ingredient.name,

                    quantity=
                        ingredient.quantity,

                    unit=
                        ingredient.unit,

                    note='',

                    is_checked=False,

                    **price_data
                )
            )


        ShoppingListItem.objects.bulk_create(
            new_items
        )


        shopping_list = (
            ShoppingList.objects
            .prefetch_related(
                "items"
            )
            .get(
                id=shopping_list.id
            )
        )


        return Response(
            ShoppingListSerializer(
                shopping_list
            ).data,
            status=status.HTTP_200_OK
        )
