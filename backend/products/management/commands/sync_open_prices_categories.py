import gzip
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import median

import requests
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from products.catalog import CATEGORY_INGREDIENT_NAMES
from products.models import IngredientPriceReference


LOCATIONS_URL = "https://prices.openfoodfacts.org/data/locations.jsonl.gz"
PRICES_URL = "https://prices.openfoodfacts.org/data/prices.jsonl.gz"
HEADERS = {"User-Agent": "Bazkit/1.0 (ingredient-price-sync; contact: admin@bazkit.local)"}


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] * Decimal(str(upper - position)) + values[upper] * Decimal(str(position - lower))


def json_lines(url):
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=(10, 120))
        response.raise_for_status()
    except requests.RequestException as error:
        raise CommandError(f"Open-Prices-Export konnte nicht geladen werden: {error}") from error
    response.raw.decode_content = False
    try:
        with gzip.GzipFile(fileobj=response.raw) as archive:
            for raw_line in archive:
                if raw_line.strip():
                    yield json.loads(raw_line.decode("utf-8"))
    finally:
        response.close()


class Command(BaseCommand):
    help = "Synchronisiert belastbare deutsche Open-Prices-Kategoriepreise für Rezeptzutaten."

    def add_arguments(self, parser):
        parser.add_argument("--lookback-days", type=int, default=730)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        cutoff = date.today() - timedelta(days=max(30, options["lookback_days"]))
        location_country = {
            item["id"]: str(item.get("osm_address_country_code") or "").upper()
            for item in json_lines(LOCATIONS_URL)
        }
        grouped = defaultdict(list)
        for item in json_lines(PRICES_URL):
            category_tag = item.get("category_tag")
            if (
                item.get("type") != "CATEGORY"
                or category_tag not in CATEGORY_INGREDIENT_NAMES
                or location_country.get(item.get("location_id")) != "DE"
                or item.get("duplicate_of") is not None
                or item.get("price_is_discounted")
            ):
                continue
            try:
                observed_on = date.fromisoformat(item.get("date") or "")
                price = Decimal(str(item.get("price")))
            except (TypeError, ValueError, ArithmeticError):
                continue
            basis = {"KILOGRAM": "kg", "UNIT": "unit"}.get(item.get("price_per"))
            if observed_on < cutoff or price <= 0 or price > Decimal("500") or basis is None:
                continue
            grouped[(category_tag, basis)].append({
                "price": price,
                "date": observed_on,
                "location_id": item.get("location_id"),
            })

        references = []
        for (category_tag, basis), observations in grouped.items():
            values = [item["price"] for item in observations]
            p25 = percentile(values, 0.25)
            p75 = percentile(values, 0.75)
            spread = p75 - p25 if p25 is not None and p75 is not None else Decimal("0")
            filtered = [
                value for value in values
                if not spread or p25 - Decimal("1.5") * spread <= value <= p75 + Decimal("1.5") * spread
            ]
            location_count = len({item["location_id"] for item in observations if item["location_id"] is not None})
            observation_count = len(filtered)
            confidence = (
                "high" if observation_count >= 10 and location_count >= 3
                else "medium" if observation_count >= 3
                else "low"
            )
            references.append({
                "canonical_name": CATEGORY_INGREDIENT_NAMES[category_tag],
                "category_tag": category_tag,
                "basis": basis,
                "median_price": Decimal(str(median(filtered))).quantize(Decimal("0.01")),
                "price_min": percentile(filtered, 0.25).quantize(Decimal("0.01")),
                "price_max": percentile(filtered, 0.75).quantize(Decimal("0.01")),
                "currency": "EUR",
                "region": "DE",
                "observation_count": observation_count,
                "location_count": location_count,
                "newest_price_date": max(item["date"] for item in observations),
                "confidence": confidence,
                "source": "open_prices_category",
                # Auch eine einzelne deutsche Beobachtung ist als grobe
                # Schätzung hilfreicher als gar kein Preis. Die Konfidenz und
                # Stichprobengröße bleiben für die transparente Anzeige erhalten.
                "is_active": observation_count >= 1 and location_count >= 1,
            })

        active_count = sum(1 for item in references if item["is_active"])
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(
                f"Testlauf: {len(references)} Referenzen erkannt, davon {active_count} produktiv freigegeben."
            ))
            return

        with transaction.atomic():
            IngredientPriceReference.objects.filter(source="open_prices_category").update(is_active=False)
            for item in references:
                lookup = {
                    "canonical_name": item.pop("canonical_name"),
                    "category_tag": item.pop("category_tag"),
                    "basis": item.pop("basis"),
                    "region": item.pop("region"),
                }
                IngredientPriceReference.objects.update_or_create(**lookup, defaults=item)

        self.stdout.write(self.style.SUCCESS(
            f"{len(references)} Preisreferenzen synchronisiert; {active_count} sind produktiv freigegeben."
        ))
