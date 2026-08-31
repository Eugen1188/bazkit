import logging
import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog import (
    average_unit_weight_grams,
    canonical_recipe_name,
    canonical_search_query,
    liquid_density_grams_per_ml,
    logical_available_units,
    product_unit_conversions,
    resolved_product_unit_name,
    recipe_ingredient_status,
    suggested_unit_for_product,
    sync_curated_unit_conversion,
)
from .ingredient_catalog import (
    definition_for_query,
    display_name_for_query,
    normalize_alias,
    preferred_product_keys,
    replace_product_aliases,
    usda_display_name,
    usda_query,
)
from .models import IngredientSearchMetric, Product, ProductAlias
from .pricing import estimate_open_price, estimate_product_price
from .serializers import ProductSerializer
from .shopping_taxonomy import infer_product_taxonomy

logger = logging.getLogger(__name__)
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"
OFF_HEADERS = {"User-Agent": "Bazkit/1.0 (product-search; contact: admin@bazkit.local)"}
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_PRODUCT_URL = "https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b"
    r"(?:\s*(?:packung|flasche|dose|beutel|glas))?\s*\)?\s*$",
    re.I,
)

SEARCH_FEEDBACK_CONTEXTS = {
    value for value, _label in IngredientSearchMetric.CONTEXT_CHOICES
}


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


def package_data(item):
    quantity = decimal_or_none(item.get("product_quantity"))
    unit = clean_text(item.get("product_quantity_unit"), 20).casefold()
    if quantity is not None and unit:
        return quantity, unit
    match = re.search(
        r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>mg|g|kg|ml|cl|dl|l)\b",
        clean_text(item.get("quantity"), 80),
        re.I,
    )
    if not match:
        return None, ""
    return decimal_or_none(match.group("amount").replace(",", ".")), match.group("unit").casefold()


def nutrition_is_complete(product):
    return all(
        product.get(field) is not None
        for field in (
            "calories_per_100g",
            "protein_per_100g",
            "carbohydrates_per_100g",
            "fat_per_100g",
            "fiber_per_100g",
        )
    )


def add_unit_metadata(product):
    unit_name = resolved_product_unit_name(
        product["name"],
        product.get("canonical_name", ""),
        product.get("source", ""),
        product.get("external_id", ""),
    )
    conversions = product_unit_conversions(
        product["name"],
        product.get("canonical_name", ""),
        product.get("package_quantity"),
        product.get("package_unit", ""),
        product.get("source", ""),
        product.get("external_id", ""),
    )
    product["unit_conversions"] = [
        {
            **conversion,
            "grams_per_unit": str(conversion["grams_per_unit"]),
        }
        for conversion in conversions
    ]
    density = liquid_density_grams_per_ml(unit_name)
    product["grams_per_ml"] = str(density) if density is not None else None
    product["available_units"] = logical_available_units(
        product.get("default_unit", ""),
        product.get("package_unit", ""),
        product.get("shopping_category", ""),
        conversions,
        unit_name,
    )
    return product


class IngredientSearchFeedbackAPIView(APIView):
    """Speichert nur aggregierte Suchqualität, niemals Nutzer- oder Rezeptdaten."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = clean_text(request.data.get("query"), 100)
        normalized_query = normalize_alias(query)
        context = clean_text(request.data.get("context"), 30)
        event = clean_text(request.data.get("event"), 20)

        if len(normalized_query) < 2:
            return Response(
                {"detail": "Der Suchbegriff ist zu kurz."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if context not in SEARCH_FEEDBACK_CONTEXTS:
            return Response(
                {"detail": "Unbekannter Suchkontext."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if event not in {"search", "selected"}:
            return Response(
                {"detail": "Unbekanntes Suchereignis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result_count = max(0, min(100, int(request.data.get("result_count", 0))))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Die Trefferanzahl ist ungültig."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        selected_product = None
        selected_rank = None
        if event == "selected":
            selected_product = Product.objects.filter(
                pk=request.data.get("product_id")
            ).first()
            if selected_product is None:
                return Response(
                    {"detail": "Das ausgewählte Produkt wurde nicht gefunden."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                selected_rank = max(1, min(100, int(request.data.get("selected_rank", 1))))
            except (TypeError, ValueError):
                selected_rank = 1

        with transaction.atomic():
            metric, _created = IngredientSearchMetric.objects.select_for_update().get_or_create(
                normalized_query=normalized_query,
                context=context,
                defaults={"display_query": query},
            )
            metric.display_query = query
            if event == "search":
                metric.search_count += 1
                metric.last_result_count = result_count
                if result_count == 0:
                    metric.zero_result_count += 1
                    if metric.review_status == "resolved":
                        metric.review_status = "open"
            else:
                metric.selection_count += 1
                metric.last_selected_product = selected_product
                metric.last_selected_rank = selected_rank
                counts = dict(metric.selection_counts or {})
                product_key = str(selected_product.pk)
                counts[product_key] = int(counts.get(product_key, 0)) + 1
                metric.selection_counts = counts
            metric.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


def usda_nutrient_values(item):
    values = {}
    energy_kj = None
    for entry in item.get("foodNutrients") or []:
        nutrient = entry.get("nutrient") or {}
        nutrient_id = entry.get("nutrientId") or nutrient.get("id")
        name = clean_text(entry.get("nutrientName") or nutrient.get("name"), 100).casefold()
        unit = clean_text(entry.get("unitName") or nutrient.get("unitName"), 20).casefold()
        value = decimal_or_none(entry.get("value", entry.get("amount")))
        if value is None:
            continue
        if nutrient_id == 1003 or name == "protein":
            values["protein_per_100g"] = value
        elif nutrient_id == 1004 or name in {"total lipid (fat)", "total fat"}:
            values["fat_per_100g"] = value
        elif nutrient_id == 1005 or name in {"carbohydrate, by difference", "carbohydrate"}:
            values["carbohydrates_per_100g"] = value
        elif nutrient_id == 1079 or name in {"fiber, total dietary", "dietary fiber"}:
            values["fiber_per_100g"] = value
        elif nutrient_id in {1008, 2047, 2048} or name.startswith("energy"):
            if unit == "kcal":
                values["calories_per_100g"] = value
            elif unit == "kj":
                energy_kj = value
    if "calories_per_100g" not in values and energy_kj is not None:
        values["calories_per_100g"] = (energy_kj / Decimal("4.184")).quantize(Decimal("0.01"))
    return values


def usda_payload(item, original_query=""):
    fdc_id = clean_text(item.get("fdcId"), 100)
    description = clean_text(item.get("description"), 150)
    if not fdc_id or not description:
        return None
    name = usda_display_name(original_query, description)
    is_recipe_ingredient, exclusion_reason = recipe_ingredient_status(
        name,
        item.get("foodCategory") or item.get("dataType"),
        "usda",
        fdc_id,
    )
    source_category = clean_text(item.get("foodCategory") or item.get("dataType"), 150)
    canonical_name = canonical_recipe_name(name, "usda", fdc_id)
    shopping_category, is_common_pantry = infer_product_taxonomy(
        name,
        canonical_name,
        source_category,
        "usda",
        fdc_id,
    )
    grams_per_unit = average_unit_weight_grams(canonical_name)
    result = {
        "id": None,
        "name": name,
        "canonical_name": canonical_name,
        "is_recipe_ingredient": is_recipe_ingredient,
        "recipe_exclusion_reason": exclusion_reason,
        "category": source_category,
        "shopping_category": shopping_category,
        "is_common_pantry": is_common_pantry,
        "brand": "USDA FoodData Central",
        "source": "usda",
        "external_id": fdc_id,
        "default_unit": suggested_unit_for_product(name, canonical_name, shopping_category),
        "grams_per_unit": str(grams_per_unit) if grams_per_unit is not None else None,
        "calories_per_100g": None,
        "protein_per_100g": None,
        "carbohydrates_per_100g": None,
        "fat_per_100g": None,
        "fiber_per_100g": None,
        "origin": "usda",
    }
    result.update(usda_nutrient_values(item))
    add_unit_metadata(result)
    result["nutrition_complete"] = nutrition_is_complete(result)
    return result


def search_usda_products(query):
    api_key = settings.USDA_FDC_API_KEY
    if not api_key:
        return []
    response = off_session().post(
        USDA_SEARCH_URL,
        params={"api_key": api_key},
        json={
            "query": usda_query(query),
            "dataType": ["Foundation", "SR Legacy"],
            "pageSize": 12,
        },
        headers=OFF_HEADERS,
        timeout=8,
    )
    response.raise_for_status()
    results = []
    for item in response.json().get("foods", []):
        product = usda_payload(item, query)
        if not product or not product["is_recipe_ingredient"] or not product["nutrition_complete"]:
            continue
        cache.set(f'usda-product:{product["external_id"]}', product, 60 * 60)
        results.append(product)
    return results


def off_payload(item):
    code = clean_text(item.get("code") or item.get("_id"), 100)
    name = clean_name(item.get("product_name_de") or item.get("product_name") or item.get("generic_name_de") or item.get("generic_name"))
    if not code or not name:
        return None
    nutriments = item.get("nutriments") or {}
    canonical_name = canonical_recipe_name(name, "open_food_facts", code)
    is_recipe_ingredient, exclusion_reason = recipe_ingredient_status(
        name,
        item.get("categories"),
        "open_food_facts",
        code,
    )
    source_category = clean_text(item.get("categories"), 150)
    shopping_category, is_common_pantry = infer_product_taxonomy(
        name,
        canonical_name,
        source_category,
        "open_food_facts",
        code,
    )
    grams_per_unit = average_unit_weight_grams(canonical_name)
    package_quantity, package_unit = package_data(item)
    result = {
        "id": None,
        "name": name,
        "canonical_name": canonical_name,
        "is_recipe_ingredient": is_recipe_ingredient,
        "recipe_exclusion_reason": exclusion_reason,
        "category": source_category,
        "shopping_category": shopping_category,
        "is_common_pantry": is_common_pantry,
        "brand": clean_text(item.get("brands"), 150),
        "source": "open_food_facts",
        "external_id": code,
        "default_unit": suggested_unit_for_product(name, canonical_name, shopping_category),
        "package_quantity": package_quantity,
        "package_unit": package_unit,
        "grams_per_unit": str(grams_per_unit) if grams_per_unit is not None else None,
        "calories_per_100g": decimal_or_none(nutriments.get("energy-kcal_100g")),
        "protein_per_100g": decimal_or_none(nutriments.get("proteins_100g")),
        "carbohydrates_per_100g": decimal_or_none(nutriments.get("carbohydrates_100g")),
        "fat_per_100g": decimal_or_none(nutriments.get("fat_100g")),
        "fiber_per_100g": decimal_or_none(nutriments.get("fiber_100g")),
        "origin": "open_food_facts",
    }
    add_unit_metadata(result)
    result["nutrition_complete"] = nutrition_is_complete(result)
    return result


class ProductSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = clean_text(request.query_params.get("q"), 100)
        recipe_only = request.query_params.get("recipe_only") in {"1", "true", "yes"}
        if len(query) < 2:
            return Response([])
        query_definition = definition_for_query(query) if recipe_only else None
        ranking_query = canonical_search_query(query) if recipe_only else query
        preferred_keys = preferred_product_keys(query) if recipe_only else ()
        products = Product.objects.filter(
            source__in=("bls", "open_food_facts", "usda"),
        )
        if recipe_only:
            products = products.filter(
                is_recipe_ingredient=True,
                calories_per_100g__isnull=False,
                protein_per_100g__isnull=False,
                carbohydrates_per_100g__isnull=False,
                fat_per_100g__isnull=False,
                fiber_per_100g__isnull=False,
            )
        catalog_products = products

        if query_definition:
            # Curated aliases such as "Tomaten", "Rinderfond" or "Wallnuss"
            # already resolve to one canonical ingredient. Query indexed canonical/source
            # fields directly instead of joining every alias and running dozens of
            # unindexed contains comparisons across the complete product catalog.
            direct_filter = Q(canonical_name=query_definition.canonical_name)
            for source, external_id in preferred_keys:
                direct_filter |= Q(source=source, external_id=external_id)
            products = products.filter(direct_filter)
            product_limit = 80
        else:
            normalized_query = normalize_alias(ranking_query)
            search_filter = (
                Q(name__icontains=query)
                | Q(canonical_name__icontains=query)
                | Q(aliases__normalized_alias__icontains=normalized_query)
            )
            products = products.filter(search_filter)
            product_limit = 100 if recipe_only else 40

        products = list(
            products.prefetch_related("aliases").distinct()[:product_limit]
        )

        if query_definition and not products:
            fallback_filter = Q()
            for term in {query, query_definition.canonical_name}:
                fallback_filter |= (
                    Q(name__icontains=term)
                    | Q(canonical_name__icontains=term)
                    | Q(aliases__normalized_alias=normalize_alias(term))
                )
            products = list(
                catalog_products
                .filter(fallback_filter)
                .prefetch_related("aliases")
                .distinct()[:100]
            )

        normalized_query = normalize_alias(ranking_query)

        if recipe_only and not products and len(normalized_query) >= 5:
            alias_candidates = ProductAlias.objects.select_related("product").filter(
                normalized_alias__startswith=normalized_query[:2],
                product__source__in=("bls", "open_food_facts", "usda"),
                product__is_recipe_ingredient=True,
                product__calories_per_100g__isnull=False,
                product__protein_per_100g__isnull=False,
                product__carbohydrates_per_100g__isnull=False,
                product__fat_per_100g__isnull=False,
                product__fiber_per_100g__isnull=False,
            )[:2000]
            fuzzy_products = {}
            for alias in alias_candidates:
                score = SequenceMatcher(
                    None,
                    normalized_query,
                    alias.normalized_alias,
                ).ratio()
                if score < 0.76:
                    continue
                current = fuzzy_products.get(alias.product_id)
                if current is None or score > current[0]:
                    fuzzy_products[alias.product_id] = (score, alias.product)
            fuzzy_ids = [
                product_id
                for product_id, _ in sorted(
                    fuzzy_products.items(),
                    key=lambda item: item[1][0],
                    reverse=True,
                )[:100]
            ]
            if fuzzy_ids:
                products = list(
                    Product.objects.filter(id__in=fuzzy_ids).prefetch_related("aliases")
                )

        def relevance(product):
            names = {
                normalize_alias(product.name),
                normalize_alias(product.canonical_name),
                *(alias.normalized_alias for alias in product.aliases.all()),
            }
            exact = normalized_query in names
            prefix = any(name.startswith(normalized_query) for name in names)
            contains = any(normalized_query in name for name in names)
            source_rank = {"bls": 0, "usda": 1, "open_food_facts": 2}.get(product.source, 3)
            generic_rank = 0 if not product.brand or product.source in {"bls", "usda"} else 1
            product_key = (product.source, str(product.external_id or ""))
            preferred_rank = (
                preferred_keys.index(product_key)
                if product_key in preferred_keys
                else len(preferred_keys) + 1
            )
            return (
                0 if exact else 1 if prefix else 2 if contains else 3,
                preferred_rank,
                source_rank,
                generic_rank,
                len(product.canonical_name or product.name),
                product.name.casefold(),
            )

        products = sorted(products, key=relevance)
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
            canonical_name = clean_name(
                item["canonical_name"] if recipe_only else item["name"]
            )
            if (
                query_definition
                and preferred_keys
                and item["source"] == "open_food_facts"
                and normalize_alias(canonical_name)
                != normalize_alias(query_definition.canonical_name)
            ):
                continue
            display_name = canonical_name
            if (
                query_definition
                and normalize_alias(canonical_name)
                == normalize_alias(query_definition.canonical_name)
            ):
                display_name = clean_name(display_name_for_query(query))
            if not display_name:
                continue
            key = (
                normalize_alias(canonical_name)
                if recipe_only
                else f'{item["source"]}:{item["external_id"]}'
            )
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
        if recipe_only:
            preferred_filter = Q()
            preferred_keys = preferred_product_keys(query)
            for source, external_id in preferred_keys:
                preferred_filter |= Q(source=source, external_id=external_id)
            if preferred_keys and Product.objects.filter(
                preferred_filter,
                is_recipe_ingredient=True,
                calories_per_100g__isnull=False,
                protein_per_100g__isnull=False,
                carbohydrates_per_100g__isnull=False,
                fat_per_100g__isnull=False,
                fiber_per_100g__isnull=False,
            ).exists():
                return Response([])
        cache_key = f"external-food-search:v3:{query.casefold()}:{int(recipe_only)}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        items = []
        try:
            response = off_session().get(OFF_SEARCH_URL, params={
                "search_terms": query, "search_simple": 1, "action": "process", "json": 1,
                "page_size": 30, "fields": "code,product_name_de,product_name,generic_name_de,generic_name,categories,brands,nutriments,quantity,product_quantity,product_quantity_unit",
            }, headers=OFF_HEADERS, timeout=8)
            response.raise_for_status()
            items = response.json().get("products", [])
        except (requests.RequestException, ValueError) as error:
            logger.warning("Open Food Facts search failed: %s", error)
        ranking_query = canonical_search_query(query)
        query_definition = definition_for_query(query) if recipe_only else None
        words = query.casefold().split()
        results, seen = [], set()
        for item in items:
            product = off_payload(item)
            if not product or product["external_id"] in seen:
                continue
            if recipe_only and (
                not product["is_recipe_ingredient"]
                or not product["nutrition_complete"]
            ):
                continue
            if query_definition and normalize_alias(product["canonical_name"]) != normalize_alias(
                query_definition.canonical_name
            ):
                continue
            searchable = f'{product["name"]} {product["brand"]}'.casefold()
            alias_match = recipe_only and product["canonical_name"].casefold() == ranking_query.casefold()
            if not alias_match and not all(word in searchable for word in words):
                continue
            seen.add(product["external_id"])
            if recipe_only:
                product["name"] = (
                    display_name_for_query(query)
                    if query_definition
                    else product["canonical_name"]
                )
            results.append(product)
        if recipe_only:
            try:
                results.extend(search_usda_products(query))
            except (requests.RequestException, ValueError) as error:
                logger.warning("USDA FoodData Central search failed: %s", error)

            normalized_query = normalize_alias(ranking_query)
            results.sort(key=lambda product: (
                0 if normalize_alias(product["canonical_name"]) == normalized_query else
                1 if normalize_alias(product["name"]) == normalized_query else
                2 if normalize_alias(product["canonical_name"]).startswith(normalized_query) else
                3 if normalize_alias(product["name"]).startswith(normalized_query) else 4,
                0 if product["source"] == "usda" else 1,
                len(product["name"]),
                product["name"].casefold(),
            ))
            deduplicated = []
            seen_names = set()
            for product in results:
                key = normalize_alias(product["canonical_name"] or product["name"])
                if key in seen_names:
                    continue
                seen_names.add(key)
                deduplicated.append(product)
            results = deduplicated
        results = results[:10]
        cache.set(cache_key, results, 60 * 15)
        return Response(results)


class SaveExternalProductAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source = request.data.get("source")
        external_id = clean_text(request.data.get("external_id"), 100)
        if source not in {"open_food_facts", "usda"} or not external_id:
            return Response({"detail": "Ungültiger externer Produktverweis."}, status=status.HTTP_400_BAD_REQUEST)
        existing = Product.objects.filter(source=source, external_id=external_id).first()
        if existing:
            return Response(ProductSerializer(existing).data)
        try:
            if source == "open_food_facts":
                response = requests.get(OFF_PRODUCT_URL.format(code=external_id), params={"fields": "code,product_name_de,product_name,generic_name_de,generic_name,categories,brands,nutriments,quantity,product_quantity,product_quantity_unit"}, headers=OFF_HEADERS, timeout=8)
                response.raise_for_status()
                body = response.json()
                product_data = off_payload(body.get("product") or {}) if body.get("status") == 1 else None
            else:
                product_data = cache.get(f"usda-product:{external_id}")
                if product_data is None:
                    response = off_session().get(
                        USDA_PRODUCT_URL.format(fdc_id=external_id),
                        params={"api_key": settings.USDA_FDC_API_KEY},
                        headers=OFF_HEADERS,
                        timeout=8,
                    )
                    response.raise_for_status()
                    product_data = usda_payload(response.json())
        except (requests.RequestException, ValueError) as error:
            logger.warning("External product lookup failed: %s", error)
            return Response({"detail": "Das externe Produkt konnte nicht geprüft werden."}, status=status.HTTP_502_BAD_GATEWAY)
        if not product_data or product_data["external_id"] != external_id:
            return Response({"detail": "Das externe Produkt existiert nicht mehr."}, status=status.HTTP_404_NOT_FOUND)
        if source == "usda" and (
            not product_data["is_recipe_ingredient"]
            or not nutrition_is_complete(product_data)
        ):
            return Response(
                {"detail": "Für diese Zutat sind keine vollständigen, geprüften Nährwerte verfügbar."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        defaults = {
            key: value
            for key, value in product_data.items()
            if key not in {
                "id", "origin", "source", "external_id", "grams_per_unit", "grams_per_ml",
                "unit_conversions", "available_units",
            }
        }
        defaults.pop("nutrition_complete", None)
        with transaction.atomic():
            product, created = Product.objects.get_or_create(source=source, external_id=external_id, defaults=defaults)
            sync_curated_unit_conversion(product)
            replace_product_aliases(product)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
