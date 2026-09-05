import json
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from openai import OpenAI

from products.catalog import ingredient_quantity_grams, recipe_ingredient_status
from products.ingredient_catalog import INGREDIENT_DEFINITIONS, normalize_alias
from products.models import Product
from products.serializers import ProductSerializer


class RecipeGenerationError(Exception):
    pass


NUTRITION_FIELDS = (
    ("calories", "calories_per_100g"),
    ("protein", "protein_per_100g"),
    ("carbohydrates", "carbohydrates_per_100g"),
    ("fat", "fat_per_100g"),
    ("fiber", "fiber_per_100g"),
)
AI_UNITS = (
    "g", "kg", "ml", "Liter", "Stück", "Stange", "Kopf", "Blatt",
    "Kugel", "Würfel", "Bund", "Zehe", "Scheibe", "Tasse", "EL", "TL",
    "Prise", "Packung", "Dose", "Glas", "Becher",
)
UNIT_ALIASES = {
    "l": "Liter",
    "liter": "Liter",
    "stueck": "Stück",
    "stuck": "Stück",
    "stk": "Stück",
    "essloeffel": "EL",
    "essloffel": "EL",
    "el": "EL",
    "teeloeffel": "TL",
    "teeloffel": "TL",
    "tl": "TL",
}


def nutrition_ready_products():
    return Product.objects.filter(
        source__in=("bls", "open_food_facts", "usda"),
        is_recipe_ingredient=True,
        calories_per_100g__isnull=False,
        protein_per_100g__isnull=False,
        carbohydrates_per_100g__isnull=False,
        fat_per_100g__isnull=False,
        fiber_per_100g__isnull=False,
    )


def product_available_units(product):
    return list(ProductSerializer(product).data.get("available_units") or ["g"])


def build_ai_ingredient_catalog(data, limit=450):
    """Return a compact, nutrition-ready product catalog for the model."""
    curated_names = {
        normalize_alias(definition.canonical_name)
        for definition in INGREDIENT_DEFINITIONS
    }
    products = []
    for product in nutrition_ready_products().order_by("canonical_name", "name", "id"):
        allowed, _reason = recipe_ingredient_status(
            product.name,
            product.category,
            product.source,
            product.external_id,
        )
        if allowed:
            products.append(product)

    source_rank = {"bls": 0, "usda": 1, "open_food_facts": 2}
    products.sort(key=lambda product: (
        0 if normalize_alias(product.canonical_name or product.name) in curated_names else 1,
        0 if product.is_common_pantry else 1,
        source_rank.get(product.source, 3),
        0 if not product.brand else 1,
        len(product.canonical_name or product.name),
        product.id,
    ))

    selected = {}
    for product in products:
        key = normalize_alias(product.canonical_name or product.name)
        if key and key not in selected:
            selected[key] = product
        if len(selected) >= limit:
            break

    # Explicitly mentioned pantry ingredients should not disappear merely
    # because the compact general catalog reached its size limit.
    mentioned = re.split(r"[,;\n]+", data.get("available_ingredients", ""))
    products_by_name = {
        normalize_alias(product.canonical_name or product.name): product
        for product in products
    }
    for value in mentioned:
        key = normalize_alias(value)
        if key in products_by_name:
            selected[key] = products_by_name[key]

    rows = []
    for product in selected.values():
        rows.append({
            "product": product,
            "id": product.id,
            "name": product.canonical_name or product.name,
            "units": product_available_units(product),
        })
    return rows


def normalize_generated_unit(value):
    raw = str(value or "").strip()
    normalized = normalize_alias(raw).replace(" ", "")
    return UNIT_ALIASES.get(normalized, raw)


def enrich_generated_recipe(result, data, catalog_rows):
    products = {row["id"]: row for row in catalog_rows}
    ingredients = []
    totals = {target: Decimal("0") for target, _source in NUTRITION_FIELDS}

    for item in result.get("ingredients") or []:
        product_id = item.get("product_id")
        row = products.get(product_id)
        if row is None:
            raise RecipeGenerationError(
                "Die KI hat eine Zutat außerhalb des geprüften Katalogs gewählt. "
                "Bitte generiere das Rezept erneut."
            )
        try:
            quantity = Decimal(str(item.get("quantity")))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise RecipeGenerationError("Eine Zutatenmenge ist ungültig.") from error
        if quantity <= 0:
            raise RecipeGenerationError("Alle Zutaten benötigen eine positive Menge.")

        unit = normalize_generated_unit(item.get("unit"))
        available_units = row["units"]
        unit = next(
            (candidate for candidate in available_units if candidate.casefold() == unit.casefold()),
            unit,
        )
        if unit not in available_units:
            raise RecipeGenerationError(
                f'Für „{row["name"]}“ ist die Einheit „{unit}“ nicht sicher umrechenbar. '
                "Bitte generiere das Rezept erneut."
            )

        product = row["product"]
        grams = ingredient_quantity_grams(
            product.canonical_name or product.name,
            quantity,
            unit,
            product=product,
        )
        if grams is None:
            raise RecipeGenerationError(
                f'Für „{row["name"]}“ fehlt eine belastbare Umrechnung für „{unit}“. '
                "Bitte generiere das Rezept erneut."
            )

        for target, source in NUTRITION_FIELDS:
            totals[target] += getattr(product, source) * grams / Decimal("100")
        ingredients.append({
            "product": product.id,
            "product_detail": ProductSerializer(product).data,
            "name": row["name"],
            "quantity": float(quantity),
            "unit": unit,
        })

    if not ingredients:
        raise RecipeGenerationError("Die KI hat keine berechenbaren Zutaten geliefert.")

    servings = max(int(data.get("servings") or 1), 1)
    result["servings"] = servings
    result["category"] = data.get("category", "dinner")
    result["preparation_time"] = min(
        max(int(result.get("preparation_time") or 1), 1),
        int(data.get("max_time") or 240),
    )
    result["ingredients"] = ingredients
    result["nutrition"] = {
        field: float((value / Decimal(servings)).quantize(Decimal("0.01")))
        for field, value in totals.items()
    }
    result["nutrition_complete"] = True
    result["nutrition_source"] = "Geprüfter Produktkatalog"
    return result


def generate_recipe_with_ai(data):
    if not settings.OPENAI_API_KEY:
        raise RecipeGenerationError(
            "OPENAI_API_KEY ist nicht konfiguriert."
        )

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    catalog_rows = build_ai_ingredient_catalog(data)
    if not catalog_rows:
        raise RecipeGenerationError(
            "Der geprüfte Zutatenkatalog enthält noch keine vollständig berechenbaren Zutaten."
        )

    prompt = build_recipe_prompt(data, catalog_rows)

    try:
        response = client.responses.create(
            model=settings.OPENAI_RECIPE_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein Kochassistent für eine "
                        "deutsche Rezept-App. "
                        "Erzeuge realistische, gut kochbare Rezepte. "
                        "Antworte ausschließlich mit gültigem JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "recipe",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "description": {
                                "type": "string"
                            },
                            "servings": {
                                "type": "integer"
                            },
                            "preparation_time": {
                                "type": "integer"
                            },
                            "category": {
                                "type": "string",
                                "enum": [
                                    "breakfast",
                                    "lunch",
                                    "dinner",
                                    "snack",
                                    "dessert",
                                    "other"
                                ]
                            },
                            "ingredients": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "product_id": {
                                            "type": "integer",
                                            "enum": [row["id"] for row in catalog_rows]
                                        },
                                        "quantity": {
                                            "type": "number"
                                        },
                                        "unit": {
                                            "type": "string",
                                            "enum": list(AI_UNITS)
                                        }
                                    },
                                    "required": [
                                        "product_id",
                                        "quantity",
                                        "unit"
                                    ],
                                    "additionalProperties": False
                                }
                            },
                            "steps": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "notes": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "name",
                            "description",
                            "servings",
                            "preparation_time",
                            "category",
                            "ingredients",
                            "steps",
                            "notes"
                        ],
                        "additionalProperties": False
                    }
                }
            }
        )

        result = json.loads(
            response.output_text
        )

        return enrich_generated_recipe(result, data, catalog_rows)

    except RecipeGenerationError:
        raise
    except Exception as error:
        raise RecipeGenerationError(
            "Der KI-Dienst ist momentan nicht erreichbar. Bitte versuche es gleich erneut."
        ) from error


def build_recipe_prompt(data, catalog_rows):
    idea = data.get(
        "idea",
        ""
    ).strip()

    available_ingredients = data.get(
        "available_ingredients",
        ""
    ).strip()

    avoid_ingredients = data.get(
        "avoid_ingredients",
        ""
    ).strip()

    diet = data.get(
        "diet",
        "none"
    )

    servings = data.get(
        "servings",
        2
    )

    max_time = data.get(
        "max_time",
        30
    )

    category = data.get(
        "category",
        "dinner"
    )

    dietary_preferences = ", ".join(
        data.get("dietary_preferences") or []
    )

    favorite_cuisines = ", ".join(
        data.get("favorite_cuisines") or []
    )

    ingredient_catalog = "\n".join(
        f'- ID {row["id"]}: {row["name"]} | erlaubte Einheiten: {", ".join(row["units"])}'
        for row in catalog_rows
    )

    return f"""
Erstelle ein vollständiges Rezept.

Wunsch oder Idee:
{idea or "Keine konkrete Vorgabe"}

Vorhandene Zutaten:
{available_ingredients or "Keine angegeben"}

Zu vermeidende Zutaten:
{avoid_ingredients or "Keine"}

Ernährungsweise:
{diet}

Weitere persönliche Ernährungspräferenzen:
{dietary_preferences or "Keine"}

Bevorzugte Küchenrichtungen:
{favorite_cuisines or "Keine Präferenz"}

Portionen:
{servings}

Maximale Zubereitungszeit:
{max_time} Minuten

Gewünschte Kategorie:
{category}

Regeln:
- Verwende ausschließlich Zutaten aus dem folgenden geprüften Katalog.
- Gib für jede Zutat exakt die zugehörige product_id aus.
- Verwende für jede Zutat ausschließlich eine bei ihr aufgeführte Einheit.
- Jede Zutat braucht eine positive, konkrete Menge; null ist nicht erlaubt.
- Mengen müssen zu den Portionen passen.
- Verwende metrische Einheiten.
- Verwende bevorzugt g, kg, ml, Liter, Stück, Stange, Kopf, Blatt,
  Kugel, Würfel, Bund, Zehe, Scheibe, Tasse, EL, TL oder Prise.
- Nutze Küchenmaße nur dann, wenn sie zur jeweiligen Zutat passen.
- Schritte sollen konkret und verständlich sein.
- Das Rezept soll realistisch kochbar sein.
- Wenn vorhandene Zutaten angegeben wurden,
  verwende möglichst viele davon.
- Vermeide ausdrücklich ausgeschlossene Zutaten.
- preparation_time darf maximal ungefähr
  der angegebenen Zeit entsprechen.

Geprüfter Zutatenkatalog mit vollständigen Nährwerten:
{ingredient_catalog}
"""
