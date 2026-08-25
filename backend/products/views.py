import logging
import re
from decimal import Decimal, InvalidOperation

import requests
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import ProductSerializer

logger = logging.getLogger(__name__)
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"
OFF_HEADERS = {"User-Agent": "Bazkit/1.0 (product-search; contact: admin@bazkit.local)"}
AMOUNT_SUFFIX = re.compile(r"\s*[,\-–]?\s*\d+(?:[.,]\d+)?\s*(?:mg|g|kg|ml|cl|dl|l)\s*$", re.I)


def clean_text(value, limit):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def clean_name(value):
    return AMOUNT_SUFFIX.sub("", clean_text(value, 150)).strip(" ,-–")


def decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        result = Decimal(str(value))
        return result if result >= 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def off_payload(item):
    code = clean_text(item.get("code") or item.get("_id"), 100)
    name = clean_name(item.get("product_name_de") or item.get("product_name") or item.get("generic_name_de") or item.get("generic_name"))
    if not code or not name:
        return None
    nutriments = item.get("nutriments") or {}
    return {
        "id": None,
        "name": name,
        "category": clean_text(item.get("categories"), 150),
        "brand": clean_text(item.get("brands"), 150),
        "source": "open_food_facts",
        "external_id": code,
        "default_unit": "g",
        "calories_per_100g": decimal_or_none(nutriments.get("energy-kcal_100g")),
        "protein_per_100g": decimal_or_none(nutriments.get("proteins_100g")),
        "carbohydrates_per_100g": decimal_or_none(nutriments.get("carbohydrates_100g")),
        "fat_per_100g": decimal_or_none(nutriments.get("fat_100g")),
        "fiber_per_100g": decimal_or_none(nutriments.get("fiber_100g")),
        "origin": "open_food_facts",
    }


class ProductSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = clean_text(request.query_params.get("q"), 100)
        if len(query) < 2:
            return Response([])
        products = Product.objects.filter(
            Q(name__istartswith=query) | Q(name__icontains=f" {query}")
        ).annotate(
            relevance=Case(When(name__istartswith=query, then=Value(0)), default=Value(1), output_field=IntegerField())
        ).order_by("relevance", "name")[:15]
        return Response(ProductSerializer(products, many=True).data)


class ExternalProductSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = clean_text(request.query_params.get("q"), 100)
        if len(query) < 3:
            return Response([])
        try:
            response = requests.get(OFF_SEARCH_URL, params={
                "search_terms": query, "search_simple": 1, "action": "process", "json": 1,
                "page_size": 30, "fields": "code,product_name_de,product_name,generic_name_de,generic_name,categories,brands,nutriments",
            }, headers=OFF_HEADERS, timeout=8)
            response.raise_for_status()
            items = response.json().get("products", [])
        except (requests.RequestException, ValueError) as error:
            logger.warning("Open Food Facts search failed: %s", error)
            return Response({"detail": "Open Food Facts ist momentan nicht erreichbar."}, status=status.HTTP_502_BAD_GATEWAY)
        words = query.casefold().split()
        results, seen = [], set()
        for item in items:
            product = off_payload(item)
            if not product or product["external_id"] in seen:
                continue
            searchable = f'{product["name"]} {product["brand"]}'.casefold()
            if not all(word in searchable for word in words):
                continue
            seen.add(product["external_id"])
            results.append(product)
            if len(results) == 10:
                break
        return Response(results)


class SaveExternalProductAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source = request.data.get("source")
        external_id = clean_text(request.data.get("external_id"), 100)
        if source != "open_food_facts" or not external_id:
            return Response({"detail": "Ungültiger externer Produktverweis."}, status=status.HTTP_400_BAD_REQUEST)
        existing = Product.objects.filter(source=source, external_id=external_id).first()
        if existing:
            return Response(ProductSerializer(existing).data)
        try:
            response = requests.get(OFF_PRODUCT_URL.format(code=external_id), params={"fields": "code,product_name_de,product_name,generic_name_de,generic_name,categories,brands,nutriments"}, headers=OFF_HEADERS, timeout=8)
            response.raise_for_status()
            body = response.json()
            product_data = off_payload(body.get("product") or {}) if body.get("status") == 1 else None
        except (requests.RequestException, ValueError) as error:
            logger.warning("Open Food Facts product lookup failed: %s", error)
            return Response({"detail": "Das externe Produkt konnte nicht geprüft werden."}, status=status.HTTP_502_BAD_GATEWAY)
        if not product_data or product_data["external_id"] != external_id:
            return Response({"detail": "Das externe Produkt existiert nicht mehr."}, status=status.HTTP_404_NOT_FOUND)
        defaults = {key: value for key, value in product_data.items() if key not in {"id", "origin", "source", "external_id"}}
        with transaction.atomic():
            product, created = Product.objects.get_or_create(source=source, external_id=external_id, defaults=defaults)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
