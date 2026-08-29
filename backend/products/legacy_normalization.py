import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


PACKAGE_SUFFIX = re.compile(
    r"^(?P<name>.+?)\s+(?:(?P<count>\d+)\s*[x×]\s*)?"
    r"(?P<amount>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>mg|g|kg|ml|cl|dl|l|liter)"
    r"(?:\s+(?:packung|flasche|dose|beutel|glas))?\s*$",
    re.I,
)


@dataclass(frozen=True)
class LegacyProductName:
    original_name: str
    normalized_name: str
    package_quantity: Decimal | None = None
    package_unit: str = ""
    package_count: int = 1


def parse_legacy_product_name(value):
    original = re.sub(r"\s+", " ", str(value or "")).strip()
    match = PACKAGE_SUFFIX.match(original)
    if not match:
        return LegacyProductName(original, original)
    try:
        amount = Decimal(match.group("amount").replace(",", "."))
    except (InvalidOperation, ValueError):
        return LegacyProductName(original, original)
    name = match.group("name").strip(" ,-–")
    if len(name) < 2 or amount <= 0:
        return LegacyProductName(original, original)
    return LegacyProductName(
        original_name=original,
        normalized_name=name,
        package_quantity=amount,
        package_unit=match.group("unit").casefold().replace("liter", "l"),
        package_count=int(match.group("count") or 1),
    )
