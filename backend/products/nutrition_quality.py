import re
from decimal import Decimal


NUTRIENT_FIELDS = (
    "calories_per_100g",
    "protein_per_100g",
    "carbohydrates_per_100g",
    "fat_per_100g",
    "fiber_per_100g",
)

PURE_SWEETENER = re.compile(
    r"^(?:honig|zucker|glukosesirup|ahornsirup|melasse|xylit|mannit|"
    r"tafelsüße|süßstoff)",
    re.I,
)
PURE_FAT = re.compile(
    r"(?:öl|oel|fett|butter|schmalz|margarine|streichfett)|"
    r"^(?:kakaobutter|sheabutter|bratöl|frittieröl)",
    re.I,
)
DAIRY_WITHOUT_FIBER = re.compile(
    r"^(?:feta|gorgonzola|mozzarella|provolone|mascarpone|ricotta|"
    r"parmesan|parmigiano|"
    r"frischkäse|schnittkäse|weichkäse|hartkäse|sauermilchkäse|"
    r"salzlakenkäse|sauerrahm|creme fraiche|crème fraîche|butter)",
    re.I,
)
ALCOHOLIC_DRINK = re.compile(
    r"\b(?:bier|wein|sekt|schaumwein|most)\b|^(?:pilsner|export hell)",
    re.I,
)
TEA_DRINK = re.compile(r"tee \(getränk\)|kaffee \(getränk\)", re.I)
VINEGAR = re.compile(r"(?:essig|vinegar)$", re.I)


def nutrition_is_complete(values):
    return all(values.get(field) is not None for field in NUTRIENT_FIELDS)


def apply_safe_zero_defaults(name, source, external_id, values):
    """Fill only biologically structural zeroes; never estimate non-zero values."""
    result = dict(values)
    if source != "bls":
        return result

    code = str(external_id or "").upper()
    product_name = str(name or "").strip()
    group = code[:1]
    zero = Decimal("0")

    # Unverarbeitete tierische Lebensmittel enthalten keine Ballaststoffe.
    if result.get("fiber_per_100g") is None and (
        group in {"T", "U", "V", "W"}
        or code.startswith(("E11", "E12"))
        or DAIRY_WITHOUT_FIBER.search(product_name)
    ):
        result["fiber_per_100g"] = zero

    # Reine Fette/Öle enthalten kein Protein und keine Ballaststoffe.
    if group == "Q" and PURE_FAT.search(product_name):
        if result.get("protein_per_100g") is None:
            result["protein_per_100g"] = zero
        if result.get("fiber_per_100g") is None:
            result["fiber_per_100g"] = zero

    # Reine Zucker und Sirupe enthalten keine Proteine, Fette oder Fasern.
    if PURE_SWEETENER.search(product_name):
        for field in ("protein_per_100g", "fat_per_100g", "fiber_per_100g"):
            if result.get(field) is None:
                result[field] = zero

    # Ungezuckerte Aufgüsse sowie Wein/Bier enthalten kein Fett; bei reinen
    # Teeaufgüssen ist auch fehlendes Protein tatsächlich null.
    if ALCOHOLIC_DRINK.search(product_name) and result.get("fat_per_100g") is None:
        result["fat_per_100g"] = zero
    if TEA_DRINK.search(product_name):
        for field in ("protein_per_100g", "fat_per_100g"):
            if result.get(field) is None:
                result[field] = zero

    # Reine Zusatzstoffe und Essige liefern kein Fett; fehlende andere Werte
    # werden bewusst nicht erfunden.
    if group == "R" and result.get("fat_per_100g") is None:
        result["fat_per_100g"] = zero
    if VINEGAR.search(product_name) and result.get("fiber_per_100g") is None:
        result["fiber_per_100g"] = zero

    return result
