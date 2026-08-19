from django.db.models import Case, IntegerField, Value, When

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Product
from .serializers import ProductSerializer


class ProductSearchAPIView(
    ListAPIView
):
    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
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
                    output_field=IntegerField()
                )
            )
            .order_by(
                "search_priority",
                "name"
            )[:10]
        )