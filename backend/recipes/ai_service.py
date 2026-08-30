import json

from django.conf import settings
from openai import OpenAI


class RecipeGenerationError(Exception):
    pass


def generate_recipe_with_ai(data):
    if not settings.OPENAI_API_KEY:
        raise RecipeGenerationError(
            "OPENAI_API_KEY ist nicht konfiguriert."
        )

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    prompt = build_recipe_prompt(data)

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
                                        "name": {
                                            "type": "string"
                                        },
                                        "quantity": {
                                            "type": [
                                                "number",
                                                "null"
                                            ]
                                        },
                                        "unit": {
                                            "type": "string"
                                        }
                                    },
                                    "required": [
                                        "name",
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

        return result

    except Exception as error:
        raise RecipeGenerationError(
            str(error)
        ) from error


def build_recipe_prompt(data):
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

Portionen:
{servings}

Maximale Zubereitungszeit:
{max_time} Minuten

Gewünschte Kategorie:
{category}

Regeln:
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
"""
