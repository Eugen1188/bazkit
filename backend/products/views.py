import logging
import re

import requests

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import ProductSerializer


logger = logging.getLogger(__name__)


OPEN_FOOD_FACTS_URL = (
    "https://world.openfoodfacts.org/cgi/search.pl"
)


OPEN_FOOD_FACTS_HEADERS = {
    "User-Agent": "Bazkit/1.0 (product-search)"
}


class ProductSearchAPIView(
    ListAPIView
):
    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(
        self
    ):
        query = (
            self.request
            .query_params
            .get(
                "q",
                ""
            )
            .strip()
        )

        if len(query) < 2:
            return Product.objects.none()

        return (
            Product.objects
            .filter(
                name__istartswith=query
            )
            .order_by(
                "name"
            )[:10]
        )


class ExternalProductSearchAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):
        query = (
            request
            .query_params
            .get(
                "q",
                ""
            )
            .strip()
        )

        if len(query) < 3:
            return Response(
                {
                    "detail":
                        "Bitte mindestens "
                        "3 Zeichen eingeben."
                },
                status=
                    status.HTTP_400_BAD_REQUEST
            )

        try:
            response = requests.get(
                OPEN_FOOD_FACTS_URL,
                params={
                    "search_terms":
                        query,

                    "search_simple":
                        1,

                    "action":
                        "process",

                    "json":
                        1,

                    "page_size":
                        50
                },
                headers=
                    OPEN_FOOD_FACTS_HEADERS,
                timeout=8
            )

            response.raise_for_status()

            response_data = (
                response.json()
            )

            external_products = (
                response_data.get(
                    "products",
                    []
                )
            )

        except requests.RequestException as error:
            logger.exception(
                "Open Food Facts request failed: %s",
                error
            )

            return Response(
                {
                    "detail":
                        "Die externe Produktsuche "
                        "ist momentan nicht erreichbar."
                },
                status=
                    status.HTTP_502_BAD_GATEWAY
            )

        except ValueError as error:
            logger.exception(
                "Invalid Open Food Facts response: %s",
                error
            )

            return Response(
                {
                    "detail":
                        "Die externe API hat eine "
                        "ungültige Antwort geliefert."
                },
                status=
                    status.HTTP_502_BAD_GATEWAY
            )

        results = []

        used_names = set()

        normalized_query = (
            query.casefold()
        )

        for item in external_products:
            raw_name = (
                item.get(
                    "product_name"
                )
                or
                item.get(
                    "generic_name"
                )
                or
                ""
            )

            name = (
                raw_name
                .strip()
            )

            if not name:
                continue

            if len(name) > 100:
                name = (
                    name[:100]
                    .strip()
                )

            normalized_name = (
                name.casefold()
            )

            words = [
                word
                for word
                in re.split(
                    r"[\s\-_/,.]+",
                    normalized_name
                )
                if word
            ]

            is_relevant = (
                normalized_name.startswith(
                    normalized_query
                )
                or
                any(
                    word.startswith(
                        normalized_query
                    )
                    for word
                    in words
                )
            )

            if not is_relevant:
                continue

            if (
                normalized_name
                in used_names
            ):
                continue

            used_names.add(
                normalized_name
            )

            category = (
                item.get(
                    "categories",
                    ""
                )
                or
                ""
            )

            category = (
                category[:100]
                .strip()
            )

            results.append(
                {
                    "id": None,
                    "name": name,
                    "category": category,
                    "default_unit": "",
                    "source": "external"
                }
            )

            if len(results) >= 10:
                break

        results.sort(
            key=lambda product: (
                0
                if product["name"]
                .casefold()
                .startswith(
                    normalized_query
                )
                else 1,
                product["name"]
                .casefold()
            )
        )

        return Response(
            results,
            status=
                status.HTTP_200_OK
        )


class SaveExternalProductAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request
    ):
        name = (
            str(
                request.data.get(
                    "name",
                    ""
                )
            )
            .strip()
        )

        category = (
            str(
                request.data.get(
                    "category",
                    ""
                )
            )
            .strip()
        )

        default_unit = (
            str(
                request.data.get(
                    "default_unit",
                    ""
                )
            )
            .strip()
        )

        if not name:
            return Response(
                {
                    "detail":
                        "Produktname fehlt."
                },
                status=
                    status.HTTP_400_BAD_REQUEST
            )

        if len(name) > 100:
            return Response(
                {
                    "detail":
                        "Der Produktname ist zu lang."
                },
                status=
                    status.HTTP_400_BAD_REQUEST
            )

        product = (
            Product.objects
            .filter(
                name__iexact=name
            )
            .first()
        )

        created = False

        if product is None:
            product = (
                Product.objects
                .create(
                    name=name,
                    category=
                        category[:100],
                    default_unit=
                        default_unit[:30]
                )
            )

            created = True

        serializer = (
            ProductSerializer(
                product
            )
        )

        response_data = {
            **serializer.data,
            "source": "local"
        }

        return Response(
            response_data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            )
        )