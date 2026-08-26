import logging
import re
from decimal import Decimal, InvalidOperation

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.core.cache import cache
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.functions import Length
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog import canonical_recipe_name, canonical_search_query, recipe_ingredient_status
from .models import Product
from .pricing import estimate_open_price, estimate_product_price
from .serializers import ProductSerializer

logger = logging.getLogger(__name__)
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"
OFF_HEADERS = {"User-Agent": "Bazkit/1.0 (product-search; contact: admin@bazkit.local)"}
AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b"
    r"(?:\s*(?:packung|flasche|dose|beutel|glas))?\s*\)?\s*$",
    re.I,
)


def off_session():
    session = requests.Session()
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.4,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


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
    canonical_name = canonical_recipe_name(name)
    is_recipe_ingredient, exclusion_reason = recipe_ingredient_status(
        name,
        item.get("categories"),
        "open_food_facts",
        code,
    )
    return {
        "id": None,
        "name": name,
        "canonical_name": canonical_name,
        "is_recipe_ingredient": is_recipe_ingredient,
        "recipe_exclusion_reason": exclusion_reason,
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
        recipe_only = request.query_params.get("recipe_only") in {"1", "true", "yes"}
        if len(query) < 2:
            return Response([])
        ranking_query = canonical_search_query(query) if recipe_only else query
        search_terms = {query, ranking_query}
        search_filter = Q()
        for term in search_terms:
            search_filter |= Q(name__icontains=term) | Q(canonical_name__icontains=term)
        products = Product.objects.filter(
            source__in=("bls", "open_food_facts", "usda"),
        ).filter(search_filter).annotate(
            relevance=Case(
                When(canonical_name__iexact=ranking_query, then=Value(0)),
                When(name__iexact=ranking_query, then=Value(0)),
                When(canonical_name__istartswith=ranking_query, then=Value(1)),
                When(name__istartswith=ranking_query, then=Value(2)),
                When(name__iendswith=ranking_query, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            ),
            name_length=Length("name"),
        )
        if recipe_only:
            products = products.filter(is_recipe_ingredient=True)
        products = products.order_by("relevance", "name_length", "name")[:160 if recipe_only else 15]
        data = ProductSerializer(products, many=True).data
        results = []
        seen = set()
        for item in data:
            if recipe_only and not recipe_ingredient_status(
                item["name"],
                item["category"],
                item["source"],
                item["external_id"],
            )[0]:
                continue
            display_name = clean_name(item["canonical_name"] if recipe_only else item["name"])
            if not display_name:
                continue
            key = display_name.casefold() if recipe_only else f'{item["source"]}:{item["external_id"]}'
            if key in seen:
                continue
            seen.add(key)
            item["name"] = display_name
            results.append(item)
            if len(results) == 15:
                break
        return Response(results)


class ProductPriceEstimateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product = None
        product_id = request.query_params.get("product_id")
        external_id = clean_text(request.query_params.get("external_id"), 100)
        source = clean_text(request.query_params.get("source"), 30)

        if product_id:
            product = Product.objects.filter(id=product_id).first()
            if product is None:
                return Response({"detail": "Produkt nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
            source = product.source or ""
            external_id = product.external_id or ""
            product_name = product.name
        else:
            product_name = clean_text(request.query_params.get("product_name"), 150)

        quantity = request.query_params.get("quantity", "1")
        unit = clean_text(request.query_params.get("unit"), 30)
        mode = request.query_params.get("mode", "purchase")
        if mode not in {"purchase", "consumption"}:
            return Response({"detail": "Ungültiger Berechnungsmodus."}, status=status.HTTP_400_BAD_REQUEST)

        if product is not None:
            return Response(estimate_product_price(product, quantity, unit, mode))
        if source == "open_food_facts":
            return Response(estimate_open_price(
                external_id,
                quantity,
                unit,
                mode,
                product_name=product_name,
                allow_similar=False,
            ))
        return Response({
            "available": False,
            "estimated_price": None,
            "message": "Für diese Zutat ist noch kein belastbarer automatischer Referenzpreis verfügbar.",
        })


class ExternalProductSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = clean_text(request.query_params.get("q"), 100)
        recipe_only = request.query_params.get("recipe_only") in {"1", "true", "yes"}
        if len(query) < 4:
            return Response([])
        cache_key = f"off-search:{query.casefold()}:{int(recipe_only)}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        try:
            response = off_session().get(OFF_SEARCH_URL, params={
                "search_terms": query, "search_simple": 1, "action": "process", "json": 1,
                "page_size": 30, "fields": "code,product_name_de,product_name,generic_name_de,generic_name,categories,brands,nutriments",
            }, headers=OFF_HEADERS, timeout=8)
            response.raise_for_status()
            items = response.json().get("products", [])
        except (requests.RequestException, ValueError) as error:
            logger.warning("Open Food Facts search failed: %s", error)
            return Response([])
        words = query.casefold().split()
        results, seen = [], set()
        for item in items:
            product = off_payload(item)
            if not product or product["external_id"] in seen:
                continue
            if recipe_only and not product["is_recipe_ingredient"]:
                continue
            searchable = f'{product["name"]} {product["brand"]}'.casefold()
            if not all(word in searchable for word in words):
                continue
            seen.add(product["external_id"])
            results.append(product)
        if recipe_only:
            normalized_query = query.casefold()
            results.sort(key=lambda product: (
                0 if product["canonical_name"].casefold() == normalized_query else
                1 if product["name"].casefold() == normalized_query else
                2 if product["canonical_name"].casefold().startswith(normalized_query) else
                3 if product["name"].casefold().startswith(normalized_query) else 4,
                len(product["name"]),
                product["name"].casefold(),
            ))
        results = results[:10]
        cache.set(cache_key, results, 60 * 15)
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
