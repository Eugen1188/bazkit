import math
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from statistics import median

import requests
from django.conf import settings
from django.core.cache import cache


OPEN_PRICES_URL = "https://prices.openfoodfacts.org/api/v1/prices"
OPEN_PRICES_HEADERS = {
    "User-Agent": "Bazkit/1.0 (price-estimation; contact: admin@bazkit.local)"
}


def decimal_or_none(value):
    try:
        result = Decimal(str(value))
        return result if result > 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def normalized_amount(value, unit):
    amount = decimal_or_none(value)
    normalized_unit = str(unit or "").strip().casefold()
    factors = {
        "g": ("mass", Decimal("1")),
        "kg": ("mass", Decimal("1000")),
        "ml": ("volume", Decimal("1")),
        "l": ("volume", Decimal("1000")),
        "liter": ("volume", Decimal("1000")),
    }
    if amount is None or normalized_unit not in factors:
        return None
    dimension, factor = factors[normalized_unit]
    return dimension, amount * factor


def scaled_price(package_price, package_amount, package_unit, quantity, unit, mode):
    requested = normalized_amount(quantity, unit)
    package = normalized_amount(package_amount, package_unit)

    if requested and package and requested[0] == package[0]:
        ratio = requested[1] / package[1]
        if mode == "purchase":
            ratio = Decimal(math.ceil(ratio))
        return package_price * ratio

    if mode == "purchase" and str(unit or "").strip().casefold() in {
        "stück", "stueck", "packung", "dose", "glas", "becher", "flasche"
    }:
        count = decimal_or_none(quantity) or Decimal("1")
        return package_price * Decimal(math.ceil(count))

    return package_price if mode == "purchase" else None


def unavailable(message):
    return {
        "available": False,
        "estimated_price": None,
        "message": message,
    }


def estimate_open_price(barcode, quantity, unit, mode="purchase"):
    barcode = str(barcode or "").strip()
    if not barcode:
        return unavailable("Für dieses Produkt ist kein Barcode hinterlegt.")

    country_code = getattr(settings, "OPEN_PRICES_COUNTRY_CODE", "DE").upper()
    lookback_days = int(getattr(settings, "OPEN_PRICES_LOOKBACK_DAYS", 730))
    start_date = date.today() - timedelta(days=lookback_days)
    cache_key = f"open-prices:{barcode}:{country_code}:{start_date.isoformat()}"
    items = cache.get(cache_key)

    if items is None:
        try:
            response = requests.get(
                OPEN_PRICES_URL,
                params={
                    "product_code": barcode,
                    "currency": "EUR",
                    "date__gte": start_date.isoformat(),
                    "order_by": "-date",
                    "page_size": 100,
                },
                headers=OPEN_PRICES_HEADERS,
                timeout=8,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            cache.set(cache_key, items, 6 * 60 * 60)
        except (requests.RequestException, ValueError):
            return unavailable("Die Preissuche ist momentan nicht erreichbar.")

    valid_items = []

    for item in items:
        location = item.get("location") or {}
        if item.get("duplicate_of") is not None or item.get("price_is_discounted"):
            continue
        if item.get("price_per") not in (None, "", "UNIT"):
            continue
        price = decimal_or_none(item.get("price"))
        store_id = item.get("location_id")
        if price is None or store_id is None:
            continue
        item["_country_code"] = str(location.get("osm_address_country_code") or "").upper()
        valid_items.append(item)

    domestic_items = [item for item in valid_items if item["_country_code"] == country_code]
    selected_items = domestic_items or valid_items
    market_label = "Deutschland" if domestic_items else "Europa (EUR)"

    latest_by_store = {}
    for item in selected_items:
        store_id = item.get("location_id")
        if store_id not in latest_by_store:
            latest_by_store[store_id] = item

    observations = list(latest_by_store.values())
    prices = [decimal_or_none(item.get("price")) for item in observations]
    prices = [price for price in prices if price is not None]
    if not prices:
        return unavailable("Für dieses Produkt wurden keine passenden Open-Prices-Marktdaten gefunden.")

    package_amount = None
    package_unit = ""
    for item in observations:
        product = item.get("product") or {}
        package_amount = decimal_or_none(product.get("product_quantity"))
        package_unit = str(product.get("product_quantity_unit") or "").strip()
        if package_amount is not None and package_unit:
            break

    center = Decimal(str(median(prices)))
    filtered = [price for price in prices if center * Decimal("0.5") <= price <= center * Decimal("2")]
    if filtered:
        prices = filtered
        center = Decimal(str(median(prices)))

    package_amount = package_amount or Decimal("1")
    estimated = scaled_price(center, package_amount, package_unit, quantity, unit, mode)
    if estimated is None:
        return unavailable("Die gewählte Menge kann nicht sicher auf die Packungsgröße umgerechnet werden.")

    scaled_min = scaled_price(min(prices), package_amount, package_unit, quantity, unit, mode)
    scaled_max = scaled_price(max(prices), package_amount, package_unit, quantity, unit, mode)
    newest_date = max((str(item.get("date") or "") for item in observations), default="")
    sample_count = len(prices)

    return {
        "available": True,
        "estimated_price": estimated.quantize(Decimal("0.01")),
        "package_price": center.quantize(Decimal("0.01")),
        "package_quantity": package_amount,
        "package_unit": package_unit,
        "price_currency": "EUR",
        "price_date": newest_date or None,
        "price_store": market_label,
        "price_sample_count": sample_count,
        "price_min": scaled_min.quantize(Decimal("0.01")) if scaled_min is not None else None,
        "price_max": scaled_max.quantize(Decimal("0.01")) if scaled_max is not None else None,
        "confidence": (
            "high" if domestic_items and sample_count >= 5
            else "medium" if sample_count >= 3
            else "low"
        ),
        "price_source": "open_prices",
        "message": (
            "Median der neuesten deutschen Preise je Geschäft."
            if domestic_items
            else "Keine deutschen Treffer: Median verfügbarer europäischer EUR-Preise."
        ),
    }
