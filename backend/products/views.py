import logging

import requests

from django.db.models import (
    Case,
    IntegerField,
    Value,
    When,
)

from rest_framework import status

from rest_framework.generics import (
    ListAPIView,
)

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import (
    Response,
)

from rest_framework.views import (
    APIView,
)

from .models import Product

from .serializers import (
    ProductSerializer,
)


logger = logging.getLogger(
    __name__
)


OPEN_FOOD_FACTS_URL = (
    "https://world.openfoodfacts.org/cgi/search.pl"
)


OPEN_FOOD_FACTS_HEADERS = {
    "User-Agent":
        "Bazkit/1.0 (product-search)"
}


class ProductSearchAPIView(
    ListAPIView
):

    serializer_class = (
        ProductSerializer
    )

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


        if (
            len(query) < 2
        ):
            return (
                Product.objects
                .none()
            )


        return (
            Product.objects
            .filter(
                name__icontains=query
            )
            .annotate(
                search_priority=Case(

                    When(
                        name__iexact=query,
                        then=Value(0)
                    ),

                    When(
                        name__istartswith=query,
                        then=Value(1)
                    ),

                    default=Value(2),

                    output_field=
                        IntegerField()
                )
            )
            .order_by(
                "search_priority",
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


        if (
            len(query) < 3
        ):

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
                        10
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


        saved_products = []

        used_names = set()


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


            if (
                not name
            ):
                continue


            if (
                len(name) > 100
            ):

                name = (
                    name[:100]
                    .strip()
                )


            normalized_name = (
                name.casefold()
            )


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


            product = (
                Product.objects
                .filter(
                    name__iexact=name
                )
                .first()
            )


            if (
                product is None
            ):

                product = (
                    Product.objects
                    .create(
                        name=name,
                        category=category,
                        default_unit=""
                    )
                )


            saved_products.append(
                product
            )


            if (
                len(saved_products)
                >= 10
            ):
                break


        serializer = (
            ProductSerializer(
                saved_products,
                many=True
            )
        )


        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )